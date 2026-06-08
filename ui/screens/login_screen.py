"""登录/设置密码屏幕"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatButton, MDTextButton
from kivymd.uix.card import MDCard
from kivy.animation import Animation
from kivy.metrics import dp
from libs.database.db_manager import init_database
from libs.auth.password_manager import (
    is_initialized, setup_master_password,
    verify_password, get_encryption_key
)


class LoginScreen(MDScreen):
    """登录界面"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.need_setup = not is_initialized()
        init_database()
        self._build_ui()

    def _build_ui(self):
        """构建界面"""
        # 主容器
        layout = MDBoxLayout(
            orientation="vertical",
            padding=[dp(40), dp(60), dp(40), dp(30)],
            spacing=dp(12),
            adaptive_height=True,
            pos_hint={"center_y": 0.5}
        )

        # 图标
        layout.add_widget(MDLabel(
            text="[size=56][b]📔[/b][/size]",
            halign="center",
            markup=True,
        ))

        # 标题
        layout.add_widget(MDLabel(
            text="私人日记",
            halign="center",
            font_style="H4",
            bold=True,
        ))

        # 描述
        if self.need_setup:
            desc = "首次使用，请设置主密码保护你的日记"
        else:
            desc = "输入主密码解锁你的日记"
        layout.add_widget(MDLabel(
            text=desc,
            halign="center",
            theme_text_color="Secondary",
            font_style="Body1",
        ))

        layout.add_widget(MDBoxLayout(size_hint_y=None, height=dp(10)))

        # 密码输入框
        self.pwd_field = MDTextField(
            hint_text="请输入主密码",
            password=True,
            mode="rectangle",
            size_hint_x=0.85,
            pos_hint={"center_x": 0.5},
        )
        layout.add_widget(self.pwd_field)

        # 确认密码框（仅首次）
        self.confirm_field = None
        if self.need_setup:
            self.confirm_field = MDTextField(
                hint_text="请再次输入主密码",
                password=True,
                mode="rectangle",
                size_hint_x=0.85,
                pos_hint={"center_x": 0.5},
            )
            layout.add_widget(self.confirm_field)

        # 错误提示
        self.error_label = MDLabel(
            text="",
            halign="center",
            theme_text_color="Error",
            font_style="Caption",
        )
        layout.add_widget(self.error_label)

        # 提交按钮
        btn_text = "设置密码并开始使用" if self.need_setup else "解锁日记"
        submit_btn = MDFillRoundFlatButton(
            text=btn_text,
            size_hint_x=0.8,
            pos_hint={"center_x": 0.5},
            on_release=self._on_submit,
        )
        layout.add_widget(submit_btn)

        self.add_widget(layout)

    def _on_submit(self, instance):
        """提交登录"""
        pwd = self.pwd_field.text.strip()
        if not pwd:
            self._show_error("请输入密码")
            return

        if self.need_setup:
            if len(pwd) < 6:
                self._show_error("密码至少需要 6 位")
                return
            confirm = self.confirm_field.text.strip() if self.confirm_field else ""
            if pwd != confirm:
                self._show_error("两次输入的密码不一致")
                return
            if not setup_master_password(pwd):
                self._show_error("设置失败，请重试")
                return
            success, key = get_encryption_key(pwd)
            if not success:
                self._show_error(f"密钥派生失败: {key}")
                return
        else:
            success, result = verify_password(pwd)
            if not success:
                self._show_error(result)
                return
            key = bytes.fromhex(result)

        # 登录成功
        app = self._get_app()
        app.after_login(key)

    def _show_error(self, msg):
        """显示错误并晃动"""
        self.error_label.text = msg
        anim = Animation(x=self.pwd_field.x + dp(5), duration=0.05) + \
               Animation(x=self.pwd_field.x - dp(5), duration=0.05) + \
               Animation(x=self.pwd_field.x, duration=0.05)
        anim.start(self.pwd_field)

    def _get_app(self):
        """获取 App 实例"""
        from kivymd.app import MDApp
        return MDApp.get_running_app()
