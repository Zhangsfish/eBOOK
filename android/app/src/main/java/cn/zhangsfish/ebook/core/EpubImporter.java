package cn.zhangsfish.ebook.core;

import java.io.*;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;
import javax.xml.parsers.SAXParserFactory;
import org.xml.sax.*;
import org.xml.sax.helpers.DefaultHandler;

/** Bounded, non-executing EPUB2/3 reader: ZIP, metadata, spine, nav/NCX and images. */
public final class EpubImporter {
    private static final int MAX_XML=8*1024*1024,MAX_IMAGE=16*1024*1024;
    private static final long MAX_EXPANDED=128L*1024*1024;
    private static final Set<String> BREAKS=new HashSet<>(Arrays.asList("p","div","section","article","h1","h2","h3","h4","li","blockquote","pre","dt","dd","tr","figure"));
    private static final class Node {
        final String name;final Map<String,String> attrs=new HashMap<>();final List<Object> children=new ArrayList<>();
        Node(String name){this.name=name;}
        String attr(String name){return attrs.containsKey(name)?attrs.get(name):"";}
        String text(){StringBuilder out=new StringBuilder();collect(out);return out.toString().trim().replaceAll("\\s+"," ");}
        void collect(StringBuilder out){for(Object child:children){if(child instanceof Node)((Node)child).collect(out);else out.append(child);}}
        List<Node> all(String name){List<Node> out=new ArrayList<>();find(name,out);return out;}
        void find(String name,List<Node> out){if(this.name.equals(name))out.add(this);for(Object child:children)if(child instanceof Node)((Node)child).find(name,out);}
    }
    private static final class Nav {String title,target;int depth;Nav(String t,String p,int d){title=t;target=p;depth=d;}}
    private final ZipFile zip;
    private final BookDocument doc;
    private final Map<String,Integer> anchors=new HashMap<>();
    private final Map<String,String> images=new HashMap<>();
    private BookDocument.Writer writer;
    private long expanded;
    private EpubImporter(ZipFile zip,BookDocument doc){this.zip=zip;this.doc=doc;}

    public static BookDocument parse(File input,File output,String fallback)throws IOException{
        if(input.length()>64L*1024*1024)throw new IOException("EPUB 超过 64 MiB，请先拆分。");
        BookDocument doc=new BookDocument();doc.directory=output;doc.title=fallback;doc.format="EPUB";
        try(ZipFile zip=new ZipFile(input)){
            EpubImporter parser=new EpubImporter(zip,doc);parser.validateArchive();
            parser.read();doc.save();return doc;
        }catch(ZipException malformed){throw new IOException("EPUB 压缩容器损坏或受加密保护。",malformed);}
    }
    private void validateArchive()throws IOException{
        Enumeration<? extends ZipEntry>entries=zip.entries();Set<String>names=new HashSet<>();long total=0;
        while(entries.hasMoreElements()){
            ZipEntry e=entries.nextElement();String name=e.getName();
            if(!safePath(name)||!names.add(name))throw new IOException("EPUB 包含不安全或重复的文件路径。");
            total+=Math.max(0,e.getSize());if(names.size()>10000||total>MAX_EXPANDED)throw new IOException("EPUB 解压后体积或文件数量过大。");
        }
        if(zip.getEntry("META-INF/encryption.xml")!=null)throw new IOException("暂不支持含加密/字体保护信息的 EPUB，请使用无 DRM 的文件。");
        if(!new String(read("mimetype",128),StandardCharsets.US_ASCII).trim().equals("application/epub+zip"))throw new IOException("文件不是有效 EPUB。");
    }
    private static boolean safePath(String name){
        return !name.startsWith("/")&&!name.contains("\\")&&!name.contains(":")&&!name.contains("\0")
                &&!Arrays.asList(name.split("/")).contains("..");
    }
    static String resolve(String base,String href)throws IOException{
        try{
            String decoded=URLDecoder.decode(href.replace("+","%2B"),"UTF-8");
            if(decoded.contains(":")||decoded.startsWith("/")||decoded.contains("\\")||decoded.contains("\0"))throw new IOException("EPUB 引用了外部或不安全路径。");
            int fragment=decoded.indexOf('#');String suffix=fragment<0?"":decoded.substring(fragment),path=fragment<0?decoded:decoded.substring(0,fragment);
            if(path.contains("?"))throw new IOException("EPUB 路径包含不支持的查询参数。");
            String joined=path.isEmpty()?base:base.substring(0,Math.max(0,base.lastIndexOf('/')+1))+path;
            Deque<String>clean=new ArrayDeque<>();
            for(String part:joined.split("/")){
                if(part.equals("..")){if(clean.isEmpty())throw new IOException("EPUB 路径越界。");clean.removeLast();}
                else if(!part.isEmpty()&&!part.equals("."))clean.add(part);
            }
            return String.join("/",clean)+suffix;
        }catch(IllegalArgumentException bad){throw new IOException("EPUB 路径编码损坏。",bad);}
    }
    private byte[]read(String path,int limit)throws IOException{
        ZipEntry e=zip.getEntry(path);if(e==null||e.isDirectory())throw new IOException("EPUB 缺少必需文件："+path);
        if(e.getSize()>limit)throw new IOException("EPUB 文件过大。");
        try(InputStream in=zip.getInputStream(e);ByteArrayOutputStream out=new ByteArrayOutputStream()){
            byte[]buffer=new byte[8192];int n,total=0;
            while((n=in.read(buffer))!=-1){total+=n;expanded+=n;if(total>limit||expanded>MAX_EXPANDED)throw new IOException("EPUB 展开体积超过安全限制。");out.write(buffer,0,n);}
            return out.toByteArray();
        }
    }
    private Node xml(String path)throws IOException{
        byte[]data=read(path,MAX_XML);
        // Detect declarations in UTF8 / UTF16 too, before any parser/entity processing.
        String probe;
        if(data.length>=2&&((data[0]&255)==255&&(data[1]&255)==254))probe=new String(data,StandardCharsets.UTF_16LE);
        else if(data.length>=2&&((data[0]&255)==254&&(data[1]&255)==255))probe=new String(data,StandardCharsets.UTF_16BE);
        else if(data.length>=4&&data[0]==0&&data[1]=='<')probe=new String(data,StandardCharsets.UTF_16BE);
        else if(data.length>=4&&data[0]=='<'&&data[1]==0)probe=new String(data,StandardCharsets.UTF_16LE);
        else probe=new String(data,StandardCharsets.UTF_8);
        if(probe.toUpperCase(Locale.ROOT).contains("<!ENTITY"))throw new IOException("EPUB 不允许自定义 XML 实体。");
        try{
            SAXParserFactory factory=SAXParserFactory.newInstance();factory.setNamespaceAware(true);
            XMLReader reader=factory.newSAXParser().getXMLReader();
            reader.setFeature("http://xml.org/sax/features/external-general-entities",false);
            reader.setFeature("http://xml.org/sax/features/external-parameter-entities",false);
            try{reader.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd",false);}catch(SAXNotRecognizedException|SAXNotSupportedException ignored){/* resolver below remains fail closed */}
            reader.setEntityResolver((publicId,systemId)->{throw new SAXException("不读取外部 XML 资源。");});
            final Deque<Node>stack=new ArrayDeque<>();final Node[]root={null};final int[]nodes={0},text={0};
            DefaultHandler handler=new DefaultHandler(){
                @Override public void startElement(String uri,String local,String qName,Attributes attributes)throws SAXException{
                    if(++nodes[0]>100000||stack.size()>=128)throw new SAXException("XML 结构过于复杂。");
                    Node node=new Node(local.isEmpty()?qName:local);
                    for(int i=0;i<attributes.getLength();i++){
                        String key=attributes.getLocalName(i);if(key.isEmpty())key=attributes.getQName(i);node.attrs.put(key,attributes.getValue(i));
                    }
                    if(stack.isEmpty())root[0]=node;else stack.peekLast().children.add(node);stack.addLast(node);
                }
                @Override public void endElement(String uri,String local,String qName){stack.removeLast();}
                @Override public void characters(char[]ch,int start,int length)throws SAXException{
                    text[0]+=length;if(text[0]>MAX_XML)throw new SAXException("XML 正文过多。");
                    if(!stack.isEmpty())stack.peekLast().children.add(new String(ch,start,length));
                }
                @Override public void error(SAXParseException e)throws SAXException{throw e;}
                @Override public void fatalError(SAXParseException e)throws SAXException{throw e;}
            };
            reader.setContentHandler(handler);reader.setErrorHandler(handler);reader.parse(new InputSource(new ByteArrayInputStream(data)));
            if(root[0]==null)throw new IOException("EPUB XML 内容为空。");return root[0];
        }catch(IOException e){throw e;}catch(Exception malformed){throw new IOException("EPUB XML/XHTML 损坏或包含不安全结构。",malformed);}
    }
    private void read()throws IOException{
        Node container=xml("META-INF/container.xml");List<Node>roots=container.all("rootfile");if(roots.isEmpty())throw new IOException("EPUB 未声明阅读包。");
        String opf=roots.get(0).attr("full-path");if(!safePath(opf))throw new IOException("EPUB 包路径不安全。");
        Node pkg=xml(opf);List<Node>titles=pkg.all("title"),authors=pkg.all("creator");
        if(!titles.isEmpty()&&!titles.get(0).text().isEmpty())doc.title=limited(titles.get(0).text(),500);
        if(!authors.isEmpty())doc.author=limited(authors.get(0).text(),500);
        Map<String,Node>manifest=new HashMap<>();String navPath="",ncxPath="";
        for(Node item:pkg.all("item")){
            manifest.put(item.attr("id"),item);
            if(Arrays.asList(item.attr("properties").split("\\s+")).contains("nav"))navPath=resolve(opf,item.attr("href"));
            if(item.attr("media-type").equals("application/x-dtbncx+xml"))ncxPath=resolve(opf,item.attr("href"));
        }
        List<Nav>navigation=new ArrayList<>();
        if(!navPath.isEmpty()){
            for(Node nav:xml(navPath).all("nav"))if(Arrays.asList(nav.attr("type").split("\\s+")).contains("toc"))readNav(nav,navPath,0,navigation);
        }
        if(navigation.isEmpty()&&!ncxPath.isEmpty())readNcx(xml(ncxPath),ncxPath,0,navigation);
        try(BookDocument.Writer w=new BookDocument.Writer(doc)){
            writer=w;int linear=0;
            for(Node ref:pkg.all("itemref")){
                if(ref.attr("linear").equals("no"))continue;
                Node item=manifest.get(ref.attr("idref"));if(item==null)throw new IOException("EPUB 阅读顺序引用不存在的章节。");
                String media=item.attr("media-type");if(!media.equals("application/xhtml+xml")&&!media.equals("text/html"))throw new IOException("EPUB 正文格式暂不支持："+media);
                String path=resolve(opf,item.attr("href"));Node page=xml(path);List<Node>bodies=page.all("body");
                if(bodies.isEmpty())throw new IOException("EPUB 正文章节没有 body。");
                int block=w.nextBlock();anchors.put(path,block);linear++;
                List<Node>h=page.all("h1");if(h.isEmpty())h=page.all("h2");
                String title=h.isEmpty()?"第 "+linear+" 节":limited(h.get(0).text(),250);
                doc.toc.add(new BookDocument.Chapter(title,block,0));render(bodies.get(0),path);
            }
        }
        if(doc.blocks.isEmpty())throw new IOException("EPUB 没有可阅读的正文。");
        if(!navigation.isEmpty()){
            List<BookDocument.Chapter>resolved=new ArrayList<>();
            for(Nav n:navigation){Integer at=anchors.get(n.target);if(at==null){int hash=n.target.indexOf('#');at=anchors.get(hash<0?n.target:n.target.substring(0,hash));}
                if(at!=null&&at<doc.blocks.size())resolved.add(new BookDocument.Chapter(limited(n.title,300),at,n.depth));}
            if(!resolved.isEmpty()){doc.toc.clear();doc.toc.addAll(resolved);}
        }
        // Remove a possible empty terminal spine destination.
        doc.toc.removeIf(c->c.block>=doc.blocks.size());
    }
    private void render(Node node,String path)throws IOException{
        if(Arrays.asList("script","style","head").contains(node.name))return;
        if(!node.attr("id").isEmpty())anchors.put(path+"#"+node.attr("id"),writer.nextBlock());
        if(node.name.equals("img")||node.name.equals("image")){
            String href=node.attr("src");if(href.isEmpty())href=node.attr("href");
            if(href.isEmpty())return;String source=resolve(path,href),name=images.get(source);
            if(name==null){
                byte[]image=read(source,MAX_IMAGE);
                String suffix=source.toLowerCase(Locale.ROOT);String ext=suffix.endsWith(".png")?".png":suffix.endsWith(".webp")?".webp":suffix.endsWith(".gif")?".gif":".jpg";
                name="image_"+images.size()+ext;
                try(OutputStream out=new FileOutputStream(new File(doc.directory,name))){out.write(image);}images.put(source,name);
            }
            writer.image(name,limited(node.attr("alt").isEmpty()?"书中插图":node.attr("alt"),300));return;
        }
        if(node.name.equals("br")){writer.append("\n");return;}
        for(Object child:node.children){
            if(child instanceof Node)render((Node)child,path);
            else writer.append(((String)child).replaceAll("\\s+"," "));
        }
        if(BREAKS.contains(node.name))writer.append("\n\n");
    }
    private void readNav(Node node,String path,int depth,List<Nav>out)throws IOException{
        if(node.name.equals("a")&&!node.attr("href").isEmpty()&&!node.text().isEmpty())out.add(new Nav(node.text(),resolve(path,node.attr("href")),Math.max(0,depth-1)));
        for(Object child:node.children)if(child instanceof Node){Node c=(Node)child;readNav(c,path,depth+(c.name.equals("ol")?1:0),out);}
    }
    private void readNcx(Node node,String path,int depth,List<Nav>out)throws IOException{
        if(node.name.equals("navPoint")){
            Node label=null,content=null;
            for(Object child:node.children)if(child instanceof Node){Node c=(Node)child;if(c.name.equals("navLabel"))label=c;if(c.name.equals("content"))content=c;}
            if(label!=null&&content!=null)out.add(new Nav(label.text(),resolve(path,content.attr("src")),Math.max(0,depth-1)));
        }
        for(Object child:node.children)if(child instanceof Node){Node c=(Node)child;readNcx(c,path,depth+(c.name.equals("navPoint")?1:0),out);}
    }
    private static String limited(String s,int n){return s.length()>n?s.substring(0,n):s;}
}
