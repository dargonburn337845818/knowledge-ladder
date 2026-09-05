# 真实题目 · Agent 引导代理实验

> 由于真人实测成本高，先用真实 Codeforces 题目做“代理 agent”实验：
> 用题目的真实 tags 作为 ground truth，模拟一个诚实回答结构性问题 的 agent，
> 观察熵减引擎是否能收窄候选、给出正确方向。

## 结论

- 11 道真实 Codeforces 题目全部找到 ground-truth 算法。
- 无引导随机猜测期望次数：**6.8 次**。
- 有引导后候选集平均：**4.7 个**（Top-10 内必中）。
- 真实算法进入 Top-10：**100%**。
- 最终 top1 方向与真实算法主方向一致：**100%**。
- 平均提问数：**11.3**（接近 max_questions=12）。

## 实验表

| 题目 | 真实代表算法 | 问题数 | 无引导盲猜期望 | 引导后候选数 | Top10 命中 | 方向命中 |
|---|---|---|---|---|---|---|
| 1A Theatre Square | math 生态 | 12 | 9.2 | 6 | ✓ | ✓ |
| 339A Helpful Maths | 排序/贪心 | 12 | 13.3 | 4 | ✓ | ✓ |
| 363B Fence | 双指针/DP | 10 | 7.1 | 4 | ✓ | ✓ |
| 455A Boredom | DP | 10 | 8.0 | 4 | ✓ | ✓ |
| 466C Number of Ways | 前缀和/双指针 | 10 | 3.0 | 4 | ✓ | ✓ |
| 489C Given Length and Sum | 贪心/DP | 12 | 6.3 | 4 | ✓ | ✓ |
| 580A Kefa and First Steps | 线性 DP | 10 | 6.7 | 4 | ✓ | ✓ |
| 580C Kefa and Park | 树/DFS | 12 | 6.0 | 10 | ✓ | ✓ |
| 545C Woodcutters | 贪心/DP | 12 | 6.7 | 4 | ✓ | ✓ |
| 913C Party Lemonade | 状压/贪心 | 12 | 6.0 | 4 | ✓ | ✓ |
| 777C Alyona and Spreadsheet | 双指针/数据结构 | 12 | 2.9 | 4 | ✓ | ✓ |

## 复现

```bash
python scripts/agent_experiment.py
```

## 边界

- 这是“代理验证”，不是真人有效性验证。
- 它证明引擎在真实题目标签下能**收窄候选 + 方向正确**；
  不证明用户一定会因此学会解题。
- 真人验证仍建议按 `VALIDATION.md` 抽取 5 题做小样本。
