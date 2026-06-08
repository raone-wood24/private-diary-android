"""推荐卡片组件"""

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton
from kivy.metrics import dp


class RecommendationCard(MDCard):
    """推荐卡片"""

    def __init__(self, rec_data, on_click=None, on_dismiss=None, **kwargs):
        super().__init__(**kwargs)
        self.rec_data = rec_data
        self.on_click = on_click
        self.on_dismiss = on_dismiss

        self.orientation = "vertical"
        self.padding = [dp(12), dp(8), dp(12), dp(8)]
        self.size_hint_y = None
        self.height = dp(60)
        self.radius = dp(10)
        self.elevation = 1
        self.md_bg_color = [0.95, 0.97, 1, 1]
        self.ripple_behavior = True

        self._build()

    def _build(self):
        self.add_widget(MDLabel(
            text=self.rec_data.get("title", ""),
            font_style="Body2", bold=True,
        ))
        self.add_widget(MDLabel(
            text=self.rec_data.get("content", ""),
            font_style="Caption", theme_text_color="Secondary",
            shorten=True, max_lines=1,
        ))

        if self.on_dismiss:
            dismiss_btn = MDIconButton(
                icon="close",
                pos_hint={"right": 1, "top": 1},
                on_release=lambda x: self.on_dismiss(self.rec_data),
            )
            self.add_widget(dismiss_btn)

        if self.on_click:
            self.bind(on_release=lambda x: self.on_click(self.rec_data))
