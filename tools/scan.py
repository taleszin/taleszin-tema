"""Varre PNGs e mede a proporção de azul Holo entre os pixels visíveis.
uso: python3 -I scan.py <dir_res_extraido> > relatorio.tsv"""
import sys, glob, os, colorsys
from PIL import Image

def stats(path):
    im = Image.open(path).convert('RGBA')
    vis = blue = other = 0
    for r, g, b, a in (im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata()):
        if a < 16: continue
        vis += 1
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255); h *= 360
        if s >= 0.40 and v >= 0.35:
            if 182 <= h <= 225: blue += 1
            else: other += 1
    return vis, blue, other

def main(root):
    dirs = [d for d in glob.glob(os.path.join(root, 'res', 'drawable*'))
            if ('hdpi' in d and 'xhdpi' not in d and 'xxhdpi' not in d) or d.endswith(('drawable', 'drawable-nodpi'))]
    for d in sorted(dirs):
        for f in sorted(glob.glob(os.path.join(d, '*.png'))):
            vis, blue, other = stats(f)
            if vis == 0: continue
            print('%s\t%d\t%d\t%d\t%.3f\t%.3f' % (os.path.relpath(f, root), vis, blue, other, blue/vis, other/vis))

if __name__ == '__main__':
    main(sys.argv[1])
