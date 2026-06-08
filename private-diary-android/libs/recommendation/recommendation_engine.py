"""综合推荐引擎 — 生成和管理各类推荐"""

from datetime import datetime, date
from libs.database import db_manager
from libs.recommendation.behavior_analyzer import BehaviorAnalyzer
from libs.recommendation.content_analyzer import ContentAnalyzer
from libs.personalization.habit_tracker import HabitTracker


class RecommendationEngine:
    """综合推荐引擎"""

    def __init__(self):
        self.behavior = BehaviorAnalyzer()
        self.content = ContentAnalyzer()
        self.habit = HabitTracker()

    def generate_all_recommendations(self) -> dict:
        """生成所有类型的推荐"""
        return {
            "time": self.generate_time_recommendation(),
            "review": self.generate_review_recommendation(),
            "mood_insight": self.generate_mood_insight(),
            "topic_template": self.generate_topic_recommendation(),
            "achievement": self.generate_achievement_recommendation(),
        }

    def generate_time_recommendation(self) -> dict | None:
        """生成时间提醒推荐"""
        time_profile = self.behavior.analyze_writing_time(60)

        if not time_profile.get("top_hours"):
            return None

        now = datetime.now()
        current_hour = now.hour
        top_hours = time_profile["top_hours"]

        # 检查现在是否在高峰时段
        in_peak = any(abs(current_hour - h) <= 1 for h in top_hours)

        # 检查今天是否已写
        today_entries = db_manager.get_entries_by_date(date.today().isoformat())

        if in_peak and not today_entries:
            formatted = [f"{h}:00" for h in top_hours[:2]]
            return {
                "type": "time_reminder",
                "title": "💡 写作提醒",
                "content": f"你通常在 {', '.join(formatted)} 左右写日记，现在是写作的好时机哦~",
                "action": "new_entry",
                "priority": 8,
                "display_level": "instant",
            }

        return None

    def generate_review_recommendation(self) -> dict | None:
        """生成内容回顾推荐"""
        # 去年今日
        worthy = self.content.get_review_worthy(days_ago=365)
        if worthy:
            entry = worthy[0]
            return {
                "type": "content_review",
                "title": "🕰️ 去年今日",
                "content": f"《{entry['title']}》— 去年今天你写下了这篇日记",
                "action": "view_entry",
                "entry_id": entry["id"],
                "priority": 6,
                "display_level": "daily",
            }

        # 半年前
        worthy_half = self.content.get_review_worthy(days_ago=180)
        if worthy_half:
            entry = worthy_half[0]
            return {
                "type": "content_review",
                "title": "📅 半年前的今天",
                "content": f"《{entry['title']}》— 半年前的回忆",
                "action": "view_entry",
                "entry_id": entry["id"],
                "priority": 4,
                "display_level": "daily",
            }

        return None

    def generate_mood_insight(self) -> dict | None:
        """生成心情洞察推荐"""
        mood_trend = self.habit.get_mood_trend(30)

        if not mood_trend:
            return None

        # 统计心情分布
        from collections import Counter
        recent_7 = Counter()
        recent_30 = Counter()

        for item in mood_trend:
            mood = item["mood"]
            day = item["d"]
            recent_30[mood] += item["cnt"]

            # 最近 7 天
            from datetime import timedelta as td
            target = (date.today() - td(days=7)).isoformat()
            if day >= target:
                recent_7[mood] += item["cnt"]

        if not recent_30:
            return None

        # 检测趋势
        total_30 = sum(recent_30.values())
        total_7 = sum(recent_7.values())

        if total_30 < 5:
            return None  # 数据太少

        # 检查负面情绪比例
        negative_moods = {"sad": "难过", "anxious": "焦虑"}
        neg_ratio_30 = sum(recent_30.get(m, 0) for m in negative_moods) / max(total_30, 1)
        neg_ratio_7 = sum(recent_7.get(m, 0) for m in negative_moods) / max(total_7, 1)

        if neg_ratio_7 > 0.5 and neg_ratio_7 > neg_ratio_30 * 1.3:
            return {
                "type": "mood_insight",
                "title": "🤗 心情关怀",
                "content": "最近负面情绪似乎多了一些，试着写下三件让你感恩的小事吧",
                "action": "new_entry_with_template",
                "template": "感恩日记",
                "priority": 7,
                "display_level": "daily",
            }

        # 检测情绪改善
        happy_moods = {"happy": "开心", "excited": "兴奋"}
        happy_ratio_30 = sum(recent_30.get(m, 0) for m in happy_moods) / max(total_30, 1)
        happy_ratio_7 = sum(recent_7.get(m, 0) for m in happy_moods) / max(total_7, 1)

        if happy_ratio_7 > happy_ratio_30 * 1.3 and total_7 >= 3:
            return {
                "type": "mood_insight",
                "title": "🌈 心情好转",
                "content": "最近一周你的心情明显好转，继续保持！",
                "action": None,
                "priority": 5,
                "display_level": "daily",
            }

        return None

    def generate_topic_recommendation(self) -> dict | None:
        """生成话题/模板推荐"""
        clusters = self.content.get_topic_clusters(90)

        if not clusters:
            return None

        # 找到频繁出现的话题
        top_topic = clusters[0]
        if top_topic["frequency"] >= 3:
            return {
                "type": "topic_suggest",
                "title": "💭 话题推荐",
                "content": f"你最近经常写关于「{top_topic['topic']}」的内容",
                "action": "search_by_topic",
                "topic": top_topic["topic"],
                "priority": 3,
                "display_level": "session",
            }

        return None

    def generate_achievement_recommendation(self) -> dict | None:
        """生成成就推荐"""
        achievements = self.habit.check_achievements()
        stats = self.habit.get_writing_stats(30)

        if not achievements:
            # 给一个统计型推荐代替
            consecutive = stats.get("consecutive_days", 0)
            if consecutive >= 2:
                return {
                    "type": "achievement",
                    "title": "🔥 写作连胜",
                    "content": f"已连续写作 {consecutive} 天，坚持就是胜利！",
                    "action": None,
                    "priority": 2,
                    "display_level": "daily",
                }

            return None

        ach = achievements[0]
        return {
            "type": "achievement",
            "title": ach["title"],
            "content": ach["description"],
            "action": "view_stats",
            "priority": 9,
            "display_level": "instant",
        }

    def get_active_recommendations(self) -> list[dict]:
        """获取当前有效的推荐（按优先级排序）"""
        all_recs = self.generate_all_recommendations()
        active = []

        for key, rec in all_recs.items():
            if rec:
                rec["id"] = db_manager.log_recommendation(rec["type"], rec["content"])
                active.append(rec)

        # 按优先级排序
        active.sort(key=lambda x: x.get("priority", 0), reverse=True)
        return active

    def dismiss_recommendation(self, rec_id: int):
        """关闭推荐"""
        db_manager.feedback_recommendation(rec_id, followed=False, dismissed=True)

    def follow_recommendation(self, rec_id: int):
        """采纳推荐"""
        db_manager.feedback_recommendation(rec_id, followed=True)
