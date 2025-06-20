import gmpy2
from gmpy2 import mpfr, get_context
import os
from pswd import generate_secure as security
from pswd import generate_basic1
def append_security_number(number, filename):
    with open(filename, 'a') as f:
        f.write(f"{number}\n")


def generate_and_save_index(filename, num,digits=10000):
    """生成并保存一万位数到key.txt作为索引"""
    # 生成一个随机数
    random_num = num
    
    # 计算平方根
    ctx = get_context()
    original_precision = ctx.precision
    try:
        ctx.precision = int(digits * 3.3219280948) + 1000
        num = mpfr(str(random_num))
        sqrt_num = gmpy2.sqrt(num)
        
        # 格式化为十进制字符串
        str_repr = format(sqrt_num, f".{digits + 100}f")
        decimal_part = str_repr.split('.')[1][:digits].ljust(digits, '0')
        
        # 保存到key.txt
        with open(filename, 'w') as f:
            f.write(decimal_part)
            
    finally:
        ctx.precision = original_precision


if __name__ == "__main__":
    secure_num = security(generate_basic1())
    append_security_number(secure_num, 'D:\min project\jiami\pswd.txt')
    generate_and_save_index('./en/keys/key.txt',num=secure_num)
    print(f"安全数已保存至 pswd.txt")
    print(f"一万位索引已保存至 keys/key.txt")

    file_size = os.path.getsize('./en/keys/key.txt')
    print(f"生成文件大小: {file_size // 1024 // 1024}MB")