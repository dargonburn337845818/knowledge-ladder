# v1.3.0 — 教师共识 + 深模块深化

## 重构（按工作共识）
- `app/widgets.py` 拆成四个深模块：`dialogs.py` / `tier_page.py` / `flow.py` / `dissect_page.py`。
- 删除旧的 `mobile/www/data.js` 死文件，移动端只保留 `entropy_data.js` 作为运行数据。
- `entropy_engine.py` 预计算 profile / direction 矩阵，减少重复 dict 查找并归一化初始先验。
- 新增 `tests/`：熵减引擎、数据完整性、教师共识数据层共 16 个测试；CI 同步运行。

## 教师共识内容
- 新增 `teacher_consensus.json`：24 条教师共识主题 + 2 条元纪律，来源于 `teacher-consensus-skill` 蒸馏成果。
- 桌面端方向页展示“教师共识线索”（触发 / 动作 / 失效边界）。
- 移动端方向页同步展示“教师共识线索”。
- 信息论微缩模块新增“教师共识”页签。
- `heuristics.json` 挂接对应方向的 teacher_theme_ids 与元纪律。

支持平台：Android（APK）/ Windows（EXE）。
