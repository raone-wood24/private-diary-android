"""日记编辑器屏幕"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton, MDFillRoundFlatButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.chip import MDChip
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import datetime, date
from libs.database import db_manager
from libs.crypto.encryption import encrypt, decrypt
from libs.personalization.habit_tracker import HabitTracker
from ui.themes import MOOD_COLORS


MOODS = ["😊 开心", "😢 难过", "😐 平静", "😃 兴奋", "😰 焦虑", "😌 放松"]
MOOD_KEYS = ["happy", "sad", "neutral", "excited", "anxious", "calm"]
CATEGORIES = ["默认", "工作", "生活", "学习", "旅行", "情感", "健康", "其他"]
TEMPLATES = {
    "日记模板": "📅 日期：\n☀️ 天气：\n😊 心情：\n\n📝 今日摘要：\n\n📋 今日事件：\n1. \n2. \n3. \n\n💭 今日感悟：\n\n📌 明日计划：",
    "工作记录": "📋 今日完成：\n1. \n2. \n\n⏳ 进行中：\n\n🚧 遇到的困难：\n\n💡 解决方案：\n\n🎯 明日目标：",
    "感恩日记": "🙏 今天感恩的三件事：\n1. \n2. \n3. \n\n😊 今天让我开心的事：\n\n💪 我今天做得好的地方：",
    "学习笔记": "📚 学习主题：\n\n📖 核心内容：\n\n💡 我的理解：\n\n❓ 疑问：\n\n🔗 相关知识点：",
    "周复盘": "📊 本周成就：\n\n⚠️ 不足之处：\n\n📈 下周计划：\n\n🎯 下周目标：",
}


class EditorScreen(MDScreen):
    """日记编辑屏幕"""

    def __init__(self, entry_id=None, **kwargs):
        super().__init__(**kwargs)
        self.entry_id = entry_id
        self.current_mood = "neutral"
        self.current_category = "默认"
        self.original_word_count = 0
        self.tracker = HabitTracker()
        self.session_id = None
        self._modified = False
        self._build_ui()

        if entry_id:
            self._load_entry(entry_id)
        else:
            self._start_session()

    def _build_ui(self):
        """构建界面"""
        # 顶部栏
        self.top_bar = MDTopAppBar(
            title="写日记" if not self.entry_id else "编辑日记",
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
            right_action_items=[
                ["content-save", lambda x: self._save()],
                ["text-box-outline", lambda x: self._show_templates()],
            ],
            elevation=2,
        )
        self.add_widget(self.top_bar)

        # 主区域
        main = MDScrollView()
        self.container = MDBoxLayout(
            orientation="vertical",
            padding=[dp(15), dp(10), dp(15), dp(20)],
            spacing=dp(10),
            adaptive_height=True,
        )
        main.add_widget(self.container)

        # 标题
        self.title_field = MDTextField(
            hint_text="日记标题...",
            mode="rectangle",
            font_style="H6",
            size_hint_y=None,
            height=dp(50),
        )
        self.container.add_widget(self.title_field)

        # 心情选择
        mood_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6),
        )
        mood_row.add_widget(MDLabel(
            text="心情:", font_style="Body2", size_hint_x=0.15,
            theme_text_color="Secondary"))
        for i, mood_text in enumerate(MOODS):
            chip = MDChip(
                text=mood_text,
                type_="choice",
                size_hint_x=None,
                width=dp(72),
                on_press=lambda x, mk=MOOD_KEYS[i]: self._select_mood(mk),
            )
            if MOOD_KEYS[i] == "neutral":
                chip.active = True
            mood_row.add_widget(chip)
        self.container.add_widget(mood_row)

        # 分类
        cat_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6),
        )
        cat_row.add_widget(MDLabel(
            text="分类:", font_style="Body2", size_hint_x=0.15,
            theme_text_color="Secondary"))
        self.cat_chips = {}
        for cat in CATEGORIES[:4]:
            chip = MDChip(
                text=cat,
                type_="choice",
                size_hint_x=None,
                width=dp(64),
                on_press=lambda x, c=cat: self._select_category(c),
            )
            if cat == "默认":
                chip.active = True
            cat_row.add_widget(chip)
            self.cat_chips[cat] = chip
        self.container.add_widget(cat_row)

        # 更多分类
        more_cats = CATEGORIES[4:]
        more_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6),
        )
        for cat in more_cats:
            chip = MDChip(
                text=cat,
                type_="choice",
                size_hint_x=None,
                width=dp(64),
                on_press=lambda x, c=cat: self._select_category(c),
            )
            more_row.add_widget(chip)
            self.cat_chips[cat] = chip
        self.container.add_widget(more_row)

        # 正文
        self.content_field = MDTextField(
            hint_text="开始写作...\n\n记录今天的故事、想法和感受",
            mode="rectangle",
            multiline=True,
            size_hint_y=None,
            height=dp(350),
        )
        self.content_field.bind(text=self._on_text_changed)
        self.container.add_widget(self.content_field)

        # 字数统计
        self.wc_label = MDLabel(
            text="0 字", halign="right",
            font_style="Caption", theme_text_color="Secondary",
            size_hint_y=None, height=dp(20),
        )
        self.container.add_widget(self.wc_label)

        # 保存按钮
        save_btn = MDFillRoundFlatButton(
            text="保存日记",
            size_hint_x=0.7,
            pos_hint={"center_x": 0.5},
            on_release=lambda x: self._save(),
        )
        self.container.add_widget(MDBoxLayout(size_hint_y=None, height=dp(10)))
        self.container.add_widget(save_btn)

        self.add_widget(main)

        # 调整主区域位置
        Clock.schedule_once(self._update_layout, 0.1)

    def _update_layout(self, dt):
        """调整布局"""
        top = self.top_bar.height
        for child in self.children:
            if isinstance(child, MDScrollView):
                child.pos_hint = {"top": 1 - top / self.height}
                child.size = (self.width, self.height - top)

    def _select_mood(self, mood_key):
        self.current_mood = mood_key

    def _select_category(self, cat):
        self.current_category = cat

    def _on_text_changed(self, instance, value):
        count = len(value.replace("\n", "").replace(" ", ""))
        self.wc_label.text = f"{count} 字"

    def _start_session(self):
        self.session_id = self.tracker.start_session()

    def _load_entry(self, entry_id):
        entry = db_manager.get_entry(entry_id)
        if not entry:
            return

        self.title_field.text = entry.get("title", "")
        self.current_mood = entry.get("mood", "neutral")
        self.current_category = entry.get("category", "默认")
        self.original_word_count = entry.get("word_count", 0)

        # 解密
        app = self._get_app()
        if app and app.encryption_key:
            try:
                content = decrypt(entry["content_encrypted"], entry["iv"], app.encryption_key)
                self.content_field.text = content
            except Exception:
                self.content_field.text = "[解密失败]"

        # 更新 UI
        for child in self.container.children:
            if isinstance(child, MDBoxLayout) and child.children:
                for chip in child.children:
                    if isinstance(chip, MDChip):
                        # 更新心情 chip
                        mood_idx = None
                        try:
                            mood_idx = MOOD_KEYS.index(self.current_mood)
                        except ValueError:
                            pass
                        if mood_idx is not None and chip.text == MOODS[mood_idx]:
                            chip.active = True

        self._start_session()
        self._modified = False

    def _save(self):
        """保存日记"""
        title = self.title_field.text.strip()
        content = self.content_field.text.strip()

        if not title:
            self._snack("请输入日记标题")
            return

        app = self._get_app()
        if not app or not app.encryption_key:
            self._snack("加密密钥不可用")
            return

        word_count = len(content.replace("\n", "").replace(" ", ""))
        word_count_delta = word_count - self.original_word_count

        # 加密
        ciphertext, iv = encrypt(content, app.encryption_key)

        try:
            if self.entry_id:
                db_manager.update_entry(
                    self.entry_id, title, ciphertext, iv,
                    mood=self.current_mood, category=self.current_category,
                    word_count=word_count)
            else:
                self.entry_id = db_manager.insert_entry(
                    title, ciphertext, iv,
                    mood=self.current_mood, category=self.current_category,
                    word_count=word_count)

            # 记录习惯
            self.tracker.record_entry_save(
                self.entry_id, word_count, word_count_delta, self.current_mood)

            # 分析关键词
            try:
                from libs.recommendation.content_analyzer import ContentAnalyzer
                ca = ContentAnalyzer()
                ca.analyze_entry(self.entry_id, content, self.current_category)
            except Exception:
                pass

            if self.session_id:
                self.tracker.end_session(self.session_id, word_count_delta)

            self.original_word_count = word_count
            self._modified = False
            self._snack("保存成功 ✅")
            Clock.schedule_once(lambda dt: self._go_back(), 0.5)

        except Exception as e:
            self._snack(f"保存失败: {e}")

    def _show_templates(self):
        """显示模板菜单"""
        menu_items = []
        for name, content in TEMPLATES.items():
            menu_items.append({
                "text": name,
                "on_release": lambda x=content: self._apply_template(x),
            })

        MDDropdownMenu(
            caller=self.top_bar.right_action_items[-1],
            items=menu_items,
        ).open()

    def _apply_template(self, content):
        """应用模板"""
        self.content_field.text = content

    def _go_back(self):
        """返回列表"""
        if self.manager.has_screen("diary_list"):
            self.manager.current = "diary_list"
            self.manager.remove_widget(self)

    def _snack(self, msg):
        """显示提示"""
        from kivymd.uix.snackbar import MDSnackbar
        MDSnackbar(MDLabel(text=msg)).open()

    def _get_app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()
