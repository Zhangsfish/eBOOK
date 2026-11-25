package cn.zhangsfish.ebook.core;

/** Stateless UTF-16-safe sentence chunking, compatible with Android TTS callbacks. */
public final class SpeechChunks {
    public static int safeOffset(String text,int offset){
        int at=Math.max(0,Math.min(text.length(),offset));
        if(at>0&&at<text.length()&&Character.isLowSurrogate(text.charAt(at))&&Character.isHighSurrogate(text.charAt(at-1)))at--;
        return at;
    }
    public static int end(String text,int start,int max){
        int from=safeOffset(text,start),limit=Math.min(text.length(),from+Math.max(8,max));
        limit=safeOffset(text,limit);
        for(int i=from;i<limit;){
            int cp=text.codePointAt(i);i+=Character.charCount(cp);
            if("。！？!?；;\n".indexOf(cp)>=0)return i;
        }
        return limit;
    }
}
