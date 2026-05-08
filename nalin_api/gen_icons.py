import os, struct, zlib, math

WWW_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')

def _png(path, size):
    if os.path.exists(path):
        print(f'Já existe: {path}')
        return
    cx = cy = (size - 1) / 2
    r_circ = size * 0.40
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            if math.hypot(x - cx, y - cy) < r_circ:
                rows += b'\xfb\xf7\xf4'
            else:
                rows += b'\xc9\x90\x7a'
    def chunk(t, d):
        c = t + d
        return struct.pack('>I', len(d)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(bytes(rows), 6))
           + chunk(b'IEND', b''))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)
    print(f'Gerado: {path}')

icons = os.path.join(WWW_DIR, 'icons')
_png(os.path.join(icons, 'icon-192.png'), 192)
_png(os.path.join(icons, 'icon-512.png'), 512)
_png(os.path.join(icons, 'icon-180.png'), 180)
print('Pronto!')