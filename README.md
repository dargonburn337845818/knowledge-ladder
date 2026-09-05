# Knowledge Ladder

> 本地优先的算法拆题工具：一次问一个问题，用信息增益逐步收敛到四大方向。包含 PySide6 桌面端与 Capacitor/PWA 移动端。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 简介

Knowledge Ladder 用于算法学习时的“拆题”练习。它不直接给答案，而是根据你对题目特征的回答，选择信息增益最大的下一个问题，逐步把不确定性收敛到四个方向之一。

- **桌面端（Python / PySide6）**：8 档知识阶梯、复盘记录、成长统计、壁纸。
- **移动端（PWA / APK）**：专注动态熵减拆题，极简问题流，完全离线可用。
- **本地运行**：运行时无远程 API、无大模型、无分析脚本；只有 JSON 状态机与 `log2` 计算。

## 功能

### 移动端

- 单一问题流：是 / 否 / 不确定 / 我感觉不对劲。
- 每步自动选择信息增益最大的未问问题。
- 最终页按计算概率列出方向，进入详情后按“条件 → 动作 → 自问”三层递进解锁。
- 候选池来自 120 个本地算法，初始权重来自公开统计。
- 支持 Editorial / Glass 两套主题。
- 完全离线可用，不加载外部字体或第三方资源。

### 桌面端

- 8 档知识阶梯：算法有哪些、是什么、怎么写、C++ 代码模板、掌握进度，可一键复制算法代码。
- 壁纸：支持图片、GIF、视频，玻璃拟态透出。
- 复盘记事本：记录解题感悟、当天看的算法卡，标记待专家点评。
- 成长统计：知识面覆盖、每周量化汇总、近 14 天趋势、算法卡摄入。
- Windows 可通过 `build_windows.bat` 打包为 EXE。

## 算法与数据

拆题过程基于信息论：

- 从 120 个本地算法中维护候选池。
- 每个问题按信息增益排序，类似 Wordle 猜词。
- “不确定”按弱证据更新，不把不确定当成强证据。
- 候选池熵低于阈值、信息增益低于阈值，或问满上限时自动收敛。

数据来源（均为公开 API，清洗为本地静态 JSON）：

- Codeforces：标签、Rating、组合统计。
- DMOJ：21 类算法分类与题分。
- AtCoder Problems：难度曲线交叉验证。

## 快速开始

### 移动端网页预览

```bash
cd mobile
./serve.sh
```

浏览器打开 `http://localhost:8000`。

### Android APK

推送 `main` 后由 GitHub Actions 自动构建 APK。本地构建：

```bash
cd mobile
npm install
npx cap add android
npx cap sync android
cd android && ./gradlew assembleDebug
```

### 桌面端

```bash
python -m pip install -r requirements.txt
python main.py
```

仓库内已有虚拟环境时：

```bash
./.venv/bin/python main.py
```

Windows 便携版：

```bat
build_windows.bat
```

## 文档

- [系统设计](docs/system-design.md)
- [Editorial 主题](docs/style-parallax-editorial.md)
- [验证与发布](VALIDATION.md)
- [更新日志](RELEASE_NOTES.md)

## 项目结构

```text
entropy_engine.py            # 桌面端熵减引擎
info_framework.py            # 信息论标签
knowledge_data.py            # 120 算法名称注册表
tiers_data.py                # 8 档难度数据
export_mobile_data.py        # 生成移动端数据
app/                         # PySide6 桌面端模块
mobile/                      # PWA + Capacitor 移动端
expert_content/              # 版本化专家方向内容
scripts/                     # 数据校验、引擎一致性、发布工具
tests/                       # Python + JS 测试
docs/                        # 长文档
```

完整模块地图见 [AGENTS.md](AGENTS.md)。

## 开发与验证

```bash
python -m unittest discover -s tests -v
ruff check .
mypy --ignore-missing-imports entropy_engine.py info_framework.py knowledge_data.py \
  tiers_data.py export_mobile_data.py app/teacher_consensus.py
python scripts/check_data_schema.py
python export_mobile_data.py
python scripts/engine_parity.py
```

## 隐私与离线承诺

- 运行时无远程 API、无大模型、无分析脚本。
- 移动端不加载外部字体或第三方资源。
- 本地进度保存在系统数据目录，不写入仓库。
- `docs/`、`reports/`、`preview/`、`系统提示词.txt` 等内部资料已在 `.gitignore` 中忽略，请勿提交。
- 公开 Issue/PR 不要贴个人路径、密钥或真实账号信息。

## 贡献

欢迎提交 Issue 和 Pull Request。改动机器行为时，请同时更新 Python 引擎与移动端 JS 引擎，并补充/更新测试。

- 贡献流程：[CONTRIBUTING.md](CONTRIBUTING.md)
- 安全与隐私上报：[SECURITY.md](SECURITY.md)
- 社区行为：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## 相关仓库

- [wallpaper-export](https://github.com/dargonburn337845818/wallpaper-export)：Wallpaper Engine 高清导出工具。

## 许可证

[MIT](LICENSE)
