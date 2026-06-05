package com.appdoula.nalin;

import android.os.Bundle;
import android.view.KeyEvent;
import android.webkit.JavascriptInterface;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    private volatile boolean volumeIntercept = false;

    public class VolumeBridge {
        @JavascriptInterface
        public void enable() { volumeIntercept = true; }

        @JavascriptInterface
        public void disable() { volumeIntercept = false; }
    }

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getBridge().getWebView().addJavascriptInterface(new VolumeBridge(), "_VolumeCtrl");
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (volumeIntercept && (keyCode == KeyEvent.KEYCODE_VOLUME_UP || keyCode == KeyEvent.KEYCODE_VOLUME_DOWN)) {
            getBridge().getWebView().post(() ->
                getBridge().getWebView().evaluateJavascript(
                    "if(typeof _volumeBtnFromNative==='function')_volumeBtnFromNative();", null
                )
            );
            return true; // consome o evento — volume não muda
        }
        return super.onKeyDown(keyCode, event); // volume funciona normalmente
    }
}
