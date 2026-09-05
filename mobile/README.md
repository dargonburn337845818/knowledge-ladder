# 知识阶梯 · 移动端（PWA / Capacitor）

这是从 `knowledge-ladder` 桌面版抽出的移动端版本，按“不能写代码、只能练拆题”的场景做了精简：

- **核心功能：动态熵减拆题 + 教师共识引导**，没有模板，保持轻量。
- 拆题页：基线暴力 → 单一问题流 → 四大方向 → 教师共识线索。
- 纯本地运行，数据由 `entropy_data.js` 提供，离线可用。
- 要生成 Android APK 时，用 Capacitor 把它包装成原生 WebView 应用。

## 数据更新

每次改了 Python 端的数据（算法、档位、信息论标签），在 `knowledge-ladder` 根目录执行：

```bash
python3 export_mobile_data.py
```

会重新生成 `mobile/www/entropy_data.js`（已删除不再使用的旧 `data.js`）。

## 本地预览

```bash
cd mobile
./serve.sh
# 或：cd www && npx serve .
```

浏览器打开 `http://localhost:8000`。

也可以直接双击 `www/index.html`（不启用 Service Worker，但功能可用）。

## 打包成 APK

前置条件：安装 Node.js、Java 17+、Android Studio / Android SDK。

```bash
cd mobile
npm install
npx cap add android
npx cap sync android
cd android
./gradlew assembleDebug
```

生成结果：

```
mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

## 云构建（不装 Android Studio）

仓库根目录已配置 `.github/workflows/build-android.yml`。提交并推送到 GitHub 后，Actions 会自动：

1. 重新生成 `mobile/www/entropy_data.js`
2. 安装 Capacitor
3. 生成 Android 工程
4. 构建 `app-debug.apk`
5. 上传为 artifact（tag `v*` 还会自动创建 GitHub Release）

在 GitHub 仓库的 **Actions** 页面运行 `Build Knowledge Ladder APK`，下载 `knowledge-ladder-apk` 即可。

## 目录

```
mobile/
├── www/                # Web 资源（Capacitor 的 webDir）
│   ├── index.html      # 移动端页面
│   ├── style.css       # 移动端样式
│   ├── app.js          # 交互逻辑
│   ├── entropy_engine.js  # 熵减引擎（JS）
│   ├── entropy_data.js # 由 export_mobile_data.py 生成
│   ├── manifest.json   # PWA 清单
│   ├── sw.js           # 离线缓存
│   └── icon.svg
├── capacitor.config.json
└── package.json
```
