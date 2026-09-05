# v1.5.0 — 性能、隐私与开源仓库整理

- 修复桌面端 `DissectPage` 缺失 `Qt` / `QHBoxLayout` 导入导致的启动崩溃。
- 熵减引擎改为列优先预计算，减少运行时属性查找与重复归一化。
- 移动端 `entropy_engine.js` 同步预计算 profile / direction 矩阵；`app.js` 消除重复教师主题计算。
- 移动端移除 Google Fonts 外链，保持纯本地 / 离线 / 无第三方请求。
- 壁纸逻辑拆为 `app/wallpaper.py` 深模块，主窗口只保留委托接口。
- 新增 `pyproject.toml`（项目元数据 + ruff / mypy / pytest 配置）。
- CI 增加 ruff、mypy、JS 语法检查、Python↔JS 引擎一致性和数据 schema 校验。
- GitHub Actions 重构：最小权限、并发取消、APK/Desktop 统一构建与 tag 自动发布；第三方 action 全部 pin 到 full SHA。
- Release 自动只提取 `RELEASE_NOTES.md` 最新版本段落。
- Wallpaper Engine 导出工具移出主仓库，独立为 [wallpaper-export](https://github.com/dargonburn337845818/wallpaper-export)。
- 新增 LICENSE、SECURITY.md、CONTRIBUTING.md、CODE_OF_CONDUCT.md、issue/PR 模板与 Dependabot。
- 隐私基线：加强 `.gitignore`，历史作者邮箱改为 GitHub noreply。

---

# v1.4.0 — 减法重构：只留经过验证的教师路径

## 教师模型视角的删改
- 撤销上一版把 9 个教师共识特征拍脑袋写进概率矩阵的做法：未校准内容不进动态引擎。
- 教师共识改为“未校准线索”：只在最终页/方向页展示触发、动作、失效边界，不伪装成 `P(feature | algorithm)`。
- 桌面端移除“算法模板”导航、C++ 模板对话框与模板按钮，避免把软件做成背模板工具。
- 删除 `knowledge_data.py` 中 120 份 C++ 模板和未使用的 `quality` 等冗余字段，压缩为轻量名称注册表。

## 删除的死代码/死内容
- 删除未使用的 `app/flow.py`（FlowDiagram）、`InfoGuideDialog`、静态“拆题四步”。
- 删除 `generate_report.py`、重复的 `style_mac.qss`、未经验证的 `tier8_thoughts.py` 28 条扩展思维条目。
- 删除 `knowledge_data.py` 中的 `quality` 等未使用字段，进一步压缩为名称注册表。
- 删除未使用的 `mobile/www/data.js`，移动端只保留 `entropy_data.js`。
- 清理主窗口对信息论/算法数据的无用导入。

## 保留的核心
- 纯本地动态熵减：基线暴力 → 单一问题流 → 四大方向 → 教师共识线索。
- 档位进度、信息论四操作/四阶段、教师共识页签。
- `entropy_engine.py` 预计算矩阵性能优化。
- `tests/`：熵减引擎、数据完整性、教师共识数据层。

支持平台：Android（APK）/ Windows（EXE）。
