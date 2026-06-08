# 私人日记 Android 版

## 方案 A：GitHub Actions 自动打包（无需本地环境）

### 步骤：

1. 把这个项目文件夹初始化为 Git 仓库，推送到 GitHub：
```bash
cd "C:\Users\Xiao ran\private-diary-android"

# 初始化 Git
git init
git add .
git commit -m "私人日记 Android v0.1"

# 在 GitHub 上创建新仓库：https://github.com/new
# 然后推送：
git remote add origin https://github.com/你的用户名/private-diary-android.git
git branch -M main
git push -u origin main
```

2. 推送后，GitHub Actions 会自动开始构建 APK
3. 在仓库页面点击 **Actions** → 找到完成的 workflow → **Artifacts** → 下载 APK
4. 也可以手动触发：Actions → Build Android APK → Run workflow

### 优点：
- 不需要安装任何本地环境
- 免费（GitHub 公开仓库）
- 每次更新代码自动构建
- APK 保存 30 天

---

## 方案 B：本地 WSL 打包

### 1. 用管理员身份打开 PowerShell，安装 WSL：
```powershell
wsl --install
```
安装完成后重启电脑，WSL 会自动打开 Ubuntu 终端。

### 2. 在 WSL Ubuntu 中：
```bash
# 更新包管理器
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3-pip python3-dev build-essential \
  libssl-dev libffi-dev zlib1g-dev git autoconf libtool pkg-config \
  libncurses5-dev libtinfo5 cmake openjdk-17-jdk unzip zip lld

# 安装 Buildozer
pip install buildozer cython

# 进入项目目录（Windows 的 C 盘在 WSL 中挂在 /mnt/c/）
cd "/mnt/c/Users/Xiao ran/private-diary-android"

# 开始构建
buildozer android debug
```

### 3. APK 输出在 `bin/` 目录，复制到 Windows：
```bash
cp bin/*.apk "/mnt/c/Users/Xiao ran/Desktop/"
```

---

## 在手机上安装
1. 把 APK 传到手机（微信/QQ 发送文件，或 USB 连接）
2. 打开 APK 文件
3. 允许「安装未知来源应用」
4. 安装完成！

---

## 技术栈
- Kivy 2.3 + KivyMD 2.0 (Material Design UI)
- AES-256-GCM 加密
- SQLite 本地数据库
- Buildozer 打包
