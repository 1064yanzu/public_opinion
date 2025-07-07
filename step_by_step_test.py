#!/usr/bin/env python3
"""
逐步测试应用模块，找出问题所在
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_step(step_name, test_func):
    """测试单个步骤"""
    print(f"\n{'='*50}")
    print(f"测试步骤: {step_name}")
    print('='*50)
    try:
        result = test_func()
        print(f"✅ {step_name} - 成功")
        return result
    except Exception as e:
        print(f"❌ {step_name} - 失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def step1_basic_imports():
    """步骤1: 基础导入"""
    from flask import Flask, render_template, jsonify, request
    from werkzeug.exceptions import Forbidden, NotFound
    import gc, atexit
    from datetime import timedelta
    return True

def step2_project_imports():
    """步骤2: 项目模块导入"""
    from views.user.user import ub
    from views.page import page
    from views.user import user
    return True

def step3_nlp_imports():
    """步骤3: NLP和爬虫模块导入"""
    import model.nlp
    import spiders.articles_spider
    return True

def step4_chart_imports():
    """步骤4: 图表库导入"""
    from pyecharts import options as opts
    from pyecharts.charts import Bar, Pie
    return True

def step5_optimization_imports():
    """步骤5: 性能优化模块导入"""
    from utils.performance_monitor import performance_monitor, monitor_performance, get_performance_report
    from utils.cache_manager import clear_cache, get_cache_stats, memory_cleanup
    from config.settings import PERFORMANCE_CONFIG
    return True

def step6_second_stage_imports():
    """步骤6: 第二阶段模块导入"""
    from utils.async_task_manager import task_manager
    from utils.data_pipeline import crawler_pipeline
    from utils.network_optimizer import spider_optimizer
    return True

def step7_third_stage_imports():
    """步骤7: 第三阶段模块导入"""
    from utils.advanced_cache import advanced_cache
    from utils.frontend_optimizer import init_frontend_optimization, static_optimizer, page_optimizer, cdn_optimizer
    from utils.monitoring_alerts import alert_manager
    from utils.smart_preprocessor import smart_preprocessor
    return True

def step8_flask_app_creation():
    """步骤8: Flask应用创建和配置"""
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    return app

def step9_blueprint_registration():
    """步骤9: 蓝图注册"""
    from flask import Flask
    from views.page import page
    from views.user import user
    
    app = Flask(__name__)
    app.register_blueprint(page.pb)
    app.register_blueprint(user.ub)
    return app

def step10_third_stage_initialization():
    """步骤10: 第三阶段功能初始化"""
    from utils.frontend_optimizer import init_frontend_optimization
    from utils.monitoring_alerts import alert_manager
    from flask import Flask
    
    app = Flask(__name__)
    
    # 初始化前端优化
    init_frontend_optimization(app)
    
    # 启动系统监控
    alert_manager.start_monitoring()
    
    return app

def main():
    print("开始逐步测试Flask应用模块...")
    
    # 测试各个步骤
    test_step("基础导入", step1_basic_imports)
    test_step("项目模块导入", step2_project_imports)
    test_step("NLP和爬虫模块导入", step3_nlp_imports)
    test_step("图表库导入", step4_chart_imports)
    test_step("性能优化模块导入", step5_optimization_imports)
    test_step("第二阶段模块导入", step6_second_stage_imports)
    test_step("第三阶段模块导入", step7_third_stage_imports)
    test_step("Flask应用创建", step8_flask_app_creation)
    test_step("蓝图注册", step9_blueprint_registration)
    test_step("第三阶段功能初始化", step10_third_stage_initialization)
    
    print(f"\n{'='*50}")
    print("所有测试完成!")
    print('='*50)

if __name__ == "__main__":
    main()
