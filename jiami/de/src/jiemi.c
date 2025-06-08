#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>
#include <sys/stat.h>

// 配置常量
#define MAX_FILE_SIZE 1073741824   // 最大支持1gb文件
#define CHAR_SET_SIZE 256

// 密钥流状态结构体
typedef struct {
    int* key_indices;      // 密钥索引数组
    int key_indices_len;   // 密钥索引数量
    int current_key_idx;   // 当前密钥文件索引
    int* current_values;   // 当前密钥值数组
    int values_len;        // 密钥值数量
    int value_ptr;         // 当前密钥值指针
} KeyStreamState;

// 函数声明
int* read_key_file(int key_index, int* len);
KeyStreamState* init_key_stream();
int next_key_value(KeyStreamState* state);
void free_key_stream(KeyStreamState* state);
void caesar_decrypt(char* content, int len, KeyStreamState* state, const char* char_set);
void substitution_decrypt(char* content, int len, const char* original, const char* substitution);
void print_progress(size_t processed, size_t total);

// 读取密钥文件（返回动态数组）
int* read_key_file(int key_index, int* len) {
    char filename[50];
    snprintf(filename, sizeof(filename), "./de/keys/key%d.txt", key_index);
    
    FILE* fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Warning: Cannot open key file %s\n", filename);
        *len = 0;
        return NULL;
    }

    // 获取文件大小
    struct stat st;
    stat(filename, &st);
    size_t file_size = st.st_size;

    // 读取文件内容
    char* buffer = malloc(file_size + 1);
    size_t bytes_read = fread(buffer, 1, file_size, fp);
    buffer[bytes_read] = '\0';
    fclose(fp);

    // 过滤非数字字符并保证偶数长度
    char* clean_buffer = malloc(bytes_read + 2);
    int clean_len = 0;
    for (size_t i = 0; i < bytes_read; i++) {
        if (isdigit(buffer[i])) {
            clean_buffer[clean_len++] = buffer[i];
        }
    }
    free(buffer);

    if (clean_len % 2 != 0) {
        clean_buffer[clean_len++] = '0'; // 填充0保证偶数长度
    }
    clean_buffer[clean_len] = '\0';

    // 转换为整数数组
    *len = clean_len / 2;
    int* result = malloc(*len * sizeof(int));
    for (int i = 0; i < *len; i++) {
        char num_str[3] = {clean_buffer[2*i], clean_buffer[2*i+1], '\0'};
        result[i] = atoi(num_str);
    }
    free(clean_buffer);

    return result;
}

// 初始化密钥流状态
KeyStreamState* init_key_stream() {
    KeyStreamState* state = malloc(sizeof(KeyStreamState));
    
    // 读取key.txt中的索引序列
    FILE* fp = fopen("./de/keys/key.txt", "r");
    if (!fp) {
        state->key_indices = malloc(sizeof(int));
        state->key_indices[0] = 0;
        state->key_indices_len = 1;
    } else {
        char buffer[100];
        size_t len = fread(buffer, 1, sizeof(buffer)-1, fp);
        buffer[len] = '\0';
        fclose(fp);

        state->key_indices_len = 0;
        state->key_indices = malloc(len * sizeof(int));
        
        for (size_t i = 0; i < len; i++) {
            if (isdigit(buffer[i])) {
                state->key_indices[state->key_indices_len++] = buffer[i] - '0';
            }
        }
        
        if (state->key_indices_len == 0) {
            state->key_indices[state->key_indices_len++] = 0;
        }
    }

    state->current_key_idx = 0;
    state->current_values = NULL;
    state->values_len = 0;
    state->value_ptr = 0;

    return state;
}

// 获取下一个密钥值
int next_key_value(KeyStreamState* state) {
    if (state->value_ptr >= state->values_len) {
        // 加载下一个密钥文件
        free(state->current_values);
        
        int key_index = state->key_indices[state->current_key_idx];
        state->current_key_idx = (state->current_key_idx + 1) % state->key_indices_len;
        
        state->current_values = read_key_file(key_index, &state->values_len);
        state->value_ptr = 0;
        
        if (state->current_values == NULL || state->values_len == 0) {
            // 递归尝试下一个密钥文件
            return next_key_value(state);
        }
    }
    
    return state->current_values[state->value_ptr++];
}

// 释放密钥流资源
void free_key_stream(KeyStreamState* state) {
    free(state->key_indices);
    if (state->current_values) free(state->current_values);
    free(state);
}

// 凯撒解密
void caesar_decrypt(char* content, int len, KeyStreamState* state, const char* char_set) {
    int min_ord = 255, max_ord = 0;
    int char_set_len = strlen(char_set);
    
    // 确定字符范围
    for (int i = 0; i < char_set_len; i++) {
        int code = (int)char_set[i];
        if (code < min_ord) min_ord = code;
        if (code > max_ord) max_ord = code;
    }
    int range = max_ord - min_ord + 1;

    for (int i = 0; i < len; i++) {
        char c = content[i];
        if (c >= min_ord && c <= max_ord) {
            int shift = next_key_value(state);
            int code = (int)c;
            int shifted = (code - min_ord - shift) % range + min_ord;
            if (shifted < min_ord) shifted += range; // 处理负数情况
            content[i] = (char)shifted;
        }
        
        // 显示进度
        // if (i % 1000 == 0) {
        //     print_progress(i, len);
        // }
    }
}

// 替换表解密
void substitution_decrypt(char* content, int len, const char* original, const char* substitution) {
    // 创建反向映射表
    char reverse_map[CHAR_SET_SIZE] = {0};
    int set_len = strlen(substitution);
    
    for (int i = 0; i < set_len; i++) {
        reverse_map[(int)substitution[i]] = original[i];
    }

    // 执行替换
    for (int i = 0; i < len; i++) {
        char c = content[i];
        if (reverse_map[(int)c] != 0) {
            content[i] = reverse_map[(int)c];
        }
    }
}

// 打印进度条
void print_progress(size_t processed, size_t total) {
    float progress = (float)processed / total * 100.0f;
    printf("\rDecrypting: [%-50s] %.1f%%", 
           (char*)memset(malloc(51), '=', (int)(progress/2)), progress);
    fflush(stdout);
}

// 主解密函数
void decryption(const char* encrypted_file, const char* output_file, 
               const char* original, const char* substitution) {
    clock_t start = clock();
    
    // 读取加密文件
    FILE* fp = fopen(encrypted_file, "r");
    if (!fp) {
        perror("Error opening encrypted file");
        return;
    }
    
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    rewind(fp);
    
    if (file_size > MAX_FILE_SIZE) {
        fprintf(stderr, "Error: File size exceeds limit (%dMB)\n", MAX_FILE_SIZE/1048576);
        fclose(fp);
        return;
    }
    
    char* content = malloc(file_size + 1);
    fread(content, 1, file_size, fp);
    content[file_size] = '\0';
    fclose(fp);
    
    // 凯撒解密
    KeyStreamState* state = init_key_stream();
    caesar_decrypt(content, file_size, state, substitution);
    free_key_stream(state);
    
    // 替换表解密
    substitution_decrypt(content, file_size, original, substitution);
    
    // 保存结果
    FILE* out = fopen(output_file, "w");
    fwrite(content, 1, file_size, out);
    fclose(out);
    free(content);
    
    printf("\n\nDecryption completed. Saved to %s\n", output_file);
    printf("Time elapsed: %.2fs\n", (double)(clock() - start) / CLOCKS_PER_SEC);
    
    // 验证结果
    FILE* orig = fopen("./test/test1.txt", "r");
    FILE* dec = fopen(output_file, "r");
    if (orig && dec) {
        int match = 1;
        int c1, c2;
        while ((c1 = fgetc(orig)) != EOF && (c2 = fgetc(dec)) != EOF) {
            if (c1 != c2) {
                match = 0;
                break;
            }
        }
        if (match) printf("Verification: Success\n");
        else printf("Verification: Failed\n");
        fclose(orig);
        fclose(dec);
    } else {
        printf("Verification: Original file not found\n");
    }
}

void decode(const char* encrypted_file, const char* output_file) {
    // 读取字符集
    FILE* fp1 = fopen("./de/char/char.txt", "r");
    FILE* fp2 = fopen("./de/char/substitution.txt", "r");
    
    if (!fp1 || !fp2) {
        fprintf(stderr, "Error: Missing character set files\n");
        exit(1);
    }
    
    char original[CHAR_SET_SIZE] = {0};
    char substitution[CHAR_SET_SIZE] = {0};
    
    fgets(original, CHAR_SET_SIZE, fp1);
    fgets(substitution, CHAR_SET_SIZE, fp2);
    fclose(fp1);
    fclose(fp2);
    
    if (strlen(original) != strlen(substitution)) {
        fprintf(stderr, "Error: Character sets length mismatch\n");
        exit(1);
    }
    
    // 执行解密
    decryption(encrypted_file, output_file, original, substitution);
}
int main() {
    const char* encrypted_file = "./result/en.txt";
    const char* output_file = "./result/de.txt";
    decode( encrypted_file,  output_file);
    return 0;
}