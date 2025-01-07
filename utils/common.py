import os
import platform
import sys
import logging
from datetime import datetime

def setup_logging():
    """配置日志系统"""
    try:
        # 获取项目根目录
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 创建日志目录
        log_dir = os.path.join(root_dir, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        # 日志文件路径
        log_file = os.path.join(log_dir, 'app.log')
        
        # 配置日志格式
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # 创建处理器
        handlers = [
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding='utf-8', mode='a')
        ]
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=handlers
        )
        
        return logging.getLogger(__name__)
    except Exception as e:
        # 如果日志配置失败，至少确保控制台输出正常工作
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logger = logging.getLogger(__name__)
        logger.error(f"日志配置失败: {str(e)}")
        return logger

# 初始化日志
logger = setup_logging()

def get_system_info():
    """获取系统信息"""
    try:
        info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
        logger.info(f"系统信息: {info}")
        return info
    except Exception as e:
        logger.error(f"获取系统信息失败: {str(e)}")
        return {}

def get_project_root():
    """获取项目根目录的绝对路径"""
    try:
        # 获取当前文件的绝对路径
        current_file = os.path.abspath(__file__)
        # 获取utils目录的父目录，即项目根目录
        project_root = os.path.dirname(os.path.dirname(current_file))
        
        # 检查是否在服务器环境
        if platform.system().lower() == 'linux':
            # 检查常见的服务器部署路径
            possible_paths = [
                '/var/www/flask_news',
                '/home/www/flask_news',
                '/opt/flask_news',
                project_root
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    logger.info(f"使用服务器路径: {path}")
                    return path
                    
        logger.info(f"使用项目根目录: {project_root}")
        return project_root
    except Exception as e:
        logger.error(f"获取项目根目录出错: {str(e)}")
        return os.getcwd()

def ensure_dir_exists(directory):
    """确保目录存在，如果不存在则创建"""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"创建目录: {directory}")
            
        # 检查目录权限
        if not os.access(directory, os.W_OK):
            logger.warning(f"目录无写入权限: {directory}")
            # 尝试修改权限
            try:
                if platform.system().lower() == 'linux':
                    os.system(f'chmod 755 {directory}')
                    logger.info(f"已修改目录权限: {directory}")
            except Exception as e:
                logger.error(f"修改目录权限失败: {str(e)}")
                
    except Exception as e:
        logger.error(f"创建/检查目录失败: {str(e)}")
        raise

def get_backup_dir():
    """获取备份目录路径"""
    root_dir = get_project_root()
    backup_dir = os.path.join(root_dir, 'backups')
    ensure_dir_exists(backup_dir)
    return backup_dir

def backup_file(file_path):
    """备份文件"""
    try:
        if not os.path.exists(file_path):
            return False
            
        backup_dir = get_backup_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{os.path.basename(file_path)}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_name)
        
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"文件已备份: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"备份文件失败: {str(e)}")
        return False

def get_persistent_file_path(prefix, suffix):
    """获取持久化文件路径"""
    try:
        # 获取项目根目录
        root_dir = get_project_root()
        
        # 构建persistent_data目录路径
        persistent_dir = os.path.join(root_dir, 'persistent_data')
        ensure_dir_exists(persistent_dir)
        
        # 构建文件路径
        file_name = f"{prefix}_{suffix}.csv"
        file_path = os.path.join(persistent_dir, file_name)
        
        logger.info(f"持久化文件路径: {file_path}")
        
        # 如果文件存在，先备份
        if os.path.exists(file_path):
            backup_file(file_path)
        
        # 如果文件不存在，创建一个空的CSV文件
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("微博作者,微博内容,发布时间,转发数,评论数,点赞数,省份,url\n")
            logger.info(f"创建新的CSV文件: {file_path}")
            
        return file_path
    except Exception as e:
        logger.error(f"获取持久化文件路径出错: {str(e)}")
        # 返回一个备用路径
        return os.path.join(get_project_root(), 'persistent_data', f"{prefix}_{suffix}.csv")

def get_temp_file_path(prefix, suffix):
    """获取临时文件路径"""
    try:
        root_dir = get_project_root()
        temp_dir = os.path.join(root_dir, 'temp_data')
        ensure_dir_exists(temp_dir)
        
        # 清理旧的临时文件
        cleanup_temp_files(temp_dir)
        
        return os.path.join(temp_dir, f"{prefix}_{suffix}.csv")
    except Exception as e:
        logger.error(f"获取临时文件路径出错: {str(e)}")
        return os.path.join(get_project_root(), 'temp_data', f"{prefix}_{suffix}.csv")

def cleanup_temp_files(temp_dir, max_age_days=7):
    """清理指定天数前的临时文件"""
    try:
        now = datetime.now()
        for file_name in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file_name)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if (now - file_time).days > max_age_days:
                    os.remove(file_path)
                    logger.info(f"清理过期临时文件: {file_path}")
    except Exception as e:
        logger.error(f"清理临时文件失败: {str(e)}")

def update_persistent_file(source_file, target_prefix, target_suffix):
    """更新持久化文件"""
    try:
        if not os.path.exists(source_file):
            logger.error(f"源文件不存在: {source_file}")
            return False
            
        target_path = get_persistent_file_path(target_prefix, target_suffix)
        
        # 备份目标文件
        if os.path.exists(target_path):
            backup_file(target_path)
        
        # 读取源文件内容
        with open(source_file, 'r', encoding='utf-8') as source:
            content = source.read()
            
        # 写入目标文件
        with open(target_path, 'w', encoding='utf-8') as target:
            target.write(content)
            
        logger.info(f"文件更新成功: {target_path}")
        return True
    except Exception as e:
        logger.error(f"更新持久化文件出错: {str(e)}")
        return False
