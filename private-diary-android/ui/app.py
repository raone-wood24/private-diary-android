"""KivyMD App 主类"""

from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivy.core.window import Window
from kivy.clock import Clock
from libs.utils.config import load_config, save_config
from ui.themes import THEMES


class DiaryApp(MDApp):
    """私人日记 Android App"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.encryption_key = None
        self.current_theme = "light"
        self.config = {}
        self.habit_tracker = None
        self.recommendation_engine = None
        self.insight_generator = None

    def build(self):
        self.title = "私人日记"
        self.config = load_config()
        self.current_theme = self.config.get("theme", "light")
        self._apply_theme()

        # 窗口基础设置
        Window.soft_input_mode = "resize"

        # 屏幕管理器
        self.sm = MDScreenManager()
        return self.sm

    def on_start(self):
        """App 启动后加载登录屏幕"""
        from ui.screens.login_screen import LoginScreen
        self.sm.add_widget(LoginScreen(name="login"))

    def _apply_theme(self):
        """应用主题"""
        theme = THEMES.get(self.current_theme, THEMES["light"])
        self.theme_cls.primary_palette = theme["primary_palette"]
        self.theme_cls.accent_palette = theme["accent_palette"]
        self.theme_cls.theme_style = theme["theme_style"]

    def switch_theme(self, theme_key):
        """切换主题"""
        self.current_theme = theme_key
        self._apply_theme()
        self.config["theme"] = theme_key
        save_config(self.config)

    def after_login(self, encryption_key):
        """登录成功后加载主界面"""
        self.encryption_key = encryption_key

        # 初始化后端模块
        from libs.personalization.habit_tracker import HabitTracker
        from libs.recommendation.recommendation_engine import RecommendationEngine
        from libs.recommendation.insight_generator import InsightGenerator

        self.habit_tracker = HabitTracker()
        self.recommendation_engine = RecommendationEngine()
        self.insight_generator = InsightGenerator()

        # 切换到主屏幕
        from ui.screens.diary_list_screen import DiaryListScreen
        self.sm.clear_widgets()
        self.sm.add_widget(DiaryListScreen(name="diary_list"))

    def get_encryption_key(self):
        return self.encryption_key
