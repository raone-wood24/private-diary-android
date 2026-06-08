# 私人日记 Android 版

基于 KivyMD 的 Android 日记应用，支持 AES-256-GCM 加密、智能推荐引擎、习惯追踪等功能。

## GitHub Actions 自动打包

本项目使用 GitHub Actions 自动构建 APK，无需本地 Buildozer 环境。

每次推送代码到 `main` 分支，workflow 自动触发构建。

### 下载 APK

1. 在仓库页面点击 **Actions** → 找到完成的 workflow → **Artifacts** → 下载 APK
2. 也可以手动触发：Actions → Build Android APK → Run workflow

### 在手机上安装
1. 把 APK 传到手机（微信/QQ 发送文件，或 USB 连接）
2. 打开 APK 文件，允许「安装未知来源应用」
3. 安装完成！

---

## 技术栈
- Kivy 2.3 + KivyMD 2.0 (Material Design UI)
- AES-256-GCM 加密
- SQLite 本地数据库
- Buildozer + GitHub Actions 打包
