import redis
from flask import Flask, app, config
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from config import config_map, redis_store

import pymysql

# 实例化redis

db = SQLAlchemy()

def create_app(dev_name):
    app = Flask(__name__)
    config_class = config_map.get(dev_name)
    app.config.from_object(config_class) # 从类中读取需要的信息
    print(app.config)
    db.init_app(app)  # 实例化的数据库 配置信息

    # 利用flask-session，将session数据保存到redis中
    Session(app)

    # 注册蓝图
    from app import main  # 导入包

    app.register_blueprint(main.main)  # 绑定包里面的蓝图对象

    return app