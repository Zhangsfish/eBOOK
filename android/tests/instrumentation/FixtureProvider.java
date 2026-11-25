package cn.zhangsfish.ebook.tests;

import android.database.*;
import android.os.*;
import android.provider.*;
import java.io.*;
import java.util.*;

/** Original-fixture source visible to the REAL system document picker, test APK only. */
public final class FixtureProvider extends DocumentsProvider {
    private static final String[]ROOTS={DocumentsContract.Root.COLUMN_ROOT_ID,DocumentsContract.Root.COLUMN_DOCUMENT_ID,DocumentsContract.Root.COLUMN_TITLE,DocumentsContract.Root.COLUMN_FLAGS,DocumentsContract.Root.COLUMN_MIME_TYPES};
    private static final String[]DOCS={DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE,DocumentsContract.Document.COLUMN_SIZE,DocumentsContract.Document.COLUMN_FLAGS};
    @Override public boolean onCreate(){return true;}
    @Override public Cursor queryRoots(String[]projection){MatrixCursor c=new MatrixCursor(ROOTS);c.addRow(new Object[]{"originals","root","eBOOK 原创测试材料",DocumentsContract.Root.FLAG_LOCAL_ONLY|DocumentsContract.Root.FLAG_SUPPORTS_IS_CHILD,"*/*"});return c;}
    private Set<String>names()throws FileNotFoundException{try{return new HashSet<>(Arrays.asList(getContext().getAssets().list("")));}catch(IOException e){throw new FileNotFoundException();}}
    private void add(MatrixCursor c,String id)throws FileNotFoundException{
        if(id.equals("root")){c.addRow(new Object[]{id,"eBOOK 原创测试材料",DocumentsContract.Document.MIME_TYPE_DIR,0,0});return;}
        if(!names().contains(id)||id.contains("/"))throw new FileNotFoundException();
        long bytes=0;try(InputStream in=getContext().getAssets().open(id)){bytes=in.available();}catch(IOException e){throw new FileNotFoundException();}
        c.addRow(new Object[]{id,id,id.endsWith(".epub")?"application/epub+zip":"text/plain",bytes,0});
    }
    @Override public Cursor queryDocument(String id,String[]projection)throws FileNotFoundException{MatrixCursor c=new MatrixCursor(DOCS);add(c,id);return c;}
    @Override public Cursor queryChildDocuments(String parent,String[]projection,String sort)throws FileNotFoundException{
        MatrixCursor c=new MatrixCursor(DOCS);if(parent.equals("root")){List<String>sorted=new ArrayList<>(names());Collections.sort(sorted);for(String name:sorted)if(name.endsWith(".txt")||name.endsWith(".epub"))add(c,name);}return c;
    }
    @Override public boolean isChildDocument(String parent,String child){try{return parent.equals("root")&&names().contains(child);}catch(FileNotFoundException bad){return false;}}
    @Override public ParcelFileDescriptor openDocument(String id,String mode,CancellationSignal signal)throws FileNotFoundException{
        if(!mode.equals("r")||!names().contains(id)||id.contains("/"))throw new FileNotFoundException();
        File file=new File(getContext().getCacheDir(),id);
        if(!file.exists())try(InputStream in=getContext().getAssets().open(id);OutputStream out=new FileOutputStream(file)){byte[]buf=new byte[32768];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);}catch(IOException e){throw new FileNotFoundException();}
        return ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY);
    }
}
