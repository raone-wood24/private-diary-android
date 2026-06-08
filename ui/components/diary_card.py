"""日记卡片组件 — 供列表屏幕使用"""

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from ui.themes import MOOD_COLORS


class DiaryCard(MDCard):
    """单条日记卡片"""

    def __init__(self, entry, on_press=None, **kwargs):
        super().__init__(**kwargs)
        self.entry = entry
        self.on_press = on_press
        self.orientation = "vertical"
        self.padding = [dp(14), dp(10), dp(14), dp(10)]
        self.size_hint_y = None
        self.height = dp(68)
        self.radius = dp(10)
        self.elevation = 1
        self.ripple_behavior = True

        self._build()

    def _build(self):
        entry = self.entry

        mood_emoji = {"happy": "😊", "sad": "😢", "neutral": "😐",
                      "excited": "😃", "anxious": "😰", "calm": "😌"}
        emoji = mood_emoji.get(entry.get("mood", "neutral"), "😐")

        title = entry.get("title", "无标题")
        if len(title) > 22:
            title = title[:21] + "…"

        time_str = entry.get("created_at", "")[11:16] if entry.get("created_at") else ""
        wc = entry.get("word_count", 0)

        self.add_widget(MDLabel(
            text=f"{emoji}  {title}",
            font_style="Body1",
            bold=True,
            shorten=True,
        ))

        self.add_widget(MDLabel(
            text=f"{time_str}  |  {wc} 字  |  {entry.get('category', '默认')}",
            font_style="Caption",
            theme_text_color="Secondary",
        ))


class DiaryCardList:
    """日记卡片列表构建工具"""

    @staticmethod
    def build_grouped_list(container, entries, on_press, on_long_press=None):
        """按日期分组构建卡片列表"""
        from collections import defaultdict
        from datetime import datetime

        container.clear_widgets()

        if not entries:
            container.add_widget(MDLabel(
                text="📝\n还没有日记\n点击下方 + 开始写作",
                halign="center",
                theme_text_color="Secondary",
                font_style="Body1",
                size_hint_y=None,
                height=dp(100),
            ))
            return

        grouped = defaultdict(list)
        for e in entries:
            day = e["created_at"][:10] if e["created_at"] else "未知"
            grouped[day].append(e)

        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for day in sorted(grouped.keys(), reverse=True):
            entries_day = grouped[day]
            try:
                dt = datetime.strptime(day, "%Y-%m-%d")
                day_label = f"📅 {day} {weekdays[dt.weekday()]}  ({len(entries_day)}篇)"
            except Exception:
                day_label = f"📅 {day}"

            container.add_widget(MDBoxLayout(
                MDLabel(text=day_label, font_style="Body2", bold=True,
                        theme_text_color="Custom", text_color=[0.2, 0.5, 0.8, 1]),
                size_hint_y=None, height=dp(30),
                adaptive_width=True,
            ))

            for entry in entries_day:
                card = DiaryCard(entry=entry, on_press=on_press)
                if on_long_press:
                    card.bind(on_long_touch=lambda x, t, e=entry: on_long_press(e["id"]))
                container.add_widget(card)
