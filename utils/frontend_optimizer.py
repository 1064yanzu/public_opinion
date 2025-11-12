"""
前端性能优化模块 - 静态资源优化和前端性能提升
"""
import os
import gzip
import hashlib
import mimetypes
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, make_response, send_file
from datetime import datetime, timedelta
from utils.performance_monitor import monitor_performance
from config.settings import PERFORMANCE_CONFIG


class StaticResourceOptimizer:
    """静态资源优化器"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        self.compressed_cache = {}
        self.etag_cache = {}
        self.compression_enabled = PERFORMANCE_CONFIG.get('enable_compression', True)
        self.cache_max_age = PERFORMANCE_CONFIG.get('static_cache_max_age', 86400)  # 1天
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """初始化Flask应用"""
        self.app = app

        # 注册请求处理器，但要小心处理静态文件
        app.before_request(self.before_request)
        app.after_request(self.after_request)

        # 添加静态资源路由
        app.add_url_rule('/static/optimized/<path:filename>',
                        'optimized_static',
                        self.serve_optimized_static)
    
    def before_request(self):
        """请求前处理"""
        # 检查是否支持gzip压缩
        if 'gzip' in request.headers.get('Accept-Encoding', ''):
            request.supports_gzip = True
        else:
            request.supports_gzip = False
    
    def after_request(self, response):
        """请求后处理"""
        try:
            # 只对优化的静态资源进行处理，避免干扰默认静态文件
            if request.endpoint == 'optimized_static':
                self._add_cache_headers(response)

            # 对所有响应添加性能头（安全的操作）
            self._add_performance_headers(response)
        except Exception as e:
            # 如果处理失败，记录错误但不影响响应
            print(f"前端优化处理失败: {str(e)}")

        return response
    
    def _add_cache_headers(self, response):
        """添加缓存头"""
        try:
            if response.status_code == 200:
                # 设置缓存控制
                response.headers['Cache-Control'] = f'public, max-age={self.cache_max_age}'

                # 设置过期时间
                from datetime import datetime, timezone
                expires = datetime.now(timezone.utc) + timedelta(seconds=self.cache_max_age)
                response.headers['Expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')

                # 对于静态文件，不尝试访问data属性，因为可能处于直通模式
                # 只设置基本的缓存头
                response.headers['Last-Modified'] = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
        except Exception as e:
            print(f"添加缓存头失败: {str(e)}")
    
    def _add_performance_headers(self, response):
        """添加性能相关头"""
        try:
            # 添加服务器时间头（用于性能分析）
            from datetime import datetime, timezone
            response.headers['X-Response-Time'] = str(int((datetime.now(timezone.utc).timestamp() * 1000) % 1000))

            # 添加压缩信息
            if 'Content-Encoding' in response.headers:
                response.headers['X-Compressed'] = 'true'
        except Exception as e:
            print(f"添加性能头失败: {str(e)}")
    
    @monitor_performance('serve_optimized_static')
    def serve_optimized_static(self, filename):
        """提供优化的静态文件"""
        try:
            # 构建文件路径
            static_dir = os.path.join(self.app.root_path, 'static')
            file_path = os.path.join(static_dir, filename)
            
            if not os.path.exists(file_path):
                return "File not found", 404
            
            # 检查文件类型
            mimetype, _ = mimetypes.guess_type(filename)
            if not mimetype:
                mimetype = 'application/octet-stream'
            
            # 检查是否需要压缩
            should_compress = (
                self.compression_enabled and
                hasattr(request, 'supports_gzip') and
                request.supports_gzip and
                self._should_compress_file(filename, mimetype)
            )
            
            if should_compress:
                return self._serve_compressed_file(file_path, mimetype)
            else:
                return send_file(file_path, mimetype=mimetype)
                
        except Exception as e:
            print(f"提供静态文件失败: {str(e)}")
            return "Internal Server Error", 500
    
    def _should_compress_file(self, filename: str, mimetype: str) -> bool:
        """判断文件是否应该压缩"""
        # 可压缩的文件类型
        compressible_types = [
            'text/', 'application/javascript', 'application/json',
            'application/xml', 'application/css', 'image/svg+xml'
        ]
        
        # 已经压缩的文件类型
        compressed_extensions = ['.gz', '.zip', '.rar', '.7z', '.bz2']
        
        # 检查文件扩展名
        _, ext = os.path.splitext(filename.lower())
        if ext in compressed_extensions:
            return False
        
        # 检查MIME类型
        for comp_type in compressible_types:
            if mimetype.startswith(comp_type):
                return True
        
        return False
    
    def _serve_compressed_file(self, file_path: str, mimetype: str):
        """提供压缩文件"""
        # 检查压缩缓存
        file_mtime = os.path.getmtime(file_path)
        cache_key = f"{file_path}:{file_mtime}"
        
        if cache_key in self.compressed_cache:
            compressed_data = self.compressed_cache[cache_key]
        else:
            # 压缩文件
            with open(file_path, 'rb') as f:
                data = f.read()
            
            compressed_data = gzip.compress(data)
            
            # 缓存压缩结果
            self.compressed_cache[cache_key] = compressed_data
            
            # 限制缓存大小
            if len(self.compressed_cache) > 100:
                # 删除最旧的缓存项
                oldest_key = min(self.compressed_cache.keys())
                del self.compressed_cache[oldest_key]
        
        # 创建响应
        response = make_response(compressed_data)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Encoding'] = 'gzip'
        response.headers['Content-Length'] = len(compressed_data)
        
        return response
    
    def get_stats(self) -> Dict:
        """获取优化器统计信息"""
        return {
            'compressed_cache_size': len(self.compressed_cache),
            'etag_cache_size': len(self.etag_cache),
            'compression_enabled': self.compression_enabled,
            'cache_max_age': self.cache_max_age
        }


class PagePerformanceOptimizer:
    """页面性能优化器"""
    
    def __init__(self):
        self.resource_hints = []
        self.critical_css = []
        self.preload_resources = []
    
    def add_resource_hint(self, href: str, rel: str = 'dns-prefetch'):
        """添加资源提示"""
        self.resource_hints.append({'href': href, 'rel': rel})
    
    def add_critical_css(self, css_content: str):
        """添加关键CSS"""
        self.critical_css.append(css_content)
    
    def add_preload_resource(self, href: str, as_type: str = 'script'):
        """添加预加载资源"""
        self.preload_resources.append({'href': href, 'as': as_type})
    
    def generate_performance_html(self) -> str:
        """生成性能优化HTML"""
        html_parts = []
        
        # 资源提示
        for hint in self.resource_hints:
            html_parts.append(f'<link rel="{hint["rel"]}" href="{hint["href"]}">')
        
        # 预加载资源
        for resource in self.preload_resources:
            html_parts.append(f'<link rel="preload" href="{resource["href"]}" as="{resource["as"]}">')
        
        # 关键CSS
        if self.critical_css:
            html_parts.append('<style>')
            html_parts.extend(self.critical_css)
            html_parts.append('</style>')
        
        return '\n'.join(html_parts)


class CDNOptimizer:
    """CDN优化器"""
    
    def __init__(self):
        # 中国大陆可用的CDN配置
        self.cdn_configs = {
            'jquery': {
                'url': 'https://cdn.bootcdn.net/ajax/libs/jquery/3.6.0/jquery.min.js',
                'integrity': 'sha384-vtXRMe3mGCbOeY7l30aIg8H9p3GdeSe4IFlP6G8JMa7o7lXvnz3GFKzPxzJdPfGK',
                'fallback': '/static/js/jquery.min.js'
            },
            'bootstrap': {
                'css': 'https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/css/bootstrap.min.css',
                'js': 'https://cdn.bootcdn.net/ajax/libs/bootstrap/5.1.3/js/bootstrap.bundle.min.js',
                'fallback_css': '/static/css/bootstrap.min.css',
                'fallback_js': '/static/js/bootstrap.bundle.min.js'
            },
            'echarts': {
                'url': 'https://cdn.bootcdn.net/ajax/libs/echarts/5.4.0/echarts.min.js',
                'fallback': '/static/js/echarts.min.js'
            }
        }
    
    def get_cdn_url(self, library: str, resource_type: str = 'js') -> str:
        """获取CDN URL"""
        if library in self.cdn_configs:
            config = self.cdn_configs[library]
            
            if resource_type == 'css' and 'css' in config:
                return config['css']
            elif resource_type == 'js':
                return config.get('js', config.get('url', ''))
        
        return ''
    
    def get_fallback_url(self, library: str, resource_type: str = 'js') -> str:
        """获取备用URL"""
        if library in self.cdn_configs:
            config = self.cdn_configs[library]
            
            if resource_type == 'css':
                return config.get('fallback_css', '')
            else:
                return config.get('fallback_js', config.get('fallback', ''))
        
        return ''
    
    def generate_cdn_html(self, library: str, resource_type: str = 'js') -> str:
        """生成CDN HTML代码"""
        cdn_url = self.get_cdn_url(library, resource_type)
        fallback_url = self.get_fallback_url(library, resource_type)
        
        if not cdn_url:
            return ''
        
        if resource_type == 'css':
            html = f'<link rel="stylesheet" href="{cdn_url}">'
            if fallback_url:
                html += f'\n<script>if(!document.querySelector(\'link[href="{cdn_url}"]\').sheet){{document.write(\'<link rel="stylesheet" href="{fallback_url}">\');}}</script>'
        else:
            html = f'<script src="{cdn_url}"></script>'
            if fallback_url:
                # 简单的fallback检测
                check_var = {
                    'jquery': 'window.jQuery',
                    'bootstrap': 'window.bootstrap',
                    'echarts': 'window.echarts'
                }.get(library, 'true')
                
                html += f'\n<script>if(!{check_var}){{document.write(\'<script src="{fallback_url}"><\\/script>\');}}</script>'
        
        return html


# 全局实例
static_optimizer = StaticResourceOptimizer()
page_optimizer = PagePerformanceOptimizer()
cdn_optimizer = CDNOptimizer()


def init_frontend_optimization(app: Flask):
    """初始化前端优化"""
    static_optimizer.init_app(app)
    
    # 添加常用的资源提示
    page_optimizer.add_resource_hint('//cdn.bootcdn.net', 'dns-prefetch')
    page_optimizer.add_resource_hint('//fonts.googleapis.com', 'dns-prefetch')
    
    print("前端性能优化已初始化")
