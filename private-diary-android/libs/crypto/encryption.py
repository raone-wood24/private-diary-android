"""AES-256-GCM 加密/解密模块"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from libs.utils.config import SECURITY_CONFIG


IV_LENGTH = SECURITY_CONFIG["iv_length"]


def generate_iv() -> bytes:
    """生成随机初始化向量"""
    return os.urandom(IV_LENGTH)


def encrypt(plaintext: str, key: bytes) -> tuple[bytes, bytes]:
    """
    使用 AES-256-GCM 加密明文
    返回 (密文, IV)
    """
    iv = generate_iv()
    aesgcm = AESGCM(key)
    # GCM 模式：密文已包含认证标签
    ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    return ciphertext, iv


def decrypt(ciphertext: bytes, iv: bytes, key: bytes) -> str:
    """
    使用 AES-256-GCM 解密密文
    返回明文字符串
    如果认证失败（数据被篡改或密钥错误），抛出异常
    """
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ciphertext, None)
    return plaintext.decode("utf-8")


def encrypt_bytes(data: bytes, key: bytes) -> tuple[bytes, bytes]:
    """加密二进制数据"""
    iv = generate_iv()
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, data, None)
    return ciphertext, iv


def decrypt_bytes(ciphertext: bytes, iv: bytes, key: bytes) -> bytes:
    """解密二进制数据"""
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ciphertext, None)
