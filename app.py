from flask import Flask
from views.user.user import ub
from views.page.page import pb
from utils.init_system import init_system
import os

def create_app():
    """创建Flask应用"""
    try:
        # 初始化系统
        init_system()
        
        # 创建Flask应用
        app = Flask(__name__)
        app.config['SECRET_KEY'] = os.urandom(24)
        
        # 注册蓝图
        app.register_blueprint(ub)
        app.register_blueprint(pb)
        
        return app
    except Exception as e:
        print(f"创建应用失败: {str(e)}")
        raise

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
