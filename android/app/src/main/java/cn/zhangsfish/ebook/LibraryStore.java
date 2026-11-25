package cn.zhangsfish.ebook;

import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.provider.OpenableColumns;
import cn.zhangsfish.ebook.core.*;
import java.io.*;
import java.security.*;
import java.util.*;

/** App-owned copies and independent reading/listening state. Book text never leaves the sandbox. */
public final class LibraryStore {
    private final Context context;
    public final SharedPreferences preferences;
    public final File books;
    public LibraryStore(Context context){
        this.context=context.getApplicationContext();preferences=context.getSharedPreferences("reader",Context.MODE_PRIVATE);
        books=new File(context.getFilesDir(),"books");books.mkdirs();
    }
    public static final class Record {
        public final String id;public final BookDocument doc;
        Record(String id,BookDocument doc){this.id=id;this.doc=doc;}
    }
    public List<Record>list()throws IOException{
        List<Record>out=new ArrayList<>();File[]dirs=books.listFiles();if(dirs==null)return out;
        for(File folder:dirs)if(folder.isDirectory()&&!folder.getName().startsWith("pending_")){
            try{out.add(new Record(folder.getName(),BookDocument.load(folder)));}
            catch(IOException broken){throw new IOException("书架索引损坏（"+folder.getName().substring(0,Math.min(8,folder.getName().length()))+"），请重试或清理应用数据前先备份原书。",broken);}
        }
        out.sort((a,b)->Long.compare(preferences.getLong("opened_"+b.id,0),preferences.getLong("opened_"+a.id,0)));return out;
    }
    public String displayName(Uri uri){
        try(Cursor cursor=context.getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){
            if(cursor!=null&&cursor.moveToFirst())return cursor.getString(0);
        }catch(RuntimeException ignored){/* fallback */}
        return "导入书籍";
    }
    public Record importUri(Uri uri,String hint)throws IOException{
        String name=displayName(uri);String lower=name.toLowerCase(Locale.ROOT);
        boolean epub=lower.endsWith(".epub");
        if(!epub&&!lower.endsWith(".txt"))throw new IOException("请选择 .epub 或 .txt 文件。");
        File pending=new File(books,"pending_"+UUID.randomUUID());if(!pending.mkdirs())throw new IOException("无法建立导入目录。");
        try{
            File input=new File(pending,"source");MessageDigest hash;
            try{hash=MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException impossible){throw new IOException(impossible);}
            long limit=epub?64L*1024*1024:TextCodec.MAX_BYTES;
            try(InputStream in=context.getContentResolver().openInputStream(uri);OutputStream out=new FileOutputStream(input)){
                if(in==null)throw new IOException("无法读取所选文件。");
                byte[]buf=new byte[32768];long total=0;int n;
                while((n=in.read(buf))!=-1){total+=n;if(total>limit)throw new IOException(epub?"EPUB 超过 64 MiB。":"TXT 超过 32 MiB。");hash.update(buf,0,n);out.write(buf,0,n);}
            }
            StringBuilder id=new StringBuilder();for(byte b:hash.digest())id.append(String.format(Locale.ROOT,"%02x",b&255));
            File dest=directory(id.toString());
            if(dest.exists())return new Record(id.toString(),BookDocument.load(dest));
            String title=name.substring(0,name.lastIndexOf('.'));if(title.length()>500)title=title.substring(0,500);
            BookDocument doc=epub?EpubImporter.parse(input,pending,title):TxtImporter.parse(input,pending,title,hint);
            if(!input.delete())throw new IOException("无法清理导入中间文件。");
            if(!pending.renameTo(dest))throw new IOException("无法保存书籍，请检查存储空间。");
            doc.directory=dest;preferences.edit().putLong("opened_"+id,System.currentTimeMillis()).apply();
            return new Record(id.toString(),doc);
        }finally{if(pending.exists())deleteTree(pending);}
    }
    public File directory(String id)throws IOException{
        if(!id.matches("[a-f0-9]{64}"))throw new IOException("书籍标识无效。");return new File(books,id);
    }
    public BookDocument open(String id)throws IOException{return BookDocument.load(directory(id));}
    public BookDocument.Position read(String id){return new BookDocument.Position(preferences.getInt("r_block_"+id,0),preferences.getInt("r_offset_"+id,0));}
    public BookDocument.Position listen(String id){return new BookDocument.Position(preferences.getInt("l_block_"+id,0),preferences.getInt("l_offset_"+id,0));}
    public void saveRead(String id,int block,int offset){preferences.edit().putInt("r_block_"+id,block).putInt("r_offset_"+id,offset).apply();}
    public void saveListen(String id,int block,int offset){preferences.edit().putInt("l_block_"+id,block).putInt("l_offset_"+id,offset).apply();}
    public void opened(String id){preferences.edit().putString("last_book",id).putLong("opened_"+id,System.currentTimeMillis()).apply();}
    public void remove(String id)throws IOException{
        deleteTree(directory(id));preferences.edit().remove("r_block_"+id).remove("r_offset_"+id).remove("l_block_"+id).remove("l_offset_"+id).remove("opened_"+id).apply();
        if(id.equals(preferences.getString("last_book","")))preferences.edit().remove("last_book").apply();
    }
    private void deleteTree(File file)throws IOException{
        String allowed=books.getCanonicalPath()+File.separator;
        if(!file.getCanonicalPath().startsWith(allowed))throw new IOException("清理路径不在书架内。");
        File[]children=file.listFiles();if(children!=null)for(File child:children)deleteTree(child);
        if(file.exists()&&!file.delete())throw new IOException("无法删除本地书籍文件。");
    }
}
