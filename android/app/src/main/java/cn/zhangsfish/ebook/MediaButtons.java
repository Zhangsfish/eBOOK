package cn.zhangsfish.ebook;

import android.content.*;
import android.view.KeyEvent;

/** Explicit PendingIntent receiver for the active system MediaSession. */
public final class MediaButtons extends BroadcastReceiver {
    @Override public void onReceive(Context context,Intent intent){
        KeyEvent key=intent.getParcelableExtra(Intent.EXTRA_KEY_EVENT);
        if(key==null||key.getAction()!=KeyEvent.ACTION_DOWN||key.getRepeatCount()!=0)return;
        String action;
        switch(key.getKeyCode()){
            case KeyEvent.KEYCODE_MEDIA_NEXT:action=SpeechService.NEXT;break;
            case KeyEvent.KEYCODE_MEDIA_PREVIOUS:action=SpeechService.PREVIOUS;break;
            case KeyEvent.KEYCODE_MEDIA_STOP:action=SpeechService.STOP;break;
            case KeyEvent.KEYCODE_MEDIA_PLAY:action=SpeechService.RESUME;break;
            case KeyEvent.KEYCODE_MEDIA_PAUSE:action=SpeechService.PAUSE;break;
            default:return; // MediaSession resolves toggle/play-pause into its callbacks.
        }
        SpeechService.command(context,action,null,null);
    }
}
