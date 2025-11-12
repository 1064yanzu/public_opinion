import pandas as pd
from datetime import datetime
import traceback
import re
import jieba
import jieba.posseg
from collections import Counter
from .ai_model_interface import create_ai_model

class ReportGenerator:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        # 使用新的模型接口
        self.ai_model = create_ai_model()
        self.client = None  # 不再使用备用客户端

        # 检查是否有可用的AI模型
        if self.ai_model is None:
            print("AI模型未配置或初始化失败")
            print("请设置环境变量后使用报告生成功能")
        else:
            print(f"AI模型初始化成功: {type(self.ai_model).__name__}")
            
        self.data_cache = {}
        self.context = {
            'analysis_results': {},
            'processed_data': {},
            'generation_state': {}
        }

    def generate_stream(self, depth='standard'):
        """优化的报告生成流程"""
        try:
            # 检查AI模型是否可用
            if self.ai_model is None:
                error_msg = """
# ⚠️ 报告生成功能不可用

## 原因
未检测到有效的AI模型配置。

## 解决方案

### 方法1：设置环境变量（推荐）
```bash
# Windows (命令提示符)
set AI_MODEL_TYPE=zhipuai
set AI_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:AI_MODEL_TYPE="zhipuai"
$env:AI_API_KEY="your_api_key_here"

# Linux/Mac
export AI_MODEL_TYPE=zhipuai
export AI_API_KEY=your_api_key_here
```

### 方法2：创建.env文件
在项目根目录创建`.env`文件：
```
AI_MODEL_TYPE=zhipuai
AI_API_KEY=your_api_key_here
AI_MODEL_ID=glm-4
```

## 支持的模型类型
- `zhipuai`: 智谱AI (推荐)
- `openai`: OpenAI
- `custom`: 自定义API

## 获取API Key
- 智谱AI: https://open.bigmodel.cn/
- OpenAI: https://platform.openai.com/

配置完成后请重启应用并重新生成报告。
"""
                yield error_msg
                return
                
            # 1. 预处理数据
            if not self.preprocess_data():
                yield self.create_error_response("数据预处理失败")
                return

            # 2. 构建分析上下文
            analysis_context = self._build_analysis_context()
            
            # 3. 生成报告结构
            report_sections = [
                {
                    'name': 'overview',
                    'title': "# 📊 舆情分析报告\n\n## 1️⃣ 舆情概述\n\n",
                    'type': 'overview'
                },
                {
                    'name': 'analysis',
                    'title': "\n\n## 2️⃣ 详细分析\n\n",
                    'type': 'analysis'
                },
                {
                    'name': 'risk',
                    'title': "\n\n## 3️⃣ 风险评估\n\n",
                    'type': 'risk'
                },
                {
                    'name': 'strategy',
                    'title': "\n\n## 4️⃣ 应对建议\n\n",
                    'type': 'strategy'
                }
            ]
            
            # 4. 顺序生成各部分内容
            for section in report_sections:
                # 输出标题
                yield {
                    'code': 200,
                    'data': {'text': section['title']}
                }

                # 构建提示词
                system_prompt = self._build_system_prompt(section, analysis_context)
                user_prompt = self._build_section_prompt(section, analysis_context)
                
                # 生成内容 - 使用新的AI接口
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]

                # 处理响应
                buffer = []
                buffer_size = 50

                # 使用统一chat接口生成内容
                try:
                    response_stream = self.ai_model.chat(
                        messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=4000
                    )

                    first_chunk = True
                    for content in response_stream:
                        if content:
                            # 检查首个分片是否包含错误信息
                            if first_chunk and any(error_keyword in content for error_keyword in [
                                "流式生成失败", "认证失败", "权限不足", "模型不存在", 
                                "请求过于频繁", "服务器错误", "网络连接失败", "请求超时"
                            ]):
                                # 流式失败，尝试降级到非流式
                                try:
                                    fallback_result = self.ai_model.chat(
                                        messages,
                                        stream=False,
                                        temperature=0.7,
                                        max_tokens=4000
                                    )
                                    if fallback_result and not any(error_keyword in fallback_result for error_keyword in [
                                        "生成失败", "认证失败", "权限不足", "模型不存在"
                                    ]):
                                        # 非流式成功，输出结果
                                        yield {
                                            'code': 200,
                                            'data': {'text': fallback_result}
                                        }
                                        break
                                    else:
                                        # 非流式也失败，返回错误
                                        yield self.create_error_response(fallback_result)
                                        return
                                except Exception as fallback_error:
                                    yield self.create_error_response(f"AI调用失败: {str(fallback_error)}")
                                    return
                            
                            first_chunk = False
                            buffer.append(content)

                            if len(buffer) >= buffer_size:
                                yield {
                                    'code': 200,
                                    'data': {'text': ''.join(buffer)}
                                }
                                buffer = []
                
                except Exception as ai_error:
                    # AI调用异常，尝试非流式降级
                    try:
                        fallback_result = self.ai_model.chat(
                            messages,
                            stream=False,
                            temperature=0.7,
                            max_tokens=4000
                        )
                        yield {
                            'code': 200,
                            'data': {'text': fallback_result}
                        }
                    except Exception as fallback_error:
                        yield self.create_error_response(f"AI模型调用失败: {str(fallback_error)}")
                        return
                
                # 发送剩余内容
                if buffer:
                    yield {
                        'code': 200,
                        'data': {'text': ''.join(buffer)}
                    }

                # 添加换行
                yield {
                    'code': 200,
                    'data': {'text': "\n\n"}
                }
                
                # 更新分析上下文
                analysis_context = self._update_analysis_context(
                    analysis_context,
                    section,
                    buffer
                )
                    
        except Exception as e:
            print(f"报告生成失败: {str(e)}")
            traceback.print_exc()
            yield self.create_error_response(f"报告生成失败: {str(e)}")

    def _build_system_prompt(self, section, context):
        """构建系统提示词"""
        try:
            # 获取主体信息
            subject_info = context.get('subject_info', {})
            subject_name = subject_info.get('name', '未知主体')
            subject_type = subject_info.get('type', '未知类型')
            
            # 获取时间范围
            time_stats = context.get('time_stats', {})
            duration_days = time_stats.get('duration_days', 0)
            
            # 基础提示词
            base_prompt = f"""你是一个专业的舆情分析专家。请从{subject_type}「{subject_name}」的角度，对近{duration_days}天的微博平台数据进行分析。

分析原则：
1. 始终站在主体的立场思考问题
2. 重点关注对主体形象和发展的影响
3. 分析要有前瞻性和战略性
4. 建议要具有可操作性和针对性

写作要求：
1. 分析要有深度，避免泛泛而谈
2. 每个观点必须有数据支撑
3. 语言要专业准确
4. 结构要清晰有序
5. 善用emoji做分类
6. 重要信息要突出
7. 注意段落换行和格式
8. 避免内容重复
9. 使用简洁的表达方式
10. 确保分析的连贯性

写作风格：
1. 保持客观专业的语气
2. 使用准确的专业术语
3. 数据分析要简明扼要
4. 结论和建议要清晰明确
5. 适当使用图表类比
6. 注意逻辑层次分明"""

            # 根据部分类型添加特定要求
            if section['type'] == 'overview':
                base_prompt += """

概述部分要求：
1. 快速抓住核心问题
2. 突出主要发现
3. 数据要简明扼要
4. 为后续分析铺垫
5. 重点关注热点话题和关键词
6. 突出时间趋势和发展脉络
7. 总结传播特征和影响范围
8. 点明主要风险和机遇"""

            elif section['type'] == 'analysis':
                base_prompt += """

分析部分要求：
1. 深入挖掘数据背后的原因
2. 多角度分析问题
3. 注意分析的逻辑性
4. 突出关键发现
5. 分析用户画像和行为特征
6. 挖掘传播规律和影响因素
7. 分析意见领袖的影响力
8. 评估传播效果和范围
9. 识别关键传播节点
10. 总结传播特征和规律"""

            elif section['type'] == 'risk':
                base_prompt += """

风险评估要求：
1. 全面识别风险点
2. 评估风险等级
3. 分析风险影响
4. 提供预警建议
5. 评估潜在危机
6. 分析风险演变趋势
7. 预判风险扩散路径
8. 评估风险处置难度
9. 分析风险关联性
10. 提供风险预警指标"""

            elif section['type'] == 'strategy':
                base_prompt += """

策略建议要求：
1. 建议要具体可行
2. 分清轻重缓急
3. 考虑资源约束
4. 注重实操性
5. 提供短中长期策略
6. 给出明确的行动方案
7. 制定应急预案
8. 设计监测指标
9. 明确责任分工
10. 设置时间节点"""

            return base_prompt
            
        except Exception as e:
            print(f"构建系统提示词失败: {str(e)}")
            traceback.print_exc()
            return "构建系统提示词失败"

    def _build_section_prompt(self, section, context):
        """构建部分提示词"""
        try:
            # 获取主体信息
            subject_info = context.get('subject_info', {})
            subject_name = subject_info.get('name', '未知主体')
            
            # 获取数据统计
            stats = context.get('data_summary', {})
            total_comments = stats.get('total_comments', 0)
            total_interactions = stats.get('total_interactions', 0)
            avg_interactions = stats.get('avg_interactions', 0)
            
            # 获取情感分析
            sentiment = context.get('sentiment_analysis', {})
            positive_ratio = sentiment.get('positive_ratio', 0)
            negative_ratio = sentiment.get('negative_ratio', 0)
            neutral_ratio = sentiment.get('neutral_ratio', 0)
            sentiment_trend = sentiment.get('sentiment_trend', '未知')
            
            # 获取时间统计
            time_stats = context.get('time_stats', {})
            duration_days = time_stats.get('duration_days', 0)
            peak_hours = time_stats.get('peak_hours', {})
            daily_stats = time_stats.get('daily_distribution', {})
            
            # 获取关键内容
            key_contents = context.get('key_contents', {})
            top_contents = key_contents.get('top_contents', [])
            negative_contents = key_contents.get('negative_contents', [])
            positive_contents = key_contents.get('positive_contents', [])
            
            # 构建内容样本
            def format_content(content, include_user=True):
                """格式化单条内容"""
                result = []
                result.append(f"- 互动量：{content.get('影响力', 0):.0f}")
                result.append(f"  转发：{content.get('转发数', 0)}")
                result.append(f"  评论：{content.get('评论数', 0)}")
                result.append(f"  点赞：{content.get('点赞数', 0)}")
                result.append(f"  情感：{content.get('情感倾向', 0):.2f}")
                if include_user:
                    result.append(f"  作者：{content.get('微博作者', '未知')}")
                result.append(f"  内容：{content.get('微博内容', '')}")
                return '\n'.join(result)

            # 高影响力内容（展示全部）
            top_content_samples = []
            top_content_samples.append("\n🔥 高影响力内容：")
            for i, content in enumerate(top_contents, 1):
                if content.get('微博内容'):
                    top_content_samples.append(f"\n[Top {i}]\n{format_content(content)}")

            # 典型正面内容（展示全部）
            positive_content_samples = []
            positive_content_samples.append("\n😊 典型正面内容：")
            for i, content in enumerate(positive_contents, 1):
                if content.get('微博内容'):
                    positive_content_samples.append(f"\n[Positive {i}]\n{format_content(content)}")

            # 典型负面内容（展示全部）
            negative_content_samples = []
            negative_content_samples.append("\n😟 典型负面内容：")
            for i, content in enumerate(negative_contents, 1):
                if content.get('微博内容'):
                    negative_content_samples.append(f"\n[Negative {i}]\n{format_content(content)}")

            # 时间分布统计
            time_distribution = []
            time_distribution.append("\n📅 时间分布统计：")
            if daily_stats:
                time_distribution.append("\n每日数据：")
                for date, stats in list(daily_stats.items())[:10]:  # 展示前10天的数据
                    time_distribution.append(
                        f"- {date}："
                        f"发帖{stats.get(('情感倾向', 'count'), 0)}条，"
                        f"转发{stats.get(('转发数', 'sum'), 0)}，"
                        f"评论{stats.get(('评论数', 'sum'), 0)}，"
                        f"点赞{stats.get(('点赞数', 'sum'), 0)}，"
                        f"平均情感{stats.get(('情感倾向', 'mean'), 0):.2f}"
                    )
            
            # 基础提示词
            base_prompt = f"""请分析「{subject_name}」的舆情数据：

数据概要：
- 监测天数：{duration_days} 天
- 总评论量：{total_comments} 条
- 总互动量：{total_interactions} 次
- 平均互动：{avg_interactions:.2f} 次/条

情感分布：
- 正面比例：{positive_ratio:.1f}%
- 负面比例：{negative_ratio:.1f}%
- 中性比例：{neutral_ratio:.1f}%
- 情感趋势：{sentiment_trend}

传播特征：
- 高峰时段：{', '.join(f"{hour}时" for hour in peak_hours.keys())}
- 最高互动：{max([c.get('影响力', 0) for c in top_contents] or [0]):.0f}

{chr(10).join(time_distribution)}

{chr(10).join(top_content_samples)}

{chr(10).join(positive_content_samples)}

{chr(10).join(negative_content_samples)}

"""

            # 根据部分类型添加特定内容
            if section['type'] == 'overview':
                base_prompt += """请基于以上全部数据，提供全面的舆情概述，包括：
1. 整体态势分析
   - 总体舆情走向
   - 关键数据指标
   - 主要传播特征
   - 传播效果评估

2. 核心发现
   - 热点话题分析
   - 重要事件梳理
   - 关键词提取
   - 传播规律总结

3. 趋势研判
   - 发展趋势预测
   - 潜在风险识别
   - 关注重点建议
   - 未来走向预判"""

            elif section['type'] == 'analysis':
                base_prompt += """请基于以上全部数据，进行深入分析，包括：
1. 情感分布分析
   - 情感占比分析
   - 情感变化趋势
   - 情感影响因素
   - 情感分布特征

2. 内容主题分析
   - 核心话题梳理
   - 话题演变脉络
   - 关键词分析
   - 内容特征总结

3. 传播特征分析
   - 传播路径分析
   - 传播规律总结
   - 影响力评估
   - 传播效果分析

4. 用户画像分析
   - 用户类型分布
   - 用户行为特征
   - 意见领袖分析
   - 用户互动模式"""

            elif section['type'] == 'risk':
                base_prompt += """请基于以上全部数据，评估各类风险，包括：
1. 声誉风险
   - 品牌形象影响
   - 公众信任度
   - 负面舆情扩散
   - 品牌认知变化

2. 传播风险
   - 信息失真程度
   - 谣言传播风险
   - 舆论发酵趋势
   - 信息控制难度

3. 危机风险
   - 潜在危机点
   - 危机升级可能
   - 应对难度评估
   - 危机处置建议

4. 潜在风险
   - 长期影响评估
   - 隐藏风险识别
   - 风险演变预测
   - 预防措施建议"""

            elif section['type'] == 'strategy':
                base_prompt += """请基于以上全部数据，提供详细的应对建议，包括：
1. 短期策略（1-2周）
   - 即时响应方案
   - 舆情引导策略
   - 危机处置建议
   - 重点任务分解

2. 中期策略（1-3月）
   - 形象修复计划
   - 传播策略优化
   - 预防机制建设
   - 管理流程完善

3. 长期策略（3-12月）
   - 品牌建设规划
   - 舆情管理体系
   - 持续优化建议
   - 长效机制建设

4. 具体行动建议
   - 优先级排序
   - 资源配置建议
   - 执行时间表
   - 效果评估指标"""

            return base_prompt
            
        except Exception as e:
            print(f"构建部分提示词失败: {str(e)}")
            traceback.print_exc()
            return "构建部分提示词失败"

    def preprocess_data(self):
        """预处理数据"""
        try:
            # 读取数据
            df = pd.read_csv(self.csv_path)
            if len(df) == 0:
                print("数据为空")
                return False
                
            # 清理数据
            df = self._clean_data(df)
            
            # 计算基础统计
            basic_stats = {
                'total_comments': len(df),
                'total_interactions': df['转发数'].sum() + df['评论数'].sum() + df['点赞数'].sum(),
                'avg_interactions': (df['转发数'].mean() + df['评论数'].mean() + df['点赞数'].mean()) / 3
            }
            
            # 计算情感分析
            sentiment_stats = {
                'positive_ratio': len(df[df['情感倾向'] > 0.7]) / len(df) * 100,
                'negative_ratio': len(df[df['情感倾向'] < 0.3]) / len(df) * 100,
                'neutral_ratio': len(df[(df['情感倾向'] >= 0.3) & (df['情感倾向'] <= 0.7)]) / len(df) * 100,
                'avg_sentiment': df['情感倾向'].mean(),
                'sentiment_trend': self._calculate_sentiment_trend(df)
            }
            
            # 计算时间分布
            time_stats = self._calculate_time_distribution(df)
            
            # 提取关键内容
            key_contents = self._extract_key_contents(df)
            
            # 识别主体
            subject_info = self._identify_subject(df)
            
            # 缓存处理后的数据
            self.data_cache = {
                'basic_stats': basic_stats,
                'sentiment_analysis': sentiment_stats,
                'time_distribution': time_stats,
                'key_contents': key_contents,
                'subject_info': subject_info,
                'processed_df': df
            }
            
            return True
            
        except Exception as e:
            print(f"数据预处理失败: {str(e)}")
            traceback.print_exc()
            return False

    def _clean_data(self, df):
        """清理数据"""
        try:
            # 复制数据框
            cleaned_df = df.copy()
            
            # 处理数值列
            numeric_columns = ['转发数', '评论数', '点赞数']
            for col in numeric_columns:
                if col in cleaned_df.columns:
                    cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
            
            # 处理情感倾向列
            cleaned_df['情感倾向'] = pd.to_numeric(cleaned_df['情感倾向'], errors='coerce')
            cleaned_df['情感倾向'] = cleaned_df['情感倾向'].clip(0, 1)
            cleaned_df['情感倾向'] = cleaned_df['情感倾向'].fillna(0.5)
            
            # 处理时间列
            if '发布时间' in cleaned_df.columns:
                cleaned_df['发布时间'] = pd.to_datetime(cleaned_df['发布时间'], errors='coerce')
                cleaned_df = cleaned_df.dropna(subset=['发布时间'])
            
            # 处理文本列
            text_columns = ['微博内容', '微博作者']
            for col in text_columns:
                if col in cleaned_df.columns:
                    cleaned_df[col] = cleaned_df[col].fillna('')
                    cleaned_df[col] = cleaned_df[col].astype(str)
                    cleaned_df[col] = cleaned_df[col].apply(self._clean_text)
            
            # 删除重复行
            cleaned_df = cleaned_df.drop_duplicates()
            
            # 计算影响力分数
            cleaned_df['影响力'] = (
                cleaned_df['转发数'] * 0.4 + 
                cleaned_df['评论数'] * 0.3 + 
                cleaned_df['点赞数'] * 0.3
            )
            
            # 按影响力排序
            cleaned_df = cleaned_df.sort_values('影响力', ascending=False)
            
            # 重置索引
            cleaned_df = cleaned_df.reset_index(drop=True)
            
            return cleaned_df
            
        except Exception as e:
            print(f"数据清理失败: {str(e)}")
            traceback.print_exc()
            return df

    def _clean_text(self, text):
        """清理文本"""
        try:
            if not isinstance(text, str):
                return ''
            
            # 移除HTML标签
            text = re.sub(r'<[^>]+>', '', text)
            
            # 移除URL
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            
            # 移除表情符号
            text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
            
            # 移除特殊字符
            text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、；：""''（）【】《》\\s]', '', text)
            
            # 移除多余空白
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text
            
        except Exception as e:
            print(f"文本清理失败: {str(e)}")
            traceback.print_exc()
            return text

    def _calculate_sentiment_trend(self, df):
        """计算情感趋势"""
        try:
            if '发布时间' not in df.columns:
                return '无法计算'
                
            # 按时间排序
            df = df.sort_values('发布时间')
            
            # 计算移动平均
            window_size = min(len(df) // 10, 100)  # 使用10%的数据或最多100条
            if window_size < 2:
                return '数据量不足'
                
            df['情感移动平均'] = df['情感倾向'].rolling(window=window_size).mean()
            
            # 计算趋势
            start_avg = df['情感移动平均'].iloc[window_size:window_size*2].mean()
            end_avg = df['情感移动平均'].iloc[-window_size:].mean()
            
            # 判断趋势
            change_rate = (end_avg - start_avg) / start_avg if start_avg > 0 else 0
            
            if change_rate > 0.1:
                return '情感向好'
            elif change_rate < -0.1:
                return '情感转差'
            else:
                return '情感稳定'
                
        except Exception as e:
            print(f"计算情感趋势失败: {str(e)}")
            traceback.print_exc()
            return '计算失败'

    def _calculate_time_distribution(self, df):
        """计算时间分布"""
        try:
            if '发布时间' not in df.columns:
                return {}
                
            # 计算时间范围
            time_range = {
                'start_time': df['发布时间'].min(),
                'end_time': df['发布时间'].max(),
                'duration_days': (df['发布时间'].max() - df['发布时间'].min()).days
            }
            
            # 计算每日分布
            daily_stats = df.groupby(df['发布时间'].dt.date).agg({
                '转发数': 'sum',
                '评论数': 'sum',
                '点赞数': 'sum',
                '情感倾向': ['mean', 'count']
            }).to_dict()
            
            # 计算高峰时段
            hourly_stats = df.groupby(df['发布时间'].dt.hour).size()
            peak_hours = hourly_stats.nlargest(3)
            
            # 计算周期分布
            weekday_stats = df.groupby(df['发布时间'].dt.dayofweek).size()
            
            return {
                'time_range': time_range,
                'daily_stats': daily_stats,
                'peak_hours': peak_hours.to_dict(),
                'weekday_stats': weekday_stats.to_dict()
            }
            
        except Exception as e:
            print(f"计算时间分布失败: {str(e)}")
            traceback.print_exc()
            return {}

    def _extract_key_contents(self, df):
        """提取关键内容"""
        try:
            # 提取高影响力内容
            top_contents = df.nlargest(10, '影响力')[
                ['微博内容', '微博作者', '转发数', '评论数', '点赞数', '情感倾向', '影响力']
            ].to_dict('records')
            
            # 提取典型负面内容
            negative_contents = df[df['情感倾向'] < 0.3].nlargest(10, '影响力')[
                ['微博内容', '微博作者', '转发数', '评论数', '点赞数', '情感倾向', '影响力']
            ].to_dict('records')
            
            # 提取典型正面内容
            positive_contents = df[df['情感倾向'] > 0.7].nlargest(10, '影响力')[
                ['微博内容', '微博作者', '转发数', '评论数', '点赞数', '情感倾向', '影响力']
            ].to_dict('records')
            
            return {
                'top_contents': top_contents,
                'negative_contents': negative_contents,
                'positive_contents': positive_contents
            }
            
        except Exception as e:
            print(f"提取关键内容失败: {str(e)}")
            traceback.print_exc()
            return {}

    def _identify_subject(self, df):
        """识别主体"""
        try:
            # 提取文本内容
            text = ' '.join(df['微博内容'].astype(str))
            
            # 分词
            words = jieba.lcut(text)
            word_counts = Counter(words)
            
            # 加载停用词
            stop_words = self._load_stop_words()
            
            # 过滤停用词和短词
            filtered_words = {
                word: count 
                for word, count in word_counts.items()
                if len(word) > 1 and word not in stop_words
            }
            
            # 获取词性标注
            words_with_flags = []
            for word, count in filtered_words.items():
                flags = jieba.posseg.cut(word)
                for w, flag in flags:
                    words_with_flags.append((w, flag, count))
            
            # 评分规则
            def score_word(word, flag, count):
                base_score = count
                
                # 根据词性加权
                weights = {
                    'nt': 2.0,  # 机构名
                    'nr': 1.8,  # 人名
                    'nz': 1.5,  # 其他专名
                    'n': 1.0,   # 普通名词
                }
                weight = weights.get(flag, 0.5)
                
                # 根据词长加权
                length_weight = min(len(word) / 2, 2)
                
                return base_score * weight * length_weight
            
            # 计算得分
            scored_words = [
                {
                    'word': word,
                    'flag': flag,
                    'count': count,
                    'score': score_word(word, flag, count)
                }
                for word, flag, count in words_with_flags
            ]
            
            # 按得分排序
            scored_words.sort(key=lambda x: x['score'], reverse=True)
            
            # 选择最佳主体
            if scored_words:
                best_word = scored_words[0]
                subject_type = self._determine_subject_type(best_word['flag'])
                
                # 计算置信度
                if len(scored_words) > 1:
                    confidence = min(
                        (best_word['score'] - scored_words[1]['score']) / best_word['score'],
                        1.0
                    )
                else:
                    confidence = 1.0
                
                return {
                    'name': best_word['word'],
                    'type': subject_type,
                    'frequency': best_word['count'],
                    'confidence': confidence
                }
            
                return {
                    'name': '未知主体',
                    'type': '未知',
                'frequency': 0,
                'confidence': 0
                }
            
        except Exception as e:
            print(f"主体识别失败: {str(e)}")
            traceback.print_exc()
            return {
                'name': '识别失败',
                'type': '未知',
                'frequency': 0,
                'confidence': 0
            }

    def _load_stop_words(self):
        """加载停用词"""
        try:
            # 基础停用词
            stop_words = {
                '的', '了', '和', '是', '就', '都', '而', '及', '与', '着',
                '或', '一个', '没有', '我们', '你们', '他们', '它们', '这个',
                '那个', '这些', '那些', '自己', '什么', '哪些', '如此', '这样',
                '那样', '怎样', '这么', '那么', '怎么', '一些', '有些', '常常',
                '常年', '一直', '总是', '经常'
            }
            
            # 时间词
            stop_words.update({
                '今天', '明天', '昨天', '前天', '后天', '上午', '下午', '晚上',
                '早上', '凌晨', '中午', '傍晚', '今年', '明年', '去年', '前年',
                '后年', '上个月', '下个月', '这个月'
            })
            
            # 数量词
            stop_words.update({
                '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
                '百', '千', '万', '亿', '第一', '第二', '第三', '第四', '第五',
                '几个', '多个', '少数', '多数', '若干'
            })
            
            # 语气词
            stop_words.update({
                '啊', '哦', '呢', '吧', '啦', '呀', '哈', '嘿', '哎', '唉',
                '嗯', '哼', '哟', '喂', '嘛', '呐', '呵', '嗨', '嘘', '嗬'
            })
            
            return stop_words
            
        except Exception as e:
            print(f"加载停用词失败: {str(e)}")
            traceback.print_exc()
            return set()

    def _determine_subject_type(self, flag):
        """确定主体类型"""
        try:
            if flag.startswith('nt'):
                return '机构'
            elif flag.startswith('nr'):
                return '个人'
            elif flag.startswith('ns'):
                return '地点'
            elif flag.startswith('nz'):
                return '专有名词'
            else:
                return '其他'
                
        except Exception as e:
            print(f"确定主体类型失败: {str(e)}")
            traceback.print_exc()
            return '未知'

    def _build_analysis_context(self):
        """构建分析上下文"""
        try:
            # 获取主体信息
            subject_info = self.data_cache.get('subject_info', {})
            
            # 获取基础统计
            basic_stats = self.data_cache.get('basic_stats', {})
            
            # 获取情感分析
            sentiment_analysis = self.data_cache.get('sentiment_analysis', {})
            
            # 获取时间分布
            time_distribution = self.data_cache.get('time_distribution', {})
            
            # 获取关键内容
            key_contents = self.data_cache.get('key_contents', {})
            
            # 构建上下文
            context = {
                'subject_info': subject_info,
                'data_summary': {
                    'total_comments': basic_stats.get('total_comments', 0),
                    'total_interactions': basic_stats.get('total_interactions', 0),
                    'avg_interactions': basic_stats.get('avg_interactions', 0)
                },
                'sentiment_analysis': {
                    'positive_ratio': sentiment_analysis.get('positive_ratio', 0),
                    'negative_ratio': sentiment_analysis.get('negative_ratio', 0),
                    'neutral_ratio': sentiment_analysis.get('neutral_ratio', 0),
                    'avg_sentiment': sentiment_analysis.get('avg_sentiment', 0.5),
                    'sentiment_trend': sentiment_analysis.get('sentiment_trend', '未知')
                },
                'time_stats': {
                    'duration_days': time_distribution.get('time_range', {}).get('duration_days', 0),
                    'peak_hours': time_distribution.get('peak_hours', {}),
                    'daily_distribution': time_distribution.get('daily_stats', {})
                },
                'key_contents': {
                    'top_contents': key_contents.get('top_contents', [])[:5],
                    'negative_contents': key_contents.get('negative_contents', [])[:5],
                    'positive_contents': key_contents.get('positive_contents', [])[:5]
                },
                'generation_state': {
                    'completed_sections': [],
                    'current_section': None
                },
                'analysis_results': {}  # 添加缺失的analysis_results键
            }
            
            return context
            
        except Exception as e:
            print(f"构建分析上下文失败: {str(e)}")
            traceback.print_exc()
            return {}

    def _update_analysis_context(self, context, section, content):
        """更新分析上下文"""
        try:
            # 确保必要的键存在
            if 'analysis_results' not in context:
                context['analysis_results'] = {}
            if 'generation_state' not in context:
                context['generation_state'] = {'completed_sections': [], 'current_section': None}

            # 保存当前部分的结果
            context['analysis_results'][section['name']] = ''.join(content)

            # 更新生成状态
            context['generation_state']['completed_sections'] = context['generation_state'].get('completed_sections', []) + [section['name']]
            context['generation_state']['current_section'] = None
            
            return context
            
        except Exception as e:
            print(f"更新分析上下文失败: {str(e)}")
            traceback.print_exc()
            return context

    def create_error_response(self, message):
        """创建错误响应"""
        return {
            'code': 500,
            'msg': message,
            'data': {'text': f"错误: {message}"}
        }
