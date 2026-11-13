# CG/SETTOKU.I2 설득 화면 사상 도표(4bpp, 폭 104px) 글자 開佐尊攘主穏 → 개좌존양주온
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
F = ImageFont.truetype(os.path.join(W, 'fonts/Galmuri11.ttf'), 12)
S, E, ROLL, WD = 1024, 12288, 74, 104     # 니블 스트림을 74px 돌리면 폭 104 도표가 정렬됨
BG, LT, DK, BD = 4, 10, 1, 2
# (y0,y1,x0,x1, 글자, 상자형)
LB = [(22, 34, 27, 41, '개', 1), (44, 58, 3, 18, '좌', 0), (43, 57, 48, 63, '존', 0),
      (70, 85, 26, 41, '양', 0), (74, 88, 3, 17, '주', 0), (74, 88, 49, 64, '온', 0)]
LINES = [('h', 51, 17, 49), ('v', 33, 34, 70), ('h', 84, 13, 50)]

def glyph(t):
    im = Image.new('L', (16, 14), 0); ImageDraw.Draw(im).text((0, 0), t, font=F, fill=255)
    a = np.array(im) >= 128; ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

def apply(D, preview=None):
    D = bytearray(D); a = np.frombuffer(bytes(D[S:E]), 'uint8')
    n = np.zeros(len(a) * 2, 'uint8'); n[0::2] = a & 15; n[1::2] = a >> 4
    k = np.roll(n, -ROLL); L = len(k) // WD * WD; img = k[:L].reshape(-1, WD).copy()
    for y0, y1, x0, x1, t, box in LB:
        img[y0:y1, x0:x1] = BG
    for o, p, q0, q1 in LINES:
        if o == 'h': img[p, q0:q1 + 1] = LT
        else: img[q0:q1 + 1, p] = LT
    for y0, y1, x0, x1, t, box in LB:
        r = img[y0:y1, x0:x1]; g = glyph(t); h, w = g.shape
        G = np.zeros(r.shape, bool); gy = (r.shape[0] - h) // 2; gx = (r.shape[1] - w) // 2
        G[gy:gy + h, gx:gx + w] = g
        if box:
            r[:, :] = DK; r[:-1, 1:-1] = LT; r[G] = DK
        else:
            Eo = ndimage.binary_dilation(G, np.ones((3, 3), bool)) & ~G
            r[Eo] = DK; r[G] = LT
    k[:L] = img.ravel(); n = np.roll(k, ROLL)
    D[S:E] = (n[0::2] | (n[1::2] << 4)).astype('uint8').tobytes()
    if preview:
        Image.fromarray(img[15:95] * 17).resize((WD * 5, 80 * 5), 0).save(preview)
    return bytes(D)

if __name__ == '__main__':
    apply(open(os.path.join(W, 'orig/CG/SETTOKU.I2'), 'rb').read(), os.path.join(W, 'scratch/settoku_ko.png'))
