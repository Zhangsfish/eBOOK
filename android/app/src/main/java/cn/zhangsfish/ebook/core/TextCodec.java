package cn.zhangsfish.ebook.core;

import java.io.*;
import java.nio.charset.*;

/** Strict streaming decoding. Detection never substitutes malformed bytes. */
public final class TextCodec {
    public static final long MAX_BYTES = 32L * 1024 * 1024;
    public static final class Encoding {
        public final String charset;
        public final int bom;
        Encoding(String charset, int bom) { this.charset = charset; this.bom = bom; }
    }
    public interface Lines { void accept(int number, String part, boolean end, boolean continued) throws IOException; }

    public static Encoding detect(File file, String hint) throws IOException {
        if (file.length() == 0) throw new IOException("TXT 文件为空。");
        if (file.length() > MAX_BYTES) throw new IOException("TXT 超过 32 MiB，请先拆分文件。");
        byte[] sample = new byte[(int) Math.min(4096, file.length())];
        try (DataInputStream in = new DataInputStream(new FileInputStream(file))) { in.readFully(sample); }
        if (starts(sample, 255,254,0,0) || starts(sample,0,0,254,255)) throw new IOException("不支持 UTF-32，请转为 UTF-8。");
        if (starts(sample,239,187,191)) return verified(file, new Encoding("UTF-8",3));
        if (starts(sample,255,254)) return verified(file, new Encoding("UTF-16LE",2));
        if (starts(sample,254,255)) return verified(file, new Encoding("UTF-16BE",2));
        if (hint != null && !hint.equals("自动")) return verified(file, new Encoding(hint,0));
        if (looksUTF16(sample,true) && file.length()%2==0) return verified(file, new Encoding("UTF-16LE",0));
        if (looksUTF16(sample,false) && file.length()%2==0) return verified(file, new Encoding("UTF-16BE",0));
        try { return verified(file, new Encoding("UTF-8",0)); } catch (IOException ignored) { /* legacy candidate */ }
        try { return verified(file, new Encoding("GB18030",0)); }
        catch (IOException invalid) { throw new IOException("无法严格解码 TXT；可重新选择编码。未使用有损字符替换。",invalid); }
    }
    private static boolean starts(byte[] data, int... prefix) {
        if (data.length < prefix.length) return false;
        for (int i=0;i<prefix.length;i++) if ((data[i]&255)!=prefix[i]) return false;
        return true;
    }
    private static boolean looksUTF16(byte[] data, boolean little) {
        int pairs=data.length/2, high=0,low=0;
        for(int i=0;i<pairs;i++){ if(data[2*i+(little?1:0)]==0)high++;if(data[2*i+(little?0:1)]==0)low++; }
        return pairs>1 && high*4>pairs && low*8<pairs;
    }
    private static Encoding verified(File file, Encoding enc) throws IOException {
        final boolean[] readable={false};
        scan(file,enc,(line,part,end,continued)->{
            for(int i=0;i<part.length();i++){
                char c=part.charAt(i);
                if(c=='\ufffd'||(c<32 && c!='\t' && c!='\f')) throw new IOException("文件含无效字符或二进制控制字节。");
                if(!Character.isWhitespace(c))readable[0]=true;
            }
        });
        if(!readable[0])throw new IOException("TXT 没有可阅读正文。");
        return enc;
    }
    public static void scan(File file, Encoding enc, Lines sink) throws IOException {
        CharsetDecoder decoder=Charset.forName(enc.charset).newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT);
        try(InputStream raw=new FileInputStream(file)){
            for(int i=0;i<enc.bom;i++) if(raw.read()<0)throw new EOFException();
            try(Reader reader=new BufferedReader(new InputStreamReader(raw,decoder))){
                StringBuilder line=new StringBuilder();int number=0;boolean skipLF=false,continued=false;
                char[] chunk=new char[8192];int n;
                while((n=reader.read(chunk))!=-1){
                    for(int i=0;i<n;i++){
                        char c=chunk[i];
                        if(c=='\n'&&skipLF){skipLF=false;continue;} skipLF=false;
                        if(c=='\n'||c=='\r'){
                            sink.accept(number++,line.toString(),true,continued);line.setLength(0);continued=false;skipLF=c=='\r';
                        }else{
                            line.append(c);
                            if(line.length()>=4096&&!Character.isHighSurrogate(c)){
                                sink.accept(number,line.toString(),false,true);line.setLength(0);continued=true;
                            }
                        }
                    }
                }
                if(line.length()>0||continued)sink.accept(number,line.toString(),true,continued);
            }
        } catch (CharacterCodingException malformed) { throw new IOException(enc.charset+" 字节无效，请检查文件或重选编码。",malformed); }
    }
}
