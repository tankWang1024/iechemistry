from binascii import Error
from matplotlib import use
import numpy as np
from app.models import IecExpImage
import app
from ...models import IecExpColor, IecExpConcentration, IecExpFormula, IecExpImage, IecExpLinear, IecExpObject, \
    IecExpPredict, IecExpRegion, IecExpScatter, db
from qiniu import Auth, put_file, etag
import os
from dl.yolov3 import yolov3Api
import random
import json
import colorsys

UPLOAD_DIR_OBJECT = "predict_result/obj"
UPLOAD_DIR_REGION = "predict_result/region"
COLOR_DIR = "predict_result/bgr"
FORMULA_DIR = "predict_result/formula"

UPLOAD_DIR_SCATTER = "predict_result/scatter"
UPLOAD_DIR_LINEAR = "predict_result/linear_regression"
AK = "ifgB2xsTb2EQ94gIS5wI3QRkuY7uLhQ1Sv0SrEam"
SK = "1QeBhytnwcwoJch4FJofE05usczEj6G4PmhKKtLg"
QINIU_URL = "http://image.ruankun.xyz/"


def saveByUrl(url, userid, remark):
    iecExpImage = IecExpImage(user_id=userid, url=url, remark=remark)
    try:
        db.session.add(iecExpImage)
        db.session.commit()
        iecExpImage = IecExpImage.query.filter_by(url=url).first()
        print(iecExpImage)
        return iecExpImage
    except Exception as e:
        db.session.rollback()
        print(e)
        return None


def saveFormula(userid, remark, power, a, b, c, d, r2, x, y):
    try:
        formula = IecExpFormula(userid=userid, remark=remark, power=power, a=a, b=b, c=c, d=d, r2=r2, x=x, y=y,
                                imageid=0)
        db.session.add(formula)
        db.session.commit()
        return formula
    except Error as e:
        print(e)
        return None


def getImageById(id):
    image = IecExpImage.query.filter_by(id=id).first()
    return image


def deleteFormulaById(formulaid):
    try:
        formula = IecExpFormula.query.filter_by(id=formulaid).first()
        db.session.delete(formula)
        db.session.commit()
        return 1
    except Exception as e:
        return -1


def getAllPredictByUserId(userid):
    datas = db.session.query(IecExpPredict.id, IecExpPredict.imageid, IecExpPredict.userid, IecExpPredict.concentration,
                             IecExpPredict.formulaid, \
                             IecExpPredict.create_time, IecExpImage.url, IecExpFormula.power, IecExpFormula.r2,
                             IecExpFormula.a, \
                             IecExpFormula.b, IecExpFormula.c, IecExpFormula.d, IecExpFormula.remark, IecExpFormula.x,
                             IecExpFormula.y) \
        .outerjoin(IecExpImage, IecExpImage.id == IecExpPredict.imageid).outerjoin(IecExpFormula,
                                                                                   IecExpFormula.id == IecExpPredict.formulaid) \
        .filter_by(userid=userid)
    result = []
    for data in datas:
        tmp = {'id': data[0], 'imageid': data[1], 'userid': data[2], 'concentration': data[3], 'formulaid': data[4], \
               'create_time': data[5], 'url': data[6], 'power': data[7], 'r2': data[8], 'a': data[9], 'b': data[10],
               'c': data[11], 'd': data[12], 'formula_remark': data[13], \
               'x': data[14], 'y': data[15]}
        result.append(tmp)
    return result


def fit(method, axiosx, axiosy, imageid, remark, userid, concentration_range):
    # userid imageid objurl remark objectid regionurl regionid rgb hsv cmyk concentration
    objects = db.session.query(IecExpColor.rgb, IecExpConcentration.concentration, IecExpObject.remark, IecExpColor.hsv) \
        .outerjoin(IecExpRegion, IecExpRegion.objectid == IecExpObject.id).outerjoin(IecExpColor, IecExpRegion.id \
                                                                                     == IecExpColor.regionid).outerjoin(
        IecExpConcentration, IecExpRegion.id == IecExpConcentration.regionid). \
        filter_by(imageid=imageid)
    # 需要浓度, rgb
    concentration = []
    rgb = []
    hsv = []
    remark = ''
    for obj in objects:
        rgb.append(obj[0].split(" "))
        hsv.append(obj[3].split(" "))
        print(obj[1])
        concentration.append(float(obj[1]))
        remark = obj[2]
    # 根据method取线性拟合或者二次拟合或者其它, 根据axiosx取R G B, 根据axiosy取浓度, 根绝remark取名字
    x = getRorGorBbyX(axiosx, rgb, hsv)
    y = getCbyAxiosy(axiosy, concentration)
    print('----------------看看拿到的数据--------------')
    print(concentration)
    print(x)
    print(y)
    if concentration_range != "" :
        pre_index = int(concentration_range.split("-")[0])-1
        next_index = int(concentration_range.split("-")[1])
        print(pre_index)
        print(next_index)
        a, b, r2 = yolov3Api.fit(method, x[pre_index:next_index], y[pre_index:next_index], remark, axiosx)
    else:
        a, b, r2 = yolov3Api.fit(method, x, y, remark, axiosx)
    # tolov3处理完这里还要上传到七牛云,然后存数据库,然后在返回
    uid = str(random.randint(0, 99999))
    rs = uploadFileByQiniu(os.path.join(UPLOAD_DIR_SCATTER, remark + ".jpg"), remark + "_" + uid + "_scatter.jpg")
    rs2 = uploadFileByQiniu(os.path.join(UPLOAD_DIR_LINEAR, remark + ".jpg"), remark + "_" + uid + "_linear.jpg")
    url_scatter = rs['url']
    url_linear = rs2['url']
    # 存数据库
    iecExpScatter = IecExpScatter(imageid=imageid, url=url_scatter, remark=remark)
    iecExpLinear = IecExpLinear(imageid=imageid, url=url_linear, remark=remark)
    iecExpFormula = IecExpFormula(imageid=imageid, userid=userid, power=1, a=a, b=b, r2=r2, remark=remark, y=axiosy,
                                  x=axiosx)
    try:
        db.session.add(iecExpScatter)
        db.session.add(iecExpLinear)
        db.session.add(iecExpFormula)
        db.session.commit()
        return 1
    except Error as e:
        e.with_traceback
        print(e)
        db.session.rollback()
        return -1


def getLinearByInamgeId(imageid):
    linear = IecExpLinear.query.filter_by(imageid=imageid).order_by(IecExpLinear.modify_time.desc()).first()
    return linear


def getFormulasByUserId(userid):
    formula = IecExpFormula.query.filter_by(userid=userid)
    print(formula)
    return formula


'''
    最近实验的两组实验, 根据用户的最近的两个formula记录可以拿到remark信息
    统计formula个数统计实验组数
    统计image个数统计上传图像个数
    统计object个数获得试管根数
    统计region个数获得选取个数
    统计用户第一个formula的创建时间获取第一次做实验的时间
'''


def statistic1(userid):
    try:
        formulas = IecExpFormula.query.filter_by(userid=userid).all()
        images = IecExpImage.query.filter_by(user_id=userid).all()
        objects = IecExpObject.query.filter_by(userid=userid).all()
        regions = IecExpRegion.query.filter_by(userid=userid).all()

        # 总共实验次数
        expNum = len(formulas)
        latestExp1 = "上个世纪"
        latestExp1_time = ""
        latestExp2 = "上个世纪"
        latestExp2_time = ""
        first_time = "上个世纪"
        if expNum == 1:
            # 最近的实验名称1
            latestExp1 = formulas[0].remark
            latestExp1_time = formulas[0].create_time
        if expNum >= 2:
            # 最近的实验名称1
            latestExp1 = formulas[expNum - 1].remark
            # 最近的实验名称2
            latestExp2 = formulas[expNum - 2].remark
            latestExp1_time = formulas[expNum - 1].create_time
            latestExp2_time = formulas[expNum - 2].create_time

        # 上传的图像总数
        imageNum = len(images)
        # 试管个数
        objectNum = len(objects)
        # 区域个数
        regionsNum = len(regions)
        # 第一次做实验的时间
        if expNum >= 1:
            first_time = formulas[0].create_time
        return {'expNum': expNum, 'latestExp1': latestExp1, 'latestExp2': latestExp2, 'first_time': first_time, \
                'imageNum': imageNum, 'objectNum': objectNum, 'regionsNum': regionsNum,
                'latestExp1_time': latestExp1_time, 'latestExp2_time': latestExp2_time}
    except Error as e:
        print(e)
        return None


def getScatterByInamgeId(imageid):
    scatter = IecExpScatter.query.filter_by(imageid=imageid).order_by(IecExpScatter.modify_time.desc()).first()
    return scatter


def getFormulasByFormulaId(formulaid):
    formula = IecExpFormula.query.filter_by(id=formulaid).first()
    return formula


def getObjectsByImageId(imageid):
    # userid imageid objurl remark objectid regionurl regionid rgb hsv cmyk concentration
    objects = db.session.query(IecExpObject.userid, IecExpObject.imageid, IecExpObject.url, IecExpObject.remark, \
                               IecExpRegion.objectid, IecExpRegion.url, IecExpColor.regionid, IecExpColor.rgb,
                               IecExpColor.hsv, \
                               IecExpColor.cmyk, IecExpConcentration.concentration) \
        .outerjoin(IecExpRegion, IecExpRegion.objectid == IecExpObject.id).outerjoin(IecExpColor,
                                                                                     IecExpRegion.id == IecExpColor.regionid).outerjoin(
        IecExpConcentration, IecExpRegion.id == IecExpConcentration.regionid).filter_by(imageid=imageid)
    print('---')
    print(objects)
    results = []
    for obj in objects:
        tmp = {'object_id': obj[4], 'userid': obj[0], \
               'imageid': obj[1], 'object_url': obj[2], 'remark': obj[3], \
               'region_url': obj[5], 'region_id': obj[6], 'rgb': obj[7], \
               'hsv': obj[8], 'cmyk': obj[9], 'concentration': obj[10]}
        results.append(tmp)
    # 拿到10个objects了, 现在需要根据每个object拿到region, 在拿到color和 concentration
    # 使用联合查询
    return results


def predict(userid, imageid, formulaid):
    # 先根据imageid拿到color[RGB]信息
    formula = IecExpFormula.query.filter_by(id=formulaid).first()
    colors = getColorByImageId(imageid, formula)
    # 因为现在只用了线性拟合, 所以我就不判断power了
    a = formula.a
    b = formula.b
    concentration = colors * a + b
    iecExpPredict = IecExpPredict(imageid=imageid, userid=userid, concentration=str(concentration), formulaid=formulaid)
    try:
        db.session.add(iecExpPredict)
        db.session.commit()
        return iecExpPredict
    except Error as e:
        print(e)
        db.session.rollback()
        return None


def getColorByImageId(imageid, formula):
    # 多个iecExpColor
    iecExpColors = IecExpColor.query.filter_by(imageid=imageid)
    axiosx = formula.x
    axiosy = formula.y
    rgb = []
    hsv = []
    for iecExpColor in iecExpColors:
        rgb.append(iecExpColor.rgb.split(" "))
        hsv.append(iecExpColor.hsv.split(" "))
    x_data = getRorGorBbyX(axiosx, rgb, hsv)
    return x_data


def saveProcessWithoutConcentration(userid, imageid, imageremark, number, remark):
    yolov3Api.cdCurrentContent()
    color = np.loadtxt(COLOR_DIR + "/%s.jpg_bgr.txt" % imageremark, dtype=np.int)
    # 随机生成的id
    obj_id = random.randint(0, 999999989)
    region_id = random.randint(0, 999999989)
    color_id = random.randint(0, 999999989)

    # 对一个imageid来说,只能存在一组数据,所以应该把之前的object region color concentration全部删掉
    db.session.query(IecExpObject).filter(IecExpObject.imageid == imageid).delete()
    db.session.query(IecExpRegion).filter(IecExpRegion.imageid == imageid).delete()
    db.session.query(IecExpColor).filter(IecExpColor.imageid == imageid).delete()

    for i in range(0, int(number)):  # 总共需要处理这么多个object
        obj_name = "%s_%s.jpg" % (str(i + 1), imageremark)
        region_name = "%s.jpg_region_%s.jpg" % (imageremark, str(i + 1))
        rs = uploadFileByQiniu(os.path.join(UPLOAD_DIR_OBJECT, obj_name), obj_name)
        rs2 = uploadFileByQiniu(os.path.join(UPLOAD_DIR_REGION, region_name), region_name)
        if rs['code'] == -1 and rs2['code'] == -1:
            break
        elif rs['code'] == 1 and rs2['code'] == 1:
            # 上传成功
            obj_url = rs['url']
            region_url = rs2['url']
            obj_id = obj_id + 1
            region_id = region_id + 1
            color_id = color_id + 1
            color_rgb = "%s %s %s" % (color[i][0], color[i][1], color[i][2])
            hsv = colorsys.rgb_to_hsv(color[i][0], color[i][1], color[i][2])
            color_hsv = "%.2f %.2f %.2f" % (hsv[0], hsv[1], hsv[2])
            cmyk = rgb_to_cmyk(color[i][0], color[i][1], color[i][2])
            color_cmyk = "%.2f %.2f %.2f %.2f" % (cmyk[0], cmyk[1], cmyk[2], cmyk[3])
            iecExpObject = IecExpObject(id=obj_id, userid=userid, imageid=imageid, url=obj_url, remark=remark)
            iecExpRegion = IecExpRegion(id=region_id, userid=userid, imageid=imageid, objectid=obj_id, url=region_url,
                                        remark=remark)
            iecExpColor = IecExpColor(id=color_id, userid=userid, imageid=imageid, objectid=obj_id, regionid=region_id,
                                      rgb=color_rgb, hsv=color_hsv, cmyk=color_cmyk)
            # 下一步该存入数据库了
            try:
                db.session.add(iecExpObject)
                db.session.add(iecExpRegion)
                db.session.add(iecExpColor)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)
                return -1  # 若抛出一个异常, 直接失败
    return imageid  # 若没有抛出异常, 则表明成功了


def saveProcess1(userid, imageid, imageremark, number, remark, concentration):
    concentration = concentration.split(" ")
    yolov3Api.cdCurrentContent()
    color = np.loadtxt(COLOR_DIR + "/%s.jpg_bgr.txt" % imageremark, dtype=np.int)
    # 随机生成的id
    obj_id = random.randint(0, 999999989)
    region_id = random.randint(0, 999999989)
    concentration_id = random.randint(0, 999999989)
    color_id = random.randint(0, 999999989)

    # 对一个imageid来说,只能存在一组数据,所以应该把之前的object region color concentration全部删掉
    db.session.query(IecExpObject).filter(IecExpObject.imageid == imageid).delete()
    db.session.query(IecExpRegion).filter(IecExpRegion.imageid == imageid).delete()
    db.session.query(IecExpConcentration).filter(IecExpConcentration.imageid == imageid).delete()
    db.session.query(IecExpColor).filter(IecExpColor.imageid == imageid).delete()
    # 保存逻辑:
    '''
    循环10次保存object:
        保存一个object, 获得obj id
        保存一个region, 获得reg id
        保存一个浓度值
        保存一个color值
    '''
    for i in range(0, int(number)):  # 总共需要处理这么多个object
        obj_name = "%s_%s.jpg" % (str(i + 1), imageremark)
        region_name = "%s.jpg_region_%s.jpg" % (imageremark, str(i + 1))
        rs = uploadFileByQiniu(os.path.join(UPLOAD_DIR_OBJECT, obj_name), obj_name)
        rs2 = uploadFileByQiniu(os.path.join(UPLOAD_DIR_REGION, region_name), region_name)
        if rs['code'] == -1 and rs2['code'] == -1:
            break
        elif rs['code'] == 1 and rs2['code'] == 1:
            # 上传成功
            obj_url = rs['url']
            region_url = rs2['url']
            obj_id = obj_id + 1
            region_id = region_id + 1
            concentration_id = concentration_id + 1
            color_id = color_id + 1
            color_rgb = "%s %s %s" % (color[i][0], color[i][1], color[i][2])
            hsv = colorsys.rgb_to_hsv(color[i][0], color[i][1], color[i][2])
            color_hsv = "%.2f %.2f %.2f" % (hsv[0], hsv[1], hsv[2])
            cmyk = rgb_to_cmyk(color[i][0], color[i][1], color[i][2])
            color_cmyk = "%.2f %.2f %.2f %.2f" % (cmyk[0], cmyk[1], cmyk[2], cmyk[3])
            iecExpObject = IecExpObject(id=obj_id, userid=userid, imageid=imageid, url=obj_url, remark=remark)
            iecExpRegion = IecExpRegion(id=region_id, userid=userid, imageid=imageid, objectid=obj_id, url=region_url,
                                        remark=remark)
            iecExpConcentration = IecExpConcentration(id=concentration_id, userid=userid, imageid=imageid,
                                                      objectid=obj_id, regionid=region_id,
                                                      concentration=concentration[i])
            iecExpColor = IecExpColor(id=color_id, userid=userid, imageid=imageid, objectid=obj_id, regionid=region_id,
                                      rgb=color_rgb, hsv=color_hsv, cmyk=color_cmyk)
            # 下一步该存入数据库了
            try:
                db.session.add(iecExpObject)
                db.session.add(iecExpRegion)
                db.session.add(iecExpConcentration)
                db.session.add(iecExpColor)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(e)
                return -1  # 若抛出一个异常, 直接失败
    return 1  # 若没有抛出异常, 则表明成功了


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
        return {'code': -1, 'message': "上传出错"}


'''
根据传入R G B取RGB的值

G/B与浓度C，R/B与浓度C，R/G与浓度C，S/V与浓度C，H/S与浓度C
(G+R)/B
'''


def getRorGorBbyX(axiosx, rgb, hsv):
    rgb = np.array(rgb, dtype=np.int)
    hsv = np.array(hsv, dtype=np.float)
    if axiosx == 'R':
        return rgb.T[2]
    elif axiosx == 'G':
        return rgb.T[1]
    elif axiosx == 'B':
        return rgb.T[0]
    elif axiosx == '(G+R)/B':
        return (rgb.T[1] + rgb.T[2]) / rgb.T[0]
    elif axiosx == 'G/B':
        return (rgb.T[1] / rgb.T[0])
    elif axiosx == 'R/B':
        return (rgb.T[2] / rgb.T[0])
    elif axiosx == 'R/G':
        return (rgb.T[2] / rgb.T[1])
    elif axiosx == 'H':
        return (hsv.T[0])
    elif axiosx == 'S':
        return (hsv.T[1])
    elif axiosx == 'V':
        return (hsv.T[2])
    elif axiosx == 'S/V':
        return (hsv.T[1] / hsv.T[2])
    elif axiosx == 'H/S':
        return (hsv.T[0] / hsv.T[1])
    else:
        return None


def getCbyAxiosy(axiosy, concentration):
    if axiosy == 'C':
        return concentration
    else:
        return None


def rgb_to_cmyk(r, g, b):
    cmyk_scale = 100
    if (r == 0) and (g == 0) and (b == 0):
        # black
        return 0, 0, 0, cmyk_scale

    # rgb [0,255] -> cmy [0,1]
    c = 1 - r / 255.
    m = 1 - g / 255.
    y = 1 - b / 255.

    # extract out k [0,1]
    min_cmy = min(c, m, y)
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    # rescale to the range [0,cmyk_scale]
    return c * cmyk_scale, m * cmyk_scale, y * cmyk_scale, k * cmyk_scale
