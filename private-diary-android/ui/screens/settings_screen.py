"""设置屏幕"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFillRoundFlatButton, MDButton, MDButtonText
from kivymd.uix.selectioncontrol import MDSwitch
from kivy.metrics import dp
from kivymd.app import MDApp
from libs.utils.config import load_config, save_config


class SettingsScreen(MDScreen):
    """设置屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = load_config()
        self._build_ui()

    def _build_ui(self):
        self.top_bar = MDTopAppBar(
            title="设置",
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
        )
        self.add_widget(self.top_bar)

        scroll = MDScrollView()
        self.container = MDBoxLayout(
            orientation="vertical",
            padding=[dp(15), dp(10), dp(15), dp(30)],
            spacing=dp(12),
            adaptive_height=True,
        )
        scroll.add_widget(self.container)

        # === 主题 ===
        self._add_section("🎨 主题设置")
        theme_card = MDCard(
            orientation="horizontal",
            padding=[dp(12), dp(12), dp(12), dp(12)],
            size_hint_y=None, height=dp(56),
            radius=dp(10),
        )
        theme_card.add_widget(MDLabel(text="选择主题", font_style="Body1"))
        self.container.add_widget(theme_card)

        themes = {"light": "☀️ 浅色", "dark": "🌙 深色", "warm": "🔥 暖色", "green": "🌿 墨绿"}
        theme_btns = MDBoxLayout(
            orientation="horizontal", spacing=dp(6),
            size_hint_y=None, height=dp(48))
        for key, label in themes.items():
            btn = MDButton(
                MDButtonText(text=label),
                on_release=lambda x, k=key: self._switch_theme(k),
                size_hint_x=1,
            )
            theme_btns.add_widget(btn)
        self.container.add_widget(theme_btns)

        # === 提醒 ===
        self._add_section("🔔 智能提醒")
        self._add_switch("启用写作提醒", "reminder_enabled")
        self._add_switch("自动学习最佳时间", "reminder_auto_learn")

        # === 推荐 ===
        self._add_section("💡 智能推荐")
        self._add_switch("启用智能推荐", "recommendation_enabled")

        # === 数据 ===
        self._add_section("📦 数据管理")

        export_row = MDBoxLayout(
            orientation="horizontal", spacing=dp(8),
            size_hint_y=None, height=dp(44))
        export_row.add_widget(MDFillRoundFlatButton(
            text="加密导出", size_hint_x=1,
            on_release=lambda x: self._export(False)))
        export_row.add_widget(MDFillRoundFlatButton(
            text="明文导出", size_hint_x=1,
            on_release=lambda x: self._export(True)))
        self.container.add_widget(export_row)

        # === 关于 ===
        self._add_section("ℹ️ 关于")
        self.container.add_widget(MDLabel(
            text="私人日记 v0.1.0\nAndroid 版\n\nAES-256-GCM 加密保护\n你的隐私，由你做主",
            halign="center", font_style="Body2",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(100)))

        self.add_widget(scroll)

        from kivy.clock import Clock
        Clock.schedule_once(self._update_layout, 0.1)

    def _update_layout(self, dt):
        top = self.top_bar.height
        for child in self.children:
            if isinstance(child, MDScrollView):
                child.pos_hint = {"top": 1 - top / self.height}
                child.size = (self.width, self.height - top)

    def _add_section(self, title):
        self.container.add_widget(MDLabel(
            text=title, font_style="H6", bold=True,
            size_hint_y=None, height=dp(32)))

    def _add_switch(self, label, config_key):
        row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(48),
            padding=[dp(5), 0])
        row.add_widget(MDLabel(text=label, font_style="Body1"))
        switch = MDSwitch(
            active=self.config.get(config_key, True),
            on_active=lambda x, k=config_key: self._toggle(k, True),
        )
        switch.bind(active=lambda inst, val, k=config_key: self._toggle_switch(k, val))
        row.add_widget(switch)
        self.container.add_widget(row)

    def _toggle_switch(self, key, value):
        self.config[key] = value
        save_config(self.config)

    def _switch_theme(self, key):
        app = MDApp.get_running_app()
        if hasattr(app, 'switch_theme'):
            app.switch_theme(key)
        self.config["theme"] = key
        save_config(self.config)

    def _export(self, decrypt=False):
        from libs.utils.backup import export_entries
        app = MDApp.get_running_app()
        key = app.encryption_key if decrypt else None
        path = export_entries(decrypt_key=key)
        if path:
            from kivymd.uix.snackbar import MDSnackbar
            MDSnackbar(MDLabel(text=f"已导出到:\n{path}")).open()

    def _go_back(self):
        if self.manager.has_screen("diary_list"):
            self.manager.current = "diary_list"
            self.manager.remove_widget(self)
