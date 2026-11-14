#!/usr/bin/env python3
"""Gera preview.png: antes (framework original) | depois (módulo) para ~12 drawables + cores."""
import os, json
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITENS = ['btn_check_on_holo_dark', 'btn_radio_on_holo_dark', 'switch_thumb_activated_holo_dark',
         'scrubber_control_pressed_holo', 'progress_primary_holo_dark', 'textfield_activated_holo_dark',
         'tab_selected_holo', 'list_focused_holo', 'fastscroll_thumb_pressed_holo',
         'text_select_handle_middle', 'btn_rating_star_on_normal_holo_dark',
         'progressbar_indeterminate_holo4', 'spinner_focused_holo_dark_am', 'btn_default_focused_holo_dark']
meta = {(a['dir'], a['nome']): a for a in json.load(open(os.path.join(ROOT, 'tools/gerado.json')))['arquivos']}
def fonte(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
F, FB = fonte(15), fonte(20)
S = 2; CEL = 220; LH = 150; W = 300 + 2 * CEL + 40
cores = json.load(open(os.path.join(ROOT, 'tools/gerado.json')))['cores']
H = 70 + len(ITENS) * LH + 120
img = Image.new('RGB', (W, H), (40, 40, 40)); d = ImageDraw.Draw(img)
d.text((20, 18), 'm7s-tema: azul Holo -> laranja basquete', font=FB, fill=(240, 240, 240))
d.text((320, 50), 'antes', font=F, fill=(200, 200, 200)); d.text((320 + CEL, 50), 'depois', font=F, fill=(200, 200, 200))
y = 75
for n in ITENS:
    a = meta[('drawable-hdpi', n)]
    antes = Image.open(os.path.join(ROOT, a['orig'])).convert('RGBA')
    ext = '.9.png' if a['ninepatch'] else '.png'
    dep = Image.open(os.path.join(ROOT, 'res', a['dir'], n + ext)).convert('RGBA')
    if a['ninepatch']: dep = dep.crop((1, 1, dep.width - 1, dep.height - 1))
    d.text((20, y + LH // 2 - 10), n, font=F, fill=(230, 230, 230))
    for i, im in enumerate((antes, dep)):
        sc = min(S, (CEL - 20) / im.width, (LH - 20) / im.height)
        im2 = im.resize((max(1, round(im.width * sc)), max(1, round(im.height * sc))), Image.NEAREST)
        bg = (16, 16, 16) if 'light' not in n else (240, 240, 240)
        x0 = 310 + i * CEL
        d.rectangle([x0, y + 5, x0 + CEL - 10, y + LH - 5], fill=bg)
        img.paste(im2, (x0 + (CEL - 10 - im2.width) // 2, y + (LH - im2.height) // 2), im2)
    y += LH
d.text((20, y + 10), 'cores (android:color)', font=F, fill=(230, 230, 230))
x = 20
for k in ('holo_blue_light', 'holo_blue_dark', 'holo_blue_bright'):
    o, nv = (int(v, 16) for v in cores[k])
    for j, v in enumerate((o, nv)):
        d.rectangle([x + j * 45, y + 40, x + j * 45 + 40, y + 80], fill=((v >> 16) & 255, (v >> 8) & 255, v & 255))
    d.text((x, y + 85), k, font=fonte(12), fill=(200, 200, 200)); x += 230
img.save(os.path.join(ROOT, 'preview.png'))
print('preview.png', img.size)
