package cn.zhangsfish.ebook;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.res.Configuration;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.speech.tts.*;
import android.text.*;
import android.util.TypedValue;
import android.view.*;
import android.view.inputmethod.InputMethodManager;
import android.widget.*;
import cn.zhangsfish.ebook.core.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

/** Quiet native reader. Dialogs never replace or resize the text viewport. */
public final class MainActivity extends Activity implements SpeechService.Listener {
    private static final int PICK=701,NOTIFY_PERMISSION=702;
    private LibraryStore store;
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private FrameLayout root;
    private ReaderList reader;
    private BlockAdapter adapter;
    private BookDocument doc;
    private String bookId="";
    private BookDocument.Position anchor=new BookDocument.Position(0,0);
    private boolean restoring,bound,destroyed;
    private int restoreRevision;
    private SpeechService speech;
    private Dialog dialog;
    private TextView speechStatus,listenProgress;
    private Button playButton;
    private ProgressDialog loading;
    private int background,foreground,muted;
    private final Runnable saveAnchor=()->{if(doc!=null&&!restoring)store.saveRead(bookId,anchor.block,anchor.offset);};
    private final ServiceConnection connection=new ServiceConnection(){
        @Override public void onServiceConnected(ComponentName name,IBinder binder){speech=((SpeechService.LocalBinder)binder).service();speech.addListener(MainActivity.this);}
        @Override public void onServiceDisconnected(ComponentName name){speech=null;changed();}
    };

    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);store=new LibraryStore(this);colors();
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING);
        if(Build.VERSION.SDK_INT>=28){WindowManager.LayoutParams attrs=getWindow().getAttributes();attrs.layoutInDisplayCutoutMode=WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;getWindow().setAttributes(attrs);}
        String requested=getIntent().getStringExtra("book");
        if(requested==null&&store.preferences.getBoolean("reader_visible",false))requested=store.preferences.getString("last_book","");
        if(requested!=null&&!requested.isEmpty())open(requested);else library();
    }
    @Override protected void onStart(){super.onStart();bound=bindService(new Intent(this,SpeechService.class),connection,BIND_AUTO_CREATE);}
    @Override protected void onResume(){super.onResume();if(doc!=null)immersive(true);}
    @Override protected void onStop(){capture();saveAnchor.run();if(speech!=null)speech.removeListener(this);if(bound){unbindService(connection);bound=false;}speech=null;super.onStop();}
    @Override protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);String id=intent.getStringExtra("book");if(id!=null&&!id.isEmpty()&&!id.equals(bookId))open(id);}
    @Override public void onConfigurationChanged(Configuration config){
        BookDocument.Position preserved=capture();super.onConfigurationChanged(config);
        if(doc!=null){if(dialog!=null&&dialog.isShowing())dialog.dismiss();colors();root.setBackgroundColor(background);adapter.notifyDataSetChanged();restore(preserved);immersive(true);}
        else library();
    }
    @Override public void onWindowFocusChanged(boolean focused){super.onWindowFocusChanged(focused);if(focused&&doc!=null)immersive(true);}
    @Override public void onBackPressed(){if(doc!=null){capture();saveAnchor.run();library();}else super.onBackPressed();}
    @Override protected void onDestroy(){destroyed=true;main.removeCallbacksAndMessages(null);io.shutdownNow();if(dialog!=null)dialog.dismiss();if(loading!=null)loading.dismiss();super.onDestroy();}
    private int dp(float value){return Math.round(value*getResources().getDisplayMetrics().density);}
    private void colors(){
        String theme=store.preferences.getString("theme","warm");
        background=Color.parseColor(theme.equals("dark")?"#171C21":theme.equals("light")?"#FCFCF7":"#F7EFDA");
        foreground=Color.parseColor(theme.equals("dark")?"#D4D6D1":"#303632");
        muted=Color.parseColor(theme.equals("dark")?"#8F9992":"#6C766B");
    }
    private TextView text(String value,float size){TextView view=new TextView(this);view.setText(value);view.setTextColor(foreground);view.setTextSize(size);return view;}
    private GradientDrawable surface(){GradientDrawable shape=new GradientDrawable();shape.setColor(background);shape.setCornerRadius(dp(18));shape.setStroke(dp(1),muted&0x44ffffff);return shape;}
    private Button button(String value,Runnable action){
        Button view=new Button(this);view.setText(value);view.setTextSize(15);view.setTextColor(foreground);view.setAllCaps(false);view.setMinHeight(dp(48));
        view.setOnClickListener(v->action.run());view.setBackgroundTintList(android.content.res.ColorStateList.valueOf((background&0x00ffffff)|0xff000000));return view;
    }
    private LinearLayout column(){LinearLayout layout=new LinearLayout(this);layout.setOrientation(LinearLayout.VERTICAL);layout.setPadding(dp(20),dp(16),dp(20),dp(16));layout.setBackgroundColor(background);return layout;}
    private LinearLayout row(){LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.HORIZONTAL);row.setGravity(Gravity.CENTER_VERTICAL);return row;}
    private void equal(LinearLayout row,View child){row.addView(child,new LinearLayout.LayoutParams(0,ViewGroup.LayoutParams.WRAP_CONTENT,1));}
    private void base(boolean reading){
        colors();root=new FrameLayout(this);root.setBackgroundColor(background);setContentView(root);
        root.setOnApplyWindowInsetsListener((v,insets)->{
            int top=reading?0:insets.getSystemWindowInsetTop(),bottom=reading?0:insets.getSystemWindowInsetBottom();
            int left=insets.getSystemWindowInsetLeft(),right=insets.getSystemWindowInsetRight();
            if(Build.VERSION.SDK_INT>=28&&insets.getDisplayCutout()!=null){
                left=Math.max(left,insets.getDisplayCutout().getSafeInsetLeft());right=Math.max(right,insets.getDisplayCutout().getSafeInsetRight());
                if(reading)top=insets.getDisplayCutout().getSafeInsetTop();
            }
            v.setPadding(left,top,right,bottom);return insets;
        });root.requestApplyInsets();immersive(reading);
    }
    private void immersive(boolean reading){
        int flags=reading?View.SYSTEM_UI_FLAG_FULLSCREEN|View.SYSTEM_UI_FLAG_HIDE_NAVIGATION|View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY:0;
        if(!store.preferences.getString("theme","warm").equals("dark"))flags|=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
        getWindow().getDecorView().setSystemUiVisibility(flags);getWindow().setStatusBarColor(background);getWindow().setNavigationBarColor(background);
    }
    private void library(){
        if(dialog!=null)dialog.dismiss();doc=null;bookId="";reader=null;adapter=null;store.preferences.edit().putBoolean("reader_visible",false).apply();base(false);
        LinearLayout page=column();page.setPadding(dp(24),dp(24),dp(24),dp(16));root.addView(page,new FrameLayout.LayoutParams(-1,-1));
        TextView heading=text("eBOOK",30);heading.setTypeface(null,Typeface.BOLD);page.addView(heading);
        TextView sub=text("把自己的书，安静地读下去。",15);sub.setTextColor(muted);sub.setPadding(0,dp(8),0,dp(20));page.addView(sub);
        Button add=button("导入 EPUB / TXT",this::pick);add.setId(R.id.library_import);page.addView(add,new LinearLayout.LayoutParams(-1,dp(52)));
        TextView note=text("书籍和进度保存在本机。长按书籍可移除。",12);note.setTextColor(muted);note.setPadding(0,dp(12),0,dp(12));page.addView(note);
        try{
            List<LibraryStore.Record>books=store.list();
            if(books.isEmpty()){
                TextView empty=text("书架还是空的\n点击上方按钮，选择一个本地书籍文件。",17);empty.setGravity(Gravity.CENTER);empty.setLineSpacing(dp(10),1);page.addView(empty,new LinearLayout.LayoutParams(-1,0,1));
            }else{
                ListView list=new ListView(this);list.setId(R.id.library_list);list.setDivider(null);page.addView(list,new LinearLayout.LayoutParams(-1,0,1));
                list.setAdapter(new BaseAdapter(){
                    public int getCount(){return books.size();}public Object getItem(int p){return books.get(p);}public long getItemId(int p){return p;}
                    public View getView(int p,View recycled,ViewGroup parent){
                        LibraryStore.Record record=books.get(p);BookDocument.Position at=store.read(record.id);
                        TextView cell=text(record.doc.title+"\n"+(record.doc.author.isEmpty()?"":record.doc.author+" · ")+record.doc.format+" · "+Math.round(record.doc.progress(at.block,at.offset)*100)+"%",19);
                        cell.setPadding(dp(8),dp(20),dp(8),dp(20));cell.setLineSpacing(dp(8),1);cell.setMinHeight(dp(90));return cell;
                    }
                });
                list.setOnItemClickListener((parent,view,position,id)->open(books.get(position).id));
                list.setOnItemLongClickListener((parent,view,position,id)->{
                    LibraryStore.Record record=books.get(position);
                    new AlertDialog.Builder(this).setTitle("移除《"+record.doc.title+"》？").setMessage("移除本应用内副本和进度，原文件不受影响。")
                        .setNegativeButton("取消",null).setPositiveButton("移除",(d,w)->{
                            if(speech!=null&&record.id.equals(speech.bookId()))SpeechService.command(this,SpeechService.STOP,null,null);
                            io.execute(()->{try{store.remove(record.id);main.post(()->{if(!destroyed)library();});}catch(IOException e){main.post(()->error(e.getMessage()));}});
                        }).show();return true;
                });
            }
        }catch(IOException failure){error(failure.getMessage());}
    }
    private void pick(){
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/epub+zip","text/plain","application/octet-stream"});
        try{startActivityForResult(intent,PICK);}catch(ActivityNotFoundException e){error("未找到系统文件选择器，请在系统中启用“文件”应用。");}
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);if(request!=PICK||result!=RESULT_OK||data==null||data.getData()==null)return;
        Uri uri=data.getData();String name=store.displayName(uri);
        if(name.toLowerCase(Locale.ROOT).endsWith(".txt")){
            String[]options={"自动","UTF-8","UTF-16LE","UTF-16BE","GBK","GB18030"};
            new AlertDialog.Builder(this).setTitle("TXT 编码").setSingleChoiceItems(options,0,(d,which)->{d.dismiss();importFile(uri,options[which]);})
                .setPositiveButton("使用自动识别",(d,w)->importFile(uri,"自动")).setNegativeButton("取消",null).show();
        }else importFile(uri,"自动");
    }
    private void importFile(Uri uri,String encoding){
        loading=ProgressDialog.show(this,"导入书籍","正在严格解码并建立章节索引…",true,false);
        io.execute(()->{
            try{LibraryStore.Record record=store.importUri(uri,encoding);main.post(()->{if(destroyed)return;loading.dismiss();openLoaded(record.id,record.doc);});}
            catch(Exception e){main.post(()->{if(!destroyed){loading.dismiss();error("导入失败："+e.getMessage());}});}
        });
    }
    private void open(String id){
        base(false);TextView opening=text("正在打开书籍…",18);opening.setGravity(Gravity.CENTER);root.addView(opening,new FrameLayout.LayoutParams(-1,-1));
        io.execute(()->{try{BookDocument loaded=store.open(id);main.post(()->{if(!destroyed)openLoaded(id,loaded);});}
            catch(IOException failure){main.post(()->{if(!destroyed){library();error(failure.getMessage());}});}});
    }
    private void openLoaded(String id,BookDocument loaded){
        if(dialog!=null)dialog.dismiss();doc=loaded;bookId=id;anchor=doc.clamp(store.read(id).block,store.read(id).offset);
        store.opened(id);store.preferences.edit().putBoolean("reader_visible",true).apply();base(true);
        reader=new ReaderList();reader.setId(R.id.reader_list);reader.setContentDescription("阅读正文");reader.setDivider(null);
        reader.setVerticalScrollBarEnabled(false);reader.setFastScrollEnabled(false);reader.setCacheColorHint(Color.TRANSPARENT);
        reader.setPadding(0,dp(16),0,dp(16));reader.setClipToPadding(true);reader.setBackgroundColor(background);
        FrameLayout.LayoutParams body=new FrameLayout.LayoutParams(-1,-1);body.bottomMargin=dp(48);root.addView(reader,body);
        adapter=new BlockAdapter();reader.setAdapter(adapter);
        reader.setOnScrollListener(new AbsListView.OnScrollListener(){
            public void onScrollStateChanged(AbsListView view,int state){if(state==SCROLL_STATE_IDLE){capture();saveAnchor.run();}}
            public void onScroll(AbsListView view,int first,int visible,int total){
                if(restoring||doc==null||view.getChildCount()==0)return;capture();main.removeCallbacks(saveAnchor);main.postDelayed(saveAnchor,200);
            }
        });
        TextView more=text("⋯",23);more.setId(R.id.reader_controls);more.setAlpha(.65f);more.setGravity(Gravity.CENTER);more.setContentDescription("阅读控制");more.setMinWidth(dp(48));more.setMinHeight(dp(48));more.setFocusable(true);more.setClickable(true);
        more.setOnClickListener(v->controls());FrameLayout.LayoutParams entry=new FrameLayout.LayoutParams(dp(48),dp(48),Gravity.END|Gravity.BOTTOM);entry.rightMargin=dp(8);root.addView(more,entry);
        restore(anchor);
    }
    private final class ReaderList extends ListView {
        ReaderList(){super(MainActivity.this);}
        @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){
            BookDocument.Position keep=anchor;boolean resize=oldw>0&&(oldw!=w||oldh!=h)&&doc!=null;
            if(resize){keep=capture();restoring=true;}super.onSizeChanged(w,h,oldw,oldh);
            if(resize){BookDocument.Position saved=keep;post(()->{if(doc!=null)restore(saved);});}
        }
    }
    private final class BlockAdapter extends BaseAdapter {
        private final android.util.LruCache<String,Bitmap>images=new android.util.LruCache<String,Bitmap>(6*1024*1024){@Override protected int sizeOf(String k,Bitmap v){return v.getAllocationByteCount();}};
        public int getCount(){return doc.blocks.size();}public Object getItem(int p){return doc.blocks.get(p);}public long getItemId(int p){return p;}
        public boolean hasStableIds(){return true;}public int getViewTypeCount(){return 2;}public int getItemViewType(int p){return doc.blocks.get(p).image.isEmpty()?0:1;}
        public View getView(int position,View recycled,ViewGroup parent){
            BookDocument.Block b=doc.blocks.get(position);int width=reader.getWidth()>0?reader.getWidth():getResources().getDisplayMetrics().widthPixels;
            int side=Math.max(dp(24),(width-dp(720))/2);
            if(b.image.isEmpty()){
                TextView cell=recycled instanceof TextView?(TextView)recycled:text("",21);cell.setTag(position);cell.setTextSize(store.preferences.getInt("font_size",21));
                cell.setTextColor(foreground);cell.setPadding(side,dp(4),side,dp(4));cell.setLineSpacing(dp(store.preferences.getInt("line_spacing",9)),1);
                cell.setIncludeFontPadding(true);cell.setBreakStrategy(0);cell.setHyphenationFrequency(0);
                try{cell.setText(doc.text(position));}catch(IOException failure){cell.setText("正文读取失败，请返回书架重新导入。 ");cell.setContentDescription("正文读取失败");}
                return cell;
            }
            ImageView picture=recycled instanceof ImageView?(ImageView)recycled:new ImageView(MainActivity.this);picture.setTag(position);picture.setAdjustViewBounds(true);picture.setScaleType(ImageView.ScaleType.FIT_CENTER);picture.setPadding(side,dp(12),side,dp(12));picture.setMaxHeight(dp(420));picture.setContentDescription(b.description);
            Bitmap bitmap=images.get(b.image);
            if(bitmap==null){
                File file=new File(doc.directory,b.image);BitmapFactory.Options bounds=new BitmapFactory.Options();bounds.inJustDecodeBounds=true;BitmapFactory.decodeFile(file.getPath(),bounds);
                bounds.inSampleSize=1;while(bounds.outWidth/bounds.inSampleSize>2048||bounds.outHeight/bounds.inSampleSize>2048)bounds.inSampleSize*=2;
                bounds.inJustDecodeBounds=false;bounds.inPreferredConfig=Bitmap.Config.RGB_565;
                bitmap=BitmapFactory.decodeFile(file.getPath(),bounds);if(bitmap!=null)images.put(b.image,bitmap);
            }
            picture.setImageBitmap(bitmap);if(bitmap==null){picture.setMinimumHeight(dp(48));picture.setContentDescription(b.description+"（图片无法显示）");}return picture;
        }
    }
    private BookDocument.Position capture(){
        if(doc==null||reader==null||restoring||reader.getChildCount()==0)return anchor;
        int block=reader.getFirstVisiblePosition(),offset=0;View first=reader.getChildAt(0);
        if(first instanceof TextView){TextView cell=(TextView)first;Layout layout=cell.getLayout();if(layout!=null){int y=Math.max(0,reader.getPaddingTop()-cell.getTop()-cell.getTotalPaddingTop());int line=layout.getLineForVertical(y);offset=layout.getLineStart(line);}}
        anchor=doc.clamp(block,offset);return anchor;
    }
    private void restore(BookDocument.Position position){
        if(doc==null||reader==null)return;BookDocument.Position at=doc.clamp(position.block,position.offset);anchor=at;restoring=true;int token=++restoreRevision;
        reader.setSelectionFromTop(at.block,0);
        reader.post(()->{
            if(doc==null||reader==null||token!=restoreRevision)return;
            View first=reader.getChildAt(0);int top=0;
            if(reader.getFirstVisiblePosition()==at.block&&first instanceof TextView){TextView cell=(TextView)first;Layout layout=cell.getLayout();if(layout!=null){int line=layout.getLineForOffset(Math.min(at.offset,cell.length()));top=-cell.getTotalPaddingTop()-layout.getLineTop(line);}}
            reader.setSelectionFromTop(at.block,top);reader.post(()->{if(token==restoreRevision){restoring=false;capture();saveAnchor.run();}});
        });
    }
    private void seek(BookDocument.Position at){restore(at);store.saveRead(bookId,at.block,at.offset);}
    private Dialog present(String title,LinearLayout content,boolean bottom){
        if(dialog!=null)dialog.dismiss();Dialog shown=new Dialog(this);shown.setTitle(title);shown.setContentView(content);shown.setCanceledOnTouchOutside(true);
        Window window=shown.getWindow();if(window!=null){window.setBackgroundDrawable(surface());window.setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING|WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);}
        shown.setOnDismissListener(d->{speechStatus=null;listenProgress=null;playButton=null;immersive(doc!=null);});
        dialog=shown;shown.show();
        int available=getResources().getDisplayMetrics().widthPixels;
        shown.getWindow().setLayout(Math.min(available-dp(16),dp(620)),ViewGroup.LayoutParams.WRAP_CONTENT);
        if(bottom)shown.getWindow().setGravity(Gravity.BOTTOM);return shown;
    }
    private void title(LinearLayout content,String title){
        LinearLayout bar=row();TextView heading=text(title,19);heading.setTypeface(null,Typeface.BOLD);bar.addView(heading,new LinearLayout.LayoutParams(0,-2,1));bar.addView(button("收起",()->{if(dialog!=null)dialog.dismiss();}));content.addView(bar);
    }
    private void controls(){
        if(doc==null)return;capture();saveAnchor.run();LinearLayout panel=column();title(panel,doc.title);
        LinearLayout actions=row();equal(actions,button("书架",()->{dialog.dismiss();capture();saveAnchor.run();library();}));equal(actions,button("目录",this::toc));equal(actions,button("字号",this::settings));equal(actions,button("朗读",this::speechPanel));panel.addView(actions);
        TextView progress=text(String.format(Locale.CHINA,"阅读 %.1f%% · %d / %d 段",doc.progress(anchor.block,anchor.offset)*100,anchor.block+1,doc.blocks.size()),13);progress.setPadding(0,dp(8),0,0);panel.addView(progress);
        SeekBar seek=new SeekBar(this);seek.setMax(1000);seek.setProgress(Math.round(doc.progress(anchor.block,anchor.offset)*1000));seek.setContentDescription("阅读进度");panel.addView(seek,new LinearLayout.LayoutParams(-1,dp(48)));
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(SeekBar bar,int value,boolean user){if(user)progress.setText("跳转至 "+(value/10f)+"%");}public void onStartTrackingTouch(SeekBar bar){}public void onStopTrackingTouch(SeekBar bar){seek(doc.atProgress(bar.getProgress()/1000f));progress.setText("阅读 "+bar.getProgress()/10f+"%");}
        });present("阅读控制",panel,true);
    }
    private void toc(){
        if(doc==null)return;BookDocument.Position live=capture();saveAnchor.run();int selected=doc.currentChapter(live.block);
        LinearLayout panel=column();title(panel,"目录");
        TextView hint=text(doc.toc.isEmpty()?"未识别到可靠章节，可使用阅读进度。":doc.format.equals("TXT")?"TXT 目录由标题格式推测，可能有遗漏。":"",12);hint.setTextColor(muted);panel.addView(hint);
        EditText query=new EditText(this);query.setId(R.id.toc_query);query.setSingleLine(true);query.setHint("查找章节");query.setTextColor(foreground);query.setHintTextColor(muted);query.setText("");panel.addView(query,new LinearLayout.LayoutParams(-1,dp(52)));
        ListView list=new ListView(this);list.setId(R.id.toc_list);list.setDivider(null);list.setChoiceMode(ListView.CHOICE_MODE_SINGLE);list.setFocusableInTouchMode(true);
        int height=Math.max(dp(160),Math.min(dp(390),getResources().getDisplayMetrics().heightPixels/2));panel.addView(list,new LinearLayout.LayoutParams(-1,height));
        List<Integer>filtered=new ArrayList<>();for(int i=0;i<doc.toc.size();i++)filtered.add(i);
        BaseAdapter tocAdapter=new BaseAdapter(){
            public int getCount(){return filtered.size();}public Object getItem(int p){return filtered.get(p);}public long getItemId(int p){return filtered.get(p);}
            public View getView(int p,View recycled,ViewGroup parent){
                int index=filtered.get(p);BookDocument.Chapter chapter=doc.toc.get(index);boolean current=index==selected;
                TextView cell=recycled instanceof TextView?(TextView)recycled:text("",17);cell.setText((current?"✓  ":"     ")+chapter.title);
                cell.setTextColor(foreground);cell.setTypeface(null,current?Typeface.BOLD:Typeface.NORMAL);cell.setMinHeight(dp(52));cell.setGravity(Gravity.CENTER_VERTICAL);
                cell.setPadding(dp(4+Math.min(chapter.depth,4)*12),dp(10),dp(4),dp(10));cell.setSelected(current);cell.setContentDescription(chapter.title+(current?"，当前阅读章节":""));return cell;
            }
        };list.setAdapter(tocAdapter);
        list.setOnItemClickListener((parent,view,position,id)->{BookDocument.Chapter chapter=doc.toc.get(filtered.get(position));dialog.dismiss();seek(new BookDocument.Position(chapter.block,0));});
        query.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int a,int c,int after){}public void onTextChanged(CharSequence s,int a,int before,int count){
            filtered.clear();String needle=s.toString().toLowerCase(Locale.ROOT);for(int i=0;i<doc.toc.size();i++)if(doc.toc.get(i).title.toLowerCase(Locale.ROOT).contains(needle))filtered.add(i);tocAdapter.notifyDataSetChanged();
            if(needle.isEmpty()&&selected>=0)list.post(()->list.setSelectionFromTop(selected,dp(90)));
        }public void afterTextChanged(Editable value){}});
        present("目录",panel,false);list.requestFocus();if(selected>=0)list.post(()->list.setSelectionFromTop(selected,dp(90)));
    }
    private void settings(){
        LinearLayout panel=column();title(panel,"阅读设置");
        slider(panel,"字号",14,36,store.preferences.getInt("font_size",21),value->applyReading("font_size",value));
        slider(panel,"行距",0,24,store.preferences.getInt("line_spacing",9),value->applyReading("line_spacing",value));
        panel.addView(text("主题",16));LinearLayout themes=row();String[]names={"浅色","护眼","深色"},keys={"light","warm","dark"};
        for(int i=0;i<3;i++){final String key=keys[i];equal(themes,button(names[i],()->{BookDocument.Position keep=capture();store.preferences.edit().putString("theme",key).apply();colors();root.setBackgroundColor(background);reader.setBackgroundColor(background);adapter.notifyDataSetChanged();TextView more=findViewById(R.id.reader_controls);more.setTextColor(foreground);restore(keep);settings();}));}panel.addView(themes);present("阅读设置",panel,false);
    }
    private interface Value {void set(int value);}
    private void slider(LinearLayout panel,String name,int min,int max,int value,Value changed){
        TextView label=text(name+" · "+value,16);label.setPadding(0,dp(12),0,0);panel.addView(label);
        SeekBar bar=new SeekBar(this);bar.setMax(max-min);bar.setProgress(value-min);bar.setContentDescription(name);panel.addView(bar,new LinearLayout.LayoutParams(-1,dp(48)));
        bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar b,int v,boolean user){label.setText(name+" · "+(v+min));}public void onStartTrackingTouch(SeekBar b){}public void onStopTrackingTouch(SeekBar b){changed.set(b.getProgress()+min);}});
    }
    private void applyReading(String key,int value){BookDocument.Position keep=capture();store.preferences.edit().putInt(key,value).apply();adapter.notifyDataSetChanged();restore(keep);}
    private void speechPanel(){
        if(doc==null)return;LinearLayout panel=column();title(panel,"朗读");
        TextView status=text("正在查询系统声音…",14);status.setId(R.id.speech_status);status.setPadding(0,dp(8),0,dp(12));panel.addView(status);
        TextView progress=text("",13);panel.addView(progress);
        Button play=button("继续听书",()->{
            if(speech!=null&&speech.bookId().equals(bookId)&&speech.state()==SpeechService.State.PLAYING)SpeechService.command(this,SpeechService.PAUSE,null,null);
            else{
                notificationPermission();
                if(speech!=null&&speech.bookId().equals(bookId)&&(speech.state()==SpeechService.State.PAUSED||speech.state()==SpeechService.State.STOPPED))SpeechService.command(this,SpeechService.RESUME,null,null);
                else SpeechService.command(this,SpeechService.PLAY,bookId,null);
            }
        });play.setId(R.id.speech_play);panel.addView(play,new LinearLayout.LayoutParams(-1,dp(48)));
        LinearLayout navigation=row();equal(navigation,button("上一章",()->{if(speech!=null)speech.navigateChapter(-1);}));equal(navigation,button("下一章",()->{if(speech!=null)speech.navigateChapter(1);}));equal(navigation,button("停止",()->SpeechService.command(this,SpeechService.STOP,null,null)));panel.addView(navigation);
        LinearLayout paragraphs=row();equal(paragraphs,button("上一段",()->{if(speech!=null)speech.paragraph(-1);}));equal(paragraphs,button("下一段",()->{if(speech!=null)speech.paragraph(1);}));panel.addView(paragraphs);
        LinearLayout origins=row();equal(origins,button("从当前阅读处朗读",()->{notificationPermission();SpeechService.command(this,SpeechService.READ,bookId,capture());}));equal(origins,button("定位听书位置",()->{if(speech!=null&&speech.bookId().equals(bookId)){BookDocument.Position at=speech.position();dialog.dismiss();seek(at);}else{BookDocument.Position at=store.listen(bookId);dialog.dismiss();seek(at);}}));panel.addView(origins);
        int rate=Math.round(store.preferences.getFloat("speech_rate",1f)*100);slider(panel,"语速（%）",50,200,rate,value->{if(speech!=null)speech.changeRate(value/100f);else store.preferences.edit().putFloat("speech_rate",value/100f).apply();});
        LinearLayout catalog=row();equal(catalog,button("选择声音",this::chooseVoice));equal(catalog,button("切换引擎",this::chooseEngine));panel.addView(catalog);
        LinearLayout system=row();equal(system,button("重新检查",()->{if(speech!=null)speech.initializeEngine();}));equal(system,button("系统语音设置",this::ttsSettings));panel.addView(system);
        TextView note=text("仅使用当前引擎报告为已安装的中文离线声音。部分引擎暂停后会从当前句重读。",12);note.setTextColor(muted);note.setPadding(0,dp(8),0,0);panel.addView(note);
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(false);scroll.addView(panel);
        LinearLayout wrapper=new LinearLayout(this);wrapper.setOrientation(LinearLayout.VERTICAL);wrapper.addView(scroll,new LinearLayout.LayoutParams(-1,Math.min(dp(660),getResources().getDisplayMetrics().heightPixels-dp(90))));
        present("朗读",wrapper,false);speechStatus=status;listenProgress=progress;playButton=play;changed();
    }
    @Override public void changed(){
        if(speechStatus==null)return;speechStatus.setText(speech==null?"正在连接系统朗读服务…":speech.message());
        if(playButton!=null){playButton.setEnabled(speech!=null&&speech.available());playButton.setText(speech!=null&&speech.bookId().equals(bookId)&&speech.state()==SpeechService.State.PLAYING?"暂停":"继续听书");}
        if(listenProgress!=null&&doc!=null){BookDocument.Position at=speech!=null&&speech.bookId().equals(bookId)?speech.position():store.listen(bookId);int chapter=doc.currentChapter(at.block);listenProgress.setText(String.format(Locale.CHINA,"听书 %.1f%%",doc.progress(at.block,at.offset)*100)+(chapter>=0?" · "+doc.toc.get(chapter).title:""));}
    }
    private void chooseVoice(){
        if(speech==null){error("系统朗读服务尚未连接。");return;}List<Voice>voices=speech.voices();if(voices.isEmpty()){error(speech.message());return;}
        String[]labels=new String[voices.size()];for(int i=0;i<labels.length;i++)labels[i]=voices.get(i).getName()+" · "+voices.get(i).getLocale().getDisplayName(Locale.CHINA)+" · 离线";
        new AlertDialog.Builder(this).setTitle("本机中文离线声音").setItems(labels,(d,which)->speech.changeVoice(voices.get(which).getName())).setNegativeButton("取消",null).show();
    }
    private void chooseEngine(){
        if(speech==null)return;List<TextToSpeech.EngineInfo>engines=speech.engines();if(engines.isEmpty()){error("系统未发现朗读引擎，请检查系统设置。");return;}
        String[]labels=new String[engines.size()];for(int i=0;i<labels.length;i++)labels[i]=engines.get(i).label;
        new AlertDialog.Builder(this).setTitle("已安装的系统引擎").setItems(labels,(d,which)->speech.changeEngine(engines.get(which).name)).setNegativeButton("取消",null).show();
    }
    private void notificationPermission(){if(Build.VERSION.SDK_INT>=33&&checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=android.content.pm.PackageManager.PERMISSION_GRANTED)requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},NOTIFY_PERMISSION);}
    private void ttsSettings(){
        try{startActivity(new Intent("com.android.settings.TTS_SETTINGS"));}
        catch(ActivityNotFoundException missing){try{startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));}catch(ActivityNotFoundException failure){error("无法打开系统语音设置，请手动进入设置中的文字转语音选项。");}}
    }
    private void error(String message){if(!destroyed)new AlertDialog.Builder(this).setTitle("eBOOK").setMessage(message==null?"操作失败，请重试。":message).setPositiveButton("好",null).show();}
}
