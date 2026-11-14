package com.m7s.tema;

import android.content.res.XModuleResources;
import android.content.res.XResources;

import java.io.File;

import de.robv.android.xposed.IXposedHookInitPackageResources;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.IXposedHookZygoteInit;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_InitPackageResources.InitPackageResourcesParam;
import de.robv.android.xposed.callbacks.XC_LoadPackage.LoadPackageParam;

/**
 * Troca o azul Holo (#33B5E5/#0099CC/#00DDFF) pelo laranja basquete (#FF7A1A/#E0650F/#FF9A4D).
 * Tabelas em {@link Tabela}, geradas por tools/gerar.py.
 *
 * Regra de ouro: nada aqui pode lançar exceção para fora — um erro no initZygote impede o boot.
 * Interruptor de emergência: criar /data/local/tmp/m7s-tema.off desliga o módulo no próximo boot.
 */
public class Tema implements IXposedHookZygoteInit, IXposedHookInitPackageResources, IXposedHookLoadPackage {
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

        // Taleszin OS: componentes redesenhados (pílula, cantos, cartões) por cima da recoloração
        int mat = 0;
        if (modRes != null) {
            for (int i = 0; i < Material.FW_NOMES.length; i++) {
                try {
                    XResources.setSystemWideReplacement("android", "drawable", Material.FW_NOMES[i],
                            modRes.fwd(Material.FW_IDS[i]));
                    mat++;
                } catch (Throwable t) {
                    log("material android:drawable/" + Material.FW_NOMES[i] + " não substituído: " + t);
                }
            }
        }
        log("material: " + mat + " de " + Material.FW_NOMES.length + " componentes");
        // o quadrado azulado atrás do ícone da notificação é uma cor (#3333b5e5), não um PNG:
        // some, e o ícone fica direto sobre o cartão
        for (String n : new String[] {"notification_template_icon_bg", "notification_template_icon_low_bg"}) {
            try {
                XResources.setSystemWideReplacement("android", "drawable", n, Integer.valueOf(0));
            } catch (Throwable t) {
                log("fundo de ícone " + n + " não substituído: " + t);
            }
        }
        interruptorSemTexto();
    }

    /** O Switch do KitKat escreve LIGADO/DESLIGADO dentro do polegar e tem 96dp de largura mínima;
     *  na pílula da Taleszin OS o polegar é só a bolinha (largura vem do padding do 9-patch). */
    private static void interruptorSemTexto() {
        try {
            XposedHelpers.findAndHookConstructor(android.widget.Switch.class, android.content.Context.class,
                    android.util.AttributeSet.class, int.class, new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            try {
                                android.widget.Switch sw = (android.widget.Switch) param.thisObject;
                                sw.setTextOn("");
                                sw.setTextOff("");
                                sw.setThumbTextPadding(0);
                                sw.setSwitchMinWidth(0);
                            } catch (Throwable ignored) {
                            }
                        }
                    });
            log("interruptor: texto do polegar removido");
        } catch (Throwable t) {
            log("interruptor: hook falhou (fica o texto)");
            logT(t);
        }
    }

    /** Barras translúcidas: o BarTransitions do KitKat só liga a transição (opaca → translúcida)
     *  se ActivityManager.isHighEndGfx(), e ro.config.low_ram=true desliga isso no aparelho todo.
     *  Respondemos "true" SÓ durante o construtor do BarTransitions na SystemUI: o resto (aceleração
     *  por GPU das janelas, recentes) segue no modo econômico do low_ram. */
    private static final ThreadLocal<Boolean> NA_BARRA = new ThreadLocal<Boolean>();

    @Override
    public void handleLoadPackage(LoadPackageParam lpparam) {
        try {
            if (!ativo || lpparam == null || !SYSTEMUI.equals(lpparam.packageName)) {
                return;
            }
            Class<?> bt = Class.forName("com.android.systemui.statusbar.phone.BarTransitions", false,
                    lpparam.classLoader);
            XposedBridge.hookAllConstructors(bt, new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    NA_BARRA.set(Boolean.TRUE);
                }

                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    NA_BARRA.set(null);
                }
            });
            XposedHelpers.findAndHookMethod(android.app.ActivityManager.class, "isHighEndGfx", new XC_MethodHook() {
                @Override
                protected void beforeHookedMethod(MethodHookParam param) {
                    if (NA_BARRA.get() != null) {
                        param.setResult(Boolean.TRUE);
                    }
                }
            });
            log("barras: transições translúcidas ligadas na SystemUI");
            cortinaDeCelular(lpparam.classLoader);
        } catch (Throwable t) {
            log("barras: não liguei a translucidez (seguem opacas)");
            logT(t);
        }
    }

    /** A tela de 480 dp cai no layout de tablet (sw480dp) do KitKat: cortina estreita com 16 dp de
     *  margem, 40% de altura mínima (o bloco preto vazio) e atalhos rápidos escondidos numa zona de
     *  arrasto à direita — e por isso o botão de atalhos some do cabeçalho. A Taleszin OS usa o padrão
     *  de celular: cortina de largura total, altura do conteúdo, botão de atalhos no cabeçalho que vira
     *  o painel (o config_hasFlipSettingsPanel=true vem por recurso em handleInitPackageResources). */
    private static void cortinaDeCelular(ClassLoader cl) {
        final String P = "com.android.systemui.statusbar.phone.";
        try {
            XposedBridge.hookAllConstructors(Class.forName(P + "PhoneStatusBarView", false, cl), new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    campo(param.thisObject, "mFullWidthNotifications", Boolean.TRUE);
                    campo(param.thisObject, "mSettingsPanelDragzoneFrac", Float.valueOf(0f));
                }
            });
            Class<?> psb = Class.forName(P + "PhoneStatusBar", false, cl);
            XposedHelpers.findAndHookMethod(psb, "loadDimens", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    campo(param.thisObject, "mNotificationPanelMarginPx", Integer.valueOf(0));
                    campo(param.thisObject, "mNotificationPanelMinHeightFrac", Float.valueOf(0f));
                }
            });
            XposedHelpers.findAndHookMethod(psb, "makeStatusBarView", new XC_MethodHook() {
                @Override
                protected void afterHookedMethod(MethodHookParam param) {
                    try {
                        java.lang.reflect.Field f = param.thisObject.getClass().getDeclaredField("mNotificationPanel");
                        f.setAccessible(true);
                        android.view.View panel = (android.view.View) f.get(param.thisObject);
                        android.view.ViewGroup.LayoutParams lp = panel.getLayoutParams();
                        lp.width = android.view.ViewGroup.LayoutParams.MATCH_PARENT;
                        if (lp instanceof android.view.ViewGroup.MarginLayoutParams) {
                            ((android.view.ViewGroup.MarginLayoutParams) lp).leftMargin = 0;
                            ((android.view.ViewGroup.MarginLayoutParams) lp).rightMargin = 0;
                        }
                        panel.setLayoutParams(lp);
                        campo(param.thisObject, "mNotificationPanelIsFullScreenWidth", Boolean.TRUE);
                    } catch (Throwable t) {
                        log("cortina: largura não ajustada");
                        logT(t);
                    }
                }
            });
            log("cortina: padrão de celular (largura total, atalhos no cabeçalho)");
        } catch (Throwable t) {
            log("cortina: hooks falharam (fica o layout de tablet)");
            logT(t);
        }
    }

    private static void campo(Object o, String nome, Object v) {
        try {
            java.lang.reflect.Field f = o.getClass().getDeclaredField(nome);
            f.setAccessible(true);
            f.set(o, v);
        } catch (Throwable t) {
            log("campo " + nome + " não ajustado: " + t);
        }
    }

    @Override
    public void handleInitPackageResources(InitPackageResourcesParam resparam) {
        try {
            if (!ativo || resparam == null
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
            for (int i = 0; i < Material.UI_NOMES.length; i++) {
                try {
                    resparam.res.setReplacement(SYSTEMUI, "drawable", Material.UI_NOMES[i],
                            modRes.fwd(Material.UI_IDS[i]));
                    ok++;
                } catch (Throwable t) {
                    log("SystemUI material/" + Material.UI_NOMES[i] + " não substituído: " + t);
                }
            }
            log("SystemUI: " + ok + " drawables substituídos");
            try {
                resparam.res.setReplacement(SYSTEMUI, "bool", "config_hasFlipSettingsPanel", Boolean.TRUE);
            } catch (Throwable t) {
                log("cortina: config_hasFlipSettingsPanel não substituído: " + t);
            }
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
