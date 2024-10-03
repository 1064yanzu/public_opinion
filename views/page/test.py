from flask import Flask , render_template,redirect,Blueprint ,request,session,url_for
from utils.query import query
from utils.errorResponse import errorResponse
from utils.info import *
from utils.get_tabledata import *
from flask import request, render_template, redirect, url_for
import time


ub = Blueprint('user',__name__,url_prefix='/user',template_folder='templates',static_folder='static')


@ub.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # 调整为直接获取查询结果
        user = query('SELECT * FROM user WHERE user_name = %s AND password = %s', [username, password], type='select')

        # 检查用户是否存在（这里假设如果查询结果不为空，则用户存在）
        if user:
            # users = session.get('username')
            users = username
            comments_data = get_info()
            unique_user_count, total_heat_value, unique_ip_count, row_count = fenxi()
            return render_template('index.html',
                                   user_name=users,
                                   row_count=row_count,
                                   unique_user_count=unique_user_count,
                                   total_heat_value=total_heat_value,
                                   unique_ip_count=unique_ip_count,
                                   comments_data=comments_data)
            # # 登录逻辑，例如设置session等
            # return render_template('index.html')  # 假设'success_page'是登录成功后的页面
        else:
            return errorResponse('用户名或密码错误')  # 假设errorResponse是一个返回错误信息的函数
    else:
        return render_template('login.html')




@ub.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template('register.html')
    else:
        cursor = query('SELECT * FROM user WHERE user_name = %s', [request.form['username']], type='select')
        if cursor:  # 现在直接检查查询结果是否存在
            return errorResponse('该用户已被注册')

        # 使用参数化查询防止SQL注入
        time_tuple = time.localtime(time.time())
        creat_time = time.strftime('%Y-%m-%d', time_tuple)  # 使用strftime格式化日期

        query('''
            INSERT INTO user(user_name, password, create_time) 
            VALUES (%s, %s, %s)
        ''', [request.form['username'], request.form['password'], creat_time])

        return redirect(url_for('user.login'))  # 假设'login'是登录视图的函数名

@ub.route('/forget', methods=['GET', 'POST'])
def forget():
    print('忘记密码')
    return render_template('forget.html')

@ub.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user.login'))

