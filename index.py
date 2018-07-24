# coding:utf-8
import redis
import tornado.web
import tornado.ioloop
import tornado.httpserver
import torndb
from tornado import options
from tornado.options import define,options

import config
import urls

define("port", default=8080, type=int, help="run server on the given port")


class Application(tornado.web.RequestHandler):
    """初始化配置"""

    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.db = torndb.Connection(**config.mysql_options)
        self.redis = redis.StrictRedis(**config.redis_options)


def main():
    options.log_file_prefix = config.log_path
    options.logging = config.log_level
    tornado.options.parse_command_line()
    app = Application(
        urls,
        **config.settings

    )

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(tornado.options.options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
