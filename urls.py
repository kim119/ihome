# coding:utf-8
from handlers import Passport

urls = [
    (r"/api/register", Passport.RegisterHandler),

]
