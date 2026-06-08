"""私人日记 Android App — 入口"""

import os
import sys

# 确保 libs 在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import DiaryApp

if __name__ == "__main__":
    DiaryApp().run()
