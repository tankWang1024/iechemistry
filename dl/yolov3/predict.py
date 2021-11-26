'''
predict.py有几个注意点
1、无法进行批量预测，如果想要批量预测，可以利用os.listdir()遍历文件夹，利用Image.open打开图片文件进行预测。
2、如果想要保存，利用r_image.save("img.jpg")即可保存。
3、如果想要获得框的坐标，可以进入detect_image函数，读取top,left,bottom,right这四个值。
4、如果想要截取下目标，可以利用获取到的top,left,bottom,right这四个值在原图上利用矩阵的方式进行截取。
'''
from PIL import Image

from .yolo import YOLO

yolo = YOLO()
img = list(map(str, input("将图片放到img目录下，并输入图片的名字(空格隔开):\n").strip().split()))
for i in range(0, len(img)):
    try:
        image = Image.open(img[i])
    except:
        print('Open Error! Try again!')
        exit()
    else:
        r_image = yolo.detect_image(image)
        r_image.show()
