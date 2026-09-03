# v1.2.0 — 深模块重构

知识阶梯桌面端完成深模块化拆分：

- `main.py` 瘦身为纯入口。
- UI 组件拆到 `app/widgets.py`，主窗口/壁纸拆到 `app/window.py`。
- 主题、状态、纯数据工具分别独立为 `app/theme.py`、`app/state.py`、`app/utils.py`。
- 新增 GitHub Actions CI：Python 编译检查 + 移动端数据再生成。
- 行为不变：仍是纯本地熵减拆题，不调用云端 API。

支持平台：Android（APK）/ Windows（EXE）。
