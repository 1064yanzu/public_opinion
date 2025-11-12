from functools import wraps
from flask import session, redirect, url_for, request, flash
import time

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session是否存在和有效
        if not session.get('username') or not session.get('logged_in'):
            flash('请先登录后再访问', 'warning')
            # 保存当前URL，登录后返回
            next_url = request.url
            session['next_url'] = next_url
            return redirect(url_for('user.login'))
            
        # 检查session是否过期
        last_active = session.get('last_active', 0)
        current_time = time.time()
        
        # 如果超过30分钟没有活动，清除session
        if current_time - last_active > 1800:  # 30分钟 = 1800秒
            session.clear()
            flash('登录已过期，请重新登录', 'warning')
            return redirect(url_for('user.login'))
            
        # 更新最后活动时间
        session['last_active'] = current_time
        return f(*args, **kwargs)
    return decorated_function

def is_logged_in():
    if not session.get('username') or not session.get('logged_in'):
        return False
    
    # 检查session是否过期
    last_active = session.get('last_active', 0)
    current_time = time.time()
    
    if current_time - last_active > 1800:  # 30分钟 = 1800秒
        session.clear()
        return False
        
    # 更新最后活动时间
    session['last_active'] = current_time
    return True 