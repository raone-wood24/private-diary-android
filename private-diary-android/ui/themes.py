"""主题定义"""

THEMES = {
    "light": {
        "name": "浅色",
        "primary_palette": "Blue",
        "accent_palette": "LightBlue",
        "theme_style": "Light",
        "bg_color": [0.95, 0.95, 0.97, 1],
        "card_color": [1, 1, 1, 1],
        "text_color": [0.1, 0.1, 0.15, 1],
        "secondary_text": [0.5, 0.5, 0.55, 1],
    },
    "dark": {
        "name": "深色",
        "primary_palette": "BlueGray",
        "accent_palette": "Blue",
        "theme_style": "Dark",
        "bg_color": [0.08, 0.08, 0.1, 1],
        "card_color": [0.15, 0.15, 0.18, 1],
        "text_color": [0.9, 0.9, 0.92, 1],
        "secondary_text": [0.55, 0.55, 0.6, 1],
    },
    "warm": {
        "name": "暖色",
        "primary_palette": "Brown",
        "accent_palette": "Orange",
        "theme_style": "Light",
        "bg_color": [0.98, 0.95, 0.9, 1],
        "card_color": [1, 0.98, 0.94, 1],
        "text_color": [0.25, 0.18, 0.12, 1],
        "secondary_text": [0.55, 0.45, 0.35, 1],
    },
    "green": {
        "name": "墨绿",
        "primary_palette": "Green",
        "accent_palette": "LightGreen",
        "theme_style": "Light",
        "bg_color": [0.92, 0.96, 0.92, 1],
        "card_color": [0.97, 1, 0.97, 1],
        "text_color": [0.1, 0.3, 0.15, 1],
        "secondary_text": [0.3, 0.5, 0.35, 1],
    },
}

MOOD_COLORS = {
    "happy": [0.3, 0.7, 0.25, 1],
    "sad": [0.2, 0.5, 0.9, 1],
    "neutral": [0.6, 0.6, 0.6, 1],
    "excited": [1, 0.55, 0, 1],
    "anxious": [0.95, 0.25, 0.25, 1],
    "calm": [0.55, 0.8, 0.25, 1],
}
