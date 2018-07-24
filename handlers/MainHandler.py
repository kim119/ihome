import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):

    def data_received(self, chunk):
        pass

    def get(self):
        # type: () -> object
        self.render("index.html")

    def post(self, *args, **kwargs):
        file_metas = self.request.files["fff"]
        # print(file_metas)
        for meta in file_metas:
            file_name = meta['filename']
            import os
            file_name = os.path.join("images", file_name)
            with open(file_name, 'wb') as up:
                up.write(meta['body'])


