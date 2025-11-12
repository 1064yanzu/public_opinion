from celery import Celery
from model.ciyuntu import *
# 配置Celery
app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def generate_wordcloud_task():
    get_wordcloud()  # 执行你的词云生成函数