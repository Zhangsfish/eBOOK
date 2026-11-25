import cn.zhangsfish.ebook.core.*;
import java.io.*;
import java.nio.charset.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Black-box tests use the actual shipped parser, not a duplicate implementation. */
public final class CoreTests {
    interface Check {void run()throws Exception;}
    static int passed,failed;
    static File temporary,root;
    static final List<String>results=new ArrayList<>();
    static void test(String name,Check action){
        long start=System.nanoTime();
        try{action.run();passed++;results.add("{\"name\":\""+name+"\",\"status\":\"PASS\",\"ms\":"+(System.nanoTime()-start)/1000000+"}");}
        catch(Throwable e){failed++;results.add("{\"name\":\""+name+"\",\"status\":\"FAIL\"}");System.err.println("FAIL "+name+": "+e);e.printStackTrace();}
    }
    static void expect(boolean condition,String reason){if(!condition)throw new AssertionError(reason);}
    static void rejects(Check action)throws Exception{boolean rejected=false;try{action.run();}catch(IOException e){rejected=true;}expect(rejected,"Expected a safe import error");}
    static File output(){File dir=new File(temporary,UUID.randomUUID().toString());dir.mkdirs();return dir;}
    static File input(byte[]bytes)throws Exception{File f=new File(temporary,UUID.randomUUID()+".txt");Files.write(f.toPath(),bytes);return f;}
    static String full(BookDocument doc)throws Exception{StringBuilder out=new StringBuilder();for(int i=0;i<doc.blocks.size();i++)out.append(doc.text(i));return out.toString();}
    static BookDocument txt(String text,String encoding)throws Exception{return TxtImporter.parse(input(text.getBytes(encoding)),output(),"原创测试",encoding);}
    static File epub(Map<String,String>files)throws Exception{
        File f=new File(temporary,UUID.randomUUID()+".epub");try(ZipOutputStream zip=new ZipOutputStream(new FileOutputStream(f))){
            for(Map.Entry<String,String>e:files.entrySet()){zip.putNextEntry(new ZipEntry(e.getKey()));zip.write(e.getValue().getBytes(StandardCharsets.UTF_8));zip.closeEntry();}
        }return f;
    }
    static Map<String,String>epubFiles(){
        Map<String,String>m=new LinkedHashMap<>();m.put("mimetype","application/epub+zip");
        m.put("META-INF/container.xml","<?xml version=\"1.0\"?><container xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\"><rootfiles><rootfile full-path=\"OEBPS/book.opf\"/></rootfiles></container>");
        m.put("OEBPS/book.opf","<package xmlns=\"http://www.idpf.org/2007/opf\"><metadata xmlns:dc=\"http://purl.org/dc/elements/1.1/\"><dc:title>折叠之间</dc:title><dc:creator>原创测试</dc:creator></metadata><manifest><item id=\"nav\" href=\"nav.xhtml\" properties=\"nav\" media-type=\"application/xhtml+xml\"/><item id=\"a\" href=\"a.xhtml\" media-type=\"application/xhtml+xml\"/><item id=\"b\" href=\"b.xhtml\" media-type=\"application/xhtml+xml\"/></manifest><spine><itemref idref=\"a\"/><itemref idref=\"b\"/></spine></package>");
        m.put("OEBPS/nav.xhtml","<html xmlns=\"http://www.w3.org/1999/xhtml\" xmlns:epub=\"http://www.idpf.org/2007/ops\"><body><nav epub:type=\"toc\"><ol><li><a href=\"b.xhtml#second\">后章</a></li><li><a href=\"a.xhtml#first\">前章</a><ol><li><a href=\"a.xhtml#first\">同目标子项</a></li></ol></li></ol></nav></body></html>");
        m.put("OEBPS/a.xhtml","<html xmlns=\"http://www.w3.org/1999/xhtml\"><body><h1 id=\"first\">展开纸页</h1><p>窗口变宽，文字仍接在原来的位置。<em>这一句来自原创材料。</em></p><script>不应显示脚本正文</script></body></html>");
        m.put("OEBPS/b.xhtml","<html xmlns=\"http://www.w3.org/1999/xhtml\"><body><h1 id=\"second\">合上纸页</h1><p>听书和阅读各自保存位置。</p></body></html>");return m;
    }
    public static void main(String[]args)throws Exception{
        root=new File(args[0]);temporary=new File(args[1]);temporary.mkdirs();
        String original="第1章 纸窗\r\n风经过纸窗。\r\n第2章 折页\r\n第二页仍留在桌面。";
        for(String enc:new String[]{"UTF-8","UTF-16LE","UTF-16BE","GBK","GB18030"})test("strict_"+enc,()->{
            BookDocument d=txt(original,enc);expect(full(d).equals(original.replace("\r\n","\n")+"\n"),"text changed");expect(d.toc.size()==2,"chapter count");
        });
        for(String enc:new String[]{"UTF-8","UTF-16LE","UTF-16BE"})test("BOM_"+enc,()->{
            byte[]bom=enc.equals("UTF-8")?new byte[]{(byte)239,(byte)187,(byte)191}:enc.equals("UTF-16LE")?new byte[]{(byte)255,(byte)254}:new byte[]{(byte)254,(byte)255};
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();bytes.write(bom);bytes.write(original.getBytes(enc));BookDocument d=TxtImporter.parse(input(bytes.toByteArray()),output(),"BOM",null);expect(d.encoding.equals(enc),"BOM ignored");
        });
        test("auto_UTF16_without_BOM",()->{for(String enc:new String[]{"UTF-16LE","UTF-16BE"}){File f=input(("第1章 ABC\n页面 123\n").getBytes(enc));expect(TextCodec.detect(f,null).charset.equals(enc),"UTF16 heuristic");}});
        test("GB18030_four_byte_and_auto",()->{BookDocument d=TxtImporter.parse(input("中文\ud840\udc00😀结束。".getBytes("GB18030")),output(),"四字节",null);expect(full(d).equals("中文\ud840\udc00😀结束。\n"),"supplementary text corrupted");});
        test("reject_invalid_UTF8_BOM",()->rejects(()->TextCodec.detect(input(new byte[]{(byte)239,(byte)187,(byte)191,(byte)255}),null)));
        test("reject_invalid_UTF16_surrogate",()->rejects(()->TextCodec.detect(input(new byte[]{(byte)255,(byte)254,0,(byte)216}),null)));
        test("reject_invalid_GB18030",()->rejects(()->TextCodec.detect(input(new byte[]{(byte)129,48,(byte)129}),"GB18030")));
        test("reject_binary_and_replacement",()->{rejects(()->txt("正文\0其他","UTF-8"));rejects(()->txt("正文\ufffd其他","UTF-8"));});
        test("reject_empty_and_UTF32",()->{rejects(()->TextCodec.detect(input(new byte[0]),null));rejects(()->TextCodec.detect(input(new byte[]{(byte)255,(byte)254,0,0,1,0,0,0}),null));});
        test("reject_size_limit",()->{File f=input(new byte[]{1});try(RandomAccessFile file=new RandomAccessFile(f,"rw")){file.setLength(TextCodec.MAX_BYTES+1);}rejects(()->TextCodec.detect(f,null));});
        test("bare_headings_require_run",()->{BookDocument d=txt("001清晨\n正文。\n002纸页\n正文。\n003灯光\n正文。\n123普通行\n第9章 正章\n99.第10章 尾章\n", "UTF-8");expect(d.toc.size()==5,"weak false positive or strong miss");});
        test("ordinary_numbers_not_chapters",()->{BookDocument d=txt("1.买纸\n2.写字\n123这是正文，带有标点。\n456普通孤立行\n下文仍在同一页。","UTF-8");expect(d.toc.isEmpty(),"misleading headings");});
        test("giant_line_bounded_and_surrogate_safe",()->{StringBuilder text=new StringBuilder();for(int i=0;i<25000;i++)text.append("原创新段😀");BookDocument d=txt(text.toString(),"UTF-8");expect(full(d).equals(text+"\n"),"giant line changed");for(int i=0;i<d.blocks.size();i++){String s=d.text(i);expect(s.length()<=1600,"unbounded view block");expect(!Character.isLowSurrogate(s.charAt(0)),"split surrogate start");expect(!Character.isHighSurrogate(s.charAt(s.length()-1)),"split surrogate end");}});
        test("long_2301482_character_fixture",()->{
            File f=new File(root,".local-test-data/android-fixtures/original_long_gb18030.txt");BookDocument d=TxtImporter.parse(f,output(),"原创长书",null);
            expect(d.toc.size()==625,"expected 624 chapters plus afterword, actual "+d.toc.size());expect(d.encoding.equals("GB18030"),"legacy detect");
            expect(d.toc.get(499).title.startsWith("第500章"),"chapter500 missing");
            int target=d.toc.get(499).block;expect(d.currentChapter(target+1)==499,"live chapter didn't advance");
            int max=0;for(BookDocument.Block b:d.blocks)max=Math.max(max,b.chars);expect(max<=1600,"max block");
            BookDocument loaded=BookDocument.load(d.directory);expect(loaded.totalChars==d.totalChars&&loaded.blocks.size()==d.blocks.size(),"disk resume index");
            for(float progress:new float[]{0,.01f,.5f,.8f,.999f,1}){BookDocument.Position p=loaded.atProgress(progress);expect(Math.abs(loaded.progress(p.block,p.offset)-progress)<.00001f,"progress round trip");}
            System.out.println("LONG_FIXTURE {\"chapters\":"+d.toc.size()+",\"blocks\":"+d.blocks.size()+",\"maxBlockUTF16\":"+max+",\"normalizedUTF16\":"+d.totalChars+"}");
        });
        test("EPUB3_spine_nav_nested_out_of_order",()->{
            BookDocument d=EpubImporter.parse(epub(epubFiles()),output(),"fallback");expect(d.title.equals("折叠之间")&&d.author.equals("原创测试"),"metadata");
            expect(d.toc.size()==3,"nav nesting");expect(d.toc.get(0).block>d.toc.get(1).block,"nav order must retain declared order");
            expect(d.currentChapter(d.toc.get(1).block)==2,"deepest same target");expect(d.currentChapter(d.toc.get(0).block)==0,"spine aware lookup");
            String body=full(d);expect(!body.contains("不应显示脚本"),"script leaked");expect(body.indexOf("展开纸页")<body.indexOf("合上纸页"),"spine order changed");
        });
        for(String fixture:new String[]{"synthetic.epub","synthetic_ncx.epub"})test("iOS_original_fixture_"+fixture,()->{
            BookDocument d=EpubImporter.parse(new File(root,"Tests/Fixtures/"+fixture),output(),"fixture");expect(d.blocks.size()>0&&!d.toc.isEmpty(),"valid original EPUB rejected");
        });
        for(String fixture:new String[]{"unsafe_entity.epub","unsafe_path.epub","bad_spine.epub"})test("reject_"+fixture,()->rejects(()->EpubImporter.parse(new File(root,"Tests/Fixtures/"+fixture),output(),"bad")));
        test("reject_EPUB_traversal_and_encoded_path",()->{Map<String,String>m=epubFiles();m.put("../outside","forbidden");File unsafe=epub(m);rejects(()->EpubImporter.parse(unsafe,output(),"bad"));m=epubFiles();m.put("OEBPS/a.xhtml",m.get("OEBPS/a.xhtml").replace("<p>","<p><img src=\"%2e%2e/%2e%2e/outside\"/>"));File f=epub(m);rejects(()->EpubImporter.parse(f,output(),"bad"));});
        test("reject_EPUB_external_entity",()->{Map<String,String>m=epubFiles();m.put("OEBPS/a.xhtml","<!DOCTYPE html [<!ENTITY leak SYSTEM 'file:///etc/passwd'>]><html><body><p>&leak;</p></body></html>");rejects(()->EpubImporter.parse(epub(m),output(),"bad"));});
        test("EPUB_missing_nav_destination_fallback",()->{Map<String,String>m=epubFiles();m.put("OEBPS/nav.xhtml",m.get("OEBPS/nav.xhtml").replace("#second","#missing"));BookDocument d=EpubImporter.parse(epub(m),output(),"fallback");expect(d.toc.size()==3,"fragment fallback lost chapter");});
        test("speech_punctuation_and_surrogates",()->{
            String s="甲😀乙。下一句！最后一行\n";int at=0;StringBuilder joined=new StringBuilder();while(at<s.length()){int end=SpeechChunks.end(s,at,8);expect(end>at&&end-at<=8,"chunk limit");joined.append(s,at,end);at=end;}expect(joined.toString().equals(s),"speech content changed");expect(SpeechChunks.safeOffset(s,2)==1,"resume bisected surrogate");
        });
        test("independent_reading_listening_values",()->{BookDocument d=txt("第1章 起点\n第一段。\n第2章 远处\n第二段。","UTF-8");BookDocument.Position reading=d.clamp(0,3),listening=d.clamp(1,5);expect(reading.block==0&&reading.offset==3,"reading");expect(listening.block==1&&listening.offset==5,"listening");expect(d.currentChapter(-1)==-1,"preface/no chapter boundary");});
        String json="{\"suite\":\"JVM core\",\"passed\":"+passed+",\"failed\":"+failed+",\"tests\":["+String.join(",",results)+"]}";
        Files.write(new File(temporary,"core-results.json").toPath(),json.getBytes(StandardCharsets.UTF_8));System.out.println(json);if(failed>0)System.exit(1);
    }
}
