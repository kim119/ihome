# coding:utf-8
import json
import logging

import constants
from handlers.BaseHandler import BaseHandler
from utils.response_code import RET


class AreaInfoHAndler(BaseHandler):
    """提供城区信息"""

    def get(self):
        # 先到redis中查询数据,如果获取到了数据,直接返回给用户

        try:
            ret = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            logging.info("hit redis :area_info")
            resp = '{"errcode":"0","errmsg":"OK","data":%s}' % ret
            return self.write(resp)

        # 查询Mysql数据库,获取城区信息
        sql = "select ai_area_id,ai_name from ih_area_info;"

        try:
            ret = self.db.query(sql)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询数据库出错"))
        if not ret:
            return self.write(dict(errcode=RET.NODATA, errmsg="没有数据"))
        # 保存转换好的区域信息

        data = []
        for row in ret:
            d = {"area_id": row.get("ai_area_id", ""), "name": row.get("ai_name", "")}
            data.append(d)

        # 在返回给用户数据之前,先向redis中保存一份数据的副本
        json_data = json.dumps(data)

        try:
            self.redis().setex("area_info", constants.REDIS_AREA_INFO_EXPIRES_SECONDES, json_data)
        except Exception as e:
            logging.error(e)

        self.write(dict(errcode=RET.OK, errmsg="OK", data=data))
