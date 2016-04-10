import cv2
import sys
import numpy as np

# Image excision algorithm

# Const:
VERT_EXC_UP = 0.48
VERT_EXC_DOWN = 0.07
HORI_EXC_L = 0.24
HORI_EXC_R = 0.24

ex_img = cv2.imread('R1_GRID.jpg', 0)
V_WIDTH, V_HEIGHT = 320, 240

def cropImage(img, exc_up, exc_down, exc_l, exc_r, tgt_w, tgt_h):
    assert(exc_up > 0 and exc_down > 0 and exc_l > 0 and exc_r > 0)
    assert(exc_up + exc_down < 1 and exc_l + exc_r < 1)
    print img.shape
    row, col = img.shape
    x = int(col * exc_l)
    y = int(row * exc_up)
    w = int(col - col * exc_r)
    h = int(row - row * exc_down)
    return cv2.resize(img[y:h, x:w], dsize = (tgt_w, tgt_h))

if __name__ == '__main__':
    cv2.imshow('non-cropped', cv2.resize(ex_img, dsize = (V_WIDTH, V_HEIGHT)))
    cv2.imshow('cropped', cropImage(ex_img, VERT_EXC_UP, VERT_EXC_DOWN,
        HORI_EXC_L, HORI_EXC_R, tgt_w = V_WIDTH, tgt_h = V_HEIGHT))
    cv2.waitKey(0)
