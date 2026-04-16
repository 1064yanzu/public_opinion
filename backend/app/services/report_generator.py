"""
报告生成服务
生成 PDF/Word 格式的分析报告
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or settings.REPORTS_DIR
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_text_report(
        self,
        keyword: str,
        data: List[Dict],
        statistics: Dict[str, Any],
        risk_info: Dict[str, Any],
        topics: List[Dict] = None,
        key_spreaders: List[Dict] = None,
    ) -> str:
        """
        生成文本格式报告
        
        Returns:
            报告内容字符串
        """
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        # 情感统计
        sentiment = statistics.get('sentiment_distribution', {})
        total = statistics.get('total_count', 0)
        positive = sentiment.get('positive', 0)
        negative = sentiment.get('negative', 0)
        neutral = sentiment.get('neutral', 0)
        
        report = f"""
================================================================================
                        舆情分析报告
================================================================================

报告生成时间：{now}
分析关键词：{keyword}
数据总量：{total} 条

--------------------------------------------------------------------------------
一、数据概览
--------------------------------------------------------------------------------

总数据量：{total} 条
互动总量：{statistics.get('total_interaction', 0):,} 次
  - 点赞数：{statistics.get('total_likes', 0):,}
  - 评论数：{statistics.get('total_comments', 0):,}
  - 转发/分享数：{statistics.get('total_shares', 0):,}

平台分布：
{self._format_dict(statistics.get('platform_distribution', {}))}

--------------------------------------------------------------------------------
二、情感分析
--------------------------------------------------------------------------------

情感分布：
  - 正面：{positive} 条 ({positive/total*100:.1f}% if total > 0 else 0)
  - 负面：{negative} 条 ({negative/total*100:.1f}% if total > 0 else 0)
  - 中性：{neutral} 条 ({neutral/total*100:.1f}% if total > 0 else 0)

--------------------------------------------------------------------------------
三、风险评估
--------------------------------------------------------------------------------

风险等级：{risk_info.get('level', '未知')}
风险分数：{risk_info.get('score', 0)}/100

风险因素：
{self._format_list(risk_info.get('factors', ['无明显风险因素']))}

详细评分：
  - 情感风险分：{risk_info.get('details', {}).get('sentiment_score', 0)}
  - 互动热度分：{risk_info.get('details', {}).get('interaction_score', 0)}
  - 传播速度分：{risk_info.get('details', {}).get('speed_score', 0)}

"""
        
        if topics:
            report += """--------------------------------------------------------------------------------
四、主题分析
--------------------------------------------------------------------------------

"""
            for topic in topics[:5]:
                keywords = ', '.join(topic.get('keywords', [])[:5])
                report += f"主题{topic.get('topic_id', 0)}: {keywords}\n"
                report += f"  文档数量：{topic.get('doc_count', 0)} ({topic.get('doc_ratio', 0)*100:.1f}%)\n\n"
        
        if key_spreaders:
            report += """--------------------------------------------------------------------------------
五、关键传播主体
--------------------------------------------------------------------------------

"""
            for i, spreader in enumerate(key_spreaders[:10], 1):
                report += f"{i}. {spreader.get('user_name', '未知')}\n"
                report += f"   发布量：{spreader.get('post_count', 0)} | "
                report += f"互动量：{spreader.get('total_likes', 0) + spreader.get('total_comments', 0)} | "
                report += f"影响力分：{spreader.get('influence_score', 0):.1f}\n\n"
        
        report += """--------------------------------------------------------------------------------
六、建议与对策
--------------------------------------------------------------------------------

"""
        if risk_info.get('level') == '高':
            report += """1. 建议立即关注并制定应对方案
2. 及时回应公众关切，发布官方声明
3. 加强舆情监控频率
4. 准备危机公关预案
"""
        elif risk_info.get('level') == '中':
            report += """1. 建议持续关注舆情发展
2. 准备相关应对话术
3. 定期监测情感变化趋势
"""
        else:
            report += """1. 舆情态势平稳，保持常规监控
2. 关注潜在风险点
"""
        
        report += f"""
================================================================================
                        报告结束
================================================================================
"""
        
        return report
    
    def save_report(
        self,
        content: str,
        filename: Optional[str] = None,
        format: str = "txt"
    ) -> str:
        """
        保存报告到文件
        
        Returns:
            文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.{format}"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def generate_and_save(
        self,
        keyword: str,
        data: List[Dict],
        statistics: Dict[str, Any],
        risk_info: Dict[str, Any],
        topics: List[Dict] = None,
        key_spreaders: List[Dict] = None,
    ) -> Dict[str, Any]:
        """
        生成并保存报告
        
        Returns:
            {'filepath': str, 'download_url': str}
        """
        content = self.generate_text_report(
            keyword, data, statistics, risk_info, topics, key_spreaders
        )
        
        filepath = self.save_report(content)
        filename = os.path.basename(filepath)
        
        return {
            'filepath': filepath,
            'download_url': f"/static/reports/{filename}",
            'filename': filename,
        }
    
    @staticmethod
    def _format_dict(d: Dict) -> str:
        """格式化字典为字符串"""
        if not d:
            return "  无数据"
        return '\n'.join(f"  - {k}: {v}" for k, v in d.items())
    
    @staticmethod
    def _format_list(lst: List) -> str:
        """格式化列表为字符串"""
        if not lst:
            return "  无"
        return '\n'.join(f"  - {item}" for item in lst)


# 便捷函数
def generate_report(
    keyword: str,
    data: List[Dict],
    statistics: Dict[str, Any],
    risk_info: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """生成报告的便捷函数"""
    generator = ReportGenerator()
    return generator.generate_and_save(keyword, data, statistics, risk_info, **kwargs)
