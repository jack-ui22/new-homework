#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>
#include <sys/stat.h>

// 密钥流状态结构体
typedef struct {
    int* key_indices;      // 密钥索引数组
    int key_indices_len;   // 密钥索引数组长度
    int current_key_idx;   // 当前使用的密钥文件索引
    int* current_values;   // 当前密钥值数组
    int values_len;        // 密钥值数组长度
    int value_ptr;         // 当前密钥值指针
} KeyStreamState;

// 全局配置常量
#define MAX_FILE_SIZE 1073741824  // 最大支持1gb文件
#define CHAR_SET_SIZE 256

// 函数声明
int* read_key_file(int key_index, int* len);
int get_current_key_index();
char substitution_encrypt(char c, const char* original, const char* substitution, int len);
void caesar_encrypt(char* content, int len, KeyStreamState* state, const char* char_set);
KeyStreamState* init_key_stream();
int next_key_value(KeyStreamState* state);
void free_key_stream(KeyStreamState* state);


// 读取密钥文件（返回动态数组）
int* read_key_file(int key_index, int* len) {
    char filename[50];
    snprintf(filename, sizeof(filename), "./en/keys/key%d.txt", key_index);
    
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

// 获取当前密钥索引
int get_current_key_index() {
    FILE* fp = fopen("./en/keys/key.txt", "r");
    if (!fp) {
        fprintf(stderr, "Warning: Using default key0.txt\n");
        return 0;
    }

    int index = 0;
    char c;
    if (fscanf(fp, "%c", &c) == 1) {
        index = c - '0';
    }
    fclose(fp);
    return index;
}

// 初始化密钥流状态
KeyStreamState* init_key_stream() {
    KeyStreamState* state = malloc(sizeof(KeyStreamState));
    
    // 读取key.txt中的索引序列
    FILE* fp = fopen("./en/keys/key.txt", "r");
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
        state->key_indices = malloc(strlen(buffer) * sizeof(int));
        
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
            // 密钥文件加载失败时递归尝试下一个
            return next_key_value(state);
        }
    }
    
    return state->current_values[state->value_ptr++];
}

// 替换加密
char substitution_encrypt(char c, const char* original, const char* substitution, int len) {
    for (int i = 0; i < len; i++) {
        if (original[i] == c) {
            return substitution[i];
        }
    }
    return c; // 未找到字符保持原样
}
void print_progress(size_t processed, size_t total) {
    float progress = (float)processed / total * 100.0f;
    printf("\rDecrypting: [%-50s] %.1f%%", 
           (char*)memset(malloc(51), '=', (int)(progress/2)), progress);
    fflush(stdout);
}

// 凯撒加密
void caesar_encrypt(char* content, int len, KeyStreamState* state, const char* char_set) {
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
            int shifted = (code - min_ord + shift) % range + min_ord;
            content[i] = (char)shifted;
        }
    //   if (i % 1000 == 0) {
    //         print_progress(i, len);
    //     }  
      
    }
}


// 主加密函数
void encryption(const char* filename, const char* original, const char* substitution) {
    clock_t start = clock();
    
    // 读取待加密文件
    FILE* fp = fopen("./test/1.txt", "r");
    if (!fp) {
        perror("Error opening input file");
        return;
    }
    
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    rewind(fp);
    
    char* content = malloc(file_size + 1);
    fread(content, 1, file_size, fp);
    content[file_size] = '\0';
    fclose(fp);
    
    // 第一步：替换加密
    int char_set_len = strlen(original);
    for (long i = 0; i < file_size; i++) {
        content[i] = substitution_encrypt(content[i], original, substitution, char_set_len);
    }
    
    // 第二步：凯撒加密
    KeyStreamState* state = init_key_stream();
    caesar_encrypt(content, file_size, state, substitution);
    free_key_stream(state);
    
    // 保存结果
    FILE* out = fopen(filename, "w");
    fwrite(content, 1, file_size, out);
    fclose(out);
    free(content);
    
    printf("\nEncryption completed. Saved to %s\n", filename);
    printf("Time elapsed: %.2fs\n", (double)(clock() - start) / CLOCKS_PER_SEC);
}

// 释放密钥流资源
void free_key_stream(KeyStreamState* state) {
    free(state->key_indices);
    free(state->current_values);
    free(state);
}

int main() {
    // 读取字符集
    FILE* fp1 = fopen("./en/char/char.txt", "r");
    FILE* fp2 = fopen("./en/char/substitution.txt", "r");
    
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
    
    // 执行加密
    encryption("./result/en.txt", original, substitution);
    return 0;
}