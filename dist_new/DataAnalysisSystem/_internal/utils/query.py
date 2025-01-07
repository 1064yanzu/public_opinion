from pymysql import connect, cursors
#
# # 建立数据库连接
# conn = connect(host='localhost', port=3306, user='root', passwd='123456', db='weiboarticles')
#
#
# def query(sql, params, type='select'):
#     params = tuple(params)
#     cursor = conn.cursor(cursors.DictCursor)  # 使用DictCursor以字典形式返回结果
#     cursor.execute(sql, params)
#     conn.ping(reconnect=True)
#
#     if type == 'select':
#         # 直接返回游标对象，让调用者决定如何获取数据
#         return cursor
#     else:
#         # 对于非SELECT语句，提交事务
#         conn.commit()
#         cursor.close()  # 关闭游标
#         return None  # 或者根据需要返回某个特定值
#
# # 记得在使用完后关闭连接
# # conn.close()
import logging
from flask import current_app

# 建立数据库连接
conn = connect(host='localhost', port=3306, user='root', passwd='123456', db='weiboarticles')


def query(sql, params, type='select'):
    try:
        # 记录执行前的SQL和参数
        current_app.logger.debug(f"Executing SQL: {sql}, with params: {params}")

        cursor = conn.cursor(cursors.DictCursor)
        cursor.execute(sql, params)
        conn.ping(reconnect=True)

        if type == 'select':
            result = cursor.fetchone()  # 获取查询结果
            cursor.close()  # 关闭游标
            return result  # 直接返回查询结果
        else:
            conn.commit()
            cursor.close()
            current_app.logger.info("Database operation successful.")
            return None
    except Exception as e:
        # 记录执行时的异常
        current_app.logger.error(f"Database operation failed: {e}")
        raise