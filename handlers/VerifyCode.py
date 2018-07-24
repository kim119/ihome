# coding:utf-8

import logging
import re

from BaseHandler import BaseHandler
from constants import PIC_CODE_EXPIRES_SECONDS, SMS_CODE_EXPIRES_SECONDS
from utils.captcha import captcha
from utils.response_code import RET


class PicCodeHandler(BaseHandler):
    """图片验证码"""

    def get(self):
        """获取图片验证码"""
        pre_code_id = self.get_argument("pre", "")
        cur_code_id = self.get_argument("cur")
        # 生成图片验证码
        name, text, pic = captcha.generate_captcha()
        try:
            if pre_code_id:
                self.redis.delete("pic_code_%s" % pre_code_id)
            # self.redis.setex(name, expries, value)
            self.redis.setex("pic_code_%s" % cur_code_id, PIC_CODE_EXPIRES_SECONDS, text)
        except Exception as e:
            logging.error(e)
            self.write("")
        else:
            self.set_header("Content-Type", "image/jpg")
            self.write(pic)


class SMSCodeHandler(BaseHandler):
    """短信验证码"""

    def post(self):
        # 获取参数对象
        mobile = self.json_args.get("mobile")
        piccode = self.json_args.get("piccode")
        piccode_id = self.json_args.get("piccode_id")

        # 参数效验

        if not all((mobile, piccode, piccode_id)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数失败"))

        if not re.match(r"^1\d{10}$", mobile):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="手机号码格式错误"))

        # 获取图片验证码真实性

        try:
            real_piccode = self.redis().get("pic_code_%s" % piccode_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DATAERR, errmsg="查询验证码错误"))

        if not real_piccode:
            return self.write(dict(errcode=RET.NODATA, errmsg="验证码过期"))

        # 删除图片验证码

        try:
            self.redis().delete("pic_code_%s" % piccode_id)
        except Exception as e:
            logging.error(e)

        if real_piccode.lower() != piccode.lower():
            return self.write(dict(errcode=RET.DATAERR, errmsg="验证码错误"))
