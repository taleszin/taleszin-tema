package de.robv.android.xposed;

/** Stub de compilação (a classe real vem do XposedBridge.jar no aparelho). */
public abstract class XC_MethodHook {
    public XC_MethodHook() {}
    protected void beforeHookedMethod(MethodHookParam param) throws Throwable {}
    protected void afterHookedMethod(MethodHookParam param) throws Throwable {}
    public static class MethodHookParam {
        public Object thisObject;
        public Object[] args;
        public Object getResult() { return null; }
        public void setResult(Object r) {}
    }
    public class Unhook {}
}
