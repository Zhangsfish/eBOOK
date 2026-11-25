package cn.zhangsfish.ebook;

import android.app.*;
import android.content.*;
import android.media.*;
import android.media.session.*;
import android.os.*;
import android.speech.tts.*;
import cn.zhangsfish.ebook.core.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

/** System TTS only. Actual callbacks own the separate, durable listening cursor. */
public final class SpeechService extends Service {
    public static final String PLAY="play", READ="read", PAUSE="pause", RESUME="resume", STOP="stop", NEXT="next", PREVIOUS="previous";
    private static final String CHANNEL="ebook_speech";
    private static final int NOTIFICATION=17;
    public enum State { INITIALIZING, READY, PLAYING, PAUSED, STOPPED, COMPLETE, MISSING_VOICE, ERROR }
    public interface Listener { void changed(); }
    public final class LocalBinder extends Binder { public SpeechService service(){return SpeechService.this;} }
    private final LocalBinder binder=new LocalBinder();
    private final Handler main=new Handler(Looper.getMainLooper());
    private final List<Listener>listeners=new ArrayList<>();
    private final ExecutorService loader=Executors.newSingleThreadExecutor();
    private LibraryStore store;
    private TextToSpeech tts;
    private int engineGeneration,loadGeneration,sequence;
    private final List<Voice>voices=new ArrayList<>();
    private List<TextToSpeech.EngineInfo>engines=new ArrayList<>();
    private State state=State.INITIALIZING;
    private String message="正在查询系统离线语音…",bookId="",activeUtterance="",voiceName="";
    private BookDocument doc;
    private int block,offset,chunkStart,chunkEnd;
    private long lastRangeSave;
    private boolean engineReady,foreground,resumeAfterFocus,destroyed;
    private MediaSession media;
    private AudioManager audio;
    private AudioFocusRequest focus;
    private PowerManager.WakeLock wake;

    private final BroadcastReceiver noisy=new BroadcastReceiver(){
        @Override public void onReceive(Context c,Intent i){if(state==State.PLAYING)pause(false,"耳机已断开，朗读已暂停。");}
    };
    @Override public void onCreate(){
        super.onCreate();store=new LibraryStore(this);audio=(AudioManager)getSystemService(AUDIO_SERVICE);
        AudioAttributes attributes=new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build();
        focus=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN).setAudioAttributes(attributes)
            .setWillPauseWhenDucked(true).setOnAudioFocusChangeListener(change->{
                if(change==AudioManager.AUDIOFOCUS_GAIN){if(resumeAfterFocus&&state==State.PAUSED){resumeAfterFocus=false;play();}}
                else if(state==State.PLAYING){boolean transientLoss=change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT||change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK;pause(transientLoss,"其他音频正在使用声音，朗读已暂停。");}
            },main).build();
        wake=((PowerManager)getSystemService(POWER_SERVICE)).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK,getPackageName()+":speech");wake.setReferenceCounted(false);
        media=new MediaSession(this,"eBOOK");media.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS|MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS);
        media.setMediaButtonReceiver(PendingIntent.getBroadcast(this,0,new Intent(this,MediaButtons.class).setAction(Intent.ACTION_MEDIA_BUTTON),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE));
        media.setCallback(new MediaSession.Callback(){
            @Override public void onPlay(){promote();play();}
            @Override public void onPause(){pause(false,"已暂停");}
            @Override public void onStop(){stopPlayback();}
            @Override public void onSkipToNext(){navigateChapter(1);}
            @Override public void onSkipToPrevious(){navigateChapter(-1);}
        },main);
        NotificationChannel channel=new NotificationChannel(CHANNEL,"听书播放控制",NotificationManager.IMPORTANCE_LOW);channel.setSound(null,null);
        ((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).createNotificationChannel(channel);
        if(Build.VERSION.SDK_INT>=33)registerReceiver(noisy,new IntentFilter(AudioManager.ACTION_AUDIO_BECOMING_NOISY),Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(noisy,new IntentFilter(AudioManager.ACTION_AUDIO_BECOMING_NOISY));
        initializeEngine();
    }
    @Override public IBinder onBind(Intent intent){return binder;}
    public void addListener(Listener listener){if(!listeners.contains(listener))listeners.add(listener);listener.changed();}
    public void removeListener(Listener listener){listeners.remove(listener);}
    public State state(){return state;}
    public String message(){return message;}
    public String bookId(){return bookId;}
    public String voiceName(){return voiceName;}
    public List<Voice>voices(){return new ArrayList<>(voices);}
    public List<TextToSpeech.EngineInfo>engines(){return new ArrayList<>(engines);}
    public boolean available(){return engineReady&&!voices.isEmpty();}
    public BookDocument.Position position(){return new BookDocument.Position(block,offset);}

    public void initializeEngine(){
        pause(false,"正在重新查询离线声音…");engineReady=false;voices.clear();voiceName="";state=State.INITIALIZING;
        int token=++engineGeneration;if(tts!=null){tts.shutdown();tts=null;}
        String selected=store.preferences.getString("tts_engine","");
        TextToSpeech.OnInitListener callback=result->main.post(()->{
            if(destroyed||token!=engineGeneration||tts==null)return;
            engines=tts.getEngines();
            if(result!=TextToSpeech.SUCCESS){missing("系统朗读引擎不可用。阅读仍可使用；请检查系统文字转语音设置。");return;}
            // Never call setLanguage: some engines use it to fall back to a network voice.
            Set<Voice>catalog=tts.getVoices();
            if(catalog!=null)for(Voice voice:catalog){
                Set<String>features=voice.getFeatures();
                if(voice.getLocale()!=null&&voice.getLocale().getLanguage().equals("zh")&&!voice.isNetworkConnectionRequired()
                        &&(features==null||!features.contains(TextToSpeech.Engine.KEY_FEATURE_NOT_INSTALLED)))voices.add(voice);
            }
            voices.sort((a,b)->{
                int aa=a.getLocale().getCountry().equals("CN")?1:0,bb=b.getLocale().getCountry().equals("CN")?1:0;
                if(aa!=bb)return Integer.compare(bb,aa);int quality=Integer.compare(b.getQuality(),a.getQuality());return quality!=0?quality:a.getName().compareTo(b.getName());
            });
            if(voices.isEmpty()){missing("当前引擎未报告已安装的中文离线声音。请打开系统设置安装或切换本机声音；不会改用云端朗读。");return;}
            String wanted=store.preferences.getString("tts_voice","");Voice chosen=voices.get(0);for(Voice voice:voices)if(voice.getName().equals(wanted))chosen=voice;
            if(!selectVoice(chosen)){missing("系统无法启用所选中文离线声音，请检查语音数据。");return;}
            tts.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build());
            tts.setOnUtteranceProgressListener(progress);
            engineReady=true;state=State.READY;message="已就绪 · "+voiceName;publish();
        });
        tts=selected.isEmpty()?new TextToSpeech(this,callback):new TextToSpeech(this,callback,selected);publish();
    }
    private boolean selectVoice(Voice voice){
        if(tts==null||voice.isNetworkConnectionRequired()||tts.setVoice(voice)!=TextToSpeech.SUCCESS)return false;
        Voice actual=tts.getVoice();if(actual==null||actual.isNetworkConnectionRequired()||!actual.getName().equals(voice.getName()))return false;
        voiceName=voice.getName();store.preferences.edit().putString("tts_voice",voiceName).apply();return true;
    }
    public void changeVoice(String name){
        boolean wasPlaying=state==State.PLAYING;pause(false,"已暂停");
        for(Voice voice:voices)if(voice.getName().equals(name)){
            if(!selectVoice(voice)){missing("离线声音启用失败。");return;}
            state=State.READY;message="已选择 · "+voiceName;publish();if(wasPlaying){promote();play();}return;
        }
    }
    public void changeEngine(String name){store.preferences.edit().putString("tts_engine",name).remove("tts_voice").apply();initializeEngine();}
    public void changeRate(float rate){
        boolean wasPlaying=state==State.PLAYING;pause(false,"已暂停");
        store.preferences.edit().putFloat("speech_rate",Math.max(.5f,Math.min(2f,rate))).apply();
        if(wasPlaying){promote();play();}else publish();
    }
    public static void command(Context context,String action,String id,BookDocument.Position position){
        Intent intent=new Intent(context,SpeechService.class).setAction(action);
        if(id!=null)intent.putExtra("book",id);
        if(position!=null){intent.putExtra("block",position.block);intent.putExtra("offset",position.offset);}
        if(action.equals(PLAY)||action.equals(READ)||action.equals(RESUME))context.startForegroundService(intent);else context.startService(intent);
    }
    @Override public int onStartCommand(Intent intent,int flags,int startId){
        if(intent==null){stopSelf();return START_NOT_STICKY;}
        String action=intent.getAction();
        if(PLAY.equals(action)||READ.equals(action)){
            promote();String id=intent.getStringExtra("book");
            BookDocument.Position requested=READ.equals(action)?new BookDocument.Position(intent.getIntExtra("block",0),intent.getIntExtra("offset",0)):null;
            openBook(id,requested);
        }else if(RESUME.equals(action)){promote();play();}
        else if(PAUSE.equals(action)){++loadGeneration;pause(false,"已暂停");}
        else if(STOP.equals(action))stopPlayback();
        else if(NEXT.equals(action))navigateChapter(1);
        else if(PREVIOUS.equals(action))navigateChapter(-1);
        return START_NOT_STICKY;
    }
    private void openBook(String id,BookDocument.Position requested){
        pause(false,"正在打开听书进度…");int token=++loadGeneration;
        if(id==null){error("请先打开书籍。");return;}
        loader.execute(()->{
            try{BookDocument loaded=store.open(id);BookDocument.Position saved=requested==null?store.listen(id):requested;
                main.post(()->{if(destroyed||token!=loadGeneration)return;doc=loaded;bookId=id;BookDocument.Position p=doc.clamp(saved.block,saved.offset);block=p.block;offset=p.offset;persist();promote();play();});
            }catch(IOException failure){main.post(()->{if(token==loadGeneration&&!destroyed)error("无法读取听书正文："+failure.getMessage());});}
        });
    }
    private void play(){
        resumeAfterFocus=false;
        if(!available()){missing(state==State.INITIALIZING?"系统声音尚未就绪，请稍候再点播放。":"没有可用的中文离线声音，请检查系统设置。");return;}
        if(doc==null){error("请从书籍面板开始朗读。");return;}
        if(audio.requestAudioFocus(focus)!=AudioManager.AUDIOFOCUS_REQUEST_GRANTED){pause(false,"暂时无法取得音频焦点，请稍后继续。");return;}
        Voice actual=tts.getVoice();
        if(actual==null||actual.isNetworkConnectionRequired()||!actual.getName().equals(voiceName)){missing("离线声音发生变化，请重新选择本机声音。");return;}
        tts.setSpeechRate(store.preferences.getFloat("speech_rate",1f));
        state=State.PLAYING;message="正在朗读 · "+doc.title;media.setActive(true);promote();publish();speakNext();
    }
    private void speakNext(){
        if(state!=State.PLAYING||destroyed)return;
        try{
            String text="";
            while(block<doc.blocks.size()){
                text=doc.text(block);offset=SpeechChunks.safeOffset(text,offset);
                while(offset<text.length()&&Character.isWhitespace(text.charAt(offset)))offset++;
                if(offset<text.length())break;
                if(block+1>=doc.blocks.size()){offset=text.length();persist();finish();return;}
                block++;offset=0;persist();
            }
            int limit=Math.max(8,Math.min(280,TextToSpeech.getMaxSpeechInputLength()-1));
            chunkStart=offset;chunkEnd=SpeechChunks.end(text,chunkStart,limit);
            if(chunkEnd<=chunkStart){finish();return;}
            activeUtterance="speech_"+(++sequence);String utterance=activeUtterance;
            if(wake.isHeld())wake.release();wake.acquire(10*60*1000L);
            Bundle params=new Bundle();params.putFloat(TextToSpeech.Engine.KEY_PARAM_VOLUME,1f);
            int accepted=tts.speak(text.substring(chunkStart,chunkEnd),TextToSpeech.QUEUE_FLUSH,params,utterance);
            if(accepted!=TextToSpeech.SUCCESS)error("系统引擎拒绝了朗读请求；听书位置已保留。");
        }catch(IOException failure){error("正文读取失败："+failure.getMessage());}
    }
    private final UtteranceProgressListener progress=new UtteranceProgressListener(){
        private boolean valid(String id){return state==State.PLAYING&&id.equals(activeUtterance)&&!destroyed;}
        @Override public void onStart(String id){main.post(()->{if(valid(id)){persist();publish();}});}
        @Override public void onDone(String id){main.post(()->{
            if(!valid(id))return;offset=chunkEnd;activeUtterance="";persist();publish();main.post(SpeechService.this::speakNext);
        });}
        @Override public void onRangeStart(String id,int start,int end,int frame){main.post(()->{
            if(valid(id)){offset=Math.max(chunkStart,Math.min(chunkEnd,chunkStart+start));if(SystemClock.elapsedRealtime()-lastRangeSave>=500){lastRangeSave=SystemClock.elapsedRealtime();persist();}}
        });}
        @Override public void onError(String id){onError(id,TextToSpeech.ERROR);}
        @Override public void onError(String id,int code){main.post(()->{if(valid(id))error("系统朗读失败（"+code+"）；听书位置已保留，可重试或检查离线语音数据。");});}
        @Override public void onStop(String id,boolean interrupted){main.post(()->{if(valid(id))pause(false,"系统引擎中断了朗读，位置已保存。");});}
    };
    private void cancelUtterance(){activeUtterance="";sequence++;if(tts!=null)tts.stop();persist();if(wake!=null&&wake.isHeld())wake.release();}
    private void pause(boolean transientLoss,String reason){
        resumeAfterFocus=transientLoss;cancelUtterance();if(doc!=null)state=State.PAUSED;message=reason;
        if(!transientLoss&&audio!=null&&focus!=null)audio.abandonAudioFocusRequest(focus);publish();
    }
    private void stopPlayback(){
        ++loadGeneration;pause(false,"已停止，听书位置已保存。");state=State.STOPPED;media.setActive(false);demote();publish();stopSelf();
    }
    private void finish(){pause(false,"已读到全书结尾。");state=State.COMPLETE;media.setActive(false);demote();publish();stopSelf();}
    private void error(String reason){pause(false,reason);state=State.ERROR;demote();publish();stopSelf();}
    private void missing(String reason){pause(false,reason);engineReady=false;state=State.MISSING_VOICE;demote();publish();stopSelf();}
    public void paragraph(int direction){
        if(doc==null)return;boolean running=state==State.PLAYING;pause(false,"已移动到相邻段落。");
        try{BookDocument.Position next=doc.paragraph(new BookDocument.Position(block,offset),direction);block=next.block;offset=next.offset;persist();publish();if(running){promote();play();}}
        catch(IOException failure){error("段落读取失败："+failure.getMessage());}
    }
    public void navigateChapter(int direction){
        if(doc==null)return;boolean running=state==State.PLAYING;pause(false,"已切换听书章节。");
        int next=direction>0?doc.blocks.size()-1:0;
        for(BookDocument.Chapter chapter:doc.toc){
            if(direction>0&&chapter.block>block)next=Math.min(next,chapter.block);
            if(direction<0&&chapter.block<block)next=Math.max(next,chapter.block);
        }
        block=Math.max(0,Math.min(doc.blocks.size()-1,next));offset=0;persist();publish();if(running){promote();play();}
    }
    private void persist(){if(store!=null&&!bookId.isEmpty())store.saveListen(bookId,block,offset);}
    private PendingIntent action(String name){return PendingIntent.getService(this,name.hashCode(),new Intent(this,SpeechService.class).setAction(name),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
    private Notification notification(){
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP).putExtra("book",bookId),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        boolean playing=state==State.PLAYING;
        return new Notification.Builder(this,CHANNEL).setSmallIcon(R.drawable.ic_book).setContentTitle(doc==null?"eBOOK 离线朗读":doc.title)
            .setContentText(message).setContentIntent(open).setVisibility(Notification.VISIBILITY_PUBLIC).setOnlyAlertOnce(true)
            .setOngoing(playing).setCategory(Notification.CATEGORY_TRANSPORT)
            .addAction(new Notification.Action.Builder(android.R.drawable.ic_media_previous,"上一章",action(PREVIOUS)).build())
            .addAction(new Notification.Action.Builder(playing?android.R.drawable.ic_media_pause:android.R.drawable.ic_media_play,playing?"暂停":"继续",action(playing?PAUSE:RESUME)).build())
            .addAction(new Notification.Action.Builder(android.R.drawable.ic_media_next,"下一章",action(NEXT)).build())
            .addAction(new Notification.Action.Builder(android.R.drawable.ic_menu_close_clear_cancel,"停止",action(STOP)).build())
            .setStyle(new Notification.MediaStyle().setMediaSession(media.getSessionToken()).setShowActionsInCompactView(0,1,2)).build();
    }
    private void promote(){
        startForeground(NOTIFICATION,notification());foreground=true;
    }
    private void demote(){if(foreground){stopForeground(STOP_FOREGROUND_REMOVE);foreground=false;}}
    private void publish(){
        if(media!=null){
            int value=state==State.PLAYING?PlaybackState.STATE_PLAYING:state==State.PAUSED?PlaybackState.STATE_PAUSED:PlaybackState.STATE_STOPPED;
            media.setPlaybackState(new PlaybackState.Builder().setActions(PlaybackState.ACTION_PLAY|PlaybackState.ACTION_PAUSE|PlaybackState.ACTION_STOP|PlaybackState.ACTION_SKIP_TO_NEXT|PlaybackState.ACTION_SKIP_TO_PREVIOUS|PlaybackState.ACTION_PLAY_PAUSE)
                .setState(value,PlaybackState.PLAYBACK_POSITION_UNKNOWN,1f).build());
            if(doc!=null)media.setMetadata(new MediaMetadata.Builder().putString(MediaMetadata.METADATA_KEY_TITLE,doc.title).putString(MediaMetadata.METADATA_KEY_ARTIST,"eBOOK · 本机系统朗读").build());
        }
        if(foreground)((NotificationManager)getSystemService(NOTIFICATION_SERVICE)).notify(NOTIFICATION,notification());
        for(Listener listener:new ArrayList<>(listeners))listener.changed();
    }
    @Override public void onDestroy(){
        destroyed=true;++loadGeneration;++engineGeneration;cancelUtterance();if(tts!=null)tts.shutdown();
        audio.abandonAudioFocusRequest(focus);media.release();unregisterReceiver(noisy);loader.shutdownNow();listeners.clear();super.onDestroy();
    }
}
