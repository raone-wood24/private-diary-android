"""日记列表主屏幕 — 底部导航 + 日记卡片列表"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFloatingActionButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import date, datetime
from collections import defaultdict
from libs.database import db_manager
from ui.components.diary_card import DiaryCardList
from ui.themes import MOOD_COLORS


class DiaryListScreen(MDScreen):
    """主屏幕 — 日记列表"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_date = None  # None = 全部
        self._build_ui()

    def on_enter(self):
        """每次进入屏幕时刷新"""
        self._refresh()

    def _build_ui(self):
        """构建界面"""
        # 顶部栏
        self.top_bar = MDTopAppBar(
            title="私人日记",
            right_action_items=[
                ["magnify", lambda x: self._go_search()],
                ["chart-bar", lambda x: self._go_stats()],
                ["cog", lambda x: self._go_settings()],
            ],
            elevation=2,
        )
        self.add_widget(self.top_bar)

        # 推荐横幅
        self.rec_banner = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(0),
            padding=[dp(15), dp(5)],
            spacing=dp(5),
            md_bg_color=[0.95, 0.97, 1, 1],
        )
        self.add_widget(self.rec_banner)

        # 可滚动日记列表
        self.scroll = MDScrollView(
            pos_hint={"top": 1},
            size_hint=(1, None),
        )
        self.scroll.bind(minimum_height=self.scroll.setter("height"))

        self.list_container = MDBoxLayout(
            orientation="vertical",
            padding=[dp(12), dp(8), dp(12), dp(80)],
            spacing=dp(6),
            adaptive_height=True,
        )
        self.scroll.add_widget(self.list_container)
        self.add_widget(self.scroll)

        # 浮动新建按钮
        self.fab = MDFloatingActionButton(
            icon="plus",
            pos_hint={"right": 0.05, "bottom": 0.02},
            on_release=self._new_entry,
        )
        self.add_widget(self.fab)

        # 更新布局
        Clock.schedule_once(self._update_layout, 0.1)

    def _update_layout(self, dt):
        """计算滚动区域位置"""
        top_h = self.top_bar.height + self.rec_banner.height
        self.scroll.pos_hint = {"top": 1 - top_h / self.height}
        self.scroll.size = (self.width, self.height - top_h)

    def _build_recommendation_banner(self):
        """构建推荐横幅"""
        self.rec_banner.clear_widgets()
        app = self._get_app()
        if not app or not app.recommendation_engine:
            self.rec_banner.height = dp(0)
            return

        try:
            recs = app.recommendation_engine.get_active_recommendations()
        except Exception:
            self.rec_banner.height = dp(0)
            return

        if not recs:
            self.rec_banner.height = dp(0)
            return

        for rec in recs[:1]:  # 只显示第一条
            card = MDCard(
                orientation="vertical",
                padding=[dp(12), dp(8), dp(12), dp(8)],
                size_hint_y=None,
                height=dp(56),
                radius=dp(10),
                md_bg_color=[0.9, 0.95, 1, 1],
                ripple_behavior=True,
                on_release=lambda x, r=rec: self._on_rec_click(r),
            )
            card.add_widget(MDLabel(
                text=rec.get("title", ""),
                font_style="Body2",
                bold=True,
            ))
            card.add_widget(MDLabel(
                text=rec.get("content", ""),
                font_style="Caption",
                theme_text_color="Secondary",
                shorten=True,
            ))
            self.rec_banner.add_widget(card)
            self.rec_banner.height = dp(64)

    def _refresh(self):
        """刷新列表"""
        entries = db_manager.get_all_entries()
        self.list_container.clear_widgets()

        # 构建推荐
        self._build_recommendation_banner()
        Clock.schedule_once(self._update_layout, 0.1)

        if not entries:
            self.list_container.add_widget(MDLabel(
                text="[size=18]📝[/size]\n还没有日记\n点击右下角 + 开始写作",
                halign="center",
                markup=True,
                theme_text_color="Secondary",
                font_style="Body1",
                size_hint_y=None,
                height=dp(120),
            ))
            return

        # 按日期分组
        grouped = defaultdict(list)
        for e in entries:
            day = e["created_at"][:10] if e["created_at"] else "未知"
            grouped[day].append(e)

        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        for day in sorted(grouped.keys(), reverse=True):
            entries_day = grouped[day]
            # 日期头
            try:
                dt = datetime.strptime(day, "%Y-%m-%d")
                day_label = f"📅 {day} {weekdays[dt.weekday()]}"
            except Exception:
                day_label = f"📅 {day}"

            self.list_container.add_widget(MDLabel(
                text=day_label,
                font_style="Body2",
                bold=True,
                theme_text_color="Custom",
                text_color=[0.2, 0.5, 0.8, 1],
                size_hint_y=None,
                height=dp(30),
            ))

            for entry in entries_day:
                card = self._build_entry_card(entry)
                self.list_container.add_widget(card)

    def _build_entry_card(self, entry):
        """构建单条日记卡片"""
        mood_emoji = {"happy": "😊", "sad": "😢", "neutral": "😐",
                      "excited": "😃", "anxious": "😰", "calm": "😌"}
        emoji = mood_emoji.get(entry.get("mood", "neutral"), "😐")
        mood_color = MOOD_COLORS.get(entry.get("mood", "neutral"), [0.6, 0.6, 0.6, 1])

        title = entry.get("title", "无标题")
        if len(title) > 20:
            title = title[:19] + "…"

        time_str = entry.get("created_at", "")[11:16] if entry.get("created_at") else ""
        wc = entry.get("word_count", 0)

        card = MDCard(
            orientation="vertical",
            padding=[dp(14), dp(10), dp(14), dp(10)],
            size_hint_y=None,
            height=dp(64),
            radius=dp(10),
            elevation=1,
            ripple_behavior=True,
            on_release=lambda x, eid=entry["id"]: self._open_entry(eid),
        )

        card.add_widget(MDLabel(
            text=f"{emoji}  {title}",
            font_style="Body1",
            bold=True,
            shorten=True,
        ))

        card.add_widget(MDLabel(
            text=f"{time_str}  |  {wc} 字  |  {entry.get('category', '默认')}",
            font_style="Caption",
            theme_text_color="Secondary",
        ))

        # 长按删除
        card.bind(on_long_touch=lambda x, t, eid=entry["id"]: self._confirm_delete(eid))

        return card

    def _open_entry(self, entry_id):
        """打开日记编辑"""
        from ui.screens.editor_screen import EditorScreen
        screen = EditorScreen(name="editor", entry_id=entry_id)
        self.manager.add_widget(screen)
        self.manager.current = "editor"

    def _new_entry(self, *args):
        """新建日记"""
        from ui.screens.editor_screen import EditorScreen
        screen = EditorScreen(name="editor", entry_id=None)
        self.manager.add_widget(screen)
        self.manager.current = "editor"

    def _go_search(self, *args):
        """跳转搜索"""
        from ui.screens.search_screen import SearchScreen
        self.manager.add_widget(SearchScreen(name="search"))
        self.manager.current = "search"

    def _go_stats(self, *args):
        """跳转统计"""
        from ui.screens.stats_screen import StatsScreen
        self.manager.add_widget(StatsScreen(name="stats"))
        self.manager.current = "stats"

    def _go_settings(self, *args):
        """跳转设置"""
        from ui.screens.settings_screen import SettingsScreen
        self.manager.add_widget(SettingsScreen(name="settings"))
        self.manager.current = "settings"

    def _on_rec_click(self, rec):
        """推荐卡片点击"""
        action = rec.get("action", "")
        if action == "new_entry":
            self._new_entry()
        elif action == "view_entry" and rec.get("entry_id"):
            self._open_entry(rec["entry_id"])
        elif action == "view_stats":
            self._go_stats()
        elif action == "search_by_topic":
            from ui.screens.search_screen import SearchScreen
            screen = SearchScreen(name="search")
            self.manager.add_widget(screen)
            self.manager.current = "search"

    def _confirm_delete(self, entry_id):
        """确认删除"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDButton, MDButtonText

        dialog = MDDialog(
            title="确认删除",
            text="确定要删除这篇日记吗？此操作不可撤销。",
            buttons=[
                MDButton(MDButtonText(text="取消"),
                         on_release=lambda x: dialog.dismiss()),
                MDButton(MDButtonText(text="删除"),
                         on_release=lambda x: self._do_delete(entry_id, dialog)),
            ],
        )
        dialog.open()

    def _do_delete(self, entry_id, dialog):
        """执行删除"""
        db_manager.delete_entry(entry_id)
        dialog.dismiss()
        self._refresh()

    def _get_app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()
