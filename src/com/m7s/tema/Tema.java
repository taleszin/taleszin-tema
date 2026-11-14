package com.m7s.tema;

import android.content.res.XModuleResources;
import android.content.res.XResources;

import java.io.File;

import de.robv.android.xposed.IXposedHookInitPackageResources;
import de.robv.android.xposed.IXposedHookZygoteInit;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.callbacks.XC_InitPackageResources.InitPackageResourcesParam;

/**
 * Troca o azul Holo (#33B5E5/#0099CC/#00DDFF) pelo laranja basquete (#FF7A1A/#E0650F/#FF9A4D).
 * Tabelas em {@link Tabela}, geradas por tools/gerar.py.
 *
 * Regra de ouro: nada aqui pode lançar exceção para fora — um erro no initZygote impede o boot.
 * Interruptor de emergência: criar /data/local/tmp/m7s-tema.off desliga o módulo no próximo boot.
 */
public class Tema implements IXposedHookZygoteInit, IXposedHookInitPackageResources {
    private static final String TAG = "m7s-tema: ";
    private static final String DESLIGA = "/data/local/tmp/m7s-tema.off";
    private static final String SYSTEMUI = "com.android.systemui";

    private static String MODULE_PATH;
    private static boolean ativo;

    @Override
    public void initZygote(StartupParam startupParam) {
        try {
            MODULE_PATH = startupParam.modulePath;
            if (desligado()) {
                log("desligado por " + DESLIGA);
                return;
            }
            ativo = true;
            aplicarFramework();
        } catch (Throwable t) {
            ativo = false;
            log("falha geral no initZygote (ignorada)");
            logT(t);
        }
    }

    private static boolean desligado() {
        try {
            return new File(DESLIGA).exists();
        } catch (Throwable t) {
            return false;
        }
    }

    private static void aplicarFramework() {
        int cores = 0, drawables = 0, falhas = 0;
        for (int i = 0; i < Tabela.CORES.length; i++) {
            try {
                XResources.setSystemWideReplacement("android", "color", Tabela.CORES[i],
                        Integer.valueOf(Tabela.CORES_VAL[i]));
                cores++;
            } catch (Throwable t) {
                falhas++;
                log("cor android:color/" + Tabela.CORES[i] + " não substituída: " + t);
            }
        }

        XModuleResources modRes = null;
        try {
            modRes = XModuleResources.createInstance(MODULE_PATH, null);
        } catch (Throwable t) {
            log("não abri os recursos do módulo em " + MODULE_PATH + "; drawables ficam no azul");
            logT(t);
        }
        if (modRes != null) {
            for (int i = 0; i < Tabela.FW_NOMES.length; i++) {
                try {
                    XResources.setSystemWideReplacement("android", "drawable", Tabela.FW_NOMES[i],
                            modRes.fwd(Tabela.FW_IDS[i]));
                    drawables++;
                } catch (Throwable t) {
                    falhas++;
                    log("drawable android:drawable/" + Tabela.FW_NOMES[i] + " não substituído: " + t);
                }
            }
        }
        log("framework: " + cores + " cores + " + drawables + " drawables substituídos, " + falhas + " falhas");
    }

    @Override
    public void handleInitPackageResources(InitPackageResourcesParam resparam) {
        try {
            if (!ativo || Tabela.UI_NOMES.length == 0 || resparam == null
                    || !SYSTEMUI.equals(resparam.packageName)) {
                return;
            }
            XModuleResources modRes = XModuleResources.createInstance(MODULE_PATH, resparam.res);
            int ok = 0;
            for (int i = 0; i < Tabela.UI_NOMES.length; i++) {
                try {
                    resparam.res.setReplacement(SYSTEMUI, "drawable", Tabela.UI_NOMES[i],
                            modRes.fwd(Tabela.UI_IDS[i]));
                    ok++;
                } catch (Throwable t) {
                    log("SystemUI drawable/" + Tabela.UI_NOMES[i] + " não substituído: " + t);
                }
            }
            log("SystemUI: " + ok + " drawables substituídos");
        } catch (Throwable t) {
            log("falha no SystemUI (ignorada)");
            logT(t);
        }
    }

    private static void log(String s) {
        try {
            XposedBridge.log(TAG + s);
        } catch (Throwable ignored) {
            // sem log não é motivo para derrubar o zygote
        }
    }

    private static void logT(Throwable t) {
        try {
            XposedBridge.log(t);
        } catch (Throwable ignored) {
        }
    }
}
