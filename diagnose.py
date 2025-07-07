#!/usr/bin/env python3
"""
诊断脚本 - 检查所有导入和依赖
"""
import sys
import traceback

def test_import(module_name, description=""):
    """测试模块导入"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} {description} - 导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"⚠️ {module_name} {description} - 其他错误: {str(e)}")
        return False

def main():
    print("开始诊断Flask应用依赖...")
    print(f"Python版本: {sys.version}")
    print("-" * 50)
    
    # 基础依赖
    print("检查基础依赖:")
    test_import("flask", "- Flask框架")
    test_import("werkzeug", "- Werkzeug工具包")
    test_import("jinja2", "- Jinja2模板引擎")
    
    print("\n检查项目模块:")
    test_import("views.user.user", "- 用户视图")
    test_import("views.page", "- 页面视图")
    test_import("model.nlp", "- NLP模型")
    test_import("spiders.articles_spider", "- 爬虫模块")
    
    print("\n检查优化模块:")
    test_import("utils.performance_monitor", "- 性能监控")
    test_import("utils.cache_manager", "- 缓存管理")
    test_import("config.settings", "- 配置设置")
    
    print("\n检查第二阶段模块:")
    test_import("utils.async_task_manager", "- 异步任务管理")
    test_import("utils.data_pipeline", "- 数据流水线")
    test_import("utils.network_optimizer", "- 网络优化")
    
    print("\n检查第三阶段模块:")
    test_import("utils.advanced_cache", "- 高级缓存")
    test_import("utils.frontend_optimizer", "- 前端优化")
    test_import("utils.monitoring_alerts", "- 监控告警")
    test_import("utils.smart_preprocessor", "- 智能预处理")
    
    print("\n检查图表库:")
    test_import("pyecharts", "- PyEcharts图表库")
    test_import("pyecharts.charts", "- PyEcharts图表组件")
    
    print("\n尝试导入主应用模块...")
    try:
        # 不执行，只检查语法
        with open('app.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 编译检查
        compile(code, 'app.py', 'exec')
        print("✅ app.py 语法检查通过")
        
    except SyntaxError as e:
        print(f"❌ app.py 语法错误: {str(e)}")
        print(f"   行号: {e.lineno}, 位置: {e.offset}")
    except Exception as e:
        print(f"❌ app.py 检查失败: {str(e)}")
    
    print("\n诊断完成!")

if __name__ == "__main__":
    main()
