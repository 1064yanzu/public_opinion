"""
系统监控告警模块 - 智能监控和自动告警
"""
import time
import threading
import smtplib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.performance_monitor import get_performance_report
from config.settings import PERFORMANCE_CONFIG


class AlertRule:
    """告警规则"""
    
    def __init__(self, name: str, condition: Callable, threshold: float, 
                 severity: str = 'warning', cooldown: int = 300):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.severity = severity  # 'info', 'warning', 'error', 'critical'
        self.cooldown = cooldown  # 冷却时间（秒）
        self.last_triggered = 0
        self.trigger_count = 0
    
    def check(self, metrics: Dict) -> Optional[Dict]:
        """检查告警条件"""
        try:
            current_time = time.time()
            
            # 检查冷却时间
            if current_time - self.last_triggered < self.cooldown:
                return None
            
            # 执行条件检查
            if self.condition(metrics, self.threshold):
                self.last_triggered = current_time
                self.trigger_count += 1
                
                return {
                    'rule_name': self.name,
                    'severity': self.severity,
                    'threshold': self.threshold,
                    'trigger_count': self.trigger_count,
                    'timestamp': datetime.now().isoformat(),
                    'metrics': metrics
                }
        
        except Exception as e:
            print(f"告警规则检查失败: {self.name}, 错误: {str(e)}")
        
        return None


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.rules = []
        self.handlers = []
        self.alert_history = []
        self.max_history = 1000
        self.monitoring_enabled = True
        self.monitoring_interval = 60  # 监控间隔（秒）
        self.monitoring_thread = None
        self.lock = threading.Lock()
        
        # 初始化默认告警规则
        self._init_default_rules()
        
        # 初始化默认处理器
        self._init_default_handlers()
    
    def _init_default_rules(self):
        """初始化默认告警规则"""
        # CPU使用率告警
        self.add_rule(AlertRule(
            name="CPU使用率过高",
            condition=lambda m, t: m.get('system', {}).get('cpu', {}).get('percent', 0) > t,
            threshold=80.0,
            severity='warning',
            cooldown=300
        ))
        
        # 内存使用率告警
        self.add_rule(AlertRule(
            name="内存使用率过高",
            condition=lambda m, t: m.get('system', {}).get('memory', {}).get('percent', 0) > t,
            threshold=85.0,
            severity='warning',
            cooldown=300
        ))
        
        # 进程内存告警
        self.add_rule(AlertRule(
            name="进程内存使用过高",
            condition=lambda m, t: m.get('system', {}).get('memory', {}).get('process_rss_mb', 0) > t,
            threshold=PERFORMANCE_CONFIG.get('memory_limit_mb', 512),
            severity='error',
            cooldown=180
        ))
        
        # 磁盘使用率告警
        self.add_rule(AlertRule(
            name="磁盘使用率过高",
            condition=lambda m, t: m.get('system', {}).get('disk', {}).get('percent', 0) > t,
            threshold=90.0,
            severity='error',
            cooldown=600
        ))
        
        # 缓存命中率告警
        self.add_rule(AlertRule(
            name="缓存命中率过低",
            condition=lambda m, t: self._parse_hit_rate(m.get('system', {}).get('cache', {}).get('hit_rate', '100%')) < t,
            threshold=50.0,
            severity='warning',
            cooldown=300
        ))
        
        # 错误率告警
        self.add_rule(AlertRule(
            name="系统错误率过高",
            condition=lambda m, t: self._calculate_error_rate(m) > t,
            threshold=5.0,
            severity='error',
            cooldown=120
        ))
    
    def _init_default_handlers(self):
        """初始化默认处理器"""
        # 日志处理器
        self.add_handler(self._log_handler)
        
        # 控制台处理器
        self.add_handler(self._console_handler)
        
        # 如果配置了邮件，添加邮件处理器
        if PERFORMANCE_CONFIG.get('email_alerts_enabled', False):
            self.add_handler(self._email_handler)
    
    def _parse_hit_rate(self, hit_rate_str: str) -> float:
        """解析命中率字符串"""
        try:
            if isinstance(hit_rate_str, str) and hit_rate_str.endswith('%'):
                return float(hit_rate_str[:-1])
            return float(hit_rate_str) * 100
        except:
            return 100.0
    
    def _calculate_error_rate(self, metrics: Dict) -> float:
        """计算错误率"""
        try:
            # 这里可以根据实际的错误统计来计算
            # 暂时返回0，实际使用时需要根据具体的错误统计逻辑
            return 0.0
        except:
            return 0.0
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self.lock:
            self.rules.append(rule)
    
    def add_handler(self, handler: Callable):
        """添加告警处理器"""
        with self.lock:
            self.handlers.append(handler)
    
    def check_alerts(self):
        """检查所有告警规则"""
        try:
            # 获取当前系统指标
            metrics = get_performance_report()
            
            triggered_alerts = []
            
            for rule in self.rules:
                alert = rule.check(metrics)
                if alert:
                    triggered_alerts.append(alert)
            
            # 处理触发的告警
            for alert in triggered_alerts:
                self._handle_alert(alert)
                
                # 记录告警历史
                with self.lock:
                    self.alert_history.append(alert)
                    
                    # 限制历史记录数量
                    if len(self.alert_history) > self.max_history:
                        self.alert_history = self.alert_history[-self.max_history:]
            
            return triggered_alerts
            
        except Exception as e:
            print(f"告警检查失败: {str(e)}")
            return []
    
    def _handle_alert(self, alert: Dict):
        """处理告警"""
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"告警处理器执行失败: {str(e)}")
    
    def _log_handler(self, alert: Dict):
        """日志处理器"""
        log_dir = PERFORMANCE_CONFIG.get('log_dir', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'alerts.log')
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                log_entry = {
                    'timestamp': alert['timestamp'],
                    'severity': alert['severity'],
                    'rule_name': alert['rule_name'],
                    'threshold': alert['threshold'],
                    'trigger_count': alert['trigger_count']
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"写入告警日志失败: {str(e)}")
    
    def _console_handler(self, alert: Dict):
        """控制台处理器"""
        severity_symbols = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        
        symbol = severity_symbols.get(alert['severity'], '📢')
        
        print(f"\n{symbol} 【{alert['severity'].upper()}】告警触发")
        print(f"规则: {alert['rule_name']}")
        print(f"阈值: {alert['threshold']}")
        print(f"触发次数: {alert['trigger_count']}")
        print(f"时间: {alert['timestamp']}")
        print("-" * 50)
    
    def _email_handler(self, alert: Dict):
        """邮件处理器"""
        try:
            # 邮件配置
            smtp_server = PERFORMANCE_CONFIG.get('smtp_server', '')
            smtp_port = PERFORMANCE_CONFIG.get('smtp_port', 587)
            smtp_user = PERFORMANCE_CONFIG.get('smtp_user', '')
            smtp_password = PERFORMANCE_CONFIG.get('smtp_password', '')
            alert_recipients = PERFORMANCE_CONFIG.get('alert_recipients', [])
            
            if not all([smtp_server, smtp_user, smtp_password, alert_recipients]):
                return
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = ', '.join(alert_recipients)
            msg['Subject'] = f"系统告警: {alert['rule_name']}"

            # 邮件内容
            body = f"""
系统监控告警通知

告警规则: {alert['rule_name']}
严重级别: {alert['severity'].upper()}
触发阈值: {alert['threshold']}
触发次数: {alert['trigger_count']}
触发时间: {alert['timestamp']}

请及时检查系统状态。

---
自动发送，请勿回复
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            print(f"告警邮件已发送: {alert['rule_name']}")
            
        except Exception as e:
            print(f"发送告警邮件失败: {str(e)}")
    
    def start_monitoring(self):
        """启动监控"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.monitoring_enabled = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        print("系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_enabled = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        print("系统监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_enabled:
            try:
                self.check_alerts()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                print(f"监控循环异常: {str(e)}")
                time.sleep(10)  # 异常时等待10秒再继续
    
    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """获取告警历史"""
        with self.lock:
            return self.alert_history[-limit:]
    
    def get_alert_stats(self) -> Dict:
        """获取告警统计"""
        with self.lock:
            total_alerts = len(self.alert_history)
            
            if total_alerts == 0:
                return {
                    'total_alerts': 0,
                    'severity_distribution': {},
                    'rule_distribution': {},
                    'recent_alerts': 0
                }
            
            # 按严重级别统计
            severity_count = {}
            rule_count = {}
            recent_count = 0
            
            recent_threshold = time.time() - 3600  # 最近1小时
            
            for alert in self.alert_history:
                # 严重级别统计
                severity = alert.get('severity', 'unknown')
                severity_count[severity] = severity_count.get(severity, 0) + 1
                
                # 规则统计
                rule_name = alert.get('rule_name', 'unknown')
                rule_count[rule_name] = rule_count.get(rule_name, 0) + 1
                
                # 最近告警统计
                try:
                    alert_time = datetime.fromisoformat(alert['timestamp']).timestamp()
                    if alert_time > recent_threshold:
                        recent_count += 1
                except:
                    pass
            
            return {
                'total_alerts': total_alerts,
                'severity_distribution': severity_count,
                'rule_distribution': rule_count,
                'recent_alerts': recent_count,
                'monitoring_enabled': self.monitoring_enabled,
                'monitoring_interval': self.monitoring_interval
            }


# 全局告警管理器实例
alert_manager = AlertManager()
