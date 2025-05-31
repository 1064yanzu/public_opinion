from amqp import NotFound
from flask import Flask,render_template,jsonify,request
from flask import send_from_directory
from werkzeug.exceptions import Forbidden
# 在这里导入和注册蓝图
from views.user.user import ub
from views.page import page
from views.user import user
from model.nlp import *
from pyecharts import options as opts
from pyecharts.charts import Bar, Pie
from spiders.articles_spider import *
from views.page.page import pb
import multiprocessing
import os
from datetime import timedelta

app = Flask(__name__)

# Session配置
app.config['SECRET_KEY'] = 'your-secret-key-123'  # 使用固定的密钥
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # session有效期7天
app.config['SESSION_COOKIE_NAME'] = 'session'  # session cookie名称
app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止XSS攻击
app.config['SESSION_COOKIE_SECURE'] = False  # 如果使用HTTPS，设置为True
app.config['SESSION_REFRESH_EACH_REQUEST'] = True  # 每次请求都刷新session
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统存储session

app.register_blueprint(page.pb)
app.register_blueprint(user.ub)

@app.route('/')
def hello_world():  # put application's code here
    return render_template('welcome.html')


@app.errorhandler(Exception)
def handle_exception(e):
    # 获取错误信息
    error_message = str(e)

    # 可以根据不同的异常类型返回不同的状态码
    if isinstance(e, NotFound):
        status_code = 404
    elif isinstance(e, Forbidden):
        status_code = 403
    else:
        status_code = 500

    # 渲染错误页面
    return render_template('error.html', error_message=error_message), status_code


@app.route('/get_chart_data')
def get_chart_data():
    infos2, share_num, comment_num, like_num = get_info2(ready_path)
    pie = (
        Pie()
        .add("", [("转发数", share_num), ("点赞数", like_num), ("评论数", comment_num)])
        .set_global_opts(title_opts=opts.TitleOpts(title="ECharts 饼图示例"))
    )
    # 将图表转换为 JSON 字符串发送给前端
    return jsonify(pie.dump_options_with_quotes())


@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    max_page = int(request.form.get('max_page', 10))  # 默认为10页
    # 在这里添加你的爬虫逻辑
    results = get_weibo_list(keyword, max_page)
    return jsonify(results)





@app.teardown_appcontext
def shutdown_session(exception=None):
    for child in multiprocessing.active_children():
        child.terminate()
        child.join()

if __name__ == '__main__':
    app.run(threaded=True)
