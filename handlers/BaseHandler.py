# coding:utf-8
import json

from tornado.web import RequestHandler, StaticFileHandler

from utils.session import Session

"""定义基类"""


class BaseHandler(RequestHandler):

    def data_received(self, chunk):
        pass

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.json_args = {}

    @property
    def db(self):
        """作为RequestHandler对象的db属性"""
        return self.application.db

    def redis(self):
        """作为RequestHandler对象的redis属性"""
        return self.application.redis

    def prepare(self):
        """预解析json数据"""
        if self.request.headers.get("Content-Type", "").startswith("application/json"):
            self.json_args = json.loads(self.request.body)
        else:
            self.json_args = {}

    def set_default_headers(self):
        """设置默认json格式"""
        self.set_header("Content-Type", "application/json; charset=UTF-8")

    def get_current_user(self):
        """判断用户是否登陆"""
        self.session = Session(self)
        return self.session.data


class StaticFileBaseHandler(StaticFileHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        super(StaticFileBaseHandler, self).__init__(*args, **kwargs)
        self.xsrf_token
