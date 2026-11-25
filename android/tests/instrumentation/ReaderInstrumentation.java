package cn.zhangsfish.ebook.tests;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.media.*;
import android.media.session.*;
import android.os.*;
import android.text.Layout;
import android.view.*;
import android.view.accessibility.*;
import android.widget.*;
import cn.zhangsfish.ebook.*;
import cn.zhangsfish.ebook.core.*;
import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;

/** Native instrumentation, no external test framework or production test hooks. */
public final class ReaderInstrumentation extends Instrumentation {
    private MainActivity activity;
    private Bundle arguments;
    private File evidence;
    private final List<String>results=new ArrayList<>();
    private int passed,failed;
    private long peakPssBytes,peakRssBytes;
    private int maxVisibleRows,maxTextUTF16;
    interface Check{void run()throws Exception;}
    interface Condition{boolean get()throws Exception;}
    @Override public void onCreate(Bundle args){arguments=args==null?new Bundle():args;start();}
    @Override public void onStart(){
        String phase=arguments.getString("phase","main");evidence=new File(getTargetContext().getFilesDir(),"test-evidence");evidence.mkdirs();
        try{
            if(phase.equals("main"))mainPhase();else resumePhase();
        }catch(Throwable failure){recordFailure("suite_setup",failure);}
        String report="{\"suite\":\"Android instrumentation\",\"completed\":true,\"phase\":\""+phase+"\",\"api\":"+Build.VERSION.SDK_INT+",\"passed\":"+passed+",\"failed\":"+failed+",\"metrics\":{\"peakSampledPssBytes\":"+peakPssBytes+",\"processVmHwmBytes\":"+peakRssBytes+",\"maxVisibleRows\":"+maxVisibleRows+",\"maxTextUTF16\":"+maxTextUTF16+"},\"tests\":["+String.join(",",results)+"]}";
        try(FileOutputStream out=new FileOutputStream(new File(evidence,"results-"+phase+".json"))){out.write(report.getBytes(StandardCharsets.UTF_8));}catch(IOException error){failed++;}
        Bundle result=new Bundle();result.putString("stream",report+"\n");result.putInt("passed",passed);result.putInt("failed",failed);finish(failed==0?Activity.RESULT_OK:Activity.RESULT_CANCELED,result);
    }
    private void test(String name,Check check){long start=SystemClock.elapsedRealtime();try{check.run();passed++;results.add("{\"name\":\""+name+"\",\"status\":\"PASS\",\"ms\":"+(SystemClock.elapsedRealtime()-start)+"}");status(name,"PASS");}catch(Throwable error){recordFailure(name,error);}}
    private void recordFailure(String name,Throwable error){failed++;String message=String.valueOf(error).replace("\\","\\\\").replace("\"","\\\"").replace("\n"," ");results.add("{\"name\":\""+name+"\",\"status\":\"FAIL\",\"error\":\""+message+"\"}");status(name,"FAIL "+message);try{screenshot("FAIL-"+name);}catch(Exception ignored){}}
    private void status(String name,String value){sampleMemory();Bundle b=new Bundle();b.putString("stream",name+": "+value+"\n");sendStatus(0,b);try(OutputStream out=new FileOutputStream(new File(evidence,"progress.json"))){out.write(("{\"last_case\":\""+name+"\",\"passed\":"+passed+",\"failed\":"+failed+"}").getBytes(StandardCharsets.UTF_8));}catch(IOException ignored){}}
    private void sampleMemory(){
        peakPssBytes=Math.max(peakPssBytes,Debug.getPss()*1024L);
        try(BufferedReader file=new BufferedReader(new FileReader("/proc/self/status"))){String line;while((line=file.readLine())!=null)if(line.startsWith("VmHWM:")){String[]parts=line.trim().split("\\s+");peakRssBytes=Math.max(peakRssBytes,Long.parseLong(parts[1])*1024L);}}
        catch(Exception ignored){/* optional kernel metric, no invented estimate */}
    }
    private static void expect(boolean value,String message){if(!value)throw new AssertionError(message);}
    private void waitFor(Condition condition,String message)throws Exception{long until=SystemClock.elapsedRealtime()+25000;while(SystemClock.elapsedRealtime()<until){if(condition.get())return;SystemClock.sleep(150);}throw new AssertionError(message);}
    private void ui(Runnable action){runOnMainSync(action);waitForIdleSync();}
    @SuppressWarnings("unchecked") private <T>T field(Object instance,String name)throws Exception{Field f=instance.getClass().getDeclaredField(name);f.setAccessible(true);return(T)f.get(instance);}
    private LibraryStore store(){return new LibraryStore(getTargetContext());}
    private BookDocument document()throws Exception{return field(activity,"doc");}
    private String book()throws Exception{return field(activity,"bookId");}
    private SpeechService speech()throws Exception{return field(activity,"speech");}
    private ListView reader(){return activity.findViewById(R.id.reader_list);}
    private Dialog dialog()throws Exception{return field(activity,"dialog");}
    private View dialogView()throws Exception{Dialog d=dialog();return d==null||!d.isShowing()?null:d.getWindow().getDecorView();}
    private List<View>walk(View root){List<View>out=new ArrayList<>();if(root==null)return out;out.add(root);if(root instanceof ViewGroup){ViewGroup g=(ViewGroup)root;for(int i=0;i<g.getChildCount();i++)out.addAll(walk(g.getChildAt(i)));}return out;}
    private View labeled(String label)throws Exception{
        List<View>all=walk(dialogView());all.addAll(walk(activity.getWindow().getDecorView()));
        for(View v:all)if(v.isShown()&&v.isClickable()&&v instanceof TextView&&((TextView)v).getText().toString().equals(label))return v;return null;
    }
    private void click(String label)throws Exception{
        waitFor(()->labeled(label)!=null||ax(label)!=null,"Missing button: "+label);View target=labeled(label);
        if(target!=null)ui(()->target.performClick());else clickAx(label);
        SystemClock.sleep(180);waitForIdleSync();
    }
    private AccessibilityNodeInfo ax(String text){
        AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();if(root==null)return null;
        List<AccessibilityNodeInfo>matches=root.findAccessibilityNodeInfosByText(text);
        for(AccessibilityNodeInfo n:matches)if((n.getText()!=null&&n.getText().toString().equals(text))||(n.getContentDescription()!=null&&n.getContentDescription().toString().equals(text)))return n;
        return findDescription(root,text);
    }
    private AccessibilityNodeInfo findDescription(AccessibilityNodeInfo node,String description){
        if(node.getContentDescription()!=null&&node.getContentDescription().toString().equals(description))return node;
        for(int i=0;i<node.getChildCount();i++){AccessibilityNodeInfo child=node.getChild(i);if(child!=null){AccessibilityNodeInfo result=findDescription(child,description);if(result!=null)return result;}}return null;
    }
    private boolean clickAx(String text){AccessibilityNodeInfo n=ax(text);for(int i=0;n!=null&&i<6;i++,n=n.getParent())if(n.isClickable())return n.performAction(AccessibilityNodeInfo.ACTION_CLICK);return false;}
    private void shell(String command)throws Exception{try(ParcelFileDescriptor fd=getUiAutomation().executeShellCommand(command);InputStream in=new ParcelFileDescriptor.AutoCloseInputStream(fd)){byte[]bytes=new byte[1024];while(in.read(bytes)!=-1){}}}
    private void launch()throws Exception{
        if(activity!=null&&!activity.isDestroyed()&&!activity.isFinishing()){
            // startActivitySync waits for onCreate; bringing an existing task
            // back from the background does not create another Activity.
            shell("am start -n cn.zhangsfish.ebook/.MainActivity -f 0x10020000");
            waitFor(()->activity.hasWindowFocus(),"Reader task didn't return to foreground");waitForIdleSync();return;
        }
        Intent intent=new Intent().setClassName("cn.zhangsfish.ebook","cn.zhangsfish.ebook.MainActivity").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        activity=(MainActivity)startActivitySync(intent);waitForIdleSync();
    }
    private void controls()throws Exception{ui(()->activity.findViewById(R.id.reader_controls).performClick());}
    private void dismiss()throws Exception{Dialog d=dialog();if(d!=null)ui(d::dismiss);}
    private void toc()throws Exception{controls();click("目录");waitFor(()->dialogView()!=null&&dialogView().findViewById(R.id.toc_list)!=null,"TOC missing");}
    private EditText query()throws Exception{return dialogView().findViewById(R.id.toc_query);}
    private ListView tocList()throws Exception{return dialogView().findViewById(R.id.toc_list);}
    private void selectChapter(String needle)throws Exception{
        toc();EditText q=query();ui(()->q.setText(needle));ListView list=tocList();waitFor(()->list.getCount()>0,"TOC search has no results");
        ui(()->list.performItemClick(list.getChildAt(0),0,list.getAdapter().getItemId(0)));SystemClock.sleep(400);waitForIdleSync();
    }
    private BookDocument.Position live()throws Exception{
        AtomicReference<BookDocument.Position>out=new AtomicReference<>();ui(()->{
            ListView list=reader();int block=list.getFirstVisiblePosition(),offset=0;View first=list.getChildAt(0);
            maxVisibleRows=Math.max(maxVisibleRows,list.getChildCount());for(View v:walk(list))if(v instanceof TextView)maxTextUTF16=Math.max(maxTextUTF16,((TextView)v).length());
            if(first instanceof TextView){TextView text=(TextView)first;Layout layout=text.getLayout();if(layout!=null)offset=layout.getLineStart(layout.getLineForVertical(Math.max(0,list.getPaddingTop()-first.getTop()-text.getTotalPaddingTop())));}
            out.set(new BookDocument.Position(block,offset));
        });return out.get();
    }
    private void screenshot(String name)throws Exception{
        Bitmap bitmap=getUiAutomation().takeScreenshot();if(bitmap==null)throw new IOException("No screenshot");try(OutputStream out=new FileOutputStream(new File(evidence,name+".png"))){bitmap.compress(Bitmap.CompressFormat.PNG,100,out);}bitmap.recycle();
    }
    private void importWithPicker(String filename)throws Exception{
        if(reader()!=null){controls();click("书架");}
        ui(()->activity.findViewById(R.id.library_import).performClick());
        waitFor(()->{AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();return root!=null&&!"cn.zhangsfish.ebook".contentEquals(root.getPackageName()==null?"":root.getPackageName());},"System picker didn't open");
        SystemClock.sleep(500);
        if(ax(filename)==null){
            if(!clickAx("Show roots")&&!clickAx("显示根目录")&&!clickAx("Open navigation drawer")){
                AccessibilityNodeInfo root=getUiAutomation().getRootInActiveWindow();List<AccessibilityNodeInfo>buttons=root.findAccessibilityNodeInfosByViewId("com.android.documentsui:id/toolbar");
                if(!buttons.isEmpty()&&buttons.get(0).getChildCount()>0)buttons.get(0).getChild(0).performAction(AccessibilityNodeInfo.ACTION_CLICK);
            }
        }
        if(ax(filename)==null){
            waitFor(()->ax("Downloads")!=null||ax("下载")!=null,"Downloads missing from system picker");if(!clickAx("Downloads"))clickAx("下载");
        }
        for(int i=0;i<12&&ax(filename)==null;i++){AccessibilityNodeInfo current=getUiAutomation().getRootInActiveWindow();AccessibilityNodeInfo scroll=scrollable(current);if(scroll!=null)scroll.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD);SystemClock.sleep(250);}
        waitFor(()->ax(filename)!=null,"Fixture missing in picker: "+filename);clickAx(filename);SystemClock.sleep(300);
        if(ax("Open")!=null)clickAx("Open");else if(ax("OPEN")!=null)clickAx("OPEN");
        if(filename.endsWith(".txt")){waitFor(()->ax("使用自动识别")!=null,"Encoding choice missing");clickAx("使用自动识别");}
        waitFor(()->reader()!=null&&reader().getChildCount()>0,"Import didn't reach reader");SystemClock.sleep(300);
        if(ax("Got it")!=null){clickAx("Got it");SystemClock.sleep(250);}
    }
    private AccessibilityNodeInfo scrollable(AccessibilityNodeInfo node){if(node==null)return null;if(node.isScrollable())return node;for(int i=0;i<node.getChildCount();i++){AccessibilityNodeInfo found=scrollable(node.getChild(i));if(found!=null)return found;}return null;}
    private void mainPhase()throws Exception{
        store().preferences.edit().putBoolean("reader_visible",false).putString("tts_engine","cn.zhangsfish.ebook.tests").commit();
        engineMode(false,false);launch();
        test("real_system_picker_long_TXT_import",()->{importWithPicker("original_long_gb18030.txt");expect(document().toc.size()==625,"625 chapters required");expect(document().blocks.size()==1888,"incremental block index");screenshot("warm-reader");});
        if(reader()==null)throw new AssertionError("No reader after import");
        test("quiet_ellipsis_and_48dp_hit_target",()->{
            AccessibilityNodeInfo active=getUiAutomation().getRootInActiveWindow();expect(active!=null&&"cn.zhangsfish.ebook".contentEquals(active.getPackageName()),"Reader is covered by another window");
            View entry=activity.findViewById(R.id.reader_controls);float density=getTargetContext().getResources().getDisplayMetrics().density;
            expect(entry.getWidth()/density>=48&&entry.getHeight()/density>=48,"hit target smaller than48dp");
            for(View view:walk(activity.getWindow().getDecorView()))if(view instanceof Button)throw new AssertionError("Persistent reader button: "+((Button)view).getText());
        });
        test("TOC_search_jump_to_chapter500",()->{selectChapter("第500章");expect(document().currentChapter(live().block)==499,"didn't reach chapter500");});
        test("TOC_reopen_clears_search_and_marks_current",()->{
            toc();expect(query().getText().length()==0,"stale search");ListView list=tocList();boolean marker=false;
            for(View v:walk(list))if(v instanceof TextView&&((TextView)v).getText().toString().startsWith("✓")&&((TextView)v).getText().toString().contains("第500章"))marker=true;
            expect(marker,"current chapter not revealed/marked");screenshot("toc-chapter500");dismiss();
        });
        test("browsing_search_dismiss_preserves_exact_viewport",()->{
            BookDocument.Position before=live();int[]top={0};ui(()->top[0]=reader().getChildAt(0).getTop());toc();ListView list=tocList();EditText q=query();ui(()->{list.setSelection(0);q.setText("第10章");});dismiss();
            BookDocument.Position after=live();expect(before.block==after.block&&before.offset==after.offset,"TOC browsing changed anchor");ui(()->expect(top[0]==reader().getChildAt(0).getTop(),"TOC moved text pixels"));
        });
        test("live_scroll_chapter_beats_last_TOC_selection",()->{
            int boundary=document().toc.get(500).block;for(int i=0;i<20&&live().block<boundary;i++){ui(()->reader().scrollListBy(reader().getHeight()));SystemClock.sleep(80);}
            BookDocument.Position current=live();int expected=document().currentChapter(current.block);expect(expected>=500,"didn't cross chapter boundary");toc();expect(query().getText().length()==0,"search retained");
            String title=document().toc.get(expected).title;boolean marked=false;for(View v:walk(tocList()))if(v instanceof TextView){String s=((TextView)v).getText().toString();if(s.startsWith("✓")&&s.contains(title))marked=true;}
            expect(marked,"TOC followed stale selection");dismiss();
        });
        test("font_and_line_spacing_keep_text_anchor",()->{
            BookDocument.Position before=live();controls();click("字号");List<SeekBar>bars=new ArrayList<>();for(View v:walk(dialogView()))if(v instanceof SeekBar)bars.add((SeekBar)v);
            expect(bars.size()==2,"reading sliders missing");drag(bars.get(0),.65f);drag(bars.get(1),.6f);dismiss();SystemClock.sleep(350);
            BookDocument.Position after=live();expect(after.block==before.block&&Math.abs(after.offset-before.offset)<100,"type change lost text");expect(store().preferences.getInt("font_size",21)!=21,"font not saved");
        });
        for(String theme:new String[]{"浅色","深色","护眼"})test("theme_"+theme,()->{BookDocument.Position before=live();controls();click("字号");click(theme);dismiss();SystemClock.sleep(250);expect(live().block==before.block,"theme moved chapter");screenshot("theme-"+(theme.equals("浅色")?"light":theme.equals("深色")?"dark":"warm"));});
        test("fold_width_reflow_keeps_anchor",()->{
            BookDocument.Position before=live();shell("wm size 1800x2200");SystemClock.sleep(900);waitForIdleSync();BookDocument.Position after=live();expect(before.block==after.block&&Math.abs(before.offset-after.offset)<160,"unfold lost anchor");screenshot("unfolded-reader");shell("wm size reset");SystemClock.sleep(900);expect(before.block==live().block,"fold lost block");
        });
        test("Android_codecs_strict_roundtrip",()->{
            String original="第1章 原创\n纸窗里留下中文和四字节\ud840\udc00。";
            for(String enc:new String[]{"UTF-8","UTF-16LE","UTF-16BE","GBK","GB18030"}){
                String value=enc.equals("GBK")?original.replace("\ud840\udc00",""):original;
                File file=new File(getTargetContext().getCacheDir(),"codec-"+enc);try(OutputStream out=new FileOutputStream(file)){out.write(value.getBytes(enc));}
                File dir=new File(getTargetContext().getCacheDir(),"parsed-"+enc);BookDocument parsed=TxtImporter.parse(file,dir,"原创",enc);StringBuilder all=new StringBuilder();for(int i=0;i<parsed.blocks.size();i++)all.append(parsed.text(i));expect(all.toString().equals(value+"\n"),"Android charset corrupted "+enc);
            }
        });
        waitFor(()->speech()!=null&&speech().state()!=SpeechService.State.INITIALIZING,"TTS initialization didn't finish");
        test("voice_catalog_excludes_network_missing_and_nonChinese",()->{expect(speech().voices().size()==1,"unsafe voice filtering");expect(speech().voiceName().equals("test-offline-zh"),"wrong voice");});
        final BookDocument.Position[]readingBefore={live()};
        test("real_TTS_callbacks_pause_resume_separate_position",()->{
            controls();click("朗读");click("从当前阅读处朗读");waitFor(()->speech().state()==SpeechService.State.PLAYING,"speech didn't start");
            BookDocument.Position started=speech().position();waitFor(()->{BookDocument.Position p=speech().position();return p.block>started.block||p.offset>started.offset;},"callbacks didn't advance");
            click("暂停");expect(speech().state()==SpeechService.State.PAUSED,"pause state");BookDocument.Position paused=speech().position();SystemClock.sleep(800);expect(speech().position().block==paused.block&&speech().position().offset==paused.offset,"paused cursor moved");
            click("继续听书");waitFor(()->speech().state()==SpeechService.State.PLAYING,"resume failed");expect(speech().position().block>=paused.block,"resume reset book");
            expect(live().block==readingBefore[0].block&&live().offset==readingBefore[0].offset,"listening moved reading");dismiss();
        });
        test("background_lockscreen_and_media_controls",()->{
            SpeechService service=speech();expect(service!=null,"service is not connected");
            try{
                BookDocument.Position before=service.position();ui(()->activity.moveTaskToBack(true));shell("input keyevent 223");SystemClock.sleep(2200);
                BookDocument.Position after=service.position();expect(after.block>before.block||after.offset>before.offset,"no lockscreen callback progress");
                NotificationManager manager=(NotificationManager)getTargetContext().getSystemService(Context.NOTIFICATION_SERVICE);expect(manager.getActiveNotifications().length>0,"no playback notification");
                MediaSession session=field(service,"media");session.getController().getTransportControls().pause();waitFor(()->service.state()==SpeechService.State.PAUSED,"media pause failed");
                session.getController().getTransportControls().play();waitFor(()->service.state()==SpeechService.State.PLAYING,"media play failed");
            }finally{shell("input keyevent 224");shell("wm dismiss-keyguard");launch();waitFor(()->speech()!=null&&reader()!=null&&activity.hasWindowFocus(),"service/reader didn't return to foreground");}
        });
        test("audio_focus_and_user_pause_interruption",()->{
            SpeechService service=speech();AudioManager audio=(AudioManager)getTargetContext().getSystemService(Context.AUDIO_SERVICE);
            AudioFocusRequest focus=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT).setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build()).setOnAudioFocusChangeListener(change->{}).build();
            expect(audio.requestAudioFocus(focus)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED,"test focus denied");waitFor(()->service.state()==SpeechService.State.PAUSED,"focus didn't pause speech");audio.abandonAudioFocusRequest(focus);waitFor(()->service.state()==SpeechService.State.PLAYING,"transient focus didn't resume");
            audio.requestAudioFocus(focus);waitFor(()->service.state()==SpeechService.State.PAUSED,"second focus pause missing");ui(()->SpeechService.command(activity,SpeechService.PAUSE,null,null));audio.abandonAudioFocusRequest(focus);SystemClock.sleep(600);expect(service.state()==SpeechService.State.PAUSED,"manual pause resumed unexpectedly");
        });
        test("headphone_noisy_event_pauses",()->{
            ui(()->SpeechService.command(activity,SpeechService.RESUME,null,null));waitFor(()->speech().state()==SpeechService.State.PLAYING,"resume missing");shell("am broadcast -a android.media.AUDIO_BECOMING_NOISY -p cn.zhangsfish.ebook");waitFor(()->speech().state()==SpeechService.State.PAUSED,"noisy event ignored");
        });
        test("speech_rate_chapter_and_paragraph_navigation",()->{
            SpeechService service=speech();ui(()->service.changeRate(1.5f));expect(store().preferences.getFloat("speech_rate",1)!=1,"rate not saved");int before=service.position().block;ui(()->service.navigateChapter(1));expect(service.position().block>before,"next chapter failed");BookDocument.Position chapter=service.position();ui(()->service.paragraph(1));BookDocument.Position next=service.position();expect(next.block>chapter.block||(next.block==chapter.block&&next.offset>chapter.offset),"next paragraph failed");
            expect(live().block==readingBefore[0].block,"speech navigation changed reading");
        });
        test("missing_offline_voice_never_blocks_reading",()->{
            engineMode(true,false);ui(()->speechUnchecked().initializeEngine());waitFor(()->speech().state()==SpeechService.State.MISSING_VOICE,"missing voice not surfaced");
            controls();click("朗读");View play=dialogView().findViewById(R.id.speech_play);expect(!play.isEnabled(),"unsafe playback allowed");expect(reader()!=null&&reader().getChildCount()>0,"reading unavailable");screenshot("missing-offline-voice");dismiss();
            engineMode(false,false);ui(()->speechUnchecked().initializeEngine());waitFor(()->speech().state()==SpeechService.State.READY,"voice refresh failed");
        });
        test("engine_error_visible_and_retryable",()->{
            engineMode(false,true);ui(()->SpeechService.command(activity,SpeechService.PLAY,bookUnchecked(),null));waitFor(()->speech().state()==SpeechService.State.ERROR,"engine error not surfaced");
            engineMode(false,false);ui(()->SpeechService.command(activity,SpeechService.PLAY,bookUnchecked(),null));waitFor(()->speech().state()==SpeechService.State.PLAYING,"retry failed");ui(()->SpeechService.command(activity,SpeechService.STOP,null,null));
        });
        test("bounded_visible_text_and_durable_checkpoint",()->{
            selectChapter("第624章");BookDocument.Position at=live();expect(document().currentChapter(at.block)==623,"deep checkpoint wrong");
            ui(()->{expect(reader().getChildCount()<20,"too many retained visible rows");for(View v:walk(reader()))if(v instanceof TextView)expect(((TextView)v).length()<=1600,"giant text component");});
            SystemClock.sleep(400);BookDocument.Position saved=store().read(book()),listening=store().listen(book());
            getTargetContext().getSharedPreferences("checkpoint",0).edit().putString("book",book()).putInt("read_block",saved.block).putInt("read_offset",saved.offset).putInt("listen_block",listening.block).putInt("listen_offset",listening.offset).commit();
            expect(saved.block!=listening.block||saved.offset!=listening.offset,"reading/listening conflated");screenshot("deep-resume-checkpoint");
        });
    }
    private SpeechService speechUnchecked(){try{return speech();}catch(Exception e){throw new RuntimeException(e);}}
    private String bookUnchecked(){try{return book();}catch(Exception e){throw new RuntimeException(e);}}
    private void engineMode(boolean missing,boolean error)throws Exception{shell("am broadcast -n cn.zhangsfish.ebook.tests/.EngineModeReceiver -a cn.zhangsfish.ebook.tests.MODE --ez missing "+missing+" --ez error "+error);}
    private void drag(SeekBar bar,float fraction)throws Exception{
        int[]location=new int[2];ui(()->bar.getLocationOnScreen(location));float x=location[0]+bar.getWidth()*fraction,y=location[1]+bar.getHeight()/2f;long now=SystemClock.uptimeMillis();
        sendPointerSync(MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,x,y,0));sendPointerSync(MotionEvent.obtain(now,now+100,MotionEvent.ACTION_MOVE,x+1,y,0));sendPointerSync(MotionEvent.obtain(now,now+180,MotionEvent.ACTION_UP,x+1,y,0));waitForIdleSync();SystemClock.sleep(200);
    }
    private void resumePhase()throws Exception{
        launch();waitFor(()->reader()!=null&&reader().getChildCount()>0,"relaunch reader missing");SystemClock.sleep(500);
        test("process_restart_restores_reading_and_listening_separately",()->{
            android.content.SharedPreferences checkpoint=getTargetContext().getSharedPreferences("checkpoint",0);expect(book().equals(checkpoint.getString("book","")),"book reset");
            BookDocument.Position at=live(),listening=store().listen(book());expect(at.block==checkpoint.getInt("read_block",-1),"reading block reset");expect(Math.abs(at.offset-checkpoint.getInt("read_offset",-1))<100,"reading offset reset");
            expect(listening.block==checkpoint.getInt("listen_block",-1)&&listening.offset==checkpoint.getInt("listen_offset",-1),"listening reset");expect(document().currentChapter(at.block)==623,"chapter624 resume failed");screenshot("process-resume");
        });
        test("relaunch_TOC_follows_current_and_dismiss_preserves",()->{BookDocument.Position before=live();toc();expect(query().getText().length()==0,"query persisted");boolean current=false;for(View v:walk(tocList()))if(v instanceof TextView){String s=((TextView)v).getText().toString();if(s.startsWith("✓")&&s.contains("第624章"))current=true;}expect(current,"deep TOC not revealed");dismiss();expect(live().block==before.block&&live().offset==before.offset,"relaunch TOC jump");});
        test("real_system_picker_EPUB_import_and_render",()->{importWithPicker("synthetic.epub");expect(document().format.equals("EPUB"),"EPUB not imported");expect(!document().toc.isEmpty(),"EPUB TOC missing");screenshot("epub-reader");});
        test("remove_book_and_local_duplicate_import",()->{
            String firstBook=book();controls();click("书架");int count=store().list().size();importWithPicker("synthetic.epub");expect(book().equals(firstBook),"duplicate created new book");expect(store().list().size()==count,"duplicate bookshelf record");
            controls();click("书架");ListView library=activity.findViewById(R.id.library_list);expect(library!=null&&library.getCount()>=2,"bookshelf lost books");
            View first=library.getChildAt(0);int[]xy=new int[2];ui(()->first.getLocationOnScreen(xy));long now=SystemClock.uptimeMillis();float x=xy[0]+first.getWidth()/2f,y=xy[1]+first.getHeight()/2f;
            sendPointerSync(MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,x,y,0));SystemClock.sleep(900);sendPointerSync(MotionEvent.obtain(now,SystemClock.uptimeMillis(),MotionEvent.ACTION_UP,x,y,0));
            waitFor(()->ax("移除")!=null,"remove confirmation missing");clickAx("移除");waitFor(()->store().list().size()==count-1,"remove failed");screenshot("bookshelf");
        });
    }
}
