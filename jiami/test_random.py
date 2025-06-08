import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import chi2, norm, entropy
import os
import sys
import math
import traceback

os.makedirs('./result', exist_ok=True)


class IncrementalStats:
    """增量计算统计量的类"""

    def __init__(self):
        self.count = 0
        self.sum = 0.0
        self.sum_sq = 0.0
        self.prev = None
        self.runs = 1

        self.window = []
        self.max_window_size = 5


        self.levels = 3
        self.derivative_counts = []
        self.current_level = []

    def update(self, digit):
        """更新统计量"""
        # 基本计数
        self.count += 1
        self.sum += digit
        self.sum_sq += digit * digit

        if self.prev is not None and digit != self.prev:
            self.runs += 1
        self.prev = digit

        self.window.append(digit)
        if len(self.window) > self.max_window_size:
            self.window.pop(0)


        if not self.current_level:
            self.current_level = [digit]
        else:

            self.current_level.append(digit)


            if len(self.current_level) > 1:
                derivative = self.current_level[-2] ^ self.current_level[-1]


                if len(self.derivative_counts) < len(self.current_level) - 1:
                    self.derivative_counts.append({})


                level_index = len(self.current_level) - 2
                if level_index < self.levels:
                    if level_index >= len(self.derivative_counts):
                        self.derivative_counts.append({})

                    self.derivative_counts[level_index][derivative] = \
                        self.derivative_counts[level_index].get(derivative, 0) + 1

    def finalize(self):
        """完成计算并返回统计量"""
        n = self.count
        mean = self.sum / n if n > 0 else 0
        total_variance = self.sum_sq - n * mean * mean

        apen = self.calculate_approximate_entropy()


        binary_derivative_result = self.analyze_binary_derivatives(n)

        return {
            'n': n,
            'mean': mean,
            'total_variance': total_variance,
            'runs': self.runs,
            'apen': apen,
            'binary_derivative': binary_derivative_result
        }

    def calculate_approximate_entropy(self):
        """计算近似熵"""
        n = len(self.window)
        if n < 100:
            return 0.0, 1.0


        m = 3
        patterns = {}
        for i in range(n - m + 1):
            pattern = tuple(self.window[i:i + m])
            patterns[pattern] = patterns.get(pattern, 0) + 1

        phi_m = 0.0
        for count in patterns.values():
            p = count / (n - m + 1)
            phi_m += p * math.log(p + 1e-10)


        m1 = m + 1
        if n < m1 + 1:
            return phi_m, 1.0

        patterns_m1 = {}
        for i in range(n - m1 + 1):
            pattern = tuple(self.window[i:i + m1])
            patterns_m1[pattern] = patterns_m1.get(pattern, 0) + 1

        # 计算Φ(m+1)
        phi_m1 = 0.0
        for count in patterns_m1.values():
            p = count / (n - m1 + 1)
            phi_m1 += p * math.log(p + 1e-10)

        # 近似熵
        apen = phi_m - phi_m1

        # 计算p值 (简化的估计)
        sd = np.sqrt(14 / n)
        z = apen / sd
        p_value = 2 * (1 - norm.cdf(np.abs(z)))

        return apen, p_value

    def analyze_binary_derivatives(self, n):
        """分析二元导数"""
        p_values = []
        max_level = min(self.levels, len(self.derivative_counts))

        for level in range(max_level):
            level_counts = self.derivative_counts[level]
            total = sum(level_counts.values())
            if total < 100:
                continue

            # 计算卡方统计量
            obs = np.zeros(16)
            for digit, count in level_counts.items():
                if digit < 16:  # 确保在0-15范围内
                    obs[digit] = count

            expected = np.full(16, total / 16)
            chi2_stat = np.sum((obs - expected) ** 2 / expected)
            df = 15
            p_value = 1 - chi2.cdf(chi2_stat, df)
            p_values.append(p_value)

        # 组合p值
        if p_values:
            chi_val = -2 * sum(np.log(p) for p in p_values)
            df = 2 * len(p_values)
            combined_p = 1 - chi2.cdf(chi_val, df)
            return p_values, combined_p

        return [], 1.0


def process_large_file(filename, chunk_size=1000000):
    """分块处理大型文件"""
    stats = IncrementalStats()

    with open(filename, 'r') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break

            for char in chunk:
                if char in '0123456789':
                    digit = int(char)
                    stats.update(digit)

    return stats.finalize()
def analyze_sequence(filename, output_file):
    """分析数字序列的随机性并生成报告"""
    try:
        print("开始分析大型序列 (分块处理)...")
        results = process_large_file(filename)

        if results['n'] == 0:
            return "错误: 文件中没有找到有效数字"

        n = results['n']

        print("处理数字频率统计...")
        counts = np.zeros(10)
        with open(filename, 'r') as f:
            while True:
                chunk = f.read(1000000)
                if not chunk:
                    break
                for char in chunk:
                    if char in '0123456789':
                        digit = int(char)
                        counts[digit] += 1

        expected = n / 10
        autocorr = {}

        print("基本统计计算完成, 执行高级分析...")

        # 1. 卡方检验
        chi2_stat = np.sum((counts - expected) ** 2 / expected)
        df = 9
        p_value_chi2 = 1 - chi2.cdf(chi2_stat, df)

        # 2. 游程检验
        runs = results['runs']
        p_is = counts / n
        expected_runs = 1 + (n - 1) * (1 - np.sum(p_is ** 2))

        variance = (n - 1) * (np.sum(p_is ** 2) - np.sum(p_is ** 3)
                              - (np.sum(p_is ** 2)) ** 2 + np.sum(p_is ** 4))

        if variance <= 0:
            p_value_runs = 1.0
        else:
            z = (runs - expected_runs) / np.sqrt(variance)
            p_value_runs = 2 * (1 - norm.cdf(abs(z)))

        # 3. 序列复杂性检测 (近似熵)
        apen, apen_p = results['apen']

        # 4. 二元导数检测
        binary_p_values, binary_combined_p = results['binary_derivative']

        # 生成可视化图表
        plot_path = './result'

        # 生成报告
        report = [
            "=" * 70,
            "大型数字序列随机性分析报告",
            "=" * 70,
            f"分析文件: {filename}",
            f"序列长度: {n:,} 个数字",
            f"分析时间: {np.datetime64('now')}",
            "",
            "[1] 各数字出现频率",
            f"- 总计: {n:,} 个数字",
            f"- 最高频率: 数字 {np.argmax(counts)} ({counts[np.argmax(counts)]:,}, {counts[np.argmax(counts)] / n:.4%})",
            f"- 最低频率: 数字 {np.argmin(counts)} ({counts[np.argmin(counts)]:,}, {counts[np.argmin(counts)] / n:.4%})",
            ""
        ]

        for digit, count in enumerate(counts):
            deviation = (count - expected) / expected * 100
            report.append(f"- 数字 {digit}: {count:,} 次 ({count / n:.4%}) | 偏离: {deviation:+.2f}%")

        report.extend([
            "",
            "[2] 卡方检验 (均匀性)",
            f"- 卡方统计量: {chi2_stat:.4f}",
            f"- 自由度: {df}",
            f"- P值: {p_value_chi2:.4e}",
            f"- 结论: {'满足均匀性 (P>0.05)' if p_value_chi2 > 0.05 else '不满足均匀性'}",
            "",
            "[3] 游程检验 (模式检测)",
            f"- 观测游程数: {runs:,}",
            f"- 期望游程数: {expected_runs:.0f}",
            f"- P值: {p_value_runs:.4e}",
            f"- 结论: {'随机模式' if p_value_runs > 0.05 else '非随机模式'}",
            "",
            "[4] 序列复杂性检测 (近似熵)",
            f"- 近似熵值: {apen:.6f}",
            f"- P值: {apen_p:.4e}",
            f"- 结论: {'复杂性高(随机)' if apen_p > 0.05 else '复杂性低(有模式)'}",
            "",
            "[5] 二元导数检测 (周期性模式)",
        ])

        for level, p in enumerate(binary_p_values):
            report.append(f"- 层级 {level + 1} p值: {p:.4e}")

        report.append(f"- 组合p值: {binary_combined_p:.4e}")
        report.append(f"- 结论: {'无周期性模式' if binary_combined_p > 0.05 else '检测到周期性模式'}")

        # 综合结论
        tests_passed = sum([
            p_value_chi2 > 0.05,
            p_value_runs > 0.05,
            apen_p > 0.05,
            binary_combined_p > 0.05
        ])

        if tests_passed == 4:
            conclusion = "序列表现出良好的随机性特征"
        elif tests_passed >= 2:
            conclusion = "序列表现出一定随机性，但有轻微异常"
        else:
            conclusion = "序列不符合随机性要求"

        report.append(conclusion)
        report.append("=" * 70)

        # 写入报告文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(report))

        return "\n".join(report)

    except Exception as e:
        return f"分析时发生错误: {str(e)}\n{traceback.format_exc()}"


def main():
    """主函数"""
    for i in range(10):

        input_file = f"./en/keys/key{i}.txt"
        output_file = f"./result/test{i}.txt"

        print("=" * 70)
        print("数字序列随机性分析工具 ")
        print("=" * 70)
        print(f"输入文件: {input_file}")
        print(f"输出报告: {output_file}")
        print(f"图表目录: ./result/")
        print("=" * 70)

        if not os.path.exists(input_file):
            print(f"错误: 输入文件不存在 - {input_file}")
            return
        report = analyze_sequence(input_file, output_file)
        print("\n分析摘要:")
        print("=" * 70)
        key_lines = [line for line in report.split('\n') if any(kw in line for kw in ['结论:', 'P值:', '检测', '熵值'])]
        for line in key_lines:
            if "=" not in line:  # 跳过分隔线
                print(line)

        print("=" * 70)
        print(f"\n完整报告已保存至: {output_file}")
        print("分析完成!")


if __name__ == "__main__":
    main()