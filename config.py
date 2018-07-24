# coding:utf-8
import os

redis_options = {

    'redis_host': '127.0.0.1',
    'redis_port': 6379,
    'redis_pass': ''
}

# Tornado app 配置

settings = {
    'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
    'static_path': os.path.join(os.path.dirname(__file__), 'statics'),
    'cookie_secret': '0Q1AKOKTQHqaa+N80XhYW7KCGskOUE2snCW06UIxXgI=',
    'xsrf_cookies': False,
    'login_url': '/login',
    'debug': True,

}

# 数据库配置参数
mysql_options = dict(
    host="127.0.0.1",
    database="ihome",
    user="root",
    password="mysql123"

)

# 日志
log_path = os.path.join(os.path.dirname(__file__), 'logs/log')
log_level = "debug"
# 密码加密密钥
passwd_hash_key = "nlgCjaTXQX2jpupQFQLoQo5N4OkEmkeHsHD9+BBx2WQ="
