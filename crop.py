from typing import Tuple
import cv2
import math
import numpy as np

def process_page(img, paper_size: Tuple[int, int], mode='color', level=None):
    if img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    _, bw = cv2.threshold(gray, 210, 255, 0)

    # detect lines
    lines = cv2.ximgproc.createFastLineDetector(
        300, # length_threshold
        1, # distance_threshold
        50, # canny_th1
        50, # canny_th2
        3, # canny_aperture_size
        False, # do_merge
    ).detect(bw)

    # for line in lines:
    #     x1, y1, x2, y2 = map(int, line[0])
    #     cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
    # return img

    ta = get_rot(lines)
    img, trans = rotate_img_margin(img, ta)


    # crop
    left_max = (img.shape[1] - paper_size[0]) / 2 + 200
    right_min = (img.shape[1] + paper_size[0]) / 2 - 200
    bottom_min = (paper_size[1]) - 20

    lft, rgt, btm = 0, img.shape[1], img.shape[0]

    ## find edge
    for l in lines:
        p1 = trans_point(l[0][0:2], trans)
        p2 = trans_point(l[0][2:4], trans)

        if abs(p2[0] - p1[0]) > abs(p2[1] - p1[1]):
            for _, y in [p1, p2]:
                if y > bottom_min and y < btm: btm = y
        else:
            for x, _ in [p1, p2]:
                if x < left_max and x > lft: lft = x
                if x > right_min and x < rgt: rgt = x

    center = (lft + rgt) / 2
    lft, rgt = center - paper_size[0] / 2, center + paper_size[0] / 2

    # img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    # cv2.rectangle(img, (int(lft), 0), (int(rgt), int(btm)), (0, 255, 0), 2)
    # return img

    cropped = img[max(0, int(btm - paper_size[1])):int(btm), int(lft):int(rgt)]
    if cropped.shape[0] != paper_size[1]:
        cropped = cv2.copyMakeBorder(cropped, paper_size[1] - cropped.shape[0], 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))

    # color level
    if level is None:
        if mode == 'color':
            level = (0, 200)
        else:
            level = (100, 200)
    y = np.clip(
        (np.arange(256) - level[0]) * (255 / (level[1] - level[0])),
        0,
        255
    ).astype(np.uint8)
    cropped = cv2.LUT(cropped, y)

    # border white
    cv2.rectangle(cropped, (0, 0), (cropped.shape[1], cropped.shape[0]), (255, 255, 255), 10)

    if mode == 'gray':
        cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    return cropped


def get_rot(lines):
    ts = []
    for line in lines:
        x1, y1, x2, y2 = map(int, line[0])
        t = math.atan2(y2 - y1, x2 - x1)
        while t < 0: t += math.pi / 2
        while t > math.pi / 4: t -= math.pi / 2
        if abs(t) > math.pi / 16: continue
        ts.append((t, math.sqrt((x1-x2)**2 + (y1-y2)**2)))
    ta = sum([t * l for t, l in ts]) / sum([l for _, l in ts])
    # if ta > math.pi / 4: ta -= math.pi / 2
    return ta

def rotate_img_margin(img, angle):
    height, width = img.shape[:2]
    trans = cv2.getRotationMatrix2D((width / 2, height / 2), angle * 180 / math.pi, 1)
    abs_cos = abs(trans[0,0])
    abs_sin = abs(trans[0,1])
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)
    bound_h = height
    trans[0, 2] += bound_w/2 - width/2
    # trans[1, 2] += bound_h/2 - height/2
    return cv2.warpAffine(img, trans, (bound_w, bound_h), borderValue=(255,255,255)), trans

def trans_point(p, trans):
    x, y = p
    return (
        x * trans[0, 0] + y * trans[0, 1] + trans[0, 2],
        x * trans[1, 0] + y * trans[1, 1] + trans[1, 2],
    )

def img_is_colored(img):
    if img.shape[2] != 3: return False
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, s, v = cv2.split(hsv)
    return (np.sum((s > 120) & (v > 50))) > (img.shape[0] * img.shape[1] * 0.05)
