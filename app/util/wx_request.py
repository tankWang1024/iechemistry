import urllib.parse, urllib.request, urllib.error
import json

# 微信小程序相关配置
APPID = "wx1e55a5666300f7e0"
SECRET = "bc574a87b92727ebd61c005c3fb81b32"
WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session?appid=APPID&secret=SECRET&js_code=JSCODE&grant_type=authorization_code"


def code2session(code):
    headers = {"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 11_0_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"}
    headers['content-type'] = "text/html;charset=UTF8"
    method="GET"
    url = WECHAT_CODE2SESSION_URL
    url = url.replace("APPID",APPID)
    url = url.replace("JSCODE", code)
    url = url.replace("SECRET", SECRET)
    request = urllib.request.Request(url, headers= headers, method= method)
    response = urllib.request.urlopen(request) 
    # json默认返回gbk编码, 需要解译一下
    # 网页页面是gbk, 但是有很多字符gbk无法编码, 采用更高级别的gb18030
    # openIdResponse = response.read().decode('gbk')
    try:
        openIdResponse = response.read().decode('gb18030')
        openIdResponse =  json.loads(openIdResponse)
        # {"session_key":"G3089N7Yb9NXenibVdcqRw==","openid":"oVibi5NLksGX7bZUr8y0oyIUVMLI"}
        # {'errcode': 40163, 'errmsg': 'code been used, hints: [ req_id: EhfcR6qNe-7wgxqa ]'}
        # {"errcode":40013,"errmsg":"invalid appid rid: 609a2ca4-5e9da895-62207837"}
        if('openid' in openIdResponse):
            return openIdResponse['openid']
        else:
            return openIdResponse['errcode']
    except UnicodeDecodeError as ue:
        print(ue)
        print('\n')
        return json.loads({"code":-1, "message":"wrong:%s" % ue})

# print(code2session("091iIL0000b2GL14bY100yLB0z2iIL0E"))