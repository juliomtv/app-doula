package com.appdoula.nalin;

import android.view.KeyEvent;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_UP || keyCode == KeyEvent.KEYCODE_VOLUME_DOWN) {
            // Repassa para o JavaScript e consome o evento (impede mudança de volume)
            getBridge().getWebView().post(() ->
                getBridge().getWebView().evaluateJavascript(
                    "if(typeof _volumeBtnFromNative==='function')_volumeBtnFromNative();", null
                )
            );
            return true; // true = evento consumido, volume não muda
        }
        return super.onKeyDown(keyCode, event);
    }
}
