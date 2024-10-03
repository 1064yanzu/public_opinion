from sqlalchemy import create_engine
import pandas as pd
from articles_spider import get_weibo_list

engine = create_engine('mysql+pymysql://root:123456@127.0.0.1:3306/weiboarticles?charset=utf8mb4')


def save_to_sql():
    # article_pd = pd.read_csv('王冰冰.csv')
    comments_pd = pd.read_csv('王冰冰.csv')
    print(comments_pd.head())
    # article_pd.to_sql('weiboarticles', con=engine, if_exists='replace', index=False)
    comments_pd.to_sql('comments', con=engine, if_exists='replace', index=False)

if __name__ == '__main__':
    save_to_sql()