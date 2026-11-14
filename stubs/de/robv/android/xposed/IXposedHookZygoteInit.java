package de.robv.android.xposed;
/** STUB de compilação (API Xposed 54). Não vai para o dex. */
public interface IXposedHookZygoteInit extends IXposedMod {
    void initZygote(StartupParam startupParam) throws Throwable;
    public static class StartupParam { public String modulePath; }
}
