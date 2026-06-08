"""统计屏幕"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from kivymd.app import MDApp


class StatsScreen(MDScreen):
    """写作统计"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def on_enter(self):
        self._refresh()

    def _build_ui(self):
        # 顶部栏
        self.top_bar = MDTopAppBar(
            title="写作统计",
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
        )
        self.add_widget(self.top_bar)

        # 滚动主体
        self.scroll = MDScrollView()
        self.container = MDBoxLayout(
            orientation="vertical",
            padding=[dp(15), dp(10), dp(15), dp(30)],
            spacing=dp(12),
            adaptive_height=True,
        )
        self.scroll.add_widget(self.container)

        # 洞察卡片区
        self.cards_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(90), spacing=dp(8))
        self.container.add_widget(self.cards_row)

        # 详细统计
        self.detail_area = MDBoxLayout(
            orientation="vertical", spacing=dp(8),
            adaptive_height=True)
        self.container.add_widget(self.detail_area)

        self.add_widget(self.scroll)

        from kivy.clock import Clock
        Clock.schedule_once(self._update_layout, 0.1)

    def _update_layout(self, dt):
        top = self.top_bar.height
        self.scroll.pos_hint = {"top": 1 - top / self.height}
        self.scroll.size = (self.width, self.height - top)

    def _refresh(self):
        self.cards_row.clear_widgets()
        self.detail_area.clear_widgets()

        app = MDApp.get_running_app()
        if not app or not app.habit_tracker:
            self.detail_area.add_widget(MDLabel(
                text="暂无统计数据\n\n开始写日记后这里会显示你的写作统计",
                halign="center", theme_text_color="Secondary",
                font_style="Body1",
                size_hint_y=None, height=dp(100)))
            return

        stats = app.habit_tracker.get_writing_stats(30)

        # 洞察卡片
        cards_data = [
            ("🔥 连续写作", f"{stats['consecutive_days']} 天", [1, 0.42, 0.42, 1]),
            ("📝 总篇数", f"{stats['total_entries']} 篇", [0.3, 0.8, 0.77, 1]),
            ("📄 总字数", f"{stats['total_words']:,}", [0.27, 0.72, 0.82, 1]),
            ("📊 日均", f"{stats['avg_words_per_day']}字", [0.59, 0.8, 0.7, 1]),
        ]

        for title, value, color in cards_data:
            card = MDCard(
                orientation="vertical",
                padding=[dp(10), dp(8), dp(10), dp(8)],
                size_hint_x=1,
                size_hint_y=None, height=dp(80),
                radius=dp(12),
                md_bg_color=color,
            )
            card.add_widget(MDLabel(
                text=title, font_style="Caption", bold=True,
                theme_text_color="Custom", text_color=[1, 1, 1, 1]))
            card.add_widget(MDLabel(
                text=value, font_style="H5", bold=True,
                theme_text_color="Custom", text_color=[1, 1, 1, 1]))
            self.cards_row.add_widget(card)

        # 详细统计
        details = [
            ("总篇数", f"{stats['total_entries']} 篇"),
            ("总字数", f"{stats['total_words']:,} 字"),
            ("连续写作", f"{stats['consecutive_days']} 天"),
            ("日均字数", f"{stats['avg_words_per_day']} 字/天"),
            ("最佳写作日", stats.get('preferred_day', '暂无')),
            ("最佳写作时段", f"{stats.get('preferred_hour', '暂无')}:00" if stats.get('preferred_hour') else '暂无'),
        ]

        for label, value in details:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(36),
                padding=[dp(5), 0])
            row.add_widget(MDLabel(
                text=label, font_style="Body1", theme_text_color="Secondary"))
            row.add_widget(MDLabel(
                text=value, font_style="Body1", bold=True, halign="right"))
            self.detail_area.add_widget(row)

        # 心情分布
        moods = stats.get("mood_distribution", {})
        if moods:
            self.detail_area.add_widget(MDLabel(
                text="心情分布", font_style="H6", bold=True,
                size_hint_y=None, height=dp(36)))
            mood_names = {"happy": "😊 开心", "sad": "😢 难过", "neutral": "😐 平静",
                          "excited": "😃 兴奋", "anxious": "😰 焦虑", "calm": "😌 放松"}
            total = sum(moods.values()) or 1
            for mk, count in sorted(moods.items(), key=lambda x: x[1], reverse=True):
                pct = count / total * 100
                row = MDBoxLayout(
                    orientation="horizontal",
                    size_hint_y=None, height=dp(30))
                row.add_widget(MDLabel(
                    text=mood_names.get(mk, mk), font_style="Body2",
                    size_hint_x=0.35))
                # 简易进度条
                bar = MDBoxLayout(
                    md_bg_color=[0.2, 0.6, 1, 0.7],
                    size_hint_x=pct / 200,
                    size_hint_y=None, height=dp(14),
                    radius=[dp(7)],
                )
                row.add_widget(bar)
                row.add_widget(MDLabel(
                    text=f"{count}篇 ({pct:.0f}%)", font_style="Caption",
                    theme_text_color="Secondary", size_hint_x=0.35))
                self.detail_area.add_widget(row)

    def _go_back(self):
        if self.manager.has_screen("diary_list"):
            self.manager.current = "diary_list"
            self.manager.remove_widget(self)
