"""智能洞察与报告生成模块"""

from datetime import datetime, date, timedelta
from collections import Counter
from libs.personalization.habit_tracker import HabitTracker
from libs.recommendation.behavior_analyzer import BehaviorAnalyzer
from libs.database import db_manager


class InsightGenerator:
    """生成写作洞察和报告"""

    def __init__(self):
        self.habit = HabitTracker()
        self.behavior = BehaviorAnalyzer()

    def generate_weekly_report(self) -> dict:
        """生成周报"""
        stats = self.habit.get_writing_stats(7)
        time_profile = self.behavior.analyze_writing_time(7)

        # 本周最佳写作日
        day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        best_day_idx = None
        if time_profile.get("day_distribution"):
            day_dist = time_profile["day_distribution"]
            if day_dist:
                best_day_idx = max(day_dist, key=day_dist.get)

        # 心情变化
        mood_data = self.habit.get_mood_trend(7)
        mood_seq = []
        for m in mood_data:
            mood_seq.append({"date": m["d"], "mood": m["mood"], "count": m["cnt"]})

        return {
            "title": f"📊 本周写作报告 ({date.today().isoformat()})",
            "summary": {
                "total_entries": stats.get("total_entries", 0),
                "total_words": stats.get("total_words", 0),
                "consecutive_days": stats.get("consecutive_days", 0),
                "best_day": day_names[best_day_idx] if best_day_idx is not None else "暂无",
                "preferred_hour": time_profile.get("preferred_time_slot", "暂无"),
            },
            "mood_timeline": mood_seq,
            "avg_words_per_day": stats.get("avg_words_per_day", 0),
        }

    def generate_monthly_report(self) -> dict:
        """生成月报"""
        stats = self.habit.get_writing_stats(30)
        time_profile = self.behavior.analyze_writing_time(30)
        frequency = self.behavior.analyze_writing_frequency(30)

        # 获取月度心情分布
        mood_dist = stats.get("mood_distribution", {})
        mood_names = {
            "happy": "开心", "sad": "难过", "neutral": "平静",
            "excited": "兴奋", "anxious": "焦虑", "calm": "放松"
        }
        mood_pie = []
        for mood_key, count in mood_dist.items():
            mood_pie.append({
                "name": mood_names.get(mood_key, mood_key),
                "count": count
            })
        mood_pie.sort(key=lambda x: x["count"], reverse=True)

        # 话题排行
        top_keywords = db_manager.get_top_keywords(30, limit=10)

        return {
            "title": f"📈 本月写作报告 ({date.today().strftime('%Y年%m月')})",
            "summary": {
                "total_entries": stats.get("total_entries", 0),
                "total_words": stats.get("total_words", 0),
                "consecutive_days": stats.get("consecutive_days", 0),
                "days_written": frequency.get("total_days_written", 0),
                "avg_interval": frequency.get("avg_interval_days", 0),
            },
            "mood_distribution": mood_pie,
            "top_keywords": [{"keyword": k["keyword"], "freq": k["freq"]} for k in top_keywords],
            "time_slot": time_profile.get("time_slot_distribution", {}),
            "weekday_ratio": time_profile.get("weekday_ratio", 0.5),
        }

    def generate_insight_cards(self) -> list[dict]:
        """生成首页洞察卡片"""
        cards = []
        stats = self.habit.get_writing_stats(30)

        # 连续天数卡片
        consecutive = stats.get("consecutive_days", 0)
        if consecutive > 0:
            cards.append({
                "title": "🔥 连续写作",
                "value": f"{consecutive} 天",
                "subtitle": "坚持下去！",
                "color": "#ff6b6b",
            })

        # 总字数卡片
        total_words = stats.get("total_words", 0)
        if total_words > 0:
            if total_words >= 10000:
                display = f"{total_words / 10000:.1f} 万字"
            else:
                display = f"{total_words} 字"
            cards.append({
                "title": "📝 累计写作",
                "value": display,
                "subtitle": f"共 {stats.get('total_entries', 0)} 篇",
                "color": "#4ecdc4",
            })

        # 平均字数
        avg_words = stats.get("avg_words_per_day", 0)
        if avg_words > 0:
            cards.append({
                "title": "📊 日均字数",
                "value": f"{int(avg_words)} 字",
                "subtitle": "每天进步一点点",
                "color": "#45b7d1",
            })

        # 最常用心情
        moods = stats.get("mood_distribution", {})
        if moods:
            mood_names = {"happy": "😊", "sad": "😢", "neutral": "😐",
                          "excited": "😃", "anxious": "😰", "calm": "😌"}
            top_mood = max(moods, key=moods.get)
            cards.append({
                "title": "😊 主要心情",
                "value": f"{mood_names.get(top_mood, '😐')} {mood_names.get(top_mood, top_mood)}",
                "subtitle": f"占 {moods[top_mood] / max(sum(moods.values()), 1) * 100:.0f}%",
                "color": "#96ceb4",
            })

        return cards

    def get_heatmap_data(self, days: int = 90) -> dict:
        """获取热力图数据"""
        return self.habit.get_writing_heatmap(days)
