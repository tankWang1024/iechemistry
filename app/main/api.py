from binascii import Error
from email import message
import pathlib
from random import random
from flask.json import JSONDecoder, JSONEncoder

from matplotlib.pyplot import sca, scatter
from sqlalchemy.util.langhelpers import md5_hex
from dl.yolov3 import yolov3Api
from operator import methodcaller
from os import error, path
import os
from time import time
from types import MethodType
from werkzeug.datastructures import Headers
from app.models import IecExpPredict, IecUser
from app.util import wx_request
from . import main
from flask import request, jsonify, session, g
from app import redis_store
import app
import urllib.parse, urllib.request, urllib.error
import hashlib
from .service import iecuserService
from .service import iecImageService
from ..util import wx_request
from ..util import RKJsonEncoder
import json
from qiniu import Auth, put_file, etag
import qiniu.config

from PIL import Image

# 常量定义
UPLOAD_DIR = "../../static/"
AK = "ifgB2xsTb2EQ94gIS5wI3QRkuY7uLhQ1Sv0SrEam"
SK = "1QeBhytnwcwoJch4FJofE05usczEj6G4PmhKKtLg"
QINIU_URL = "http://image.ruankun.xyz/"

"""
    1.user 相关的api
"""


# 初始页面
@main.route("/index", methods=["GET"])
def index():
    return {'code': 1, 'message': "iechemistry backend API is in progressing..."}


@main.route("/login", methods=["POST"])
def loginAndRegister():
    try:
        code = request.form["code"]
        openid = wx_request.code2session(code)
        if type(openid) != int:
            # 有效获得openid, 开始登录
            user = iecuserService.getUserByOpenid(openid)
            if user is None:
                # 没有注册
                user = IecUser(openid=openid)
                user = iecuserService.saveUser(user)
                access_token = iecuserService.getTokenAndSaveToRedis(user)
                print(type(user.id))
                print(type(access_token))
                return jsonify(code=1, newUser=True, message="login succeed!", id=user.id,
                               token=bytes.decode(access_token))
            # 注册过了,登录成功
            access_token = iecuserService.getTokenAndSaveToRedis(user)
            # print(type(user.id))
            # print(type(access_token))
            return jsonify(code=1, message="login succeed!", id=user.id, token=bytes.decode(access_token))
        else:
            return jsonify(code=-1, message='openid error', openid=openid)
    except KeyError as ke:
        print("KeyError: no code")
        return jsonify(code=-1, message="key error, login failed", KeyError=str(ke))


'''
    更新用户的状态, 传入微信名, 电话, 头像, 微信号等信息.
'''


@main.route("/user", methods=["POST"])
def refreshUserInfo():
    try:
        name = request.form["name"]
        phone = request.form["phone"]
        avatar = request.form["avatar"]
        wxid = request.form["wxid"]
        openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
        user = iecuserService.getUserByOpenid(openid)
        user = refreshUser(user, name, phone, avatar, wxid)
        user = iecuserService.saveUser(user)
        if (user != None):
            return jsonify(code=1, message="update success!!", user=userSerializer(user))
        else:
            return jsonify(code=-1, message="update failed")
    except KeyError as e:
        return jsonify(code=-1, message="name,phone,avatar,wxid must in form data, if None must be \"\" ", error=str(e))


@main.route("/user", methods=["GET"])
def getUserInfo():
    openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
    user = iecuserService.getUserByOpenid(openid)
    if user == None:
        return jsonify(message="get data failed", code=-1)
    return jsonify(code=1, message="get data success", user=RKJsonEncoder.usertodict(user))


# 保存图像信息
@main.route("/image", methods=["POST"])
def saveImage():
    # 保证读取文件不会出现问题 @mrruan
    # 改变当前工作目录到指定目录(去掉文件名,只留目录(获取当前脚本的完整路径))
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        # 若rotate=1则需要对图像逆向旋转90度,若rotate=0则不需要旋转90度
        rotate = int(request.form['rotate'])

        f = request.files['image']
        remark = request.form['remark']
        suffix = f.filename.split(".")[1]
        filename = hashlib.md5(str(time()).encode('utf-8')).hexdigest()
        filename = filename + "." + suffix
        # 将文件保存到临时目录,然后上传到qiniu,然后将url保存到数据库
        print(os.listdir())
        print(os.path.join(UPLOAD_DIR, filename))
        f.save(os.path.join(UPLOAD_DIR, filename))
        if False:  # rotate == 1:
            print('对图像进行旋转...')
            # 读出来旋转一下在存回去
            image = Image.open(UPLOAD_DIR + filename)
            out = image.transpose(Image.ROTATE_270)
            out.save(UPLOAD_DIR + filename)
            image.close()
            print('图像旋转成功...')
        # 调用七牛云来干点正事
        rs = uploadFileByQiniu(os.path.join(UPLOAD_DIR, filename), filename)
        if rs['code'] == -1:
            return jsonify(code=-1, message='save picture failed, upload to qiniu failed')
        elif rs['code'] == 1:
            # 上传成功 保存到数据库
            openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
            user = iecuserService.getUserByOpenid(openid)
            image = iecImageService.saveByUrl(rs['url'], user.id, remark)
            return jsonify(code=1, message='upload success', image=RKJsonEncoder.imagetodict(image))
    except Error as e:
        return jsonify(code=-1, message='%s' % e.with_traceback)


@main.route("/process", methods=['POST'])
def process1():
    '''
    第一步处理,传入图像 ID, 实验名, 试管个数, 分割参数4个, 试管浓度参数
    拿到参数后下载图像 -> 调用算法处理 -> 判断算法处理结果是否正确 -> 将处理结果存到数据库 -> 返回前端正确结果
    '''
    remark = request.form['remark']  # 实验标题
    number = request.form['number']  # 试管个数
    top = float(request.form['top'])
    right = float(request.form['right'])
    left = float(request.form['left'])
    bottom = float(request.form['bottom'])
    concentration = request.form['concentration']
    imageid = request.form['imageid']

    # 下载
    image = iecImageService.getImageById(imageid)
    imgpath = "img/"
    yolov3Api.cdCurrentContent()
    filename = downloadBinary(image.url, image.remark, imgpath)  # 1234.jpg
    saveConcentration(imgpath, concentration, image.remark)

    # 已经存到 img/1234.jpg     img/1234.txt
    # 处理
    obj_num = yolov3Api.orrh(image.remark, xmin=left, xmax=right, ymin=top, ymax=bottom)  # remark是图像和浓度文件的名称
    if int(obj_num) != int(number):
        return jsonify(code=-1, message='algorithm cannot work with this image,%s tubes in image,%s tubes actually' % (
        obj_num, number))
    else:
        # 先存数据库在返回成功的信息
        # 需要保存:concentration, object, region, color  这些内容需要使用事务机制保存，保证它们是一致的
        # userid imageid image.remark number, remark[实验名称], concentration
        openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
        user = iecuserService.getUserByOpenid(openid)
        result = iecImageService.saveProcess1(user.id, imageid, image.remark, number, remark, concentration)
        if int(result) == 1:
            return jsonify(code=1, message='%d tubes processed!' % obj_num, userid=user.id, imageid=imageid)
        return jsonify(code=-1, message='cannot save to database.')


@main.route("/processresult", methods=["GET"])
def processresult():
    imageid = request.args.get('imageid')
    datas = iecImageService.getObjectsByImageId(int(imageid))
    return jsonify(code=1, datas=datas)


@main.route("/fit", methods=["GET"])
def fitting():
    openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
    user = iecuserService.getUserByOpenid(openid)

    method = request.args['method']  # SVM
    axiosy = request.args['axiosy']
    axiosx = request.args['axiosx']
    imageid = request.args['imageid']  # imageid可以拿到remark
    concentration_range = request.args['concentration_range']
    image = iecImageService.getImageById(imageid)
    remark = image.remark
    print("/fit api")
    print(method)
    print(axiosy)
    print(axiosx)
    print(imageid)
    print(remark)
    print(concentration_range)
    result = iecImageService.fit(method, axiosx, axiosy, imageid, remark, user.id, concentration_range)
    if result == 1:
        # 查询scatter和linear然后返回
        scatter = iecImageService.getScatterByInamgeId(imageid)
        linear = iecImageService.getLinearByInamgeId(imageid)
        return jsonify(code=1, message='succeed!', scatter=RKJsonEncoder.scattertodict(scatter),
                       linear=RKJsonEncoder.lineartodict(linear))
    else:
        return jsonify(code=-1, message='one error accured,I dont know what to do next...')


# 获取用户的所有 formula
@main.route("/formula", methods=["GET"])
def getMyFormula():
    openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
    user = iecuserService.getUserByOpenid(openid)
    formulas = iecImageService.getFormulasByUserId(user.id)
    data = []
    for formula in formulas:
        data.append(RKJsonEncoder.formulatodict(formula))
    # 连接查询, user - image
    return jsonify(code=1, data=data)


'''
    传入一张图片id, 直接从数据库拿到图片id,拿到公式,
    先处理图片, 一样的过程, 分割, balabala处理完成后, 根据公式求出浓度, 直接返回到前端
'''


@main.route("/predict", methods=["POST"])
def predict():
    number = request.form['number']  # 试管个数
    top = float(request.form['top'])
    right = float(request.form['right'])
    left = float(request.form['left'])
    bottom = float(request.form['bottom'])
    imageid = request.form['imageid']
    formulaid = request.form['formulaid']
    # 随便生成一个remark
    zt_pwd = hashlib.md5()
    zt_pwd.update(str(time()).encode(encoding='utf-8'))
    remark = zt_pwd.hexdigest()
    # 下载
    image = iecImageService.getImageById(imageid)
    imgpath = "img/"
    yolov3Api.cdCurrentContent()
    filename = downloadBinary(image.url, image.remark, imgpath)  # 1234.jpg

    # 已经得到了object region rgb
    obj_num = yolov3Api.orrh(image.remark, xmin=left, xmax=right, ymin=top, ymax=bottom)  # remark是图像和浓度文件的名称
    if int(obj_num) != int(number):
        return jsonify(code=-1, message='algorithm cannot work with this image,%s tubes in image,%s tubes actually' % (
        obj_num, number))
    else:
        # 图像分割处理完成 saveProcessWithoutConcentration
        openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
        user = iecuserService.getUserByOpenid(openid)
        try:
            result = iecImageService.saveProcessWithoutConcentration(user.id, imageid, image.remark, number, remark)
            if int(result) == -1:
                return jsonify(code=-1, message='exception with saving to db.')
            formula = iecImageService.getFormulasByFormulaId(formulaid)
            # 没有报错, 返回的是imageid, 接着根据 formulaid找到公式, 然后预测出浓度, 存到数据库, 然后返回浓度到前端
            iecExpPredict = iecImageService.predict(user.id, imageid, formulaid)
            if iecExpPredict != None:
                return jsonify(code=1, message='success!', iecExpPredict=RKJsonEncoder.predicttodict(iecExpPredict),
                               formula=RKJsonEncoder.formulatodict(formula))
            else:
                return jsonify(code=-1, message='failed!', iecExpPredict="")
        except ValueError as ve:
            ve.with_traceback(None)
            print(ve)
            return jsonify(code=-1, message='cannot convert float NaN to integer', iecExpPredict="")


@main.route("/predictrecord", methods=["GET"])
def getPredictRecord():
    openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
    user = iecuserService.getUserByOpenid(openid)
    userid = user.id
    # 通过userid拿到所有的predict记录
    result = iecImageService.getAllPredictByUserId(userid)
    return jsonify(code=1, data=result)


@main.route("/onepredictrecord", methods=["GET"])
def getOnePredictRecordbyId():
    predictid = request.args['predictid']  # SVM
    predict = iecImageService.findPredictById(predictid)
    formula = iecImageService.getFormulasByFormulaId(predict.formulaid)
    return jsonify(code=1, predict=RKJsonEncoder.predictAndFormulaTodict(predict, formula))


@main.route("/image", methods=["GET"])
def getImageById():
    imageid = request.args['imageid']
    image = iecImageService.getImageById(imageid)
    return jsonify(code=1, image=RKJsonEncoder.imagetodict(image))


@main.route("/statistic", methods=["GET"])
def expstatistic():
    openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
    user = iecuserService.getUserByOpenid(openid)
    userid = user.id
    result = iecImageService.statistic1(userid)
    if result != None:
        return jsonify(code=1, message="success", data=result)
    else:
        return jsonify(code=-1, message="failed")


@main.route("/clean", methods=["GET"])
def cleanServerTmp():
    password = request.args['password']
    if password != "ruankun":
        return jsonify(code=-1, message="password error!")
    rs = yolov3Api.cleanTmpImageFile()
    if rs != -1:
        return jsonify(code=1, message="clean tmp succee!d")
    else:
        return jsonify(code=-1, message="clean tmp failed!")


# 增加接口 1. 获得用户的公式列表 见上方/formula get
#  2. 删除公式
#  3. 增加公式


@main.route("/deleteformula", methods=["POST"])
def deleteMyFormula():
    formulaid = request.args["formulaid"]
    rs = iecImageService.deleteFormulaById(formulaid)
    if rs != -1:
        return jsonify(code=1, message="success")
    else:
        return jsonify(code=-1, message="failed")


'''
    power = db.Column(db.Integer)
    a = db.Column(db.Float, nullable=True)
    b = db.Column(db.Float, nullable=True)
    c = db.Column(db.Float, nullable=True)
    d = db.Column(db.Float, nullable=True)
    r2 = db.Column(db.Float, nullable=True)
    y = db.Column(db.String(255))
    x = db.Column(db.String(255))
    remark  = db.Column(db.String(255))
'''


@main.route("/addformula", methods=["POST"])
def addOneFormula():
    openid = iecuserService.getOpenidInRedis(request.headers.get("token"))
    user = iecuserService.getUserByOpenid(openid)
    userid = user.id
    remark = request.args['remark']
    power = request.args['power']
    a = request.args['a']
    b = request.args['b']
    c = request.args['c']
    d = request.args['d']
    r2 = request.args['r2']
    x = request.args['x']
    y = request.args['y']
    formula = iecImageService.saveFormula(userid, remark, power, a, b, c, d, r2, x, y)
    if formula == None:
        return jsonify(code=-1, message="failed")
    else:
        return jsonify(code=1, message="success", formula=RKJsonEncoder.formulatodict(formula))


# -----------------------------------------------------------------------------
# ----------------------------common method------------------------------------
# -----------------------------------------------------------------------------
def refreshUser(user, name, phone, avatar, wxid):
    if name != "":
        user.name = name
    if name != "":
        user.phone = phone
    if name != "":
        user.avatar = avatar
    if name != "":
        user.wxid = wxid
    return user


def userSerializer(user):
    id = user.id
    name = user.name
    phone = user.phone
    avatar = user.avatar
    wxid = user.wxid
    create_time = user.create_time
    modify_time = user.modify_time
    return '{id:%d, name: %s, phone: %s, avatar: %s, wxid: %s, create_time: %s, modify_time: %s}' % (
    id, name, phone, avatar, wxid, str(create_time), str(modify_time))


def imageSerializer(image):
    id = image.id
    user_id = image.user_id
    url = image.url
    remark = image.remark
    create_time = image.create_time
    modify_time = image.modify_time
    return '{id:%d, user_id: %d, url: %s, remark: %s, create_time: %s, modify_time: %s}' % (
    id, user_id, url, remark, str(create_time), str(modify_time))


def uploadFileByQiniu(filePath, fileName):
    # 构建鉴权对象
    q = Auth(AK, SK)
    # 要上传的空间
    bucket_name = 'public'
    # 上传后保存的文件名
    key = fileName
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)
    # 要上传文件的本地路径
    localfile = filePath
    try:
        ret, info = put_file(token, key, localfile)
        assert ret['key'] == key
        return {'code': 1, 'url': QINIU_URL + key, 'key': key}
    except Error as e:
        print(e)
        e.with_traceback()
        print("上传出错")
        return {'code': -1, 'message': "failed"}


'''
    url: 图片的url
    name: 图像保存的名称 没有后缀
    path: 路径 需要加上/
'''


def downloadBinary(url, name, path):
    # 取url的最后四位为后缀,判断是否含有. 没有得话要加上
    suffix = url[len(url) - 4:]
    if suffix.find(".") == -1:
        suffix = "." + suffix
    try:
        urllib.request.urlretrieve(url, path + name + suffix)
        return (name + suffix)
    except urllib.error.URLError as e:
        print(e)


def saveConcentration(concentrationpath, concentration, filename):
    pathlib.Path(concentrationpath + filename + ".txt").touch()
    file = open(concentrationpath + filename + ".txt", 'w')
    file.write(concentration)
    file.flush()
    file.close()
    return (concentrationpath + filename + ".txt")
