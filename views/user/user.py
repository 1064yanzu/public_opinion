import csv
import os
import bcrypt
from flask import render_template, redirect, Blueprint, request, session, url_for
from utils.errorResponse import errorResponse
from utils.info import *
from utils.get_tabledata import *
import time

ub = Blueprint('user', __name__, url_prefix='/user', template_folder='templates', static_folder='static')

CSV_FILE = 'users.csv'


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)


def check_user(username, password=None):
    if not os.path.exists(CSV_FILE):
        return False
    with open(CSV_FILE, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == username:
                if password is None:
                    return True  # 用户存在
                return check_password(row[1].encode('utf-8'), password)
    return False

@ub.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if check_user(username, password):
            session['username'] = username
            # 登录成功后重定向到主页
            return redirect(url_for('page.home'))
        else:
            # 如果用户名或密码错误，返回错误响应
            return errorResponse('用户名或密码错误')
    else:
        # GET 请求时渲染登录页面
        return render_template('login.html')


@ub.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template('register.html')
    else:
        username = request.form['username']
        password = request.form['password']

        if check_user(username):
            return errorResponse('该用户已被注册')

        hashed_password = hash_password(password)
        creat_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))

        with open(CSV_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, hashed_password.decode('utf-8'), creat_time])

        return redirect(url_for('user.login'))


@ub.route('/forget', methods=['GET', 'POST'])
def forget():
    if request.method == "GET":
        return render_template('forget.html')
    else:
        # 这里添加处理忘记密码的逻辑
        # 例如，发送重置密码的邮件等
        return errorResponse('密码重置功能尚未实现')


@ub.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('user.login'))