# coding:utf-8

SESSION_EXPIRES_SECONDS = 86400  # session数据有效期,单位秒
PIC_CODE_EXPIRES_SECONDS = 180  # 图片验证码的有效期，单位秒
SMS_CODE_EXPIRES_SECONDS = 300  # 图片验证码的有效期，单位秒
REDIS_AREA_INFO_EXPIRES_SECONDES = 86400 # redis缓存城区信息的有效期
REDIS_HOUSE_INFO_EXPIRES_SECONDES = 86400 # redis缓存房屋信息的有效期
QINIU_URL_PREFIX = "http://o91qujnqh.bkt.clouddn.com/" # 七牛存储空间的域名