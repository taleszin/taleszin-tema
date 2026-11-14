#!/usr/bin/env python3
"""Confere o APK gerado: (1) dex só com com.m7s.tema (nada de stub do Xposed);
(2) assets/xposed_init e meta-data; (3) cada 9-patch recompilado tem os MESMOS divs,
padding e layout bounds do original do framework; (4) pixels fora do azul ficaram idênticos."""
import json, os, re, subprocess, sys, tempfile, zipfile
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import pngchunks
from gerar import recolor_px

apk = sys.argv[1]
z = zipfile.ZipFile(apk)
nomes = z.namelist()
erros = []
BT = os.path.expanduser('~/Library/Android/sdk/build-tools/35.0.0')

# (1) dex
dd = subprocess.run([os.path.join(BT, 'dexdump')], capture_output=True)
with tempfile.TemporaryDirectory() as t:
    p = os.path.join(t, 'classes.dex'); open(p, 'wb').write(z.read('classes.dex'))
    out = subprocess.run([os.path.join(BT, 'dexdump'), p], capture_output=True, text=True).stdout
classes = re.findall(r"Class descriptor\s+: 'L([^;]+);'", out)
ruins = [c for c in classes if not c.startswith('com/m7s/tema/')]
if ruins: erros.append('classes estranhas no dex: %s' % ruins)
# (2) xposed_init / manifest
if z.read('assets/xposed_init').decode().strip() != 'com.m7s.tema.Tema': erros.append('xposed_init errado')
man = subprocess.run([os.path.join(BT, 'aapt'), 'dump', 'xmltree', apk, 'AndroidManifest.xml'],
                     capture_output=True, text=True).stdout
for k in ('xposedmodule', 'xposeddescription', 'xposedminversion'):
    if k not in man: erros.append('manifest sem %s' % k)

# (3)+(4)
meta = json.load(open(os.path.join(ROOT, 'tools/gerado.json')))
idx = {}
for n in nomes:
    m = re.match(r'res/(drawable[^/]*)/([^/.]+)\.(9\.png|png)$', n)
    if m: idx[(re.sub(r'-v4$', '', m.group(1)), m.group(2))] = n
# redesenhados pela tools/material.py: geometria própria, conferida à parte (padding não vazio)
mat = set(re.findall(r'"([a-z0-9_]+)"', open(os.path.join(ROOT, 'src/com/m7s/tema/Material.java')).read()))
nmat = 0
with tempfile.TemporaryDirectory() as t:
    for (d, nome), arq in idx.items():
        if nome not in mat and not nome.startswith('tz_'): continue
        p = os.path.join(t, 'm.png'); open(p, 'wb').write(z.read(arq))
        np_ = pngchunks.ninepatch(p) if arq.endswith('.9.png') else None
        if np_:
            w, h = Image.open(p).size
            l, r, tp, b = np_['pad']
            if l + r >= w or tp + b >= h: erros.append('%s: conteúdo vazio (pad %r em %dx%d)' % (nome, np_['pad'], w, h))
        nmat += 1
print('material: %d recursos redesenhados conferidos' % nmat)
n9 = nimg = 0
with tempfile.TemporaryDirectory() as t:
    for a in meta['arquivos']:
        k = (a['dir'], a['nome'])
        if a['nome'] in mat: continue
        if k not in idx: erros.append('ausente no APK: %s/%s' % k); continue
        p = os.path.join(t, 'x.png'); open(p, 'wb').write(z.read(idx[k]))
        orig = os.path.join(ROOT, a['orig'])
        if a['ninepatch']:
            got = pngchunks.ninepatch(p)
            exp = a['ninepatch']
            if got is None: erros.append('%s perdeu o npTc' % (k,)); continue
            for f in ('xdivs', 'ydivs', 'pad', 'layout'):
                if (list(got[f]) if got[f] else None) != (list(exp[f]) if exp[f] else None):
                    erros.append('%s: %s mudou %r -> %r' % (k, f, exp[f], got[f]))
            n9 += 1
        A = Image.open(orig).convert('RGBA'); B = Image.open(p).convert('RGBA')
        if A.size != B.size: erros.append('%s: tamanho mudou %r -> %r' % (k, A.size, B.size)); continue
        pa, pb = A.load(), B.load()
        for y in range(A.size[1]):
            for x in range(A.size[0]):
                o, g = pa[x, y], pb[x, y]
                if o[3] != g[3]: erros.append('%s: alfa mudou em %d,%d' % (k, x, y)); break
                if o[3] == 0: continue
                c = recolor_px(*o[:3])
                exp = o[:3] if c is None else c
                if max(abs(exp[i] - g[i]) for i in range(3)) > 2:
                    erros.append('%s: pixel %d,%d %r esperado %r' % (k, x, y, g, exp)); break
            else: continue
            break
        nimg += 1
print('verificação: %d classes no dex, %d imagens conferidas (%d 9-patch com divs/padding/bounds idênticos)'
      % (len(classes), nimg, n9))
if erros:
    print('\n'.join(erros[:40])); sys.exit('FALHOU: %d problemas' % len(erros))
print('OK')
