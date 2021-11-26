# 主要预测rgb和浓度c之间的关系用

from PIL import Image
from torch._C import dtype

import cv2 as cv
from .yolo import YOLO
import numpy as np
from matplotlib import pyplot as plt

from sklearn.svm import SVR
from sklearn import linear_model

def linear(x: list, a, b):
    y = []
    for i in range(0, len(x)):
        y.append(a * x[i] + b)
    return y

def plot_linear_img(model, x, y, title, color, savePath):
    x = np.array(x).reshape(-1, 1)
    y = np.array(y).reshape(-1, 1)
    model.fit(x, y)
    # 系数
    a = model.coef_[0][0]
    # 截距
    b = model.intercept_[0]
    y2 = linear(x, a, b)
    plt.plot(x, y2, color=color)
    plt.scatter(x, y, color=color)
    plt.title(title)
    plt.savefig(savePath)
    plt.cla()

# 第三步 将bgr值与浓度值进行映射
bgrtable = np.loadtxt('./predict_result/bgr/table.txt', dtype=str)
bgrtable = np.unique(bgrtable)

x1 = [] # b
x2 = [] # g
x3 = [] # r
c  = [] # concentration

#每一次循环读取一个region的rgb 文件名如1.jpg_bgr.txt 如何解析该文件:
#   1.jpg对应文件名通过1.jpg可以读取到img/1.txt,里面存放着浓度值, 而1.jpg_bgr.txt中存放着每一个region的bgr值
for i in range(0, len(bgrtable)):
    file_name = bgrtable[i]
    f_bgr = np.loadtxt("./predict_result/bgr/%s" % file_name, dtype=np.int)
    b = f_bgr.T[0]
    g = f_bgr.T[1]
    r = f_bgr.T[2]

    # 读取浓度文件
    name = file_name.split('.')[0]
    name = 'img/%s.txt' % name
    print('读取浓度文件%s' % name)
    concentration = np.loadtxt(name, dtype=np.int)
    print('浓度值:')
    print(concentration)


    x1 = np.append(x1, list(b))
    x2 = np.append(x2, list(g))
    x3 = np.append(x3, list(r))
    c = np.append(c, list(concentration))
    
    #每张图片的浓度分布图 
    plt.scatter(b, concentration, color='blue')
    plt.scatter(g, concentration, color='green')
    plt.scatter(r, concentration, color='red')
    plt.title(file_name)
    plt.savefig('./predict_result/scatter/%s.jpg' % file_name)
    plt.cla()
    print(len(x1))
    print(x1)
    print(len(c))
    print(c)

# 所有图片的浓度分布图
plt.scatter(x1, c, color='blue')
plt.scatter(x2, c, color='green')
plt.scatter(x3, c, color='red')
plt.title("%s_all" % file_name)
plt.savefig('./predict_result/scatter/all.jpg')
plt.cla()

# 线性回归
model = linear_model.LinearRegression()
plot_linear_img(model, x1, c, 'B value and Concentration regression', 'blue', './predict_result/linear_regression/B_regression.jpg')
plot_linear_img(model, x2, c, 'G value and Concentration regression', 'green', './predict_result/linear_regression/G_regression.jpg')
plot_linear_img(model, x3, c, 'R value and Concentration regression', 'red', './predict_result/linear_regression/R_regression.jpg')