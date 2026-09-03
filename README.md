# Knowledge Ladder · 动态熵减拆题引导

> 不背模板，练拆题。
> 一次只问一个问题，把算法题的不确定性一步步降下来。

---

## 这是什么

这不是刷题工具，而是一个“教师模型”：

- 机器负责基于公开题目标签做**动态二分**，每次都选当前“信息增益最大”的问题问你。
- 人负责回答是/否/不确定，以及用“我感觉不对劲”强行打断机器。
- 软件不直接甩答案，最终只给**四大方向**和当前候选算法权重，引导你自己收敛。

整个过程**纯本地运行**：不调用任何云端 API，不部署大模型，只有 JSON 状态机 + log2 运算。

---

## 核心流程

```text
基线暴力确认
    ↓
动态问题流（是 / 否 / 不确定 + 我感觉不对劲）
    ↓
自动收敛 / 人类探测器打断
    ↓
四大方向 + 候选算法权重
    ↓
详细启发 + 教师共识线索（触发 / 动作 / 失效边界）
```

- 每步自动选择 **IG 最大的未问问题**，类似 Wordle 猜词。
- 候选池来自 120 个本地算法，初始权重来自多源公开统计。
- “不确定”按弱证据更新，不过度自信。
- 候选池熵低于阈值、IG 低于阈值、或问满上限时自动收敛。

---

## 数据来源

- **Codeforces**：官方 API，标签、rating、缝合组合统计
- **DMOJ**：公开 API v2，21 类算法分类和题分
- **AtCoder Problems**：公开难度曲线，用于交叉验证

数据全部清洗成静态 JSON：

- `algorithm_prior.json`：先验概率、难度区间、组合频次、可调参数
- `feature_algorithm_matrix.json`：29 个特征问题（20 基础 + 9 教师共识）× 120 算法条件概率
- `heuristics.json`：四大方向的深度启发话术
- `teacher_consensus.json`：`teacher-consensus-skill` 蒸馏出的 24 条教师共识主题 + 元纪律

---

## 功能

### 移动端（PWA / APK）

- 打开就是拆题，极简三按钮
- 问题流实时显示当前 Top3 候选算法权重
- 最终页展示四大方向 + 权重 ≥2% 的候选算法清单
- 方向页追加“教师共识线索”：触发条件 / 动作 / 失效边界
- 支持 Editorial / Glass 双主题
- 完全离线可用

### 桌面端（Python / PySide6）

- 同一套熵减状态机
- 保留深色亚克力界面、算法模板导航、壁纸功能
- 方向页追加“教师共识线索”；信息论微缩模块新增“教师共识”页签
- 支持回退、重新开始、隐藏调试信息
- PyInstaller 打包为 Windows EXE

---

## 快速开始

### 移动端网页预览

```bash
cd mobile
./serve.sh
```

浏览器打开：

```text
http://localhost:8000
```

### Android APK

推送到 `main` 分支后由 GitHub Actions 自动构建 APK。

本地构建：

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

仓库内已有本地虚拟环境时：

```bash
./.venv/bin/python main.py
```

Windows 便携版：

```bat
build_windows.bat
```

---

## 可调参数

编辑 `algorithm_prior.json -> params`：

| 参数 | 默认 | 含义 |
|---|---|---|
| `entropy_stop_threshold` | 0.45 | 池熵低于此值自动收敛 |
| `ig_stop_threshold` | 0.03 | 最大信息增益低于此值自动收敛 |
| `detector_entropy_threshold` | 0.30 | 低于此熵时“我感觉不对劲”才强打断 |
| `anomaly_surprise_threshold` | 0.85 | 回答惊讶度低于此值标记反常 |
| `uncertain_decay` | 0.5 | “不确定”的弱证据强度 |
| `max_questions` | 12 | 最多问题数 |
| `algorithm_weight_threshold` | 0.02 | 最终页展示候选算法的权重门槛 |
| `realtime_top_n` | 3 | 问题流实时显示的候选数 |

也可以手动调整 `feature_algorithm_matrix.json` 中每个算法的 `profile` / `direction_weights`，以及 `heuristics.json` 中的话术。

---

## 四大方向

- **编码压缩**：重复信息提前存好，把慢查询变快查询。
- **传播松弛**：沿着依赖关系一层层推，让前驱替后继铺路。
- **剪枝决策**：利用单调性/可行性一次排除大批候选。
- **变换域映射**：换坐标系/差分/对偶/重表述，让纠缠变简单。

---

## 项目结构

```text
├── main.py                    # 入口：只负责启动
├── app/
│   ├── theme.py               # 视觉常量 / QSS / 壁纸模式
│   ├── state.py               # 本地进度持久化
│   ├── utils.py               # 标签聚合与纯数据工具
│   ├── dialogs.py             # 算法模板 / 信息论导论 / 微缩模块
│   ├── tier_page.py           # 档位知识树 / 掌握勾选 / 分组展开
│   ├── flow.py                # 拆题流程图
│   ├── dissect_page.py        # 动态熵减拆题页
│   ├── teacher_consensus.py   # 教师共识数据层
│   └── window.py              # 主窗口 / 标题栏 / 壁纸集成
├── entropy_engine.py          # 桌面端熵减引擎（预计算矩阵）
├── algorithm_prior.json       # 多源先验与参数
├── feature_algorithm_matrix.json
├── heuristics.json            # 四大方向深度启发 + 教师主题引用
├── teacher_consensus.json     # 24 条教师共识主题 + 元纪律
├── knowledge_data.py          # 120 个算法数据
├── tiers_data.py              # 8 档难度数据
├── info_framework.py          # 信息论标签
├── export_mobile_data.py      # 生成 mobile/www/entropy_data.js
├── tests/                     # 熵减引擎 / 数据完整性 / 教师共识测试
├── mobile/                    # PWA + Capacitor
│   └── www/
└── .github/workflows/         # CI / APK / EXE 自动构建
```

---

## License

MIT
