"""搜索屏幕"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.chip import MDChip
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from datetime import date, timedelta
from libs.database import db_manager

MOODS = ["全部", "😊 开心", "😢 难过", "😐 平静", "😃 兴奋", "😰 焦虑", "😌 放松"]
MOOD_KEYS = ["", "happy", "sad", "neutral", "excited", "anxious", "calm"]
CATEGORIES = ["全部", "工作", "生活", "学习", "旅行", "情感", "健康", "其他"]


class SearchScreen(MDScreen):
    """搜索屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._build_ui()

    def _build_ui(self):
        # 顶部栏
        self.top_bar = MDTopAppBar(
            title="搜索日记",
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
        )
        self.add_widget(self.top_bar)

        # 主体
        main = MDScrollView()
        self.container = MDBoxLayout(
            orientation="vertical",
            padding=[dp(15), dp(10), dp(15), dp(20)],
            spacing=dp(10),
            adaptive_height=True,
        )
        main.add_widget(self.container)

        # 搜索框
        search_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(50), spacing=dp(8))
        self.search_field = MDTextField(
            hint_text="输入关键词搜索...",
            mode="rectangle",
            size_hint_x=0.78,
        )
        search_row.add_widget(self.search_field)
        search_row.add_widget(MDIconButton(
            icon="magnify", on_release=lambda x: self._do_search()))
        self.container.add_widget(search_row)

        # 心情筛选
        self.container.add_widget(MDLabel(
            text="心情筛选", font_style="Body2", bold=True,
            size_hint_y=None, height=dp(28)))
        mood_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(36), spacing=dp(6))
        self.mood_chips = []
        for i, m in enumerate(MOODS):
            chip = MDChip(text=m, type_="choice",
                          size_hint_x=None, width=dp(68),
                          on_press=lambda x, idx=i: self._select_mood(idx))
            if i == 0:
                chip.active = True
            mood_row.add_widget(chip)
            self.mood_chips.append(chip)
        self.container.add_widget(mood_row)
        self._selected_mood = 0

        # 分类筛选
        self.container.add_widget(MDLabel(
            text="分类筛选", font_style="Body2", bold=True,
            size_hint_y=None, height=dp(28)))
        cat_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(36), spacing=dp(6))
        self.cat_chips = []
        for i, c in enumerate(CATEGORIES):
            chip = MDChip(text=c, type_="choice",
                          size_hint_x=None, width=dp(64),
                          on_press=lambda x, idx=i: self._select_cat(idx))
            if i == 0:
                chip.active = True
            cat_row.add_widget(chip)
            self.cat_chips.append(chip)
        self.container.add_widget(cat_row)
        self._selected_cat = 0

        # 结果区域
        self.results_label = MDLabel(
            text="", font_style="Caption", theme_text_color="Secondary",
            size_hint_y=None, height=dp(24))
        self.container.add_widget(self.results_label)
        self.results_box = MDBoxLayout(
            orientation="vertical", spacing=dp(6),
            adaptive_height=True)
        self.container.add_widget(self.results_box)

        self.add_widget(main)

        # 调整布局
        from kivy.clock import Clock
        Clock.schedule_once(self._update_layout, 0.1)
        Clock.schedule_once(lambda dt: self._do_search(), 0.3)

    def _update_layout(self, dt):
        top = self.top_bar.height
        for child in self.children:
            if isinstance(child, MDScrollView):
                child.pos_hint = {"top": 1 - top / self.height}
                child.size = (self.width, self.height - top)

    def _select_mood(self, idx):
        for i, chip in enumerate(self.mood_chips):
            chip.active = (i == idx)
        self._selected_mood = idx
        self._do_search()

    def _select_cat(self, idx):
        for i, chip in enumerate(self.cat_chips):
            chip.active = (i == idx)
        self._selected_cat = idx
        self._do_search()

    def _do_search(self):
        keyword = self.search_field.text.strip()
        mood = MOOD_KEYS[self._selected_mood]
        cat = CATEGORIES[self._selected_cat] if self._selected_cat > 0 else ""

        results = db_manager.search_entries(
            keyword=keyword, mood=mood, category=cat)

        self.results_box.clear_widgets()
        self.results_label.text = f"找到 {len(results)} 篇日记"

        mood_emoji = {"happy": "😊", "sad": "😢", "neutral": "😐",
                      "excited": "😃", "anxious": "😰", "calm": "😌"}

        for entry in results:
            emoji = mood_emoji.get(entry.get("mood", "neutral"), "😐")
            title = entry.get("title", "无标题")
            if len(title) > 24:
                title = title[:23] + "…"

            card = MDCard(
                orientation="vertical",
                padding=[dp(12), dp(8), dp(12), dp(8)],
                size_hint_y=None, height=dp(60),
                radius=dp(8), elevation=1,
                ripple_behavior=True,
                on_release=lambda x, eid=entry["id"]: self._open_entry(eid),
            )
            card.add_widget(MDLabel(
                text=f"{emoji} {title}",
                font_style="Body1", bold=True, shorten=True))
            card.add_widget(MDLabel(
                text=f"{entry.get('created_at', '')} | {entry.get('word_count', 0)}字 | {entry.get('category', '默认')}",
                font_style="Caption", theme_text_color="Secondary"))
            self.results_box.add_widget(card)

    def _open_entry(self, entry_id):
        from ui.screens.editor_screen import EditorScreen
        screen = EditorScreen(name="editor", entry_id=entry_id)
        self.manager.add_widget(screen)
        self.manager.current = "editor"

    def _go_back(self):
        if self.manager.has_screen("diary_list"):
            self.manager.current = "diary_list"
            self.manager.remove_widget(self)
