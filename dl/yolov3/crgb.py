# 主要预测rgb和浓度c之间的关系用

from PIL import Image
from torch._C import dtype
from matplotlib import pyplot as plt
import cv2 as cv
from .yolo import YOLO
import numpy as np
from sklearn import linear_model

#---------------------#
# 通过cv2的image对象进行裁剪获得要识别的目标  size[ymin, xmin, ymax, xmax]
#---------------------#
def crop_object(image: np.ndarray, size: list):
    print(int(size[0]))
    dst = image[int(size[0]): int(size[2]), int(size[1]): int(size[3])]
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

    return b, g, r
    # (b, g, r) = cv.split(image)

# y = kx + b
def linear(x: list, a, b):
    y = []
    for i in range(0, len(x)):
        y.append(a * x[i] + b)
    return y

# 根据传入的参数做线性回归
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

# 线性回归的模型
model = linear_model.LinearRegression()

yolo = YOLO()

# 开始之前先把文件夹清空


# 第一步获得图像的object选框
if True:
    img = list(map(str, input("将图片放到img目录下，并输入图片的名字(空格隔开,不用输入.jpg后缀):\n").strip().split()))
    for i in range(0, len(img)):
        print("%s%s%s" % ("img/", img[i],".jpg"))
        try:
            image = Image.open("%s%s%s" % ("img/", img[i],".jpg"))
        except:
            print('Open Error! Try again!')
            exit()
        else:
            r_image = yolo.detect_image(image)
            print('目标已保存... %s' % img[i])
            #r_image.show()

# 第二步将object裁剪出来
imgtable = np.loadtxt('./predict_result/pos/table.txt', dtype=str)
imgtable = np.unique(imgtable)
print('预测得到的pos文件表:\n')
print(imgtable)
print('\n')
for i in range(0, len(imgtable)):
    # 读取文件, 然后根据文件将obj给裁剪出来
    posStr = np.loadtxt(imgtable[i], dtype=str)
    file_name = posStr[0][0]
    file_name = file_name.split("/")[1]
    # 两次变换只取出每一个obj的pos信息,删除其它信息
    pos = posStr.T[2:]
    pos = pos.T
    pos = pos.astype(np.int)
    print(pos)
    pos = pos[np.argsort(pos[:,1])]
    print('排序')
    print(pos)
    # 开始裁剪
    #   把文件名加到文件列表中

    f_obj_table = open('./predict_result/obj/table.txt', 'a')
    f_obj_table.write("%s_%d.jpg" % ( file_name, i+1))
    f_obj_table.write(" ")
    f_obj_table.close()

    #   循环len(pos)次, 将obj信息分割出来
    for i in range(0, len(pos)): # 这么多个obj
        print('process%s: %d object...' % (file_name, (i + 1)))
        image = cv.imread("%s%s" % ("img/", file_name))
        obj = crop_object(image, (pos[i]))
        cv.imwrite('./predict_result/obj/%d_%s' % (i+1, file_name), obj)


        # 每一个obj有一个region需要处理
        f_region_table = open('./predict_result/region/table.txt', 'a')
        f_region_table.write("%s%s%s" % (file_name, "_region", ".jpg"))
        f_region_table.write(" ")
        f_region_table.close()
        region = crop(obj)
        cv.imwrite('./predict_result/region/%s_region_%d.jpg' % (file_name, i+1), region)

        # 顺便把每一个region对应的一个BGR值给搞定
        f_BGR_table = open('./predict_result/bgr/table.txt', 'a')
        f_BGR_table.write("%s%s%s" % (file_name, "_bgr", ".txt"))
        f_BGR_table.write(" ")
        f_BGR_table.close()
        
        B,G,R = average_BGR(region)
        f_bgr = open('./predict_result/bgr/%s_bgr.txt' % (file_name), 'a')
        f_bgr.write(str(B))
        f_bgr.write(' ')
        f_bgr.write(str(G))
        f_bgr.write(' ')
        f_bgr.write(str(R))
        f_bgr.write('\n')
        f_bgr.close()

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

    # 每张图进行线性回归
    plot_linear_img(model, b, concentration, 'Single B value and Concentration regression for %s' % file_name, 'blue', './predict_result/linear_regression/Single_B_regression_for_%s.jpg' % file_name)
    plot_linear_img(model, g, concentration, 'Single G value and Concentration regression for %s' % file_name, 'green', './predict_result/linear_regression/Single_G_regression_for_%s.jpg' % file_name)
    plot_linear_img(model, r, concentration, 'Single R value and Concentration regression for %s' % file_name, 'red', './predict_result/linear_regression/Single_R_regression_for_%s.jpg' % file_name)

# 所有图片的浓度分布图
plt.scatter(x1, c, color='blue')
plt.scatter(x2, c, color='green')
plt.scatter(x3, c, color='red')
plt.title("%s_all" % file_name)
plt.savefig('./predict_result/scatter/all.jpg')
plt.cla()

# 线性回归
plot_linear_img(model, x1, c, 'All B value and Concentration regression', 'blue', './predict_result/linear_regression/All_B_regression.jpg')
plot_linear_img(model, x2, c, 'All G value and Concentration regression', 'green', './predict_result/linear_regression/All_G_regression.jpg')
plot_linear_img(model, x3, c, 'All R value and Concentration regression', 'red', './predict_result/linear_regression/All_R_regression.jpg')