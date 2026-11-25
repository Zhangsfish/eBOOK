package cn.zhangsfish.ebook.core;

import java.io.*;
import java.util.*;
import java.util.regex.*;

public final class TxtImporter {
    private static final Pattern STRONG=Pattern.compile("^(?:[0-9]{1,5}[.、]\\s*)?第[0-9零〇一二三四五六七八九十百千万两壹贰叁肆伍陆柒捌玖拾佰仟]{1,12}[章节回卷部集](?:\\s*[^。！？；]{0,40})?$");
    private static final Pattern BARE=Pattern.compile("^([0-9]{3,5})([\\p{IsHan}][^\\s。！？，、：；.?!,:;]{0,30})$");
    private static final Set<String> SPECIAL=new HashSet<>(Arrays.asList("后记","尾声","序章","序言"));
    private static final class Candidate {
        int line,number;String title;boolean strong;
        Candidate(int line,String title,int number,boolean strong){this.line=line;this.title=title;this.number=number;this.strong=strong;}
    }
    public static BookDocument parse(File input,File output,String title,String hint)throws IOException{
        TextCodec.Encoding enc=TextCodec.detect(input,hint);
        List<Candidate> candidates=new ArrayList<>();
        TextCodec.scan(input,enc,(line,value,end,continued)->{
            if(!end||continued)return;String t=value.trim();if(t.length()>64)return;
            if(STRONG.matcher(t).matches()||SPECIAL.contains(t))candidates.add(new Candidate(line,t,0,true));
            else { Matcher m=BARE.matcher(t);if(m.matches())candidates.add(new Candidate(line,t,Integer.parseInt(m.group(1)),false)); }
        });
        Map<Integer,String> headings=new HashMap<>();List<Candidate> run=new ArrayList<>();
        for(Candidate c:candidates){
            if(c.strong){accept(run,headings);headings.put(c.line,c.title);}
            else{if(!run.isEmpty()&&c.number!=run.get(run.size()-1).number+1)accept(run,headings);run.add(c);}
        }accept(run,headings);
        BookDocument doc=new BookDocument();doc.directory=output;doc.title=title;doc.format="TXT";doc.encoding=enc.charset;
        try(BookDocument.Writer writer=new BookDocument.Writer(doc)){
            TextCodec.scan(input,enc,(line,part,end,continued)->{
                if(headings.containsKey(line)&&!continued)doc.toc.add(new BookDocument.Chapter(headings.get(line),writer.nextBlock(),0));
                writer.append(part);if(end)writer.append("\n");
            });
        }
        if(doc.blocks.isEmpty())throw new IOException("TXT 没有正文。");
        doc.save();return doc;
    }
    private static void accept(List<Candidate>run,Map<Integer,String>result){
        if(run.size()>=3)for(Candidate c:run)result.put(c.line,c.title);run.clear();
    }
}
