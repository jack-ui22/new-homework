import re


def read_pswd(filename):
    """解析包含混合格式的密码文件"""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read().splitlines()

    # 初始化数据结构
    header_num = None
    key_numbers = []
    lambda_numbers = []
    final_number = None
    all_numbers = []

    # 匹配首行开头的数字序列（不指定长度）
    if content:
        # 尝试匹配首行开头的数字序列
        header_match = re.match(r'^(\d+)', content[0])
        if header_match:
            header_num = int(header_match.group(1))
            # 移除已解析的数字部分
            content[0] = content[0][len(header_match.group(0)):]

    # 处理所有内容（包括修改后的首行）
    for line in content:
        # 处理Key行并提取"位"后的数字
        if re.search(r'Key\d+:\s*\d+\s*->\s*\d+位', line):
            # 提取"位"后面的所有数字
            bits = re.findall(r'位(\d+)', line)
            for num in bits:
                all_numbers.append(int(num))

            # 提取Key前后的数字
            key_match = re.search(r'Key\d+:\s*(\d+)\s*->\s*(\d+)\s*位', line)
            if key_match:
                key_numbers.append(int(key_match.group(1)))
                lambda_numbers.append(int(key_match.group(2)))
        else:
            # 处理独立的数字行
            digits = re.findall(r'\d+', line)
            for num in digits:
                all_numbers.append(int(num))

    # 取最后一个数字作为最终位
    if all_numbers:
        final_number = all_numbers[-1]

    return header_num, key_numbers, lambda_numbers, final_number
if __name__ == "__main__":
    try:
        h, keys, lams, final = read_pswd('D:/min project/jiami/pswd.txt')
        print("首行十位:", h)
        print("密钥列表:", keys)
        print("精度列表:", lams)
        print("最终十位:", final)
    except Exception as e:
        print(f"错误: {str(e)}")

