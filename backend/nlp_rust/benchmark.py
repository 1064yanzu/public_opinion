"""
性能基准测试：对比 Python 和 Rust 实现的文本清洗性能
"""
import time
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import nlp_rust
    RUST_AVAILABLE = True
    print("✓ Rust 模块已加载")
except ImportError:
    RUST_AVAILABLE = False
    print("✗ Rust 模块未找到，仅测试 Python 实现")

from app.services.nlp_analyzer import NLPAnalyzer

# 测试数据
TEST_TEXTS = [
    "这是一条包含 http://example.com 的微博 @用户名 #热门话题# [emoji]",
    "今天天气真不错，推荐大家去 https://weather.com 查看详情 @weatherbot",
    "<p>HTML 标签测试</p> 包含多余   空白   的文本",
    "纯中文测试没有特殊字符",
    "@user1 @user2 #多个话题# #话题2# http://link1.com http://link2.com",
] * 20000  # 10 万条文本


def benchmark_python():
    """测试 Python 实现"""
    print("\n=== Python 实现 ===")
    start = time.time()

    for text in TEST_TEXTS:
        NLPAnalyzer.clean_text(text)

    elapsed = time.time() - start
    print(f"耗时: {elapsed:.3f} 秒")
    print(f"速度: {len(TEST_TEXTS) / elapsed:.0f} 条/秒")
    return elapsed


def benchmark_rust():
    """测试 Rust 实现"""
    if not RUST_AVAILABLE:
        print("\nRust 模块未安装，跳过测试")
        return None

    print("\n=== Rust 实现 ===")
    start = time.time()

    for text in TEST_TEXTS:
        nlp_rust.clean_text(text)

    elapsed = time.time() - start
    print(f"耗时: {elapsed:.3f} 秒")
    print(f"速度: {len(TEST_TEXTS) / elapsed:.0f} 条/秒")
    return elapsed


def benchmark_rust_batch():
    """测试 Rust 批量实现"""
    if not RUST_AVAILABLE:
        return None

    print("\n=== Rust 批量实现 ===")
    start = time.time()

    nlp_rust.clean_texts(TEST_TEXTS)

    elapsed = time.time() - start
    print(f"耗时: {elapsed:.3f} 秒")
    print(f"速度: {len(TEST_TEXTS) / elapsed:.0f} 条/秒")
    return elapsed


if __name__ == "__main__":
    print(f"测试数据量: {len(TEST_TEXTS):,} 条文本\n")

    python_time = benchmark_python()
    rust_time = benchmark_rust()
    rust_batch_time = benchmark_rust_batch()

    if rust_time:
        print(f"\n=== 性能对比 ===")
        speedup = python_time / rust_time
        print(f"Rust 单条加速比: {speedup:.2f}x")

        if rust_batch_time:
            batch_speedup = python_time / rust_batch_time
            print(f"Rust 批量加速比: {batch_speedup:.2f}x")

            if speedup >= 3.0:
                print("\n✓ 性能提升达标（>= 3x），建议集成到生产环境")
            elif speedup >= 2.0:
                print("\n⚠ 性能提升中等（2-3x），可选集成")
            else:
                print("\n✗ 性能提升不足（< 2x），不建议集成")
