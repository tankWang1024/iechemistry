from datetime import datetime, timedelta
from flask import Flask, request, session
import jwt

from functools import wraps

'''
备用:
FJ_9Dr1Kmtbp^m^Z
lDcto(8g#S&9Kyvf
XfZ3TwEpVl89x1iD
1zcu^U*Wa#_oCHki
(yqrOw_uAx$m6Dbo
W6GjtC7w)nfgzbBm
'''
key = "Z03PFvKiJd8Qw&2I"

def generate_access_token(user_name: str = "", algorithm: str = 'HS256', exp: float = 2):
    """
    生成access_token
    :param user_name: 自定义部分
    :param algorithm:加密算法
    :param exp:过期时间
    :return:token
    """

    now = datetime.utcnow()
    exp_datetime = now + timedelta(hours=exp)
    access_payload = {
        'exp': exp_datetime,
        'flag': 0,  # 标识是否为一次性token，0是，1不是
        'iat': now,  # 开始时间
        'iss': 'qin',  # 签名
        'user_name': user_name  # 自定义部分
    }
    access_token = jwt.encode(access_payload, key, algorithm=algorithm)
    return access_token


def generate_refresh_token(user_name: str = "", algorithm: str = 'HS256', fresh: float = 30):
    """
    生成 refresh_token
    :param user_name: 自定义部分
    :param algorithm:加密算法
    :param fresh:过期时间
    :return:token
    """
    now = datetime.utcnow()
    # 刷新时间为30天
    exp_datetime = now + timedelta(days=fresh)
    refresh_payload = {
        'exp': exp_datetime,
        'flag': 1,  # 标识是否为一次性token，0是，1不是
        'iat': now,  # 开始时间
        'iss': 'qin',  # 签名，
        'user_name': user_name  # 自定义部分
    }

    refresh_token = jwt.encode(refresh_payload, key, algorithm=algorithm)
    return refresh_token

def decode_auth_token(token: str):
    """
    解密token
    :param token:token字符串
    :return:
    """
    try:
        # 取消过期时间验证
        # payload = jwt.decode(token, key, options={'verify_exp': False})
        payload = jwt.decode(token, key=key, )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.InvalidSignatureError):
        return ""
    else:
        return payload

def identify(auth_header: str):
    """
    用户鉴权
    :return: 
    """
    if auth_header:
        payload = decode_auth_token(auth_header)
        if not payload:
            return False
        if "user_name" in payload and "flag" in payload:
            if payload["flag"] == 1:
                # 用来获取新access_token的refresh_token无法获取数据
                return False
            elif payload["flag"] == 0:
                return payload["user_name"]
            else:
                # 其他状态暂不允许
                return False
        else:
            return False
    else:
        return False

def login_required(f):
    """
    登陆保护，验证用户是否登陆
    :param f:
    :return:
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", default=None)
        if not token:
            return "请登陆"
        user_name = identify(token)
        if not user_name:
             return "请登陆"
        # 获取到用户并写入到session中,方便后续使用
        session["user_name"] = user_name  
        return f(*args, **kwargs)
    return wrapper