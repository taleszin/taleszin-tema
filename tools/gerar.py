#!/usr/bin/env python3
"""Gera os recursos recoloridos do m7s-tema a partir do framework-res.apk / SystemUI.apk extraídos.

uso: python3 -P tools/gerar.py
Lê  stock/fw/res e stock/ui/res (zip extraído) + stock/fw-res.txt (aapt dump --values resources).
Escreve res/drawable*/ (PNG e .9.png fonte com borda reconstruída a partir do chunk npTc),
src/com/m7s/tema/Tabela.java e build/gerado.json (para verificação/prévia)."""
import colorsys, glob, json, os, re, shutil, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import pngchunks
import scan

# Densidades relevantes para tela de 160 dpi com sw=600dp: default(mdpi), hdpi (o firmware
# não tem mdpi, então o sistema reduz o hdpi), nodpi e variações sw600dp/land/en no hdpi.
DIRS_OK = re.compile(r'^drawable(-(sw600dp|land|en|ldrtl|sw480dp))*(-(hdpi|nodpi))?$')
# Excluídos de propósito: azul com significado (chamada recebida, ponto de localização).
EXCLUIR = {'sym_call_incoming', 'ic_maps_indicator_current_position',
           'ic_maps_indicator_current_position_anim1', 'ic_maps_indicator_current_position_anim2',
           'ic_maps_indicator_current_position_anim3', 'search_dropdown_dark', 'search_dropdown_light'}

HUE_MIN, HUE_MAX = 175.0, 230.0

def azul(h, s):
    return HUE_MIN <= h <= HUE_MAX and s >= 0.12

def recolor_px(r, g, b):
    """Leva o azul Holo para o laranja basquete preservando luminância relativa.
    Âncoras: #33B5E5->#FF761A(~#FF7A1A)  #0099CC->#E0590A(~#E0650F)  #00DDFF->#FF9A4D"""
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h *= 360
    if not azul(h, s):
        return None
    t = min(max((196.0 - h) / 8.0, 0.0), 1.0)          # 1 = puxado pro ciano (holo_blue_bright)
    nh = (24.0 + 2.0 * t) / 360
    ns = min(s * (1.15 * (1 - t) + 0.70 * t), 0.94)
    nv = min(v * (1.11 * (1 - t) + 1.00 * t), 1.0)
    rr, gg, bb = colorsys.hsv_to_rgb(nh, ns, nv)
    return round(rr * 255), round(gg * 255), round(bb * 255)

def recolor_img(im):
    im = im.convert('RGBA')
    px = im.load(); w, h = im.size; n = 0
    cache = {}
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0: continue
            k = (r, g, b)
            if k not in cache: cache[k] = recolor_px(r, g, b)
            c = cache[k]
            if c is not None:
                px[x, y] = (c[0], c[1], c[2], a); n += 1
    return im, n

def com_borda(im, np):
    """Reconstrói o .9.png fonte (borda de 1px) a partir dos metadados compilados."""
    w, h = im.size
    out = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0))
    out.paste(im, (1, 1))
    P = out.load(); BK = (0, 0, 0, 255); RD = (255, 0, 0, 255)
    xd, yd = np['xdivs'], np['ydivs']
    for i in range(0, len(xd), 2):
        for x in range(xd[i], xd[i + 1]): P[1 + x, 0] = BK
    for i in range(0, len(yd), 2):
        for y in range(yd[i], yd[i + 1]): P[0, 1 + y] = BK
    pl, pr, pt, pb = np['pad']
    if not (0 <= pl < w - pr <= w and 0 <= pt < h - pb <= h):
        raise ValueError('padding não representável %r em %dx%d' % (np['pad'], w, h))
    for x in range(pl, w - pr): P[1 + x, h + 1] = BK
    for y in range(pt, h - pb): P[w + 1, 1 + y] = BK
    if np['layout']:
        ll, lt, lr, lb = np['layout']
        for x in list(range(0, ll)) + list(range(w - lr, w)): P[1 + x, h + 1] = RD
        for y in list(range(0, lt)) + list(range(h - lb, h)): P[w + 1, 1 + y] = RD
    return out

def selecionar(res_dir):
    sel = []
    for d in sorted(glob.glob(os.path.join(res_dir, 'drawable*'))):
        dn = os.path.basename(d)
        if not DIRS_OK.match(dn): continue
        for f in sorted(glob.glob(os.path.join(d, '*.png'))):
            nome = os.path.basename(f).split('.')[0]
            if nome in EXCLUIR: continue
            vis, blue, other = scan.stats(f)
            # claramente azul: tem azul de verdade e praticamente nenhuma outra cor saturada
            if (blue >= 4 or (blue > 0 and blue == vis)) and other <= 0.02 * vis and other <= 0.1 * blue:
                sel.append((dn, f, nome, vis, blue))
    return sel

def gerar_pacote(tag, res_dir, out_res, meta):
    nomes = {}
    for dn, f, nome, vis, blue in selecionar(res_dir):
        np = pngchunks.ninepatch(f) if f.endswith('.9.png') else None
        im, n = recolor_img(Image.open(f))
        if n == 0: continue
        od = os.path.join(out_res, dn); os.makedirs(od, exist_ok=True)
        if f.endswith('.9.png'):
            if np is None:
                print('aviso: %s sem npTc, ignorado' % f); continue
            try:
                com_borda(im, np).save(os.path.join(od, nome + '.9.png'))
            except ValueError as e:
                print('aviso: %s: %s, ignorado' % (f, e)); continue
        else:
            im.save(os.path.join(od, nome + '.png'))
        nomes.setdefault(nome, []).append(dn)
        meta.append(dict(pkg=tag, dir=dn, nome=nome, orig=os.path.relpath(f, ROOT),
                         ninepatch=np, px=n, vis=vis))
    return sorted(nomes)

COR_FIXA = {0xff33b5e5: 0xffff7a1a, 0xff35b5e5: 0xffff7a1a, 0xff0099cc: 0xffe0650f, 0xff00ddff: 0xffff9a4d}

def cores_framework(dump):
    cores = {}
    for l in open(dump):
        m = re.search(r'resource 0x0106[0-9a-f]{4} android:color/([a-z0-9_]+): t=0x1[c-f] d=0x([0-9a-f]{8})', l)
        if not m: continue
        nome, v = m.group(1), int(m.group(2), 16)
        a, rgb = v >> 24, v & 0xffffff
        if a == 0: continue
        r, g, b = rgb >> 16, (rgb >> 8) & 255, rgb & 255
        h, s, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if not (182 <= h * 360 <= 225 and s >= 0.35): continue
        if (0xff000000 | rgb) in COR_FIXA:
            nv = (a << 24) | (COR_FIXA[0xff000000 | rgb] & 0xffffff)
        else:
            c = recolor_px(r, g, b); nv = (a << 24) | (c[0] << 16) | (c[1] << 8) | c[2]
        if nome in cores and cores[nome][0] != v:
            print('aviso: cor %s varia por config; mantida a primeira' % nome); continue
        cores[nome] = (v, nv)
    return cores

def main():
    out_res = os.path.join(ROOT, 'res')
    for d in glob.glob(os.path.join(out_res, 'drawable*')): shutil.rmtree(d)
    meta = []
    fw = gerar_pacote('android', os.path.join(ROOT, 'stock/fw/res'), out_res, meta)
    ui = gerar_pacote('com.android.systemui', os.path.join(ROOT, 'stock/ui/res'), out_res, meta)
    clash = set(fw) & set(ui)
    if clash: sys.exit('nomes repetidos entre framework e SystemUI: %s' % clash)
    cores = cores_framework(os.path.join(ROOT, 'stock/fw-res.txt'))

    J = ['// GERADO por tools/gerar.py — não editar à mão.', 'package com.m7s.tema;', '',
         'final class Tabela {', '    private Tabela() {}', '']
    J.append('    static final String[] CORES = {')
    J += ['        "%s", // 0x%08x' % (n, cores[n][0]) for n in sorted(cores)]
    J.append('    };'); J.append('    static final int[] CORES_VAL = {')
    J += ['        0x%08x,' % cores[n][1] for n in sorted(cores)]
    J.append('    };'); J.append('')
    for nomeArr, lista in (('FW', fw), ('UI', ui)):
        J.append('    static final String[] %s_NOMES = {' % nomeArr)
        J += ['        "%s",' % n for n in lista]
        J.append('    };')
        J.append('    static final int[] %s_IDS = {' % nomeArr)
        J += ['        R.drawable.%s,' % n for n in lista]
        J.append('    };'); J.append('')
    J.append('}'); J.append('')
    open(os.path.join(ROOT, 'src/com/m7s/tema/Tabela.java'), 'w').write('\n'.join(J))
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    json.dump(dict(cores={k: ['0x%08x' % v[0], '0x%08x' % v[1]] for k, v in cores.items()},
                   fw=fw, ui=ui, arquivos=meta),
              open(os.path.join(ROOT, 'tools/gerado.json'), 'w'), indent=1)
    print('cores: %d | drawables framework: %d nomes (%d arquivos) | SystemUI: %d nomes'
          % (len(cores), len(fw), sum(1 for m in meta if m['pkg'] == 'android'), len(ui)))

if __name__ == '__main__':
    main()
