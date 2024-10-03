# 导入必要的库
import pandas as pd
import pymysql

def fenxi_mysqql() :
    # 连接到MySQL数据库
    conn = pymysql.connect(
      host="localhost",
      user="root",
      password="123456",
      database='weiboarticles',
      charset='utf8mb4',
    )

    # 使用Pandas执行SQL查询
    sql_query = "SELECT * FROM comments"
    df = pd.read_sql(sql_query, conn)
    if df.empty:  # 如果DataFrame为空
        # 直接返回默认值0
        return [],[],[],[]
    else:
        row_count = len(df) - 1
        # 计算user_id的唯一数量
        unique_user_count = df['user_id'].nunique()

        # 假设DataFrame中有'forward_count', 'comment_count', 'like_count'这些列
        # 计算每行的热力值并求和
        df['heat_value'] = df['转发数'] + df['评论数'] + df['点赞数']
        total_heat_value = df['heat_value'].sum()

        # 计算ip_address的唯一数量
        unique_ip_count = df['ip'].nunique()

        # 打印结果
        print(f"Unique User Count: {unique_user_count}")
        print(f"Total Heat Value: {total_heat_value}")
        print(f"Unique IP Count: {unique_ip_count}")

        return unique_user_count, total_heat_value, unique_ip_count,row_count
        # 关闭数据库连接
        conn.close()

def fenxi():
    df = pd.read_csv('E:\\python\\flaskProject\\model\\database.csv')
    if df.empty:  # 如果DataFrame为空
        # 直接返回默认值0
        return [], [], [], []
    else:
        row_count = len(df) - 1
        # 计算user_id的唯一数量
        unique_user_count = df['微博bid'].nunique()
        # 计算每行的热力值并求和
        df['heat_value'] = df['转发数'] + df['评论数'] + df['点赞数']
        total_heat_value = df['heat_value'].sum()

        # 计算ip_address的唯一数量
        unique_ip_count = df['省份'].nunique()

        # 打印结果
        print(f"Unique User Count: {unique_user_count}")
        print(f"Total Heat Value: {total_heat_value}")
        print(f"Unique IP Count: {unique_ip_count}")

        return unique_user_count, total_heat_value, unique_ip_count, row_count

if __name__ == '__main__':
  fenxi()