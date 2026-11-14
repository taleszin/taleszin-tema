#!/usr/bin/env python3
"""Linguagem visual da Taleszin OS: desenha (não recolore) os componentes do sistema.

uso: python3 tools/material.py      (depois de tools/gerar.py, se ele for rodado de novo)
Escreve res/drawable-hdpi/*.png|*.9.png com os MESMOS nomes do framework/SystemUI (sobrescreve as
versões recoloridas) e src/com/m7s/tema/Material.java com as listas que o Tema.java aplica por cima.

Tokens (dp; desenho em hdpi = 1,5 px/dp, o firmware não tem mdpi e reduz o hdpi para a tela de 160 dpi):
  superfície  #1C2026   superfície 2 #262C33   painel #0E1114   contorno #8A939C   laranja #FF7A1A
  cantos: janelas 16dp, menus 12dp, cartões 8dp, toast e interruptor em pílula.
Sem custo de CPU: são bitmaps do mesmo tamanho dos originais (9-patch esticam de graça)."""
import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'res', 'drawable-hdpi')
OUTX = os.path.join(ROOT, 'res', 'drawable')
SS = 4  # supersampling para antialias

ACCENT = (0xFF, 0x7A, 0x1A)
DARK = dict(surface=(0x1C, 0x20, 0x26), surface2=(0x26, 0x2C, 0x33), outline=(0x8A, 0x93, 0x9C),
            track=(0x3A, 0x41, 0x4A), thumb=(0xE6, 0xE9, 0xEC), card=(0x1E, 0x23, 0x29),
            card_pressed=(0x2A, 0x30, 0x38), card_low=(0x18, 0x1C, 0x21))
LIGHT = dict(surface=(0xFF, 0xFF, 0xFF), surface2=(0xF1, 0xF3, 0xF5), outline=(0x5F, 0x66, 0x70),
             track=(0xB8, 0xBE, 0xC4), thumb=(0xFA, 0xFA, 0xFA), card=(0xFF, 0xFF, 0xFF),
             card_pressed=(0xEE, 0xF0, 0xF2), card_low=(0xF5, 0xF6, 0xF7))

FW, UI = [], []   # (nome do recurso, arquivo) aplicados no framework / SystemUI


def canvas(w, h):
    return Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))


def down(im):
    return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def rrect(d, box, r, fill=None, outline=None, width=0):
    x0, y0, x1, y1 = [v * SS for v in box]
    d.rounded_rectangle((x0, y0, x1 - 1, y1 - 1), radius=r * SS, fill=fill, outline=outline, width=width * SS)


def shadow(w, h, box, r, blur, alpha=110, dy=2):
    sh = canvas(w, h)
    x0, y0, x1, y1 = box
    rrect(ImageDraw.Draw(sh), (x0, y0 + dy, x1, y1 + dy), r, fill=(0, 0, 0, alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur * SS))


def save_png(name, im, where=FW):
    os.makedirs(OUT, exist_ok=True)
    down(im).save(os.path.join(OUT, name + '.png'))
    where.append(name)


def save_9(name, im, sx, sy, pad, where=FW):
    """im: imagem SS-ampliada; sx/sy: (início, fim) da faixa esticável; pad: (l, r, t, b) em px."""
    im = down(im)
    w, h = im.size
    out = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0))
    out.paste(im, (1, 1))
    px = out.load()
    blk = (0, 0, 0, 255)
    for spans, horiz in ((sx, True), (sy, False)):
        if isinstance(spans[0], int):
            spans = [spans]
        for a, b in spans:
            for i in range(a, b):
                if horiz: px[1 + i, 0] = blk
                else: px[0, 1 + i] = blk
    l, r, t, b = pad
    for i in range(l, w - r): px[1 + i, h + 1] = blk
    for i in range(t, h - b): px[w + 1, 1 + i] = blk
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, name + '.9.png'))
    where.append(name)


# ------------------------------------------------------------------ caixa de marcar e rádio (48x48)
def halo(d, c, a):
    d.ellipse((2 * SS, 2 * SS, 46 * SS, 46 * SS), fill=rgba(c, a))


def check(on, pal, state):
    im = canvas(48, 48); d = ImageDraw.Draw(im)
    if state in ('pressed', 'focused'):
        halo(d, ACCENT if on else pal['outline'], 46 if state == 'pressed' else 28)
    a = 97 if 'disabled' in state else 255
    box = (10.5, 10.5, 37.5, 37.5)
    if on:
        rrect(d, box, 4, fill=rgba(ACCENT, a))
        pts = [(16 * SS, 24.5 * SS), (21.5 * SS, 30 * SS), (32 * SS, 18.5 * SS)]
        d.line(pts, fill=(255, 255, 255, a), width=int(3.4 * SS), joint='curve')
    else:
        rrect(d, box, 4, outline=rgba(pal['outline'], a), width=3)
    return im


def radio(on, pal, state):
    im = canvas(48, 48); d = ImageDraw.Draw(im)
    if state in ('pressed', 'focused'):
        halo(d, ACCENT if on else pal['outline'], 46 if state == 'pressed' else 28)
    a = 97 if 'disabled' in state else 255
    c = ACCENT if on else pal['outline']
    d.ellipse((9 * SS, 9 * SS, 39 * SS, 39 * SS), outline=rgba(c, a), width=3 * SS)
    if on:
        d.ellipse((16.5 * SS, 16.5 * SS, 31.5 * SS, 31.5 * SS), fill=rgba(c, a))
    return im


STATES = {'': 'normal', '_pressed': 'pressed', '_focused': 'focused', '_disabled': 'disabled',
          '_disabled_focused': 'disabled', '_disable': 'disabled', '_disable_focused': 'disabled',
          '_normal': 'normal'}


def checks_and_radios():
    for theme, pal in (('dark', DARK), ('light', LIGHT)):
        for on in (True, False):
            onoff = 'on' if on else 'off'
            for suf, st in STATES.items():
                save_png(f'btn_check_{onoff}{suf}_holo_{theme}', check(on, pal, st))
                if suf not in ('_disable', '_disable_focused', '_normal'):
                    save_png(f'btn_radio_{onoff}{suf}_holo_{theme}', radio(on, pal, st))


# ------------------------------------------------------------------ interruptor em pílula
def switches():
    H = 42
    for theme, pal in (('dark', DARK), ('light', LIGHT)):
        # trilho: pílula de 14dp (21 px) com faixa central esticável; trilho "ligado" vem num seletor XML
        for name, col, a in ((f'tz_track_off_{theme}', pal['track'], 255),
                             (f'tz_track_on_{theme}', ACCENT, 120),
                             (f'tz_track_disabled_{theme}', pal['track'], 110)):
            im = canvas(44, H); d = ImageDraw.Draw(im)
            rrect(d, (6, 10.5, 38, 31.5), 10.5, fill=rgba(col, a))
            save_9(name, im, (21, 23), (20, 22), (0, 0, 0, 0), where=[])
        # bolinha: 20dp (30 px) num quadro 42x42; padding 21/21 = largura do polegar (texto zerado no hook)
        for name, col, a, pressed in ((f'switch_thumb_holo_{theme}', pal['thumb'], 255, False),
                                      (f'switch_thumb_activated_holo_{theme}', ACCENT, 255, False),
                                      (f'switch_thumb_pressed_holo_{theme}', ACCENT, 255, True),
                                      (f'switch_thumb_disabled_holo_{theme}', pal['thumb'], 110, False)):
            # quadro 44x42: padding 21+22 = 43 px de polegar (precisa sobrar 1 px de conteúdo no 9-patch)
            im = canvas(44, H)
            im.alpha_composite(shadow(44, H, (7, 6, 37, 36), 15, 1.6, 90 if a == 255 else 30, 1))
            d = ImageDraw.Draw(im)
            if pressed:
                d.ellipse((2 * SS, 1 * SS, 42 * SS, 41 * SS), fill=rgba(ACCENT, 50))
            d.ellipse((7 * SS, 6 * SS, 37 * SS, 36 * SS), fill=rgba(col, a))
            save_9(name, im, [(0, 1), (43, 44)], [(0, 1), (41, 42)], (21, 22, 3, 3))
        os.makedirs(OUTX, exist_ok=True)
        open(os.path.join(OUTX, f'switch_track_holo_{theme}.xml'), 'w').write(f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Taleszin OS: trilho em pílula; laranja translúcido quando ligado -->
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_enabled="false" android:drawable="@drawable/tz_track_disabled_{theme}" />
    <item android:state_checked="true" android:drawable="@drawable/tz_track_on_{theme}" />
    <item android:drawable="@drawable/tz_track_off_{theme}" />
</selector>
''')
        FW.append(f'switch_track_holo_{theme}')


# ------------------------------------------------------------------ janelas, menus, toast
def panel(name, pal_c, r, sh, pad_inner, corners='all', where=FW, alpha=255):
    """Superfície arredondada com sombra suave na margem `sh` (px). pad_inner: padding do conteúdo."""
    fix = sh + r + 2
    W = H = fix * 2 + 4
    top = corners in ('all', 'top'); bot = corners in ('all', 'bottom')
    im = canvas(W, H)
    y0 = sh if top else -r - 4
    y1 = H - sh if bot else H + r + 4
    im.alpha_composite(shadow(W, H, (sh, y0, W - sh, y1), r, sh / 2.2, 120, 2))
    d = ImageDraw.Draw(im)
    rrect(d, (sh, y0, W - sh, y1), r, fill=rgba(pal_c, alpha))
    sy = (fix, H - fix) if (top and bot) else ((0, H - fix) if bot else (fix, H)) if corners != 'none' else (0, H)
    save_9(name, im, (fix, W - fix), sy, pad_inner, where=where)


def surfaces():
    for theme, pal in (('dark', DARK), ('light', LIGHT)):
        panel(f'dialog_full_holo_{theme}', pal['surface'], 24, 12, (12, 12, 12, 12))
        panel(f'dialog_top_holo_{theme}', pal['surface'], 24, 12, (12, 12, 12, 0), 'top')
        panel(f'dialog_middle_holo_{theme}', pal['surface'], 24, 12, (12, 12, 0, 0), 'none')
        panel(f'dialog_bottom_holo_{theme}', pal['surface'], 24, 12, (12, 12, 0, 12), 'bottom')
        panel(f'menu_dropdown_panel_holo_{theme}', pal['surface2'], 18, 12, (12, 12, 12, 12))
        panel(f'menu_popup_panel_holo_{theme}', pal['surface2'], 18, 12, (12, 12, 12, 12))
    panel('spinner_dropdown_background_down', DARK['surface2'], 18, 9, (9, 9, 6, 9))
    panel('spinner_dropdown_background_up', DARK['surface2'], 18, 9, (9, 9, 9, 6))
    # toast: pílula escura
    W, H = 96, 66
    im = canvas(W, H)
    im.alpha_composite(shadow(W, H, (6, 6, W - 6, H - 6), 27, 2.5, 110, 2))
    rrect(ImageDraw.Draw(im), (6, 6, W - 6, H - 6), 27, fill=rgba(DARK['surface2'], 245))
    save_9('toast_frame', im, (36, 60), (32, 34), (36, 36, 17, 17))


# ------------------------------------------------------------------ notificações e atalhos rápidos
def notifications():
    # cartões de 8dp (12 px) com 4dp de respiro nas laterais e 3 px entre um e outro
    for name, col in (('notification_bg_normal', DARK['card']),
                      ('notification_bg_normal_pressed', DARK['card_pressed']),
                      ('notification_bg_low_normal', DARK['card_low']),
                      ('notification_bg_low_pressed', DARK['card_pressed'])):
        W = H = 40
        im = canvas(W, H)
        rrect(ImageDraw.Draw(im), (6, 2, W - 6, H - 2), 12, fill=rgba(col))
        save_9(name, im, (18, 22), (14, 26), (6, 6, 2, 2))
    # fundo do painel (SystemUI): grafite quase preto, sem a textura listrada
    im = canvas(30, 6)
    ImageDraw.Draw(im).rectangle((0, 0, 30 * SS, 6 * SS), fill=(0x0E, 0x11, 0x14, 248))
    save_9('notification_panel_bg', im, (12, 18), (0, 6), (0, 0, 0, 0), where=UI)
    # bloco das configurações rápidas: cartão arredondado (seletor XML aponta para os dois)
    for name, col in (('tz_qs_tile', DARK['card']), ('tz_qs_tile_pressed', DARK['card_pressed'])):
        W = H = 48
        im = canvas(W, H)
        rrect(ImageDraw.Draw(im), (3, 3, W - 3, H - 3), 18, fill=rgba(col))
        save_9(name, im, (22, 26), (22, 26), (6, 6, 6, 6), where=[])
    open(os.path.join(OUTX, 'qs_tile_background.xml'), 'w').write('''<?xml version="1.0" encoding="utf-8"?>
<!-- Taleszin OS: bloco arredondado nas configurações rápidas -->
<selector xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:state_pressed="true" android:drawable="@drawable/tz_qs_tile_pressed" />
    <item android:drawable="@drawable/tz_qs_tile" />
</selector>
''')
    UI.append('qs_tile_background')


# ------------------------------------------------------------------ listas (Configurações etc.)
def lists():
    # item ativo: pílula laranja translúcida com respiro, não o bloco chapado do Holo
    W = H = 36
    im = canvas(W, H)
    rrect(ImageDraw.Draw(im), (4, 2, W - 4, H - 2), 12, fill=rgba(ACCENT, 52))
    save_9('list_activated_holo', im, (16, 20), (16, 20), (0, 0, 0, 0))
    # título de seção: sem o sublinhado do Holo (a hierarquia fica com a cor/peso do texto)
    for theme in ('dark', 'light'):
        save_9(f'list_section_divider_holo_{theme}', canvas(9, 48), (3, 6), (3, 6), (0, 0, 0, 0))


def java():
    def arr(xs):
        return ''.join(f'        "{x}",\n' for x in xs)
    def ids(xs):
        return ''.join(f'        R.drawable.{x},\n' for x in xs)
    src = f'''// GERADO por tools/material.py — não editar à mão.
package com.m7s.tema;

/** Componentes redesenhados da Taleszin OS (aplicados depois da recoloração da {{@link Tabela}}). */
final class Material {{
    private Material() {{}}

    static final String[] FW_NOMES = {{
{arr(FW)}    }};
    static final int[] FW_IDS = {{
{ids(FW)}    }};
    static final String[] UI_NOMES = {{
{arr(UI)}    }};
    static final int[] UI_IDS = {{
{ids(UI)}    }};
}}
'''
    open(os.path.join(ROOT, 'src', 'com', 'm7s', 'tema', 'Material.java'), 'w').write(src)


if __name__ == '__main__':
    checks_and_radios(); switches(); surfaces(); notifications(); lists()
    # sem duplicatas (o mesmo nome em hdpi e drawable/ geraria dois IDs)
    FW[:] = list(dict.fromkeys(FW)); UI[:] = list(dict.fromkeys(UI))
    # só substitui o que existe no firmware (nome inexistente faria o Xposed registrar falha)
    import glob
    def existe(base, n):
        return any(os.path.splitext(os.path.splitext(os.path.basename(p))[0])[0] == n
                   for p in glob.glob(os.path.join(ROOT, 'stock', base, 'res', 'drawable*', n + '.*')))
    for lst, base in ((FW, 'fw'), (UI, 'ui')):
        for n in [x for x in lst if not existe(base, x)]:
            lst.remove(n)
            for p in glob.glob(os.path.join(OUT, n + '.*')) + glob.glob(os.path.join(OUTX, n + '.*')):
                os.remove(p)
            print('  sem equivalente no firmware, ignorado:', n)
    java()
    print(f'material: {len(FW)} recursos do framework + {len(UI)} da SystemUI')
