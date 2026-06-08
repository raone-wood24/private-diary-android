"""主密码管理模块 - PBKDF2 密钥派生与验证"""

import os
import hashlib
import time
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from libs.utils.config import SECURITY_CONFIG
from libs.database.db_manager import get_setting, set_setting, delete_setting


SALT_KEY = "auth_salt"
HASH_KEY = "auth_hash"
LOCKOUT_KEY = "auth_lockout_until"
FAILED_COUNT_KEY = "auth_failed_count"


def _derive_key(password: str, salt: bytes) -> bytes:
    """使用 PBKDF2 从密码派生 32 字节密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=SECURITY_CONFIG["pbkdf2_iterations"],
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


def _hash_key(key: bytes) -> str:
    """对密钥做一次哈希（用于存储验证）"""
    return hashlib.sha256(key).hexdigest()


def is_initialized() -> bool:
    """检查是否已设置主密码"""
    salt = get_setting(SALT_KEY)
    hash_val = get_setting(HASH_KEY)
    return salt is not None and hash_val is not None


def setup_master_password(password: str) -> bool:
    """
    首次设置主密码
    返回 True 表示设置成功
    """
    if len(password) < SECURITY_CONFIG["min_password_length"]:
        return False

    salt = os.urandom(16)
    key = _derive_key(password, salt)
    key_hash = _hash_key(key)

    set_setting(SALT_KEY, salt.hex())
    set_setting(HASH_KEY, key_hash)
    set_setting(FAILED_COUNT_KEY, "0")

    return True


def check_lockout() -> tuple[bool, int]:
    """
    检查是否被锁定
    返回 (是否锁定, 剩余秒数)
    """
    lockout_str = get_setting(LOCKOUT_KEY)
    if lockout_str:
        lockout_until = float(lockout_str)
        remaining = lockout_until - time.time()
        if remaining > 0:
            return True, int(remaining)
        else:
            # 锁定已过期
            delete_setting(LOCKOUT_KEY)
            set_setting(FAILED_COUNT_KEY, "0")

    return False, 0


def _record_failed_attempt():
    """记录一次失败尝试"""
    count_str = get_setting(FAILED_COUNT_KEY)
    count = int(count_str) if count_str else 0
    count += 1
    set_setting(FAILED_COUNT_KEY, str(count))

    if count >= SECURITY_CONFIG["max_login_attempts"]:
        # 锁定
        lockout_until = time.time() + SECURITY_CONFIG["lockout_duration_seconds"]
        set_setting(LOCKOUT_KEY, str(lockout_until))
        set_setting(FAILED_COUNT_KEY, "0")


def verify_password(password: str) -> tuple[bool, str]:
    """
    验证主密码
    返回 (验证成功, 派生密钥hex 或 错误信息)
    """
    # 检查锁定
    locked, remaining = check_lockout()
    if locked:
        minutes = remaining // 60
        seconds = remaining % 60
        return False, f"账户已锁定，请等待 {minutes} 分 {seconds} 秒后重试"

    salt_hex = get_setting(SALT_KEY)
    hash_value = get_setting(HASH_KEY)

    if not salt_hex or not hash_value:
        return False, "尚未设置主密码"

    salt = bytes.fromhex(salt_hex)
    key = _derive_key(password, salt)
    key_hash = _hash_key(key)

    if key_hash == hash_value:
        # 验证成功，清除失败记录
        set_setting(FAILED_COUNT_KEY, "0")
        delete_setting(LOCKOUT_KEY)
        return True, key.hex()
    else:
        _record_failed_attempt()
        count_str = get_setting(FAILED_COUNT_KEY)
        count = int(count_str) if count_str else 0
        remaining = SECURITY_CONFIG["max_login_attempts"] - count
        if remaining > 0:
            return False, f"密码错误，还剩 {remaining} 次尝试机会"
        else:
            return False, "密码错误次数过多，账户已锁定 5 分钟"


def change_password(old_password: str, new_password: str) -> tuple[bool, str]:
    """
    修改主密码：先用旧密码验证，再设置新密码
    返回 (成功, 消息)
    """
    success, result = verify_password(old_password)
    if not success:
        return False, result

    # 先解密所有旧日记数据... 但这需要知道有多少日记
    # 简化处理：重新生成 salt 和 hash
    # 注意：这会导致旧密钥丢失，旧数据无法解密！
    # 实际修改密码需要重新加密所有日记，在 backup.py 中处理
    return False, "修改密码功能需要配合数据重加密，请在设置界面操作"


def get_encryption_key(password: str) -> tuple[bool, str | bytes]:
    """
    获取加密密钥（登录时调用）
    返回 (成功, 密钥bytes 或 错误信息)
    """
    success, result = verify_password(password)
    if success:
        key = bytes.fromhex(result)
        return True, key
    return False, result


def get_pending_lockout_time() -> int:
    """获取当前剩余锁定时间（秒）"""
    locked, remaining = check_lockout()
    return remaining if locked else 0
