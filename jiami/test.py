import os
import sys
from collections import defaultdict


def analyze_character_distribution(file_path):
    """分析文本文件中指定字符集的出现频率"""
    target_chars = ''.join(sorted(
        r'!"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~'
    ))
    char_counts = defaultdict(int)
    total_valid_chars = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                for char in line:
                    if char in target_chars:
                        char_counts[char] += 1
                        total_valid_chars += 1

    except FileNotFoundError:
        print(f"错误: 文件 {file_path} 不存在")
        return None, None, 0

    # 计算占比
    char_percentages = {}
    if total_valid_chars > 0:
        for char, count in char_counts.items():
            char_percentages[char] = (count, count / total_valid_chars * 100)

    return char_counts, char_percentages, total_valid_chars


def generate_report(char_percentages, total):
    """生成统计报告和可视化图表"""
    if not char_percentages:
        print("未找到有效字符统计")
        return

    # 创建结果目录
    os.makedirs('./result', exist_ok=True)

    # 按ASCII码排序
    sorted_chars = sorted(char_percentages.items(), key=lambda x: ord(x[0]))

    # 生成文本报告
    report = ["字符统计报告", "=" * 40]
    report.append(f"总有效字符数: {total}\n")
    report.append("字符 | 出现次数 | 占比(%)")
    report.append("----|---------|--------")

    for char, (count, percentage) in sorted_chars:
        report.append(f"'{char}' | {count} | {percentage:.4f}%")

    report_path = './result/char_statistics.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    return report_path


if __name__ == "__main__":
    # 分析文件
    file_path = './result/en.txt'
    counts, percentages, total = analyze_character_distribution(file_path)

    if percentages:
        # 生成报告
        report_path = generate_report(percentages, total)
        print(f"分析完成！结果已保存至: {report_path}")

        # 在终端显示统计概览
        print("\n字符分布概览:")
        print("类别     字符数  占比(%)")
        print("-----------------------")

        category_counts = defaultdict(float)
        for char, (count, percent) in percentages.items():
            if '0' <= char <= '9':
                category_counts['数字'] += percent
            elif 'a' <= char <= 'z':
                category_counts['小写字母'] += percent
            elif 'A' <= char <= 'Z':
                category_counts['大写字母'] += percent
            elif char in r'''!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~''':
                category_counts['标点符号'] += percent
            else:
                category_counts['其他符号'] += percent

        for category, percent_sum in category_counts.items():
            print(f"{category:6} {percent_sum:10.2f}%")

        print("\n详细统计请查看报告文件")