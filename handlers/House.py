# coding:utf-8
import json
import logging
import math

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
        # 查询房屋的图片信息
        sql = "select hi_url from ih_home_image where hi_houser_id=%s"

        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None

        # 如果查询到设施
        facilities = []
        if ret:
            for facility in ret:
                facilities.append(facility["hf_facility_id"])
        data["facilities"] = facilities

        # 查询评论信息
        sql = "select oi_comment,up_name,oi_utime,up_mobile from ih_order_info inner  join ih_user_profile" \
              "on oi_user_id=up_user_id where oi_house_id=%s and oi_status=4 and oi_comment is not null "

        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        comments = []
        if ret:
            for comment in ret:
                comments.append(
                    dict(user_name=comment["up_name"] if comment["up_name"] != comment["up_mobile"] else "匿名用户",
                         content=comment["io_comment"],
                         ctime=comment["oi_utime"].strftime("%Y-%m-%d %H:%M:%S")
                         ))
        data["comments"] = comments

        # 存入到redis中
        json_data = json.dumps(data)

        try:
            self.redis().setex("house_info_%s" % house_id, constants.REDIS_HOUSE_INFO_EXPIRES_SECONDES, json_data)
        except Exception as e:
            logging.error(e)
        resp = '{"errcode": "0", "errmsg":"OK","data":%s,"user_id":%s}' % (json_data, user_id)
        self.write(resp)


class HouseListHandler(BaseHandler):
    """房源列表页面"""

    def get(self):
        # 获取参数
        start_date = self.get_argument("sd", "")
        end_date = self.get_argument("ed", "")
        area_id = self.get_argument("aid", "")
        sort_key = self.get_argument("sk", "new")
        page = self.get_argument("p", "")

        # 检查参数
        sql = "select distinct hi_title,hi_house_id,hi_price,hi_room_count,hi_address,hi_order_count,up_avatar," \
              "hi_index_image_url,hi_ctime" \
              " from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id left join ih_order_info" \
              " on hi_house_id=oi_house_id"
        sql_total_count = "select count(distinct hi_house_id) count from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id " \
                          "left join ih_order_info on hi_house_id=oi_house_id"
        sql_where = []
        sql_params = {}

        if start_date and end_date:
            sql_part = "((oi_begin_date>%(end_date)s or oi_end_date<%(start_date)s) " \
                       "or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
            sql_params["end_date"] = end_date
        elif start_date:
            sql_part = "(oi_end_date<%(start_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
        elif end_date:
            sql_part = "(oi_begin_date>%(end_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["end_date"] = end_date
        if area_id:
            sql_part = "hi_area_id=%(area_id)s"
            sql_where.append(sql_part)
            sql_params["area_id"] = area_id
        if sql_where:
            sql += " where "
            sql += " and ".join(sql_where)

        try:
            ret = self.db.get(sql_total_count, **sql_params)
        except Exception as e:
            logging.error(e)
            total_page = -1

        else:
            total_page = int(math.ceil(ret["count"] / float(constants.HOUSE_LIST_PAGE_CAPACITY)))
            page = int(page)
            if page > total_page:
                return self.write(dict(errcode=RET.OK, errmsg="OK", data=[], total_page=total_page))
        # 排序
        if "new" == sort_key:  # 按最新上传时间排序
            sql += " order by hi_ctime desc"
        elif "booking" == sort_key:  # 最受欢迎
            sql += " order by hi_order_count desc"
        elif "price-inc" == sort_key:  # 价格由低到高
            sql += " order by hi_price asc"
        elif "price-des" == sort_key:  # 价格由高到低
            sql += " order by hi_price desc"

        # 分页
        # limit 10 返回前10条
        # limit 20,3 从20条开始，返回3条数据
        if 1 == page:
            sql += " limit %s" % constants.HOUSE_LIST_PAGE_CAPACITY
        else:
            sql += " limit %s,%s" % (
            (page - 1) * constants.HOUSE_LIST_PAGE_CAPACITY, constants.HOUSE_LIST_PAGE_CAPACITY)

        logging.debug(sql)
        try:
            ret = self.db.query(sql, **sql_params)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询出错"))
        data = []
        if ret:
            for l in ret:
                house = dict(
                    house_id=l["hi_house_id"],
                    title=l["hi_title"],
                    price=l["hi_price"],
                    room_count=l["hi_room_count"],
                    address=l["hi_address"],
                    order_count=l["hi_order_count"],
                    avatar=constants.QINIU_URL_PREFIX + l["up_avatar"] if l.get("up_avatar") else "",
                    image_url=constants.QINIU_URL_PREFIX + l["hi_index_image_url"] if l.get(
                        "hi_index_image_url") else ""
                )
                data.append(house)
        self.write(dict(errcode=RET.OK, errmsg="OK", data=data, total_page=total_page))


class HouseListRedisHandler(BaseHandler):
    """使用了缓存的房源列表页面"""

    def get(self):
        # 获取参数
        start_date = self.get_argument("sd", "")
        end_date = self.get_argument("ed", "")
        area_id = self.get_argument("aid", "")
        sort_key = self.get_argument("sk", "new")
        page = self.get_argument("p", "1")

        # 先从redis中获取数据
        try:
            redis_key = "houses_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
            ret = self.redis.hget(redis_key, page)
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            logging.info("hit redis")
            return self.write(ret)

        # 数据查询
        sql = "select distinct hi_title,hi_house_id,hi_price,hi_room_count,hi_address,hi_order_count,up_avatar,hi_index_image_url,hi_ctime" \
              " from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id left join ih_order_info" \
              " on hi_house_id=oi_house_id"

        sql_total_count = "select count(distinct hi_house_id) count from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id " \
                          "left join ih_order_info on hi_house_id=oi_house_id"
        sql_where = []  # 用来保存sql语句的where条件
        sql_params = {}  # 用来保存sql查询所需的动态数据

        if start_date and end_date:
            sql_part = "((oi_begin_date>%(end_date)s or oi_end_date<%(start_date)s) " \
                       "or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
            sql_params["end_date"] = end_date
        elif start_date:
            sql_part = "(oi_end_date<%(start_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
        elif end_date:
            sql_part = "(oi_begin_date>%(end_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["end_date"] = end_date

        if area_id:
            sql_part = "hi_area_id=%(area_id)s"
            sql_where.append(sql_part)
            sql_params["area_id"] = area_id

        if sql_where:
            sql += " where "
            sql += " and ".join(sql_where)
