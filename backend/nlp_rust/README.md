# NLP Rust 模块

Rust 实现的文本处理模块，为舆情分析系统提供高性能的文本清洗和词频统计功能。

## 功能

- **clean_text(text: str) -> str**: 清理单个文本
  - 移除 URL、@用户、话题标签、表情符号、HTML 标签
  - 规范化空白字符
  - 性能提升：3-5倍（相比 Python 正则）

- **clean_texts(texts: List[str]) -> List[str]**: 批量清理文本

- **word_frequency(words: List[str], stopwords: List[str], min_length: int) -> Dict[str, int]**: 词频统计
  - 过滤停用词
  - 仅保留包含中文的词
  - 使用 AHashMap 加速

## 构建

```bash
# 安装 maturin（如果未安装）
pip install maturin

# 开发模式构建（用于测试）
cd backend/nlp_rust
maturin develop --release

# 生产构建（生成 wheel）
maturin build --release
```

## 使用

```python
import nlp_rust

# 清理文本
cleaned = nlp_rust.clean_text("这是一条包含 http://example.com 的微博 @用户")
# 输出: "这是一条包含  的微博"

# 批量清理
texts = ["文本1 http://...", "文本2 #话题#"]
cleaned_texts = nlp_rust.clean_texts(texts)

# 词频统计（假设已用 jieba 分词）
words = ["舆情", "分析", "系统", "的", "是", "舆情"]
stopwords = ["的", "是", "在"]
freq = nlp_rust.word_frequency(words, stopwords, min_length=2)
# 输出: {"舆情": 2, "分析": 1, "系统": 1}
```

## 集成到 nlp_analyzer.py

模块已设计为可选依赖，如果 Rust 模块不可用，会自动降级到 Python 实现：

```python
try:
    import nlp_rust
    USE_RUST = True
except ImportError:
    USE_RUST = False

class NLPAnalyzer:
    @staticmethod
    def clean_text(text: str) -> str:
        if USE_RUST:
            return nlp_rust.clean_text(text)
        else:
            # Python 实现作为 fallback
            return _clean_text_python(text)
```

## 性能基准测试

见 `benchmark.py`，测试 10 万条文本的清洗性能。

## 注意事项

1. **不包含分词**：Rust 模块不实现中文分词（jieba 已经是 C 扩展，够快了）
2. **可选依赖**：确保应用在 Rust 模块缺失时仍能运行
3. **跨平台编译**：需要在 Windows/macOS/Linux 分别编译
