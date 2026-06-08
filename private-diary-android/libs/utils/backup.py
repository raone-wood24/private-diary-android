"""数据导出/导入模块"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from libs.database import db_manager
from libs.utils.config import BACKUP_DIR, DATABASE_PATH, ensure_data_dir


def export_entries(export_path: str = None, decrypt_key: bytes = None) -> str | None:
    """
    导出日记数据为 JSON 文件
    如果提供 decrypt_key，则导出明文 JSON
    如果不提供，则导出加密的数据库副本
    """
    ensure_data_dir()

    if export_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = str(BACKUP_DIR / f"diary_export_{timestamp}.json")

    entries = db_manager.get_all_entries()

    export_data = {
        "app": "私人日记",
        "version": "0.1",
        "exported_at": datetime.now().isoformat(),
        "entry_count": len(entries),
        "entries": [],
    }

    for entry in entries:
        full_entry = db_manager.get_entry(entry["id"])
        if not full_entry:
            continue

        entry_data = {
            "id": full_entry["id"],
            "title": full_entry["title"],
            "mood": full_entry.get("mood", "neutral"),
            "category": full_entry.get("category", "默认"),
            "created_at": full_entry.get("created_at", ""),
            "updated_at": full_entry.get("updated_at", ""),
            "word_count": full_entry.get("word_count", 0),
        }

        if decrypt_key:
            # 解密导出
            try:
                from libs.crypto.encryption import decrypt
                content = decrypt(
                    full_entry["content_encrypted"],
                    full_entry["iv"], decrypt_key)
                entry_data["content"] = content
            except Exception:
                entry_data["content"] = "[解密失败]"
        else:
            # 加密导出（保留密文和 IV 的 hex 格式，可重新导入）
            entry_data["content_encrypted_hex"] = full_entry[
                "content_encrypted"].hex()
            entry_data["iv_hex"] = full_entry["iv"].hex()

        export_data["entries"].append(entry_data)

    try:
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        return export_path
    except IOError as e:
        print(f"导出失败: {e}")
        return None


def import_entries(import_path: str, encrypt_key: bytes = None) -> tuple[bool, str]:
    """
    从 JSON 文件导入日记数据
    返回 (成功, 消息)
    """
    try:
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        return False, f"读取文件失败: {e}"

    if "entries" not in data:
        return False, "无效的导出文件格式"

    imported = 0
    skipped = 0

    for entry_data in data["entries"]:
        title = entry_data.get("title", "无标题")
        mood = entry_data.get("mood", "neutral")
        category = entry_data.get("category", "默认")

        if "content" in entry_data and encrypt_key:
            # 明文导入，重新加密
            from libs.crypto.encryption import encrypt
            content = entry_data["content"]
            word_count = len(content.replace("\n", "").replace(" ", ""))
            ciphertext, iv = encrypt(content, encrypt_key)
            db_manager.insert_entry(
                title, ciphertext, iv,
                mood=mood, category=category, word_count=word_count
            )
            imported += 1
        elif "content_encrypted_hex" in entry_data and "iv_hex" in entry_data:
            # 加密格式导入（需要相同密钥）
            ciphertext = bytes.fromhex(entry_data["content_encrypted_hex"])
            iv = bytes.fromhex(entry_data["iv_hex"])
            db_manager.insert_entry(
                title, ciphertext, iv,
                mood=mood, category=category,
                word_count=entry_data.get("word_count", 0)
            )
            imported += 1
        else:
            skipped += 1

    return True, f"导入完成：{imported} 篇成功，{skipped} 篇跳过"


def backup_database() -> str | None:
    """备份整个数据库文件"""
    ensure_data_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"diary_backup_{timestamp}.db"

    try:
        if DATABASE_PATH.exists():
            shutil.copy2(str(DATABASE_PATH), str(backup_path))
            return str(backup_path)
    except IOError as e:
        print(f"数据库备份失败: {e}")
    return None


def restore_database(backup_path: str) -> bool:
    """从备份恢复数据库"""
    try:
        shutil.copy2(backup_path, str(DATABASE_PATH))
        return True
    except IOError as e:
        print(f"数据库恢复失败: {e}")
        return False


def list_backups() -> list[str]:
    """列出所有备份文件"""
    ensure_data_dir()
    backups = []
    if BACKUP_DIR.exists():
        for f in sorted(BACKUP_DIR.glob("*")):
            backups.append(str(f))
    return backups
