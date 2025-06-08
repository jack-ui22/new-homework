import gmpy2
from gmpy2 import mpfr, get_context
import secrets
import os
import time
from tqdm import tqdm
from pswd import generate_secure as security
def generate_ascii_charset(filename):
    """生成包含完整ASCII 32-126字符集的文件"""
    print("正在生成ASCII字符集...")
    ascii_chars = [chr(i) for i in range(32, 127)]
    with open(filename, 'wb') as f:
        f.write(''.join(ascii_chars).encode('utf-8'))
    return ''.join(ascii_chars)


def create_substitution_table(original, key_file='D:\min project\jiami\pswd.txt'):
    if ' ' not in original:
        raise ValueError("字符集缺少空格字符")
    if len(original) != 95:
        missing = set(chr(i) for i in range(32, 127)) - set(original)
        raise ValueError(f"缺失字符: {''.join(sorted(missing))}")

    print("正在初始化加密上下文...")
    ctx = get_context()
    original_precision = ctx.precision
    ctx.precision = 300

    try:
        print("正在生成加密种子...")
        rand_num = security(21)
        with open(key_file, 'w') as f:
            f.write(str(rand_num))

        num = mpfr(rand_num)
        sqrt_num = gmpy2.sqrt(num)
        sqrt_str = format(sqrt_num, ".500f").split('.')[1]

        num_pool = [int(sqrt_str[i:i + 3]) for i in range(0, 450, 3)]

        chars = list(original)
        for i in tqdm(range(len(chars) - 1, 0, -1), desc="进度", unit="步"):
            if not num_pool:
                new_rand = secrets.randbelow(10 ** 8)
                new_sqrt = gmpy2.sqrt(mpfr(new_rand))
                sqrt_str = format(new_sqrt, ".500f").split('.')[1]
                num_pool = [int(sqrt_str[i:i + 3]) for i in range(0, 450, 3)]
                with open(key_file, 'ab') as f:
                    f.write(new_rand.to_bytes(4, 'big'))

            idx = num_pool.pop() % (i + 1)
            chars[i], chars[idx] = chars[idx], chars[i]

        return ''.join(chars)
    finally:
        ctx.precision = original_precision


def verify_substitution(original, substitution):
    print("\n[验证结果]")
    print(f"原字符集长度: {len(original)}")
    print(f"替换表长度: {len(substitution)}")
    print(f"字符差异: {set(original) - set(substitution) or '无'}")
    print(f"重复字符: {[c for c in substitution if substitution.count(c) > 1] or '无'}")


if __name__ == "__main__":
    start_time = time.time()
    char_file = './en/char/char.txt'
    if not os.path.exists(char_file):
        original = generate_ascii_charset(char_file)
    else:
        with open(char_file, 'rb') as f:
            original = f.read().decode('utf-8').strip('\n')
        print("已加载现有ASCII字符集文件")

    # 生成替换表
    try:
        substitution = create_substitution_table(original)
        print("\n替换表生成成功！")
    except ValueError as e:
        print(f"\n生成失败: {str(e)}")
        exit(1)
    with open('./en/char/substitution.txt', 'w', encoding='utf-8') as f:
        f.write(substitution)
    print("替换表已保存至 substitution.txt")
    verify_substitution(original, substitution)
    
    # 输出总耗时
    end_time = time.time()
    print(f"\n总耗时: {end_time - start_time:.2f}秒")