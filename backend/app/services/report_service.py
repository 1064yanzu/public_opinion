"""Report generation service"""
import os
import sys
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from datetime import datetime

# 添加项目根目录到路径，以便导入现有模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


class ReportService:
    """舆情报告生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.generator = None
    
    async def generate_report_stream(
        self,
        dataset_id: int = None,
        depth: str = "standard",
        include_sections: list = None,
        user_id: int = None
    ) -> AsyncGenerator[dict, None]:
        """
        流式生成报告
        
        Args:
            dataset_id: 数据集ID
            depth: 报告深度（simple, standard, detailed）
            include_sections: 包含的章节
            user_id: 用户ID
        
        Yields:
            dict: 报告片段
        """
        try:
            # 导入现有的报告生成器
            from utils.report_generator import ReportGenerator
            from utils.common import get_persistent_file_path
            
            # 获取数据文件路径
            if dataset_id:
                # TODO: 根据dataset_id获取对应的CSV文件
                csv_path = get_persistent_file_path('all', 'any')
            else:
                csv_path = get_persistent_file_path('all', 'any')
            
            if not os.path.exists(csv_path):
                yield {
                    "type": "error",
                    "content": "数据文件不存在，请先爬取数据"
                }
                return
            
            # 初始化报告生成器
            self.generator = ReportGenerator(csv_path)
            
            # 生成报告
            sections_content = {
                'summary': [],
                'analysis': [],
                'suggestions': [],
                'risks': []
            }
            
            current_section = "summary"
            
            # 流式生成
            for chunk in self.generator.generate_stream(depth):
                if chunk.get('code') != 200:
                    yield {
                        "type": "error",
                        "content": chunk.get('msg', '生成失败')
                    }
                    return
                
                content = chunk.get('data', {}).get('text', '')
                
                if content:
                    # 判断当前章节
                    if "舆情分析" in content or "数据分析" in content:
                        current_section = "analysis"
                    elif "应对建议" in content or "建议" in content:
                        current_section = "suggestions"
                    elif "风险提示" in content or "风险" in content:
                        current_section = "risks"
                    
                    sections_content[current_section].append(content)
                    
                    # 实时输出
                    yield {
                        "type": current_section,
                        "content": content
                    }
            
            # 输出完整报告
            yield {
                "type": "complete",
                "sections": {
                    "summary": ''.join(sections_content['summary']),
                    "analysis": ''.join(sections_content['analysis']),
                    "suggestions": ''.join(sections_content['suggestions']),
                    "risks": ''.join(sections_content['risks'])
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"报告生成错误: {str(e)}")
            yield {
                "type": "error",
                "content": f"报告生成失败: {str(e)}"
            }
    
    def get_report_history(self, user_id: int, limit: int = 20):
        """获取报告历史"""
        # TODO: 实现报告历史记录
        return []
    
    def save_report(self, user_id: int, dataset_id: int, report_content: dict):
        """保存报告"""
        # TODO: 实现报告保存功能
        pass
