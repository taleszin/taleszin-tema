"""Leitura de chunks PNG (npTc = 9-patch compilado, npOl/npLb = optical bounds)."""
import struct, zlib

def chunks(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    i, out = 8, []
    while i < len(data):
        n, = struct.unpack('>I', data[i:i+4]); t = data[i+4:i+8]
        out.append((t.decode('latin1'), data[i+8:i+8+n])); i += 12 + n
    return out

def ninepatch(path):
    """Devolve dict com xdivs, ydivs, padding (l,r,t,b) e layout bounds, ou None."""
    np = None; ol = None
    for t, d in chunks(path):
        if t == 'npTc':
            nx, ny, nc = d[1], d[2], d[3]
            pl, pr, pt, pb = struct.unpack('>iiii', d[12:28])
            off = 32
            xd = list(struct.unpack('>%di' % nx, d[off:off+4*nx])); off += 4*nx
            yd = list(struct.unpack('>%di' % ny, d[off:off+4*ny])); off += 4*ny
            np = dict(xdivs=xd, ydivs=yd, pad=(pl, pr, pt, pb), ncolors=nc)
        elif t == 'npLb':  # npOl (outline, Android 5+) é ignorado pelo KitKat
            ol = struct.unpack('<iiii', d[:16])  # aapt grava npLb em little-endian
    if np is not None:
        np['layout'] = ol
    return np
