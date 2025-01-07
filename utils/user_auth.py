import os
import csv
import bcrypt
import json
from datetime import datetime
import shutil

class UserAuth:
    def __init__(self):
        self.users_file = 'persistent_data/users/users.csv'
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """确保必要的目录结构存在"""
        directories = [
            'persistent_data/users',
            'persistent_data/shared/cases',
            'persistent_data/shared/news',
            'persistent_data/shared/templates',
            'persistent_data/logs'
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _hash_password(self, password):
        """对密码进行哈希处理"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def _check_password(self, password, hashed):
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def _get_user_dir(self, username):
        """获取用户个人目录路径"""
        return os.path.join('persistent_data/users', username)

    def _create_user_directory(self, username):
        """创建用户个人目录结构"""
        user_dir = self._get_user_dir(username)
        os.makedirs(user_dir, exist_ok=True)
        os.makedirs(os.path.join(user_dir, 'keywords'), exist_ok=True)
        
        # 创建用户设置文件
        settings_file = os.path.join(user_dir, 'settings.csv')
        if not os.path.exists(settings_file):
            with open(settings_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['setting_key', 'setting_value', 'updated_at'])

        # 创建用户任务文件
        tasks_file = os.path.join(user_dir, 'tasks.csv')
        if not os.path.exists(tasks_file):
            with open(tasks_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['task_id', 'task_name', 'task_type', 'task_config', 'status', 'created_at', 'updated_at'])

    def register(self, username, password, email=None):
        """注册新用户"""
        if self.check_user_exists(username):
            return False, "用户名已存在"

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        hashed_password = self._hash_password(password).decode('utf-8')

        with open(self.users_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([username, hashed_password, email or '', current_time, current_time, '1'])

        self._create_user_directory(username)
        return True, "注册成功"

    def login(self, username, password):
        """用户登录"""
        if not os.path.exists(self.users_file):
            return False, "系统错误"

        with open(self.users_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username and row['is_active'] == '1':
                    if self._check_password(password, row['password_hash']):
                        self._update_last_login(username)
                        return True, "登录成功"
                    return False, "密码错误"
        return False, "用户不存在"

    def _update_last_login(self, username):
        """更新用户最后登录时间"""
        rows = []
        with open(self.users_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['username'] == username:
                    row['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                rows.append(row)

        with open(self.users_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['username', 'password_hash', 'email', 'created_at', 'last_login', 'is_active'])
            writer.writeheader()
            writer.writerows(rows)

    def check_user_exists(self, username):
        """检查用户是否存在"""
        if not os.path.exists(self.users_file):
            return False

        with open(self.users_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return any(row['username'] == username for row in reader)

    def get_user_settings(self, username):
        """获取用户设置"""
        settings_file = os.path.join(self._get_user_dir(username), 'settings.csv')
        if not os.path.exists(settings_file):
            return {}

        settings = {}
        with open(settings_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                settings[row['setting_key']] = row['setting_value']
        return settings

    def update_user_setting(self, username, key, value):
        """更新用户设置"""
        settings_file = os.path.join(self._get_user_dir(username), 'settings.csv')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 读取现有设置
        rows = []
        updated = False
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['setting_key'] == key:
                        row['setting_value'] = value
                        row['updated_at'] = current_time
                        updated = True
                    rows.append(row)

        if not updated:
            rows.append({
                'setting_key': key,
                'setting_value': value,
                'updated_at': current_time
            })

        # 写入更新后的设置
        with open(settings_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['setting_key', 'setting_value', 'updated_at'])
            writer.writeheader()
            writer.writerows(rows)

    def add_user_task(self, username, task_name, task_type, task_config):
        """添加用户任务"""
        tasks_file = os.path.join(self._get_user_dir(username), 'tasks.csv')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 获取新任务ID
        task_id = 1
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                task_ids = [int(row['task_id']) for row in reader]
                if task_ids:
                    task_id = max(task_ids) + 1

        # 添加新任务
        with open(tasks_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if task_id == 1:  # 如果是第一个任务，写入表头
                writer.writerow(['task_id', 'task_name', 'task_type', 'task_config', 'status', 'created_at', 'updated_at'])
            writer.writerow([
                task_id,
                task_name,
                task_type,
                json.dumps(task_config, ensure_ascii=False),
                'pending',
                current_time,
                current_time
            ])
        return task_id

    def update_task_status(self, username, task_id, status):
        """更新任务状态"""
        tasks_file = os.path.join(self._get_user_dir(username), 'tasks.csv')
        if not os.path.exists(tasks_file):
            return False

        rows = []
        updated = False
        with open(tasks_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row['task_id']) == task_id:
                    row['status'] = status
                    row['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    updated = True
                rows.append(row)

        if updated:
            with open(tasks_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['task_id', 'task_name', 'task_type', 'task_config', 'status', 'created_at', 'updated_at'])
                writer.writeheader()
                writer.writerows(rows)
            return True
        return False

    def get_user_tasks(self, username, status=None):
        """获取用户任务列表"""
        tasks_file = os.path.join(self._get_user_dir(username), 'tasks.csv')
        if not os.path.exists(tasks_file):
            return []

        tasks = []
        with open(tasks_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if status is None or row['status'] == status:
                    row['task_config'] = json.loads(row['task_config'])
                    tasks.append(row)
        return tasks

    def save_keyword_data(self, username, keyword, platform, data):
        """保存关键词数据"""
        keyword_dir = os.path.join(self._get_user_dir(username), 'keywords', keyword)
        os.makedirs(keyword_dir, exist_ok=True)
        
        filename = f"{platform}_{datetime.now().strftime('%Y%m%d')}.csv"
        filepath = os.path.join(keyword_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)

    def get_keyword_data(self, username, keyword, platform=None, date=None):
        """获取关键词数据"""
        keyword_dir = os.path.join(self._get_user_dir(username), 'keywords', keyword)
        if not os.path.exists(keyword_dir):
            return []

        data = []
        for filename in os.listdir(keyword_dir):
            if platform and not filename.startswith(f"{platform}_"):
                continue
            if date and not filename.endswith(f"{date}.csv"):
                continue
            
            filepath = os.path.join(keyword_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                data.extend(list(reader))
        return data 