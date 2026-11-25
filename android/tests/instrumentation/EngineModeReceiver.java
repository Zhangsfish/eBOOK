package cn.zhangsfish.ebook.tests;
import android.content.*;
/** Test APK only; broadcasts let the native harness control an isolated engine process. */
public final class EngineModeReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context,Intent intent){
        context.getSharedPreferences("engine",0).edit().putBoolean("missing",intent.getBooleanExtra("missing",false))
            .putBoolean("error",intent.getBooleanExtra("error",false)).commit();
    }
}
