import pandas as pd
from zhipuai import ZhipuAI
from datetime import datetime
import traceback

class ReportGenerator:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.client = ZhipuAI(api_key="5b52ed5d9e8c17f7bae003991ca22def.Z6fO0tH4uV1yWVxm")
        self.context = {}  # 存储每部分的生成结果
        
    def analyze_data(self):
        try:
            df = pd.read_csv(self.csv_path)
            
            # 基础数据处理
            numeric_columns = ['转发数', '评论数', '点赞数']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # 计算影响力并排序
            df['影响力'] = df['转发数'] * 0.4 + df['评论数'] * 0.3 + df['点赞数'] * 0.3
            df_sorted = df.sort_values('影响力', ascending=False)
            
            # 获取高影响力内容（TOP 20）
            top_contents = df_sorted.head(20)[['微博内容', '转发数', '评论数', '点赞数', '情感倾向', '发布时间', '微博作者']].to_dict('records')
            
            # 基础统计
            stats = {
                'total_posts': len(df),
                'total_reposts': int(df['转发数'].sum()),
                'total_comments': int(df['评论数'].sum()),
                'total_likes': int(df['点赞数'].sum()),
                'sentiment_stats': self._calculate_sentiment_stats(df),
                'time_stats': self._calculate_time_stats(df),
                'location_stats': self._calculate_location_stats(df),
                'top_contents': top_contents,
                'keyword_stats': self._extract_keywords(df),
                'engagement_stats': self._calculate_engagement_stats(df)
            }
            
            return stats
        except Exception as e:
            print(f"数据分析错误: {str(e)}")
            return None

    def _calculate_sentiment_stats(self, df):
        """计算情感统计，基于0-1的情感分数（越大越积极）"""
        try:
            # 确保情感倾向列存在且为数值类型
            if '情感倾向' not in df.columns:
                print("警告：数据中缺少'情感倾向'列")
                return self._get_default_sentiment_stats()

            # 将情感倾向转换为浮点数
            df['情感分数'] = pd.to_numeric(df['情感倾向'], errors='coerce').fillna(0.5)
            
            # 根据0-1数重新定义情感分类
            def classify_sentiment(score):
                try:
                    if score < 0.3:  # 0-0.3为负面
                        return '负面'
                    elif score > 0.7:  # 0.7-1为正面
                        return '正面'
                    else:  # 0.3-0.7为中性
                        return '中性'
                except:
                    return '中性'
            
            # ���算情感分布
            df['情感类别'] = df['情感分数'].apply(classify_sentiment)
            sentiment_counts = df['情感类别'].value_counts()
            total = len(df)
            
            # 计算平均情感分数
            avg_sentiment = df['情感分数'].mean()
            
            # 计算情感趋势
            sentiment_trend = self._analyze_sentiment_trend(df)
            
            return {
                'positive_ratio': round((sentiment_counts.get('正面', 0) / total) * 100, 2),
                'negative_ratio': round((sentiment_counts.get('负面', 0) / total) * 100, 2),
                'neutral_ratio': round((sentiment_counts.get('中性', 0) / total) * 100, 2),
                'avg_sentiment': round(avg_sentiment, 3),
                'sentiment_trend': sentiment_trend,
                'sentiment_distribution': {
                    'high': len(df[df['情感分数'] > 0.7]),
                    'medium': len(df[(df['情感分数'] >= 0.3) & (df['情感分数'] <= 0.7)]),
                    'low': len(df[df['情感分数'] < 0.3])
                }
            }
        except Exception as e:
            print(f"情感统计计算错误: {str(e)}")
            return self._get_default_sentiment_stats()

    def _get_default_sentiment_stats(self):
        """返回默认的情感统计数据"""
        return {
            'positive_ratio': 0,
            'negative_ratio': 0,
            'neutral_ratio': 100,
            'avg_sentiment': 0.5,
            'sentiment_trend': {},
            'sentiment_distribution': {
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }

    def _analyze_sentiment_trend(self, df):
        """分析情感趋势"""
        try:
            df['发布时间'] = pd.to_datetime(df['发布时间'])
            df = df.sort_values('发布时间')
            
            # 按天分组并计算统计数据
            daily_stats = df.groupby(df['发布时间'].dt.date).agg({
                '情感倾向': ['mean', 'count'],  # 使用情感倾向列
                '转发数': 'sum',
                '评论数': 'sum',
                '点赞数': 'sum'
            }).round(3)
            
            # 获取最近5天的数据
            recent_stats = daily_stats.tail(5)
            
            # 将 MultiIndex 列转换为单层索引
            recent_stats.columns = ['情感_mean', '情感_count', '转发数', '评论数', '点赞数']
            
            return recent_stats.to_dict('index')
            
        except Exception as e:
            print(f"情感趋势分析错误: {str(e)}")
            traceback.print_exc()
            return {}

    def _calculate_engagement_stats(self, df):
        # 计算互动指标
        total_posts = len(df)
        high_engagement_threshold = df['影响力'].quantile(0.8)
        
        stats = {
            'avg_reposts': round(df['转发数'].mean(), 2),
            'avg_comments': round(df['评论数'].mean(), 2),
            'avg_likes': round(df['点赞数'].mean(), 2),
            'high_engagement_ratio': round(len(df[df['影响力'] > high_engagement_threshold]) / total_posts * 100, 2),
            'engagement_distribution': {
                'high': round(len(df[df['影响力'] > high_engagement_threshold]) / total_posts * 100, 2),
                'medium': round(len(df[(df['影响力'] <= high_engagement_threshold) & (df['影响力'] > df['影响力'].median())]) / total_posts * 100, 2),
                'low': round(len(df[df['影响力'] <= df['影响力'].median()]) / total_posts * 100, 2)
            }
        }
        return stats

    def generate_stream(self, depth='standard'):
        try:
            stats = self.analyze_data()
            if not stats:
                yield self.create_error_response("数据分析失败")
                return

            # 定义报告各部分的提示词
            sections = [
                {
                    'title': "# 舆情分析报告\n\n## 1. 舆情概述\n\n",
                    'prompt': self._build_overview_prompt(stats, depth)
                },
                {
                    'title': "\n## 2. 详细分析\n\n",
                    'prompt': self._build_detailed_analysis_prompt(stats, depth)
                },
                {
                    'title': "\n## 3. 风险评估\n\n",
                    'prompt': self._build_risk_prompt(stats, depth)
                },
                {
                    'title': "\n## 4. 应对建议\n\n",
                    'prompt': self._build_strategy_prompt(stats, depth)
                }
            ]

            # 依次生成每个部分
            for section in sections:
                # 先输出标题
                yield {
                    'code': 200,
                    'data': {'text': section['title']}
                }

                try:
                    # 调用API生成内容
                    response = self.client.chat.completions.create(
                        model="glm-4-flash",
                        messages=[{"role": "user", "content": section['prompt']}],
                        stream=True
                    )
                    
                    for chunk in response:
                        if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                            content = chunk.choices[0].delta.content
                            if content:
                                yield {
                                    'code': 200,
                                    'data': {'text': content}
                                }

                    # 每部分之间添加换行
                    yield {
                        'code': 200,
                        'data': {'text': "\n\n"}
                    }

                except Exception as api_error:
                    print(f"生成部分内容时出错: {str(api_error)}")
                    continue

        except Exception as e:
            print(f"报告生成错误: {str(e)}")
            yield self.create_error_response(f"报告生成失败: {str(e)}")
            return

    def create_error_response(self, message):
        return {
            'code': 500,
            'msg': message,
            'data': {'text': f"错误: {message}"}
        }

    def _build_overview_prompt(self, stats, depth):
        return f"""作为资深舆情分析专家，请基于以下数据生成舆情概述部分。
首先请分析评论主体的性质（政府、企业、教育机构等），并根据主体性质提供相应的分析。

数据概要：
{self._format_basic_stats(stats)}

高影响力内容TOP5：
{self._format_top_contents(stats['top_contents'][:5])}

请生成"舆情概述"部分，包含以下内容：

1. 评论主体性质分析
[识别并确定评论针对的是什么类型的主体，如政府部门、企业、教育机构等]

2. 总体态势
[基于主体性质，分析评论的关注点和倾向]

3. 核心发现
[提炼3-5个重要发现，并详细论述，有理有据]

注意事项：
1. 建议必须与主体性质相符，使用emoji增强可读性
2. 避免泛泛而谈
3. 不要混淆不同性质主体的分析角度
4. 确保分析的专业性和针对性
5. 内容详实，每个部分至少300字
6. 观点鲜明，有理有据
7. 案例具体，分析深入
8. 结构清晰，重点突出
"""

    def _build_detailed_analysis_prompt(self, stats, depth):
        # 添加前序分析作为背景信息
        context_info = f"""前序分析概述：
{self.context.get('overview', '暂无概述')}

"""
        # 保持原有的提示词不变，只在前面加入背景信息
        original_prompt = f"""作为资深舆情分析专家，请基于以下数据生成详细分析部分，内容要有理有据，并使用emoji增强可读性。

数据概要：
{self._format_basic_stats(stats)}

高影响力内容：
{self._format_top_contents(stats['top_contents'])}

情感分析：
{self._format_sentiment_summary(stats)}

请生成"详细分析"部分，包含以下内容：

### 2.1 内容特征分析

📝 **热点内容分析**
[分析高影响力内容的主题分布、传播特点和影响力]

🔍 **传播规律总结**
[总结内容传播的关键特征和规律]

### 2.2 情感态势分析

😊 **情感分布特征**
- 正面情绪（{stats['sentiment_stats']['positive_ratio']}%）分析
- 负面情绪（{stats['sentiment_stats']['negative_ratio']}%）分析
- 中性情绪（{stats['sentiment_stats']['neutral_ratio']}%）分析

📈 **情感演变分析**
[分析情感变化趋势及原因]"""

        return context_info + original_prompt

    def _build_risk_prompt(self, stats, depth):
        # 添加前序分析作为背景信息
        context_info = f"""前序分析概述：
{self.context.get('overview', '暂无概述')}

详细分析：
{self.context.get('analysis', '暂无分析')}

"""
        # 保持原有的提示词不变
        original_prompt = f"""作为资深舆情分析专家，请基于以下数据生成风险评估部分。

数据概要：
{self._format_basic_stats(stats)}

负面内容分析：
{self._format_negative_contents(stats)}

情感分析：
{self._format_sentiment_summary(stats)}

请生成"风险评估"部分，包含以下内容：

⚠️ **当前风险**
[识别并分析当前主要风险点]

🔮 **潜在风险**
[预测可能出现的风险及其发展趋势]

📋 **风险等级评估**
[对各风险点进行等级评估和影响范围分析]

🎯 **重点关注建议**
[提供风险监测和预警建议]"""

        return context_info + original_prompt

    def _build_strategy_prompt(self, stats, depth):
        # 添加前序分析作为背景信息
        context_info = f"""前序分析概述：
{self.context.get('overview', '暂无概述')}

详细分析：
{self.context.get('analysis', '暂无分析')}

风险评估：
{self.context.get('risk', '暂无风险评估')}

"""
        # 保持原有的提示词不变
        original_prompt = f"""作为资深舆情分析专家，请基于以下数据生成应对建议部分，内容要有理有据，并使用emoji增强可读性。

数据概要：
{self._format_basic_stats(stats)}
{self._format_sentiment_summary(stats)}

风险概要：
{self._format_risk_summary(stats)}

请生成"应对建议"部分，包含以下内容：

### 4.1 近期策略

🎯 **优先处理事项**
[列出需要立即采取的行动]

🔧 **具体执行方案**
[提供详细的执行步骤]

### 4.2 长期建议

📈 **持续优化方向**
[提供长期改进建议]

⚡ **预防机制建设**
[建议完善的预防措施]"""

        return context_info + original_prompt

    def _get_depth_requirements(self, depth):
        if depth == 'deep':
            return """
补充要求：
1. 结合行业背景深入分析
2. 提供多个可能的发展方案
3. 详细的执行步骤说明
4. 完整的评估体系设计
5. 长期发展建议
"""
        elif depth == 'basic':
            return """
简化要求：
1. 突出最关键的行动点
2. 优先级明确
3. 执行简单接
4. 重点突出
5. 内容详实，每个部分至少300字
6. 观点鲜明，有理有据
7. 案例具体，分析深入
8. 结构清晰，重点突出
9. 使用emoji增强可读性
"""
        return ""

    def _format_basic_stats(self, stats):
        return f"""
总体数据：
- 总发文量：{stats['total_posts']} 条
- 累计转发：{stats['total_reposts']} 次（平均{stats['total_reposts']/stats['total_posts']:.1f}次/条）
- 累计评论：{stats['total_comments']} 条（平均{stats['total_comments']/stats['total_posts']:.1f}条/条
- 累计点赞：{stats['total_likes']} 次（平均{stats['total_likes']/stats['total_posts']:.1f}次/条）
- 总体互动率：{(stats['total_reposts'] + stats['total_comments'] + stats['total_likes'])/stats['total_posts']:.1f}
"""

    def _format_sentiment_summary(self, stats):
        return f"""
情感分布：
- 正面情绪：{stats['sentiment_stats']['positive_ratio']}%
- 负面情绪：{stats['sentiment_stats']['negative_ratio']}%
- 中性情绪：{stats['sentiment_stats']['neutral_ratio']}%
- 平均情感分数：{stats['sentiment_stats']['avg_sentiment']:.3f}
- 情感倾向指数：{(stats['sentiment_stats']['positive_ratio'] - stats['sentiment_stats']['negative_ratio']):.1f}

近期情感走势：
{self._format_sentiment_trend(stats['sentiment_stats']['sentiment_trend'])}
"""

    def _format_top_contents(self, contents):
        formatted = []
        for i, content in enumerate(contents, 1):
            formatted.append(f"""
内容{i}：
- 正文：{content['微博内容'][:200]}...
- 作者：{content['微博作者']}
- 发布时间：{content['发布时间']}
- 转发：{content['转发数']} | 评论：{content['评论数']} | 点赞：{content['点赞数']}
- 情感倾向：{content['情感倾向']}
""")
        return '\n'.join(formatted)

    def _format_sentiment_trend(self, trend):
        """格式化情感趋势数据"""
        try:
            formatted = []
            for date, stats in trend.items():
                formatted.append(
                    f"- {date}: 平均情感分数{stats['情感_mean']:.3f} ({stats['情感_count']}条内容)"
                )
            return '\n'.join(formatted)
        except Exception as e:
            print(f"情感趋势格式化错误: {str(e)}")
            traceback.print_exc()
            return "暂无情感趋势数据"

    def _calculate_time_stats(self, df):
        """计算时间相关统计"""
        df['发布时间'] = pd.to_datetime(df['发布时间'])
        df = df.sort_values('发布时间')
        
        # 计算时间分布
        time_stats = {
            'start_date': df['发布时间'].min().strftime('%Y-%m-%d'),
            'end_date': df['发布时间'].max().strftime('%Y-%m-%d'),
            'peak_date': df.groupby(df['发布时间'].dt.date).size().idxmax(),
            'daily_stats': df.groupby(df['发布时间'].dt.date).agg({
                '转发数': 'sum',
                '评论数': 'sum',
                '点赞数': 'sum',
                '情感倾向': lambda x: x.value_counts().to_dict()
            }).to_dict('index')
        }
        return time_stats

    def _calculate_location_stats(self, df):
        """计算地域分布统计"""
        if '省份' not in df.columns:
            return {}
        
        location_stats = df.groupby('省份').agg({
            '微博内容': 'count',
            '转发数': 'sum',
            '评论数': 'sum',
            '点赞数': 'sum',
            '情感倾向': lambda x: x.value_counts().to_dict()
        }).to_dict('index')
        
        return location_stats

    def _extract_keywords(self, df):
        """提取关键词统计"""
        # 这里可以使用jieba等工具进行关键词提取
        # 简单示例返回空字典
        return {}

    def _format_negative_contents(self, stats):
        """格式化负面内容"""
        try:
            negative_contents = []
            for content in stats['top_contents']:
                # 将情感倾向转换为浮点数
                sentiment_score = float(content['情感倾向'])
                if sentiment_score < 0.3:  # 负面内容的判断标准
                    negative_contents.append(content)
            
            formatted = []
            for i, content in enumerate(negative_contents[:5], 1):
                formatted.append(f"""
负面内容{i}：
- 正文：{content['微博内容'][:200]}...
- 作者：{content['微博作者']}
- 发布时间：{content['发布时间']}
- 转发：{content['转发数']} | 评论：{content['评论数']} | 点赞：{content['点赞数']}
- 情感分数：{float(content['情感倾向']):.3f}
- 影响力指数：{content.get('影响力', 0):.1f}
""")
            return '\n'.join(formatted) if formatted else "暂无显著负面内容"
        except Exception as e:
            print(f"负面内容格式化错误: {str(e)}")
            return "负面内容分析失败"

    def _format_risk_summary(self, stats):
        """格式化风险概要"""
        # 计算风险指标
        sentiment_stats = stats['sentiment_stats']
        negative_ratio = sentiment_stats['negative_ratio']
        
        # 获取高影响力的负面内容
        high_impact_negative = [
            content for content in stats['top_contents'][:10] 
            if content['情感倾向'] == '负面'
        ]
        
        # 计算传播风险
        spread_risk = (
            len(high_impact_negative) / 10 * 100 if high_impact_negative else 0
        )
        
        return f"""
风险指标：
- 负面情绪占比：{negative_ratio}%
- 高影响力负面内容占比：{spread_risk:.1f}%
- 主要负面观点：
{self._format_negative_contents(stats)}

传播趋势：
{self._format_sentiment_trend(stats['sentiment_stats']['sentiment_trend'])}

地域分布：
{self._format_location_summary(stats['location_stats'])}
"""

    def _format_location_summary(self, location_stats):
        """格式化地域分布概要"""
        if not location_stats:
            return "暂无地域数据"
        
        formatted = []
        for location, stats in list(location_stats.items())[:5]:
            total = stats['微博内容']
            negative = stats['情感倾向'].get('负面', 0)
            formatted.append(
                f"- {location}: {total}条内容，负面占比{negative/total*100:.1f}%"
            )
        return '\n'.join(formatted)

    def _format_engagement_stats(self, stats):
        """格式化互动数据"""
        engagement = stats['engagement_stats']
        return f"""
互动概况：
- 平均转发：{engagement['avg_reposts']}
- 平均评论：{engagement['avg_comments']}
- 平均点赞：{engagement['avg_likes']}

互动分布：
- 高互动内容：{engagement['engagement_distribution']['high']}%
- 中等互动：{engagement['engagement_distribution']['medium']}%
- 低互动内容：{engagement['engagement_distribution']['low']}%

高互动内容占比：{engagement['high_engagement_ratio']}%
"""
