"""写作习惯追踪模块 - 记录和分析写作行为"""

from datetime import datetime, date
from libs.database import db_manager


class HabitTracker:
    """追踪和管理写作习惯"""

    def __init__(self):
        pass

    def start_session(self, entry_id: int = None) -> int:
        """开始写作会话，返回会话 ID"""
        return db_manager.start_session(entry_id)

    def end_session(self, session_id: int, word_count_delta: int = 0):
        """结束写作会话"""
        db_manager.end_session(session_id, word_count_delta)

    def record_entry_save(self, entry_id: int, total_words: int,
                          word_count_delta: int, mood: str):
        """记录日记保存事件，更新习惯数据"""
        today = date.today().isoformat()
        now_str = datetime.now().strftime("%H:%M:%S")

        # 更新每日习惯汇总
        db_manager.upsert_habit(
            today=today,
            entry_count=0,  # 创建日记时已计入，这里仅更新
            write_time=now_str,
            total_words=max(0, word_count_delta),  # 仅计算新增字数
            duration_sec=0,  # 由 session 管理时长
            mood=mood
        )

    def get_writing_stats(self, days: int = 30) -> dict:
        """获取写作统计信息"""
        habits = db_manager.get_habits(days)
        sessions = db_manager.get_writing_sessions(days)
        stats = db_manager.get_stats()

        if not habits:
            return {
                "total_days_written": 0,
                "avg_words_per_day": 0,
                "preferred_hour": None,
                "preferred_day": None,
                "consecutive_days": 0,
                "total_entries": stats["total_entries"],
                "total_words": stats["total_words"],
            }

        # 计算平均每日字数
        total_words = sum(h.get("total_words", 0) for h in habits)
        days_written = len(habits)
        avg_words = total_words / max(days_written, 1)

        # 最常用写作时段
        hour_counts = {}
        for s in sessions:
            h = s.get("hour_of_day")
            if h is not None:
                hour_counts[h] = hour_counts.get(h, 0) + 1

        preferred_hour = None
        if hour_counts:
            preferred_hour = max(hour_counts, key=hour_counts.get)

        # 最常用写作日
        day_counts = {}
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        for s in sessions:
            dow = s.get("day_of_week")
            if dow is not None:
                day_counts[dow] = day_counts.get(dow, 0) + 1

        preferred_day = None
        if day_counts:
            preferred_day = day_names[max(day_counts, key=day_counts.get)]

        return {
            "total_days_written": days_written,
            "avg_words_per_day": round(avg_words, 1),
            "preferred_hour": preferred_hour,
            "preferred_day": preferred_day,
            "consecutive_days": db_manager.get_consecutive_days(),
            "total_entries": stats["total_entries"],
            "total_words": stats["total_words"],
            "mood_distribution": stats.get("moods", {}),
            "category_distribution": stats.get("categories", {}),
        }

    def get_writing_heatmap(self, days: int = 90) -> dict:
        """生成写作热力图数据"""
        habits = db_manager.get_habits(days)
        heatmap = {}
        for h in habits:
            heatmap[h["date"]] = h.get("total_words", 0)
        return heatmap

    def check_achievements(self) -> list[dict]:
        """检查并返回解锁的成就"""
        stats = self.get_writing_stats(365)
        achievements = []

        # 连续写作成就
        consecutive = stats["consecutive_days"]
        milestones = [7, 21, 50, 100, 365]
        for m in milestones:
            if consecutive >= m:
                achievements.append({
                    "type": "achievement",
                    "title": f"🏆 连续写作 {m} 天",
                    "description": f"你已经连续 {consecutive} 天写作了！",
                    "icon": "🏆"
                })

        # 字数成就
        total_words = stats["total_words"]
        word_milestones = [
            (10000, "1 万字", "相当于一篇长论文"),
            (50000, "5 万字", "相当于一本中篇小说"),
            (100000, "10 万字", "相当于一本长篇小说"),
        ]
        for milestone, label, desc in word_milestones:
            if total_words >= milestone:
                achievements.append({
                    "type": "achievement",
                    "title": f"📝 总字数突破 {label}",
                    "description": desc,
                    "icon": "📝"
                })

        # 心情多样性
        moods = stats.get("mood_distribution", {})
        if len(moods) >= 6:
            achievements.append({
                "type": "achievement",
                "title": "🌈 情感探索者",
                "description": "你使用了全部 6 种心情标签！",
                "icon": "🌈"
            })

        # 返回最近 3 个未读成就
        return achievements[:3]

    def get_mood_trend(self, days: int = 30) -> list[dict]:
        """获取心情趋势数据"""
        conn = db_manager.get_connection()
        try:
            rows = conn.execute(
                "SELECT date(created_at) as d, mood, COUNT(*) as cnt "
                "FROM entries WHERE created_at >= date('now', ?) "
                "GROUP BY d, mood ORDER BY d",
                (f"-{days} days",)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
