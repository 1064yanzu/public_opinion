# 导入必要的库
import pandas as pd
import pymysql

def get_info() :
    # 连接到MySQL数据库
    conn = pymysql.connect(
      host="localhost",
      user="root",
      password="123456",
      database='weiboarticles',
      charset='utf8mb4',
    )
    try:
        # 使用Pandas执行SQL查询
        sql_query = "SELECT 用户昵称,微博正文,发布工具,发布时间,ip,sentiment_result FROM comments"
        df = pd.read_sql(sql_query, conn)
        # 将DataFrame转换为字典列表
        comments_data = df.to_dict(orient='records')
        # 检查DataFrame是否为空以及列名是否存在
        if not df.empty:
            try:
                share_num = df['转发数'].iloc[0]
                comment_num = df['评论数'].iloc[0]
                like_num = df['点赞数'].iloc[0]
            except KeyError:
                print("列名错误或数据缺失，请检查SQL查询及DataFrame列名")
                share_num, comment_num, like_num = 0, 0, 0  # 或者根据需要处理错误情况
        else:
            share_num, comment_num, like_num = 0, 0, 0  # 数据为空时的处理
    finally:
        # 确保数据库连接关闭
        return comments_data
        conn.close()

if __name__ == '__main__':
  get_info()