import gmpy2
from gmpy2 import mpfr, get_context
import time
from multiprocessing import Process
import asyncio
import aiofiles
from pswd import generate_secure as security
from pswd import generate_basic as basic
from tqdm import tqdm
from pswd import generate_basic1


async def async_write(file, content):
    """异步写入纯小数部分"""
    async with aiofiles.open(file, "w") as f:
        await f.write(content)




def sqrt_task(key, file, digits):
    """动态位数平方根计算"""
    ctx = get_context().copy()
    ctx.precision = int(digits * 3.321928 * 1.1)
    gmpy2.set_context(ctx)

    num = mpfr(str(key))
    result = gmpy2.sqrt(num)

    full_str = format(result, f".{digits + 1000}f")  # 多生成1000位防止截断
    #decimal_part = full_str.split('.')[1][:digits]  # 精确截取
    decimal_string = full_str.split('.')[1]


    if len(decimal_string) < 10 + digits:

        decimal_part = decimal_string[10:10 + digits].ljust(digits, '0')[:digits]
    else:
        decimal_part = decimal_string[10:10 + digits]
    asyncio.run(async_write(file, decimal_part))


if __name__ == "__main__":
    start_time = time.time()
    print("开始生成密钥...")
    
    # 生成密钥和对应的位数
    keys = [security(generate_basic1()) for _ in tqdm(range(10), desc="生成密钥", unit="个")]
    digits_list = [basic() for _ in range(10)]

    print("正在保存密钥信息...")

    with open('pswd.txt', 'a') as f:  # 模式改为追加模式 'a'
        # 添加换行符确保从新行开始
        f.write( "\n".join(f"Key{i}: {k} -> {d}位"
                    for i, (k, d) in enumerate(zip(keys, digits_list))))

    print("正在创建进程池...")
    processes = [
        Process(target=sqrt_task,
                args=(key, f"./en/keys/key{i}.txt", digits))
        for i, (key, digits) in enumerate(zip(keys, digits_list))
    ]

    # 执行并计时
    print("开始计算平方根...")
    process_start = time.time()
    for p in processes:
        p.start()
    for p in tqdm(processes, desc="计算进度", unit="进程"):
        p.join()
    total_digits = sum(digits_list)
    total_time = time.time() - start_time
    process_time = time.time() - process_start
    
    print("\n=== 生成完成 ===")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"计算耗时: {process_time:.2f}秒")
    print(f"总生成位数: {total_digits:,} (平均 {total_digits / 10 / 1e6:.2f}百万/文件)")
    print(f"平均速度: {total_digits / process_time / 1e6:.2f}百万位/秒")
    print("\n=== 详细信息 ===")
    print("位数列表:", digits_list)
    print("密钥列表:", keys)
    print("\n生成成功！")