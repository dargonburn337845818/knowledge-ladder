# 《系统设计：动态熵减拆题引导》

> 版本：v0.2.0（阶段二）
> 目标：在现有 `Knowledge Ladder` 框架上，把“四张静态卡片 + 四个方向标签”改造成“单一问题流 + 动态信息增益选择 + 人类探测器”。

---

## 1. 设计目标

1. 不直接给答案，用“是/否/不确定”动态二分，降低候选算法池的不确定性。
2. 先有基线暴力，后有四大策略。四大方向只在最终收敛或异常打断时出现。
3. 纯本地状态机：输入只有静态 JSON，运算只有加、减、乘、除、log2。
4. 移动端（`mobile/www`）与桌面端（PySide6）共享同一套逻辑/数据思想，分别实现为 JS 与 Python。

---

## 2. 现有 UI 的改造映射

| 现有元素 | 改为 |
|---|---|
| 四张静态卡片：数据形状 / 是否变化 / 运算规则 / 数据规模 | 变成 20 个是/否“特征问题”池，每次只显示 IG 最大的一个 |
| 卡片选项（线性/树图/...、静态/动态、加法/异或/...、n 范围） | 统一变成“是 / 否 / 不确定”三个大按钮 |
| 底部四个方向标签：编码压缩 / 传播松弛 / 剪枝决策 / 变换域映射 | 问题流阶段完全隐藏；自动收敛或异常打断时作为大按钮弹出 |
| 下一步“引导式思考” | 保留为最终方向详情页，展示模棱两可话术（不含具体算法名） |

### 交互约束（硬性）

- 问题流主屏永远只显示：
  - 一个问题
  - 三个大按钮：是 / 否 / 不确定
  - 一个入口：我感觉不对劲
- 不显示已答轨迹。
- 支持回退上一步（返回最近一次快照）。
- 四方向不先入为主：提问期间不出现。

---

## 3. 数据文件

| 文件 | 作用 |
|---|---|
| `algorithm_prior.json` | 多源静态先验：CF 标签、CF 组合、DMOJ 类型、AtCoder 难度、120 算法先验 |
| `feature_algorithm_matrix.json` | 条件概率矩阵：`P(feature | algorithm)`，以及每个算法的四方向权重 |
| `params`（在 JSON 中） | 熵阈值、IG 阈值、异常阈值、不确定衰减、最大问题数 |

`feature_algorithm_matrix.json` 结构：

```json
{
  "features": [
    {
      "id": "monotonic",
      "dimension": "排查",
      "question": "答案或可行性判定具有单调性，可以二分吗？",
      "kind": "extra"
    }
  ],
  "directions": ["编码压缩", "传播松弛", "剪枝决策", "变换域映射"],
  "algorithms": [
    {
      "algorithm_name": "二分答案",
      "cf_tags": ["binary search"],
      "dmoj_types": ["Divide and Conquer"],
      "prior_probability": 0.006,
      "profile": {
        "monotonic": 0.85,
        "metric_bool": 0.9,
        "dependency": 0.15
      },
      "direction_weights": {
        "剪枝决策": 1.0,
        "编码压缩": 0.05,
        "传播松弛": 0.05,
        "变换域映射": 0.05
      }
    }
  ]
}
```

### 问题池（20 个特征问题）

| id | 维度 | 问题 | 类型 |
|---|---|---|---|
| shape_linear | 形状 | 数据主体是线性/序列/区间结构吗？ | 基础 |
| shape_graph | 形状 | 数据主体是树/图/依赖结构吗？ | 基础 |
| shape_algebra | 形状 | 数据主体是抽象数学对象/集合/值域吗？ | 基础 |
| dynamic | 变化 | 运行过程中数据会修改、需要实时维护吗？ | 基础 |
| metric_sum | 规则 | 合并规则是加法/最值/路径权值吗？ | 基础 |
| metric_xor | 规则 | 核心涉及异或/线性独立/异或空间吗？ | 基础 |
| metric_count | 规则 | 需要计数/组合/卷积/方案数吗？ | 基础 |
| metric_bool | 规则 | 问题只问可行性/判定（布尔）吗？ | 基础 |
| metric_geom | 规则 | 核心是几何/向量/距离/凸性吗？ | 基础 |
| metric_num | 规则 | 核心是数论/模运算/整除/质数吗？ | 基础 |
| scale_tiny | 规模 | n ≤ 20，可以状压/指数级枚举吗？ | 基础 |
| scale_small | 规模 | n ≤ 5000，可以接受 O(n²)/O(n³) 吗？ | 基础 |
| scale_large | 规模 | n ≥ 1e5，需要 O(n log n) 或更好吗？ | 基础 |
| monotonic | 排查 | 答案或可行性判定具有单调性，可以二分吗？ | 额外 |
| dependency | 排查 | 当前状态依赖前驱/递推关系，需要按顺序传递吗？ | 额外 |
| multi_query | 排查 | 有大量/多次查询，需要批量或数据结构维护吗？ | 额外 |
| preprocess | 排查 | 允许离线/预处理来换取查询更快吗？ | 额外 |
| optimization | 排查 | 求的是最优值/最值，而不只是可行性吗？ | 额外 |
| range_ops | 排查 | 核心在线性序列的区间操作/区间查询上吗？ | 额外 |
| graph_path | 排查 | 核心在树/图的路径、连通、最短路或流上吗？ | 额外 |

---

## 4. 熵减决策引擎

### 4.1 候选池

- 候选 = 120 个本地算法。
- 初始权重 = `algorithm_prior.json -> algorithms[].prior_probability`。
- 每次用户回答后更新为后验分布 `P(algorithm | answers)`。

### 4.2 条件概率

矩阵 `feature_algorithm_matrix.json` 中每个算法对每个特征给一个：

```
p_yes = P(feature=true | algorithm)
p_no  = 1 - p_yes
```

它们在更新时被当作“如果答案是真，该算法有多合理”的似然。

### 4.3 信息增益

当前池分布：

```
H(P) = - Σ_i P(i) * log2(P(i))
```

对未问特征 `q`：

```
p_yes(q) = Σ_i P(i) * p_yes(i,q)
p_no(q)  = 1 - p_yes(q)
```

回答“是”后的后验：

```
P(i | yes) = P(i) * p_yes(i,q) / p_yes(q)
P(i | no)  = P(i) * p_no(i,q)  / p_no(q)
```

回答后的期望熵：

```
E[H_after(q)] = p_yes(q) * H(P|yes) + p_no(q) * H(P|no)
```

信息增益：

```
IG(q) = H(P) - E[H_after(q)]
```

**选择规则**：每个问题只问一次；每次选择 `argmax IG(q)` 的未问问题。

### 4.4 “不确定”的更新

“不确定”不是纯是/否，而是弱证据：

```
P_unc(i) ∝ 0.5 * P(i | yes) + 0.5 * P(i | no)
```

也就是让“是”和“否”各取一半，再做归一化。这样可以缩小候选池，但不会像单选是/否那么强地剪枝。

### 4.5 停止条件

满足任一条件即自动进入“四大方向结果页”：

1. `H(P) < entropy_stop_threshold`
2. 剩余所有未问问题的 `max IG < ig_stop_threshold`
3. 已问问题数达到 `max_questions`
4. 用户触发“我感觉不对劲”且 `H(P) < detector_entropy_threshold`

### 4.6 伪代码

```
state = {
  prior: [...],
  weights: [...],
  asked: [],
  history: [],
  mode: "baseline" | "question" | "finished" | "direction"
}

loop:
  if mode == "baseline":
      show "是否已经先想了暴力/模拟方案？"
      if answer == "no" or "uncertain":
          stay and prompt "请先写一个暴力/模拟再继续"
      else:
          mode = "question"

  if mode == "question":
      q = argmax IG among unasked features
      if stop_condition_reached(weights, q):
          mode = "finished"; break
      show q + [是 | 否 | 不确定 | 我感觉不对劲]
      answer = user_click()
      history.push(snapshot(weights, asked, q))
      update_weights(weights, q, answer)
      asked.add(q)
      if answer == "我感觉不对劲" and entropy(weights) < threshold:
          mode = "finished"; break

  if mode == "finished":
      show four direction big buttons (ranked by P(direction))
      user clicks a direction -> mode = "direction"; show vague heuristic
```

---

## 5. 人类探测器机制

### 5.1 主动打断

- 按钮：**“我感觉不对劲”**。
- 如果当前 `H(P) < detector_entropy_threshold`：立即停止发问，展示四大方向。
- 如果当前熵还高：不打断，提示“先再回答 1–2 个问题，让机器把范围收小”。

### 5.2 反常检测

每回答一个问题后计算“惊讶度”：

```
surprise = P(user_answer | current_pool)
```

如果 `surprise < anomaly_surprise_threshold`，说明用户答案与当前模型预期严重冲突。此时系统标记一次异常，并可选地提示“这个回答有点反直觉；如果觉得不对，可以点‘我感觉不对劲’”。

### 5.3 人工优先原则

即使机器已经自动收敛，用户仍可点“我感觉不对劲”强行跳出，直接以主观直觉选择四大方向。机器不能阻止人工接管。

---

## 6. 四大方向引导卡片

### 6.1 方向概率

对每个方向 `d`：

```
P(d) = Σ_i P(i) * weight_d(i)
```

其中 `weight_d(i)` 来自矩阵中每个算法的 `direction_weights`。

按 `P(d)` 从高到低显示。

### 6.2 话术约束

- 严禁说出具体算法名：如“前缀和”“线段树”“二分”“单调队列”等。
- 只能使用以下四类模糊引导：
  - 编码压缩：重复信息提前存储、预处理、压缩状态
  - 传播松弛：顺着依赖/递推一层层推、状态传递
  - 剪枝决策：排除不可能候选、利用单调性缩小范围
  - 变换域映射：换坐标系、差分/对偶/重表述
- 用户点击某个方向后，展示该方向的启发话术，流程结束。

---

## 7. 状态快照与回退

- 每次提问前保存快照：`weights`、`asked`、`mode`。
- “回退上一步”弹出最后一个快照，恢复后重新计算下一个 IG 最大问题。
- “重新开始”清空所有历史，回到基线暴力确认状态。
- 回退不改变静态 JSON，只影响本次会话内存。

---

## 8. 平台实现要点

### 8.1 移动端（JS）

- 新增 `mobile/www/entropy_engine.js`，读取内嵌的 `feature_algorithm_matrix` 和 `algorithm_prior`（随 `data.js` 或独立 `system_data.js` 打包）。
- 或把 JSON 以 `window.ENTROPY_DATA = {...}` 形式内嵌，避免运行时 fetch。
- 所有计算用 `Math.log2`，纯前端。
- UI 保持当前玻璃拟态/Editorial 双主题，只替换 `stage.innerHTML` 的渲染逻辑。

### 8.2 桌面端（PySide6）

- 新增 `entropy_engine.py`，加载 `algorithm_prior.json` 和 `feature_algorithm_matrix.json`。
- `DissectPage` 改为状态机渲染：
  - `baseline`
  - `question`
  - `finished`
  - `direction`
- 保留现有 `FlowDiagram`、`OP_INFO`、四方向弹卡逻辑，但只用于 final/direction 阶段。

---

## 9. 可调参数

| 参数 | 默认 | 含义 |
|---|---|---|
| `entropy_stop_threshold` | 0.45 | 低于此熵自动收束 |
| `ig_stop_threshold` | 0.03 | 最大 IG 低于此值自动收束 |
| `detector_entropy_threshold` | 0.30 | 低于此熵时“不对劲”才强打断 |
| `anomaly_surprise_threshold` | 0.85 | 回答惊讶度低于此值标记反常 |
| `uncertain_decay` | 0.5 | “不确定”是的/否各占一半的权重 |
| `max_questions` | 12 | 最大问题数 |

用户可直接编辑 JSON 中的 `params` 调整“脾气”。

---

## 10. 验证示例（洛谷 P3957 跳房子）

阶段二不实现代码，只描述预期路径：

- 基线暴力确认：是。
- 引擎先问高 IG 问题：
  - “n 是否 ≥ 1e5 / 需要 O(n log n)？”——是。
  - “答案或可行性判定具有单调性，可以二分吗？”——是（剪枝决策方向增强）。
  - “当前状态依赖前驱/递推关系，需要按顺序传递吗？”——是（传播松弛方向增强）。
  - “是否有多轮查询/滑动窗口类批量维护？”——是（进一步偏向数据结构中的队列/窗口）。
- 最终 H(P) 下降后停止，四大方向概率中“剪枝决策 + 传播松弛”排前。
- 话术只提示“利用单调性排除大块范围 / 顺着前驱关系滑动维护”，不直接说“二分+单调队列”。

---

## 11. 阶段边界

- 本文件是**阶段二交付物**：设计文档 + 特征矩阵。
- **阶段三**：根据本文写出可直接粘贴给代码生成器的《系统提示词.txt》。
- **阶段四**：在移动端 `mobile/www` 与桌面端 `main.py / DissectPage` 中落地实现。
