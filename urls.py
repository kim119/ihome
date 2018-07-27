# coding:utf-8
from handlers import Passport, VerifyCode

urls = [
    (r"/api/smscode", VerifyCode.SMSCodeHandler),
    (r"/api/register$",Passport.RegisterHandler),
    (r"/api/login$",Passport.CheckLoginHandler),
    (r"/api/logout$",Passport.LogoutHandler),

]
