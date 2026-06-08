"""用户行为模式分析模块 — 时间画像和行为画像"""

from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
from libs.database import db_manager


class BehaviorAnalyzer:
    """分析用户写作行为模式"""

    def __init__(self):
        pass

    def analyze_writing_time(self, days: int = 60) -> dict:
        """分析写作时间模式"""
        sessions = db_manager.get_writing_sessions(days)

        if not sessions:
            return self._empty_time_profile()

        hour_counts = Counter(s.get("hour_of_day") for s in sessions if s.get("hour_of_day") is not None)
        day_counts = Counter(s.get("day_of_week") for s in sessions if s.get("day_of_week") is not None)

        # Top-3 高峰时段
        top_hours = hour_counts.most_common(3)
        top_hour_values = [h for h, _ in top_hours]

        # 时段分类
        time_slots = {"morning": 0, "afternoon": 0, "evening": 0, "night": 0}
        for hour, count in hour_counts.items():
            if 5 <= hour < 12:
                time_slots["morning"] += count
            elif 12 <= hour < 17:
                time_slots["afternoon"] += count
            elif 17 <= hour < 22:
                time_slots["evening"] += count
            else:
                time_slots["night"] += count

        preferred_slot = max(time_slots, key=time_slots.get)

        # 工作日 vs 周末
        weekday_count = sum(day_counts.get(d, 0) for d in range(5))
        weekend_count = sum(day_counts.get(d, 0) for d in range(5, 7))

        return {
            "top_hours": top_hour_values,
            "preferred_time_slot": preferred_slot,
            "time_slot_distribution": time_slots,
            "weekday_ratio": round(weekday_count / max(weekday_count + weekend_count, 1), 2),
            "hour_distribution": dict(hour_counts.most_common()),
            "day_distribution": dict(day_counts.most_common()),
            "total_sessions": len(sessions),
        }

    def analyze_writing_frequency(self, days: int = 60) -> dict:
        """分析写作频率"""
        habits = db_manager.get_habits(days)

        if not habits:
            return self._empty_frequency_profile()

        # 计算写作间隔
        dates = sorted([h["date"] for h in habits])
        intervals = []
        for i in range(1, len(dates)):
            d1 = date.fromisoformat(dates[i - 1])
            d2 = date.fromisoformat(dates[i])
            intervals.append((d2 - d1).days)

        avg_interval = sum(intervals) / len(intervals) if intervals else 0

        # 每日平均篇数
        total_entries = sum(h.get("entry_count", 0) for h in habits)
        avg_daily = total_entries / max(days, 1)

        # 连续天数
        consecutive = db_manager.get_consecutive_days()

        return {
            "avg_interval_days": round(avg_interval, 1),
            "avg_entries_per_day": round(avg_daily, 2),
            "consecutive_days": consecutive,
            "total_days_written": len(habits),
            "total_entries": total_entries,
        }

    def detect_deviation(self, days: int = 30) -> dict:
        """检测行为偏离（用于触发不同推荐策略）"""
        recent = self.analyze_writing_frequency(14)
        baseline = self.analyze_writing_frequency(60)

        alerts = []

        # 写作频率下降
        if baseline["avg_entries_per_day"] > 0.1:
            drop_ratio = recent["avg_entries_per_day"] / max(baseline["avg_entries_per_day"], 0.01)
            if drop_ratio < 0.5:
                alerts.append({
                    "type": "frequency_drop",
                    "message": "最近写作频率下降较多",
                    "severity": "warning",
                    "ratio": round(drop_ratio, 2)
                })
            elif drop_ratio > 1.5:
                alerts.append({
                    "type": "frequency_spike",
                    "message": "最近写作频率显著增加",
                    "severity": "positive",
                    "ratio": round(drop_ratio, 2)
                })

        # 连续中断风险
        if 1 <= recent["consecutive_days"] <= 3 and baseline["consecutive_days"] > 7:
            alerts.append({
                "type": "streak_risk",
                "message": "连续写作中断风险",
                "severity": "info",
                "previous_streak": baseline["consecutive_days"]
            })

        return {
            "recent": recent,
            "baseline": baseline,
            "alerts": alerts,
        }

    def get_mood_hour_correlation(self, days: int = 90) -> dict:
        """分析心情-时段相关性"""
        conn = db_manager.get_connection()
        try:
            rows = conn.execute(
                "SELECT e.mood, s.hour_of_day "
                "FROM entries e JOIN writing_sessions s ON e.id = s.entry_id "
                "WHERE e.created_at >= date('now', ?) AND s.hour_of_day IS NOT NULL",
                (f"-{days} days",)
            ).fetchall()

            correlation = defaultdict(Counter)
            for r in rows:
                correlation[r["mood"]][r["hour_of_day"]] += 1

            result = {}
            for mood, hours in correlation.items():
                result[mood] = {
                    "top_hours": [h for h, _ in hours.most_common(3)],
                    "distribution": dict(hours)
                }

            return result
        finally:
            conn.close()

    def _empty_time_profile(self) -> dict:
        return {
            "top_hours": [],
            "preferred_time_slot": "evening",
            "time_slot_distribution": {"morning": 0, "afternoon": 0, "evening": 0, "night": 0},
            "weekday_ratio": 0.5,
            "hour_distribution": {},
            "day_distribution": {},
            "total_sessions": 0,
        }

    def _empty_frequency_profile(self) -> dict:
        return {
            "avg_interval_days": 0,
            "avg_entries_per_day": 0,
            "consecutive_days": 0,
            "total_days_written": 0,
            "total_entries": 0,
        }
