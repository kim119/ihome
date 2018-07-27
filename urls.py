# coding:utf-8
from handlers import Passport, VerifyCode, House

urls = [
    (r"/api/smscode", VerifyCode.SMSCodeHandler),
    (r"/api/register$", Passport.RegisterHandler),
    (r"/api/login$", Passport.CheckLoginHandler),
    (r"/api/logout$", Passport.LogoutHandler),
    (r"/api/house/area$", House.AreaInfoHAndler),

]
