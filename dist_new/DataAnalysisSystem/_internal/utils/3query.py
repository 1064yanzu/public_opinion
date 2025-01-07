import pymysql

def query(sql, params, type='select'):
    # 使用上下文管理器确保数据库连接和游标被正确关闭
    with pymysql.connect(host='localhost', port=3306, user='root', passwd='123456', db='weiboarticles') as conn:
        with conn.cursor() as cursor:
            # 使用参数化查询
            cursor.execute(sql, params)
            conn.ping(reconnect=True)
            if type == 'select':
                # 对于SELECT查询，获取并返回所有数据
                data_list = cursor.fetchall()
                return data_list
            else:
                # 对于非SELECT语句，提交事务但无需返回数据
                conn.commit()

# 使用修正后的query函数执行SELECT查询
result = query('SELECT * FROM user WHERE user_name = %s', ('username',), type='select')