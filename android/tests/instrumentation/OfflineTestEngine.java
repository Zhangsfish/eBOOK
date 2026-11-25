package cn.zhangsfish.ebook.tests;

import android.media.AudioFormat;
import android.speech.tts.*;
import java.util.*;

/** Controlled PCM engine for actual Android callback/focus tests, NEVER shipped. */
public final class OfflineTestEngine extends TextToSpeechService {
    private volatile boolean stopped;
    @Override protected String[]onGetLanguage(){return new String[]{"zho","CHN",""};}
    @Override protected int onIsLanguageAvailable(String language,String country,String variant){return language.equals("zho")||language.equals("zh")?TextToSpeech.LANG_COUNTRY_AVAILABLE:TextToSpeech.LANG_NOT_SUPPORTED;}
    @Override protected int onLoadLanguage(String language,String country,String variant){return onIsLanguageAvailable(language,country,variant);}
    @Override protected void onStop(){stopped=true;}
    @Override public List<Voice>onGetVoices(){
        if(getSharedPreferences("engine",0).getBoolean("missing",false))return Collections.emptyList();
        return Arrays.asList(new Voice("test-offline-zh",Locale.SIMPLIFIED_CHINESE,Voice.QUALITY_NORMAL,Voice.LATENCY_NORMAL,false,Collections.emptySet()),
            new Voice("test-network-zh",Locale.SIMPLIFIED_CHINESE,Voice.QUALITY_HIGH,Voice.LATENCY_NORMAL,true,Collections.emptySet()),
            new Voice("test-not-installed-zh",Locale.SIMPLIFIED_CHINESE,Voice.QUALITY_HIGH,Voice.LATENCY_NORMAL,false,Collections.singleton(TextToSpeech.Engine.KEY_FEATURE_NOT_INSTALLED)),
            new Voice("test-offline-en",Locale.US,Voice.QUALITY_NORMAL,Voice.LATENCY_NORMAL,false,Collections.emptySet()));
    }
    @Override public int onLoadVoice(String name){return onIsValidVoiceName(name);}
    @Override public int onIsValidVoiceName(String name){return name.equals("test-offline-zh")?TextToSpeech.SUCCESS:TextToSpeech.ERROR;}
    @Override public String onGetDefaultVoiceNameFor(String language,String country,String variant){return "test-offline-zh";}
    @Override protected void onSynthesizeText(SynthesisRequest request,SynthesisCallback callback){
        stopped=false;
        if(getSharedPreferences("engine",0).getBoolean("error",false)){callback.error(TextToSpeech.ERROR_SYNTHESIS);return;}
        String text=request.getCharSequenceText().toString();
        if(callback.start(16000,AudioFormat.ENCODING_PCM_16BIT,1)!=TextToSpeech.SUCCESS)return;
        int frame=0;float rate=Math.max(.5f,request.getSpeechRate()/100f);int frames=Math.round(1600/rate);
        for(int index=0;index<text.length()&&!stopped;){
            int width=Character.charCount(text.codePointAt(index));callback.rangeStart(frame,index,index+width);
            byte[]pcm=new byte[frames*2];for(int i=0;i<frames;i++){short value=(short)(Math.sin((frame+i)*2*Math.PI*220/16000)*320);pcm[i*2]=(byte)value;pcm[i*2+1]=(byte)(value>>>8);}
            for(int at=0;at<pcm.length&&!stopped;){int n=Math.min(callback.getMaxBufferSize(),pcm.length-at);if(callback.audioAvailable(pcm,at,n)!=TextToSpeech.SUCCESS)return;at+=n;}
            index+=width;frame+=frames;
        }
        if(!stopped)callback.done();
    }
}
