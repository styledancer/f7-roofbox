package __PKG__;

import android.content.Context;
import android.os.Build;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.os.VibratorManager;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

// Crisp haptic cues for the web app: tick, click, heavy, tension (a rising pull that ends in a click).
@CapacitorPlugin(name = "Buzz")
public class BuzzPlugin extends Plugin {
    private Vibrator vib() {
        Context c = getContext();
        if (Build.VERSION.SDK_INT >= 31) {
            VibratorManager m = (VibratorManager) c.getSystemService(Context.VIBRATOR_MANAGER_SERVICE);
            return m != null ? m.getDefaultVibrator() : null;
        }
        return (Vibrator) c.getSystemService(Context.VIBRATOR_SERVICE);
    }

    @PluginMethod
    public void fx(PluginCall call) {
        String k = call.getString("k", "click");
        try {
            Vibrator v = vib();
            if (v == null || !v.hasVibrator()) { call.resolve(); return; }
            if (Build.VERSION.SDK_INT >= 30 && k.equals("tension")
                    && v.areAllPrimitivesSupported(VibrationEffect.Composition.PRIMITIVE_SLOW_RISE, VibrationEffect.Composition.PRIMITIVE_CLICK)) {
                v.vibrate(VibrationEffect.startComposition()
                        .addPrimitive(VibrationEffect.Composition.PRIMITIVE_SLOW_RISE, 0.45f)
                        .addPrimitive(VibrationEffect.Composition.PRIMITIVE_CLICK, 1.0f, 20)
                        .compose());
            } else if (Build.VERSION.SDK_INT >= 26 && k.equals("tension")) {
                if (v.hasAmplitudeControl())
                    v.vibrate(VibrationEffect.createWaveform(new long[]{0, 14, 14, 14, 22}, new int[]{0, 50, 100, 160, 255}, -1));
                else
                    v.vibrate(VibrationEffect.createWaveform(new long[]{0, 10, 45, 28}, -1));
            } else if (Build.VERSION.SDK_INT >= 29) {
                int id = k.equals("tick") ? VibrationEffect.EFFECT_TICK
                        : k.equals("heavy") ? VibrationEffect.EFFECT_HEAVY_CLICK
                        : VibrationEffect.EFFECT_CLICK;
                v.vibrate(VibrationEffect.createPredefined(id));
            } else if (Build.VERSION.SDK_INT >= 26) {
                int ms = k.equals("tick") ? 6 : k.equals("heavy") ? 28 : 12;
                int amp = k.equals("tick") ? 70 : k.equals("heavy") ? 255 : 160;
                v.vibrate(VibrationEffect.createOneShot(ms, v.hasAmplitudeControl() ? amp : VibrationEffect.DEFAULT_AMPLITUDE));
            } else {
                v.vibrate(k.equals("heavy") ? 28 : 10);
            }
        } catch (Exception ignored) { }
        call.resolve();
    }
}
