import json
from app.models import IecUser
from app import create_app, db
from  flask import request, jsonify
from flask_script import Manager  # 管理项目的 额外制定一些命令
from flask_migrate import Migrate, MigrateCommand  # 管理数据库需要的脚本 追踪数据库变化的脚本
from app.main.service import iecuserService
from flasgger import Swagger

app = create_app("develop")  # 工厂函数模式选择

'''
    定义一个拦截器用于验证是否登录
'''

@app.before_request
def before():
    url = request.path
    print(url)
    if url == '/login' or url == '/index' or url == '/clean':
        pass
    elif request.headers.get("token") == None:
        return jsonify(error="-1", message="request header中没有token信息,未登录")
    else:
        access_token = request.headers.get("token")
        # 验证token
        openid = iecuserService.verifyToken(access_token)
        if openid is None:
            return jsonify(message='没有查询到用户openid信息', code=-1)
        user = IecUser.query.filter_by(openid=openid).first()
        if user == None:
            return jsonify(message='没有查询到用户信息', code=-1)
        pass

if __name__ == '__main__':
    app.run(port=8080)
"""
# 启动命令 gunicorn -w 4 -b 0.0.0.0:5050 manage:app
Gunicorn 的常用运行参数说明：
-w WORKERS, –workers: worker 进程的数量，通常每个 CPU 内核运行 2-4 个 worker 进程。
-b BIND, –bind: 指定要绑定的服务器端口号或 socket
-c CONFIG, –config: 指定 config 文件
-k WORKERCLASS, –worker-class: worker 进程的类型，如 sync, eventlet, gevent, 默认为 sync
-n APP_NAME, –name: 指定 Gunicorn 进程在进程查看列表里的显示名（比如 ps 和 htop 命令查看）
"""