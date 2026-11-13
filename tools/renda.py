# CG/RENDA.I2 연타 미니게임 도장 현판(連打命, 8bpp 192폭, CLUT 512바이트) 한글화
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
F = ImageFont.truetype(os.path.join(W, 'fonts/Galmuri11.ttf'), 12)
TEXT = '연타일념'
X0, X1, Y0, Y1 = 62, 129, 28, 48   # 현판 안쪽

def apply(D, preview=None):
    D = bytearray(D)
    c = np.frombuffer(bytes(D[:512]), '<u2').astype(int)
    P = np.stack([(c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3], 1)
    lum = P @ [0.3, 0.59, 0.11]
    a = np.frombuffer(bytes(D[512:512 + 242 * 192]), 'uint8').reshape(242, 192).copy()
    r = a[Y0:Y1, X0:X1]
    L = lum[r]
    red = (P[r][..., 0] > P[r][..., 1] + 30)          # 낙관(붉은 도장)은 보존
    bg = np.bincount(r[L > np.percentile(L, 50)].ravel()).argmax()
    ink = r[L <= np.percentile(L, 3)].ravel()
    ink = np.bincount(ink).argmax() if len(ink) else np.argmin(lum)
    r[(L < lum[bg] - 12) & ~red] = bg
    im = Image.new('L', (X1 - X0, Y1 - Y0), 0); dr = ImageDraw.Draw(im)
    tw = dr.textlength(TEXT, font=F); x = (X1 - X0 - tw) / 2; y = (Y1 - Y0 - 12) / 2 - 1
    for dx in (0,): dr.text((x + dx, y), TEXT, font=F, fill=255)   # 붓글씨 느낌으로 1px 굵게
    g = np.array(im) >= 128
    r[g] = ink
    a[Y0:Y1, X0:X1] = r
    D[512:512 + 242 * 192] = a.tobytes()
    if preview:
        Image.fromarray(P[a[:130]].astype('uint8')).resize((192 * 3, 130 * 3), 0).save(preview)
    return bytes(D)

if __name__ == '__main__':
    apply(open(os.path.join(W, 'orig/CG/RENDA.I2'), 'rb').read(), os.path.join(W, 'scratch/renda_ko.png'))
