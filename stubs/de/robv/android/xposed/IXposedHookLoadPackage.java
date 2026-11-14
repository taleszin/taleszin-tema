package de.robv.android.xposed;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
/** STUB de compilação (API Xposed 54). Não vai para o dex. */
public interface IXposedHookLoadPackage extends IXposedMod {
    void handleLoadPackage(XC_LoadPackage.LoadPackageParam lpparam) throws Throwable;
}
