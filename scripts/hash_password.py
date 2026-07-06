"""生成管理员密码哈希。

用法：
    python scripts/hash_password.py
    （按提示输入密码，复制输出到 .env 的 ADMIN_PASSWORD_HASH=）
"""
import getpass
import sys

sys.path.insert(0, "backend")
try:
    from app.auth import hash_password
except Exception:
    # 独立运行时无需 fastapi 等依赖，内联实现
    import hashlib, secrets

    def hash_password(password: str, iterations: int = 200_000) -> str:
        salt = secrets.token_hex(16)
        raw = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return f"pbkdf2_sha256${iterations}${salt}${raw.hex()}"

if __name__ == "__main__":
    pw = getpass.getpass("请输入管理员密码: ")
    if not pw:
        print("密码不能为空"); sys.exit(1)
    h = hash_password(pw)
    print("\n将下面这一行填入 .env：\n")
    print(f"ADMIN_PASSWORD_HASH={h}")
