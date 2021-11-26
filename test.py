import json
import os
import app
import urllib

# from dl.yolov3 import yolov3Api

# 保证读取文件不会出现问题 @mrruan
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

def downloadBinary(url, name, path):
    # 取url的最后四位为后缀,判断是否含有. 没有得话要加上
    suffix = url[len(url) - 4:]
    if suffix.find(".") == -1:
        suffix = "." + suffix
    try:
        urllib.request.urlretrieve(url,path + name + suffix)
    except urllib.error.URLError as e:
        print(e)

# print(os.path.join("upload/"))
url = "http://image.ruankun.xyz/1.png"
suffix = url[len(url) - 4:]
# print(suffix)
# print(suffix.find("."))
path = "./dl/yolov3/img/"
# downloadBinary(url, "xxx", path)
# imgpath = "./data/yolov3/image/xxx.png"
# concentrationpath = "./data/yolov3/concentration/concentration.txt"
# yolov3Api.process("example")
class A:
    def __init__(self) -> None:
        self.a = 1
        self.b = "a"

a = A()
b = {'a':a, 'messge':"嘿嘿"}
print(json.dumps(b, default=lambda obj: obj.__dict__, sort_keys=True, indent=None))