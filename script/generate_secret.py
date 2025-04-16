import secrets
import string

def generate_secret_key(length=50):
    # 使用字母、数字和特殊字符的组合
    characters = string.ascii_letters + string.digits + string.punctuation
    # 确保至少包含一个特殊字符
    secret_key = ''.join(secrets.choice(characters) for _ in range(length))
    return secret_key

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print(f"生成的SECRET_KEY: {secret_key}") 