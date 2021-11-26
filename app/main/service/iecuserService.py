from ... import models
from ...models import IecUser, db
from ...util import jwtutil
from app import redis_store


def getUserByOpenid(openid):
    print(openid)
    user = IecUser.query.filter_by(openid= openid).first()
    return user

def saveUser(user):
    try:
        db.session.add(user)
        db.session.commit()
        user = IecUser.query.filter_by(openid= user.openid).first()
        return user
    except Exception as e:
        db.session.rollback()
        print(e)
        return None

'''
    用户登录成功后或者token,后端存到redis，然后返回前端
'''
def getTokenAndSaveToRedis(user):
    minute = 10
    if user is None:
        return None
    access_token = jwtutil.generate_access_token(user_name=user.openid)
    # 登录成功存redis   name time value
    redis_store.setex(access_token, minute * 1000, user.openid)
    return access_token


def verifyToken(access_token):
    openid = redis_store.get(access_token)
    return openid

def getOpenidInRedis(access_token):
    openid = redis_store.get(access_token)
    return openid