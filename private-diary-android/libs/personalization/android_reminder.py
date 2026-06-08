"""Android 本地通知提醒"""

import threading
import time
from datetime import datetime, date
from libs.database import db_manager
from libs.recommendation.behavior_analyzer import BehaviorAnalyzer


class AndroidReminderService:
    """后台提醒服务 — Android 版"""

    def __init__(self, callback=None):
        self.callback = callback
        self._running = False
        self._thread = None
        self.analyzer = BehaviorAnalyzer()
        self._check_interval = 300
        self._last_reminder_date = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                self._check_and_remind()
            except Exception:
                pass
            time.sleep(self._check_interval)

    def _check_and_remind(self):
        now = datetime.now()
        today = date.today().isoformat()
        if self._last_reminder_date == today:
            return
        today_entries = db_manager.get_entries_by_date(today)
        if today_entries:
            return
        time_profile = self.analyzer.analyze_writing_time(60)
        top_hours = time_profile.get("top_hours", [])
        if not top_hours:
            return
        current_hour = now.hour
        should_remind = any(abs(current_hour - h) <= 1 for h in top_hours)
        if should_remind and self.callback:
            self._last_reminder_date = today
            self.callback({
                "title": "私人日记",
                "message": "现在是你习惯写日记的时间，今天还没写哦~",
            })


def send_android_notification(title, message):
    """发送 Android 系统通知"""
    try:
        from plyer import notification
        notification.notify(
            title=title, message=message,
            app_name="私人日记", timeout=5,
        )
    except Exception:
        pass
