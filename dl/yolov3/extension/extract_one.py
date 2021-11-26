from functools import reduce
import operator
import cv2 as cv
import numpy as np
from numpy.core.defchararray import center
from numpy.core.fromnumeric import size
from numpy.lib.type_check import imag
#---------------------#
# 通过cv2的image对象进行裁剪获得要识别的目标  size[ymin, xmin, ymax, xmax]
#---------------------#
def crop_object(image: np.ndarray, size: list):
    dst = image[size[0]: size[2], size[1]: size[3]]
    return dst


#---------------------#
# 通过cv2的image对象裁剪,获得受关注的目标区域
#
#---------------------#
def crop(image: np.ndarray):
    height, width, dimention = image.shape
    xmin = int(width * 1 / 5)
    xmax = int(width * 4 / 5)
    ymin = int(height * 3 / 6)
    ymax = int(height * 5 / 6)
    dst = image[ymin: ymax, xmin: xmax]
    return dst

def average_BGR(image: np.ndarray):
    # dimentions = image.shape
    # print(image.shape)
    b = image[:, :, 0]
    g = image[:, :, 1]
    r = image[:, :, 2]

    b = np.mean(b)
    g = np.mean(g)
    r = np.mean(r)

    return [b, g, r]
    # (b, g, r) = cv.split(image)

def draw_circle(BGR: list):
    canvas = np.zeros((330, 330, 3), dtype="uint8")
    (centerX, centerY) = (canvas.shape[1] // 2, canvas.shape[0] // 2)
    black = (0, 0, 0)

    for r in range(0, 175, 25):
        cv.circle(canvas, (centerX, centerY), r, black)

    # 半径为50
    # radius = 50
    color = BGR
    # 中心点
    pt = [60, 60]
    for i in range(0, 50):
        cv.circle(canvas, tuple(pt), i, color, 1)
        cv.circle(canvas, tuple([180, 60]), i, color, 1)

    cv.imshow("canvas", canvas)
    cv.waitKey(0)


#---------------------------------------------------#
# example
#---------------------------------------------------#

# b'tube 0.99' 303 295 467 352
'''
b'tube 1.00' 55 250 291 331
b'tube 1.00' 55 172 289 247
b'tube 0.99' 48 667 299 743
b'tube 0.99' 51 503 296 580
b'tube 0.99' 32 829 314 911
b'tube 0.99' 41 747 307 823
b'tube 0.99' 49 588 294 662
b'tube 0.99' 65 82 277 169
b'tube 0.99' 52 336 296 414
b'tube 0.97' 51 419 299 499
'''
regionNum = np.loadtxt('./extension/region.txt',dtype=int)
length = len(regionNum)
print(length)
print(regionNum[0])
file = open('./extension/BGR.txt', 'w')

for i in range(0, 10):
    print('process %d object...' % (i + 1))
    image = cv.imread('img/test1.jpg')
    obj = crop_object(image, regionNum[i])
    cv.imwrite('./extension/object/obj000' + str(i) + ".jpg",obj)
    region = crop(obj)
    cv.imwrite('./extension/interest/region000' + str(i) + ".jpg", region)
    BGR = average_BGR(region)
    file.write(str(BGR) + '\n')
    # draw_circle(BGR)
