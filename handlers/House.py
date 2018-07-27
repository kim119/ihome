# coding:utf-8
import json
import logging
import constants
from handlers.BaseHandler import BaseHandler
from utils.commons import required_login
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


""""""


class MyHousesHandler(BaseHandler):

    @required_login
    def get(self):
        user_id = self.session.data["user_id"]
        try:
            sql = "select a.hi_house_id, a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url" \
                  "from ih_house_info a inner join ih_area_info b on a.hi_area_id=b.ao_area_id where a.hi_user_id=%s;"
            ret = self.db.query(sql, user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errcode": RET.DBERR, "errmsg": "get data erro"})
        houses = []
        if ret:
            for l in ret:
                house = {
                    "house_id": l["hi_house_id"],
                    "title": l["hi_title"],
                    "price": l["hi_price"],
                    "ctime": l["hi_ctime"].strftime("%Y-%m-%d"),
                    "area_name": l["ai_name"],
                    "img_url": constants.QINIU_URL_PREFIX + l["hi_index_image_url"] if l["hi_index_image_url"] else ""

                }
                houses.append(house)
        self.write({"errcode": RET.OK, "errmsg": "OK", "houses": houses})

    pass
