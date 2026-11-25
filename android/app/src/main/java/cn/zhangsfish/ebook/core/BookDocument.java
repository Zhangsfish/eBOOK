package cn.zhangsfish.ebook.core;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Disk-backed text blocks. No complete-book string is retained by the reader. */
public final class BookDocument {
    public static final int MAX_BLOCK = 1600;
    private static final int MAGIC = 0x45424b32;
    public String title = "", author = "", encoding = "", format = "";
    public final List<Block> blocks = new ArrayList<>();
    public final List<Chapter> toc = new ArrayList<>();
    public int totalChars;
    public File directory;

    public static final class Block {
        public final long byteOffset;
        public final int bytes, chars, textStart;
        public final String image, description;
        public Block(long offset, int bytes, int chars, int start, String image, String description) {
            this.byteOffset = offset; this.bytes = bytes; this.chars = chars; this.textStart = start;
            this.image = image; this.description = description;
        }
    }
    public static final class Chapter {
        public final String title;
        public final int block, depth;
        public Chapter(String title, int block, int depth) {
            this.title = title; this.block = block; this.depth = depth;
        }
    }
    public static final class Position {
        public final int block, offset;
        public Position(int block, int offset) { this.block = block; this.offset = offset; }
    }
    public Position clamp(int block, int offset) {
        if (blocks.isEmpty()) return new Position(0, 0);
        int b = Math.max(0, Math.min(blocks.size() - 1, block));
        return new Position(b, Math.max(0, Math.min(blocks.get(b).chars, offset)));
    }
    public int currentChapter(int liveBlock) {
        int result = -1;
        for (int i = 0; i < toc.size(); i++) {
            Chapter c = toc.get(i);
            if (c.block < 0 || c.block >= blocks.size() || c.block > liveBlock) continue;
            if (result < 0 || c.block > toc.get(result).block
                    || (c.block == toc.get(result).block && c.depth > toc.get(result).depth)) result = i;
        }
        return result;
    }
    public float progress(int block, int offset) {
        if (blocks.isEmpty() || totalChars == 0) return 0;
        Position p = clamp(block, offset);
        return Math.min(1f, (blocks.get(p.block).textStart + p.offset) / (float) totalChars);
    }
    public Position atProgress(float progress) {
        if (blocks.isEmpty()) return new Position(0, 0);
        int target = (int) (totalChars * Math.max(0, Math.min(1, progress)));
        int lo = 0, hi = blocks.size();
        while (lo < hi) {
            int mid = (lo + hi) >>> 1;
            if (blocks.get(mid).textStart <= target) lo = mid + 1; else hi = mid;
        }
        int b = Math.max(0, lo - 1);
        return clamp(b, target - blocks.get(b).textStart);
    }
    public String text(int index) throws IOException {
        Block b = blocks.get(index);
        if (!b.image.isEmpty()) return "";
        if (b.bytes < 0 || b.bytes > MAX_BLOCK * 4) throw new IOException("正文索引损坏，请重新导入。 ");
        byte[] buffer = new byte[b.bytes];
        try (RandomAccessFile file = new RandomAccessFile(new File(directory, "text.dat"), "r")) {
            file.seek(b.byteOffset); file.readFully(buffer);
        }
        return new String(buffer, StandardCharsets.UTF_8);
    }
    /** Navigate actual newline paragraphs, independently of rendering block size. */
    public Position paragraph(Position position,int direction)throws IOException{
        Position p=clamp(position.block,position.offset);
        if(direction>=0){
            boolean crossed=false;
            for(int b=p.block;b<blocks.size();b++){
                String value=text(b);int from=b==p.block?SpeechChunks.safeOffset(value,p.offset):0;
                for(int i=from;i<value.length();){int cp=value.codePointAt(i);
                    if(crossed&&!Character.isWhitespace(cp))return new Position(b,i);
                    if(cp=='\n')crossed=true;i+=Character.charCount(cp);
                }
            }
            return clamp(blocks.size()-1,blocks.get(blocks.size()-1).chars);
        }
        boolean content=false;
        for(int b=p.block;b>=0;b--){
            String value=text(b);int from=b==p.block?Math.min(value.length(),p.offset)-1:value.length()-1;
            for(int i=from;i>=0;i--){char c=value.charAt(i);
                if(content&&c=='\n'){
                    for(int next=b;next<blocks.size();next++){
                        String v=text(next);for(int j=next==b?i+1:0;j<v.length();j++)if(!Character.isWhitespace(v.charAt(j)))return new Position(next,j);
                    }
                }
                if(!Character.isWhitespace(c))content=true;
            }
        }
        return new Position(0,0);
    }
    public void save() throws IOException {
        try (DataOutputStream out = new DataOutputStream(new BufferedOutputStream(new FileOutputStream(new File(directory, "index.bin"))))) {
            out.writeInt(MAGIC); out.writeUTF(title); out.writeUTF(author); out.writeUTF(encoding);
            out.writeUTF(format); out.writeInt(totalChars); out.writeInt(blocks.size());
            for (Block b : blocks) {
                out.writeLong(b.byteOffset); out.writeInt(b.bytes); out.writeInt(b.chars);
                out.writeInt(b.textStart); out.writeUTF(b.image); out.writeUTF(b.description);
            }
            out.writeInt(toc.size());
            for (Chapter c : toc) { out.writeUTF(c.title); out.writeInt(c.block); out.writeInt(c.depth); }
        }
    }
    public static BookDocument load(File directory) throws IOException {
        BookDocument doc = new BookDocument(); doc.directory = directory;
        try (DataInputStream in = new DataInputStream(new BufferedInputStream(new FileInputStream(new File(directory, "index.bin"))))) {
            if (in.readInt() != MAGIC) throw new IOException("书籍索引版本无效，请重新导入。");
            doc.title = in.readUTF(); doc.author = in.readUTF(); doc.encoding = in.readUTF();
            doc.format = in.readUTF(); doc.totalChars = in.readInt();
            int count = checkedCount(in.readInt(), 200000);
            for (int i = 0; i < count; i++) {
                long at = in.readLong(); int bytes = in.readInt(), chars = in.readInt(), start = in.readInt();
                String image = in.readUTF(), description = in.readUTF();
                if (at < 0 || bytes < 0 || bytes > MAX_BLOCK * 4 || chars < 0 || chars > MAX_BLOCK
                        || start < 0 || (!image.isEmpty() && (image.contains("..") || image.contains("/") || image.contains("\\"))))
                    throw new IOException("书籍索引损坏。");
                doc.blocks.add(new Block(at, bytes, chars, start, image, description));
            }
            int chapters = checkedCount(in.readInt(), 50000);
            for (int i = 0; i < chapters; i++) doc.toc.add(new Chapter(in.readUTF(), in.readInt(), in.readInt()));
            if (doc.blocks.isEmpty() || doc.totalChars < 0) throw new IOException("书籍没有正文。");
        }
        return doc;
    }
    private static int checkedCount(int n, int max) throws IOException {
        if (n < 0 || n > max) throw new IOException("书籍索引超出安全范围。");
        return n;
    }

    public static final class Writer implements Closeable {
        public final BookDocument doc;
        private final OutputStream out;
        private final StringBuilder pending = new StringBuilder();
        private long bytes;
        public Writer(BookDocument doc) throws IOException {
            this.doc = doc;
            if (!doc.directory.isDirectory() && !doc.directory.mkdirs()) throw new IOException("无法创建书籍目录。");
            out = new BufferedOutputStream(new FileOutputStream(new File(doc.directory, "text.dat")));
        }
        public void append(String text) throws IOException {
            for (int i = 0; i < text.length();) {
                int cp = text.codePointAt(i), size = Character.charCount(cp);
                if (pending.length() + size > MAX_BLOCK) flushBlock();
                pending.appendCodePoint(cp); i += size;
                if (pending.length() >= 1200 && (cp == '\n' || cp == '。' || cp == '！' || cp == '？')) flushBlock();
            }
        }
        public void flushBlock() throws IOException {
            if (pending.length() == 0) return;
            if (doc.blocks.size() >= 200000) throw new IOException("书籍段落过多。");
            String text = pending.toString(); byte[] data = text.getBytes(StandardCharsets.UTF_8);
            out.write(data);
            doc.blocks.add(new Block(bytes, data.length, text.length(), doc.totalChars, "", ""));
            bytes += data.length; doc.totalChars += text.length(); pending.setLength(0);
        }
        public void image(String filename, String description) throws IOException {
            flushBlock(); doc.blocks.add(new Block(bytes, 0, 0, doc.totalChars, filename, description));
        }
        public int nextBlock() throws IOException { flushBlock(); return doc.blocks.size(); }
        @Override public void close() throws IOException { try { flushBlock(); } finally { out.close(); } }
    }
}
