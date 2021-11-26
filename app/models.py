from . import db
from datetime import datetime



class IecExpColor(db.Model):
    '''
        保存region区域得平均rgb值以及其它颜色通道的平均值
    '''
    __tablename__ = "iec_expcolor"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    imageid = db.Column(db.Integer, nullable=False)
    objectid = db.Column(db.Integer, nullable=False)
    regionid = db.Column(db.Integer, nullable=False)
    # [255.0, 255.0, 255.0]
    rgb  = db.Column(db.String(255), nullable=False)
    hsv  = db.Column(db.String(255), nullable=False)
    cmyk  = db.Column(db.String(255), nullable=False)
    is_delete  = db.Column(db.Boolean, nullable=False, default=False)
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)

class IecExpConcentration(db.Model):
    '''
        保存某张图片image对应的浓度数组[1,2,3,4,5,6,7]
        regionid objectid 这些可以重复
    '''
    __tablename__ = "iec_expconcentration"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    imageid = db.Column(db.Integer, nullable=False)
    objectid = db.Column(db.Integer, nullable=False)
    regionid = db.Column(db.Integer, nullable=False)
    # [1,2,3,4,5,6,7,8,9,10]
    concentration  = db.Column(db.String(255), nullable=False)
    is_delete  = db.Column(db.Boolean, nullable=False, default=False)
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)

class IecExpImage(db.Model):
    '''
        图像信息
    '''
    __tablename__ = "iec_expimage"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    url  = db.Column(db.String(255), nullable=False)
    # 备注:这是第11组数据
    remark  = db.Column(db.String(255))
    is_delete  = db.Column(db.Boolean, nullable=False, default=False)
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)


class IecExpLinear(db.Model):
    '''
        保存线性回归的图像对应某一张图像，某一组颜色和浓度
    '''
    __tablename__ = "iec_explinear"
    id = db.Column(db.Integer, primary_key=True)
    imageid = db.Column(db.Integer, nullable=False)
    colorid = db.Column(db.Integer, nullable=True)
    concentrationid = db.Column(db.Integer, nullable=True)
    url  = db.Column(db.String(255), nullable=False)
    remark  = db.Column(db.String(255))
    is_delete  = db.Column(db.Boolean, nullable=False, default=False)
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)

class IecExpObject(db.Model):
    '''
        保存object图像信息
    '''
    __tablename__ = "iec_expobject"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    imageid = db.Column(db.Integer, nullable=False)
    url  = db.Column(db.String(255), nullable=False)
    remark  = db.Column(db.String(255))
    is_delete  = db.Column(db.Boolean, nullable=False, default=False)
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)

class IecExpRegion(db.Model):
    '''
        保存region图像信息
    '''
    __tablename__ = "iec_expregion"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable=False)
    imageid = db.Column(db.Integer, nullable=False)
    objectid = db.Column(db.Integer, nullable=False)
    url  = db.Column(db.String(255), nullable=False)
    remark  = db.Column(db.String(255))
    is_delete  = db.Column(db.Boolean, nullable=False, default=False)
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)

class IecExpScatter(db.Model):
    '''
        保存scatter图像
        imageid  colorid concentrationid 解释同linear数据表
    '''
    __tablename__ = "iec_expscatter"
    id = db.Column(db.Integer, primary_key=True)
    imageid = db.Column(db.Integer, nullable=False)
    colorid = db.Column(db.Integer, nullable=True)
    concentrationid = db.Column(db.Integer, nullable=True)
    url  = db.Column(db.String(255), nullable=False)
    remark  = db.Column(db.String(255))
    is_delete  = db.Column(db.Boolean, nullable=False, default=False)
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)

class IecExpFormula(db.Model):
    __tablename__ = "iec_expformula"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    imageid = db.Column(db.Integer, nullable=False)
    power = db.Column(db.Integer)
    a = db.Column(db.Float, nullable=True)
    b = db.Column(db.Float, nullable=True)
    c = db.Column(db.Float, nullable=True)
    d = db.Column(db.Float, nullable=True)
    r2 = db.Column(db.Float, nullable=True)
    y = db.Column(db.String(255))
    x = db.Column(db.String(255))
    remark  = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)


class IecExpPredict(db.Model):
    __tablename__ = "iec_exppredict"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    imageid = db.Column(db.Integer, nullable=False)
    formulaid = db.Column(db.Integer)
    concentration = db.Column(db.String(255))
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)

class IecUser(db.Model):
    __tablename__ = "iec_user"
    id = db.Column(db.Integer, primary_key=True)
    openid = db.Column(db.String(255), nullable = False)
    name = db.Column(db.String(24))
    phone = db.Column(db.String(24))
    avatar = db.Column(db.String(255))
    wxid = db.Column(db.String(32))
    is_valid  = db.Column(db.Boolean, nullable=False, default=True)
    create_time = db.Column(db.DateTime, index=True, default=datetime.now)
    modify_time = db.Column(db.DateTime, default=datetime.now)

