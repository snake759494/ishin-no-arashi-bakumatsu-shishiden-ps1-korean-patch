# INFOCOM/CHOTIN.I2 축제 등롱 14개 한글화 (두 뱅크: 점등/소등, 각 CLUT 256색 + 48x256 8bpp, 등롱 24x32 2열x8행)
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
F = ImageFont.truetype(os.path.join(W, 'fonts/Galmuri9.ttf'), 10)
# ねぶた おわら 竿灯祭 祇園祭 なまはげ 大文字 七夕祭 だんじり 三社祭 西大寺 花火祭 阿波踊 御柱祭 おくんち
NAMES = ['네부타', '오와라', '간토', '기온', '나마하게', '다이몬지', '칠석', '단지리', '산자', '사이다이', '불꽃', '아와춤', '온바시라', '오쿤치']

def glyph(t):
    if len(t) > 1:
        gs = [glyph(ch) for ch in t]; h = max(g.shape[0] for g in gs)
        out = np.zeros((h, sum(g.shape[1] for g in gs) + len(gs) - 1), bool); x = 0
        for g in gs:
            out[h - g.shape[0]:, x:x + g.shape[1]] = g; x += g.shape[1] + 1
        return out
    im = Image.new('L', (24, 12), 0); ImageDraw.Draw(im).text((0, 0), t, font=F, fill=255)
    a = np.array(im) >= 128; ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def lines(t):
    if len(t) <= 2: return list(t)
    if len(t) == 3: return [t[:2], t[2:]]
    if len(t) == 4: return [t[:2], t[2:]]
    return [t[:3], t[3:]]

def pal(d, o):
    c = np.frombuffer(d[o:o + 512], '<u2').astype(int)
    return np.stack([(c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3], 1)

def apply(D, preview=None):
    D = bytearray(D); prev = []
    for base in (0, 0x3800):
        P = pal(D, base); lum = P @ [0.3, 0.59, 0.11]
        a = np.frombuffer(bytes(D[base + 0x800:base + 0x3800]), 'uint8').reshape(256, 48).copy()
        for k in range(14):
            r, c = k // 2, k % 2
            L = a[r * 32:(r + 1) * 32, c * 24:(c + 1) * 24]
            rgb = P[L].astype(float)
            body = np.zeros(L.shape, bool); body[3:27, 3:21] = True
            body &= (L != 0)
            # 몸통 내부만(테두리 제외)
            inner = ndimage.binary_erosion(body, np.ones((3, 3)))
            l2 = lum[L]
            dark = inner & (l2 < np.percentile(l2[inner], 55))
            dark = ndimage.binary_dilation(dark, np.ones((3, 3))) & inner
            ok = inner & ~dark
            colsh = np.ones(24)
            for x in range(24):
                m = ok[:, x]
                if m.sum() >= 3: colsh[x] = l2[m, x].mean()
            ref = np.median(colsh[8:16]); colsh = np.clip(colsh / max(ref, 1), 0.5, 1.1)
            prow = None
            for y in range(32):
                m = ok[y] & (colsh > 0.85)
                if m.sum() == 0: m = ok[y]
                if m.sum(): prow = (rgb[y][m] / colsh[m][:, None]).mean(0)
                if prow is not None:
                    xs = inner[y]; rgb[y][xs] = prow[None] * colsh[xs][:, None]
            # 한글 그리기
            ls = [glyph(t) for t in lines(NAMES[k])]
            H = sum(g.shape[0] for g in ls) + 2 * (len(ls) - 1)
            y = 3 + (24 - H) // 2
            G = np.zeros(L.shape, bool)
            for g in ls:
                h, w = g.shape; x = (24 - w) // 2
                G[y:y + h, x:x + w] |= g; y += h + 2
            idx = np.argmin(((rgb[..., None, :] - P[None, None]) ** 2).sum(-1) + (P.sum(1) == 0)[None, None] * 1e9, 2)
            out = L.copy(); out[inner] = idx[inner]
            out[G] = np.argmin(lum + (P.sum(1) == 0) * 1e9)
            a[r * 32:(r + 1) * 32, c * 24:(c + 1) * 24] = out
        D[base + 0x800:base + 0x3800] = a.tobytes()
        prev.append(np.concatenate([P[a[(k // 2) * 32:(k // 2 + 1) * 32, (k % 2) * 24:(k % 2 + 1) * 24]] for k in range(14)], 1))
    if preview:
        im = np.concatenate(prev, 0).astype('uint8')
        Image.fromarray(im).resize((im.shape[1] * 4, im.shape[0] * 4), 0).save(preview)
    return bytes(D)

if __name__ == '__main__':
    apply(open(os.path.join(W, 'orig/INFOCOM/CHOTIN.I2'), 'rb').read(), os.path.join(W, 'scratch/chotin.png'))
