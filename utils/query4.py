import pymysql

def query(sql, params, type='no select'):
    # 使用上下文管理器确保数据库连接和游标被正确关闭
    with pymysql.connect(host='localhost', port=3306, user='root', passwd='123456', db='weiboarticles') as conn:
        with conn.cursor() as cursor:
            # 使用参数化查询
            cursor.execute(sql, params)
            conn.ping(reconnect=True)
            if type == 'no select':
                data_list = cursor.fetchall()
                conn.commit()
                return data_list
            else:
                conn.commit()

# 使用query函数
result = query('SELECT * FROM user WHERE user_name = %s', ('username',))
