# coding:utf-8
import json
import logging
import constants
from handlers.BaseHandler import BaseHandler
from utils.commons import required_login
from utils.response_code import RET
from utils.session import Session


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


"""查询房源"""


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


class HouseInfoHandler(BaseHandler):
    """房屋信息"""

    @required_login
    def post(self):
        """保存"""
        # 获取参数
        user_id = self.session.data.get("user_id")
        title = self.json_args.get("title")
        price = self.json_args.get("price")
        area_id = self.json_args.get("area_id")
        address = self.json_args.get("address")
        room_count = self.json_args.get("room_count")
        acreage = self.json_args.get("acreage")
        unit = self.json_args.get("unit")
        capacity = self.json_args.get("capacity")
        beds = self.json_args.get("beds")
        deposit = self.json_args.get("deposit")
        min_days = self.json_args.get("min_days")
        max_days = self.json_args.get("max_days")
        facility = self.json_args.get("facility")  # 对一个房屋的设施，是列表类型
        # 校验

        if not all((title.price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days,
                    max_days)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))

        try:
            price = int(price) * 100
            deposit = int(deposit) * 100
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数错误"))

        # 数据
        try:
            sql = "insert into ih_house_info(hi_user_id,hi_title,hi_price,hi_area_id,hi_address,hi_room_count," \
                  "hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days) " \
                  "values(%(user_id)s,%(title)s,%(price)s,%(area_id)s,%(address)s,%(room_count)s,%(acreage)s," \
                  "%(house_unit)s,%(capacity)s,%(beds)s,%(deposit)s,%(min_days)s,%(max_days)s)"

            house_id = self.db.execute(sql, user_id=user_id, title=title, price=price, area_id=area_id, address=address,
                                       room_count=room_count, acreage=acreage, house_unit=unit, capacity=capacity,
                                       beds=beds, deposit=deposit, min_days=min_days, max_days=max_days)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="save data error"))

        try:
            sql = "insert into ih_home_facility(hf_house_id,hf_facility_id) values"
            sql_val = []
            vals = []
            for facility_id in facility:
                sql_val.append("(%s,%s)")
                vals.append(house_id)
                vals.append(facility_id)
            sql += ",".join(sql_val)
            vals = tuple(vals)  # 转换为元组
            self.db.execute(sql, *vals)
        except Exception as e:
            logging.error(e)
            try:
                self.db.execute("delete from ih_house_info where hi_house_id=%s", house_id)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DBERR, errmsg="delete fail"))
            else:
                return self.write(dict(errcode=RET.DBERR, errmsg="no data save"))
        # 返回
        self.write(dict(errcode=RET.OK, errmsg="OK", house_id=house_id))

    def get(self):
        """获取房屋信息"""
        session = Session(self)
        user_id = session.data.get("user_id", "-1")
        house_id = self.get_argument("house_id")
        # 效验参数
        if not house_id:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))
        # 先从 redis缓存中获取信息
        try:
            ret = self.redis().get("house_info_%s" % house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            # 此时从redis中获取到的是缓存的json格式数据
            resp = '{"errcode":0,"errmsg":"OK","data":%s,"user_id":%s}' % (ret, user_id)
            return self.write(resp)

        # 查询数据库
        # 查询房屋基本信息

        sql = "select hi_title, hi_price,hi_address,hi_room_count,hi_house_unit,hi_capacity,hi_beds," \
              "hi_deposit,hi_min_days,hi_max_days,up_name,up_avatar,hi_user_id" \
              "from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id where hi_house_id=%s"

        try:
            ret = self.db.get(sql, house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询错误"))
        if not ret:
            return self.write(dict(errcode=RET.NODATA, errmsg="查无此房"))

        data = {
            "hid": house_id,
            "user_id": ret["hi_user_id"],
            "title": ret["hi_title"],
            "price": ret["hi_price"],
            "address": ret["hi_address"],
            "room_count": ret["hi_room_count"],
            "acreage": ret["hi_acrege"],
            "unit": ret["hi_house_unit"],
            "capacity": ret["hi_capacity"],
            "beds": ret["hi_beds"],
            "deposit": ret["hi_deposit"],
            "min_days": ret["hi_min_days"],
            "max_days": ret["hi_max_days"],
            "user_name": ret["up_name"],
            "user_avatar": constants.QINIU_URL_PREFIX + ret["up_avatar"] if ret.get("up_avatar") else ""
        }
        # 查询房屋的图片xinx
        sql = "select hi_url from ih_home_image where hi_houser_id=%s"
