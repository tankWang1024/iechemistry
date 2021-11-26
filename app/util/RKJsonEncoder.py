import json
from typing import Any
from .. import models
from flask import jsonify

def scattertodict(scatter: models.IecExpScatter) -> Any:
    return {'id':scatter.id, 'imageid':scatter.imageid, 'url':scatter.url, 'remark': scatter.remark, 'is_delete': scatter.is_delete\
        , 'create_time': scatter.create_time, 'modify_time':scatter.modify_time}

def lineartodict(linear: models.IecExpLinear) -> Any:
    return {'id':linear.id, 'imageid':linear.imageid, 'url':linear.url, 'remark': linear.remark, 'is_delete': linear.is_delete\
        , 'create_time': linear.create_time, 'modify_time':linear.modify_time}

def usertodict(user: models.IecUser) -> Any:
    return {'id':user.id,'name':user.name,'phone':user.phone,'avatar':user.avatar,'wxid':user.wxid,'is_valid':user.is_valid,\
        'create_time':user.create_time,'modify_time':user.modify_time}

def imagetodict(image: models.IecExpImage) -> Any:
    return {'id':image.id,'user_id': image.user_id, 'url': image.url, 'remark': image.remark, 'is_delete': image.is_delete, \
        'create_time':image.create_time,'modify_time':image.modify_time}

def formulatodict(formula: models.IecExpFormula) -> Any:
    return {'id':formula.id,'userid': formula.userid, 'imageid': formula.imageid, 'power': formula.power, 'a': formula.a, \
        'b': formula.b, 'c': formula.c, 'd': formula.d, 'r2': formula.r2,'create_time':formula.create_time,'modify_time':formula.modify_time,\
            'remark': formula.remark, 'x': formula.x, 'y': formula.x}

def predicttodict(predict: models.IecExpPredict) -> Any:
    return {'id':predict.id,'userid': predict.userid, 'imageid': predict.imageid ,\
        'concentration':predict.concentration, 'formulaid':predict.formulaid ,'create_time':predict.create_time,'modify_time':predict.modify_time}


def predictAndFormulaTodict(predict, formula) -> Any:
    return {'id':predict.id,'userid': predict.userid, 'imageid': predict.imageid ,\
        'concentration':predict.concentration, 'formulaid':predict.formulaid ,'create_time':predict.create_time,'modify_time':predict.modify_time\
            , 'x':formula.x, 'y': formula.y}
 