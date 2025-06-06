from flask import Flask, render_template, redirect, Blueprint, request, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
from datetime import datetime

# 先创建SQLAlchemy和Migrate实例，不立即绑定app
db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'  # 用于flash消息的密钥
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/weiboarticles'  # 数据库连接字符串

    # 初始化db和migrate到app
    db.init_app(app)
    migrate.init_app(app, db)

    return app


app = create_app()


# 定义User模型（保持不变）
class User(db.Model):
    # 创建蓝图（保持不变）
    ub = Blueprint('user', __name__, url_prefix='/user', template_folder='templates', static_folder='static')
    # 路由定义（保持不变）
    # ...

    # 注册蓝图（保持不变）
    app.register_blueprint(ub)

if __name__ == '__main__':
    app.run(debug=True)