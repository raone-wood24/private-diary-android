[app]

title = 私人日记
package.name = private-diary
package.domain = com.diary.privateapp

source.dir = .
source.include_exts = py,png,jpg,kv,ttf,md

version = 0.1.0

requirements = python3,kivy>=2.3.0,kivymd>=2.0.0,cryptography,jieba,plyer,pillow

orientation = portrait

osx.python_version = 3
osx.kivy_version = 2.3.0

# Android
android.permissions = INTERNET,POST_NOTIFICATIONS,VIBRATE,USE_BIOMETRIC
android.api = 34
android.minapi = 26
android.ndk = 25b
android.sdk = 34
android.accept_sdk_license = True

# Architecture (arm64-v8a for modern devices)
android.arch = arm64-v8a

# Enable backup
android.allow_backup = True

# App theme colors
android.presplash_color = #1F6FD0
android.statusbar_color = #1565C0
android.navbar_color = #1565C0

# Icon
android.icon.filename = assets/icon.png
android.presplash.filename = assets/icon.png

# Keep app alive with service
android.services = reminder:libs/personalization/android_reminder.py

# Log
android.logcat_filters = *:S python:D

# Release
android.release_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
