# 阶段一清洗报告：多源先验熵词典

- 生成时间：2026-08-30T03:51:04.845453+00:00
- 数据源：Codeforces 官方 API、DMOJ 公开 API v2、AtCoder Problems（kenkoooo）
- 洛谷：按用户确认不接入。

## 规模

- CF 题目总数：11370；带标签：11190；有 rating：11087
- CF 标签种数：38；两两组合：610
- DMOJ 题目：5259；类型种数：21
- AtCoder Problems 题目：9435；有 difficulty model：4814
- 本地算法数：120

## 清洗规则

- Codeforces problemset.problems 与 problemStatistics 按 (contestId,index) 合并
- 仅保留带标签的 CF 题目参与标签/组合统计
- CF 难度统计只使用有 rating 的题目
- DMOJ 仅统计带 types 的题目，points 作为难度代理
- AtCoder 仅使用有 difficulty 的 model，不参与标签分类
- 本地算法先验 = CF 标签频率映射 + DMOJ 类型频率映射的 50/50 综合
- 洛谷不接入

## Top 30 CF 标签

| 标签 | 频率 | P(题含此标签) | 难度中位 |
|---|---|---|---|
| greedy | 3553 | 0.317516 | 1600.0 |
| math | 3487 | 0.311618 | 1700 |
| implementation | 3050 | 0.272565 | 1400 |
| dp | 2526 | 0.225737 | 2200.0 |
| constructive algorithms | 2112 | 0.18874 | 1800 |
| data structures | 2043 | 0.182574 | 2250.0 |
| brute force | 1994 | 0.178195 | 1700 |
| binary search | 1294 | 0.115639 | 2000 |
| sortings | 1253 | 0.111975 | 1600 |
| graphs | 1228 | 0.109741 | 2300 |
| dfs and similar | 1078 | 0.096336 | 2100 |
| trees | 974 | 0.087042 | 2400 |
| number theory | 899 | 0.08034 | 1900 |
| combinatorics | 839 | 0.074978 | 2300.0 |
| strings | 821 | 0.073369 | 1600 |
| bitmasks | 714 | 0.063807 | 2200.0 |
| two pointers | 654 | 0.058445 | 1900 |
| *special | 560 | 0.050045 | 1800 |
| geometry | 430 | 0.038427 | 2200 |
| dsu | 415 | 0.037087 | 2200 |
| divide and conquer | 366 | 0.032708 | 2500 |
| interactive | 311 | 0.027793 | 2400 |
| games | 303 | 0.027078 | 1900 |
| shortest paths | 295 | 0.026363 | 2200 |
| probabilities | 269 | 0.024039 | 2400.0 |
| hashing | 238 | 0.021269 | 2300 |
| flows | 162 | 0.014477 | 2600.0 |
| matrices | 141 | 0.012601 | 2500 |
| fft | 115 | 0.010277 | 2900.0 |
| graph matchings | 106 | 0.009473 | 2500.0 |

## Top 20 DMOJ 类型

| 类型 | 频率 | P(题含此类型) | 题分中位 |
|---|---|---|---|
| Implementation | 1232 | 0.234265 | 5.0 |
| Graph Theory | 977 | 0.185777 | 15.0 |
| Data Structures | 699 | 0.132915 | 17.0 |
| Dynamic Programming | 686 | 0.130443 | 15.0 |
| Ad Hoc | 604 | 0.114851 | 15.0 |
| Simple Math | 561 | 0.106674 | 5.0 |
| Greedy Algorithms | 352 | 0.066933 | 10.0 |
| Intermediate Math | 291 | 0.055334 | 12.0 |
| Geometry | 203 | 0.0386 | 15.0 |
| String Algorithms | 191 | 0.036319 | 10.0 |
| Uncategorized | 190 | 0.036129 | 15.0 |
| Brute Force | 139 | 0.026431 | 7.0 |
| Advanced Math | 105 | 0.019966 | 20.0 |
| Interactive | 84 | 0.015973 | 15.0 |
| Simulation | 79 | 0.015022 | 7.0 |
| Recursion | 64 | 0.01217 | 10.0 |
| Divide and Conquer | 62 | 0.011789 | 20.0 |
| Constructive | 57 | 0.010839 | 12.0 |
| Game Theory | 48 | 0.009127 | 12.0 |
| Capture the Flag | 28 | 0.005324 | 7.0 |

## Top 30 缝合怪两两组合（CF）

| 组合 | 频率 | P(题含此组合) |
|---|---|---|
| greedy + math | 1044 | 0.093298 |
| constructive algorithms + greedy | 879 | 0.078552 |
| greedy + implementation | 876 | 0.078284 |
| dp + greedy | 761 | 0.068007 |
| implementation + math | 751 | 0.067113 |
| constructive algorithms + math | 726 | 0.064879 |
| brute force + math | 706 | 0.063092 |
| dp + math | 706 | 0.063092 |
| greedy + sortings | 698 | 0.062377 |
| brute force + implementation | 692 | 0.061841 |
| data structures + greedy | 686 | 0.061305 |
| math + number theory | 673 | 0.060143 |
| brute force + greedy | 639 | 0.057105 |
| dfs and similar + graphs | 573 | 0.051206 |
| data structures + dp | 534 | 0.047721 |
| combinatorics + math | 533 | 0.047632 |
| binary search + greedy | 509 | 0.045487 |
| dfs and similar + trees | 498 | 0.044504 |
| binary search + data structures | 488 | 0.04361 |
| data structures + implementation | 484 | 0.043253 |
| constructive algorithms + implementation | 478 | 0.042717 |
| brute force + dp | 464 | 0.041466 |
| combinatorics + dp | 437 | 0.039053 |
| dp + implementation | 390 | 0.034853 |
| dp + trees | 389 | 0.034763 |
| data structures + math | 365 | 0.032618 |
| data structures + sortings | 359 | 0.032082 |
| dfs and similar + dp | 356 | 0.031814 |
| binary search + math | 355 | 0.031725 |
| data structures + trees | 354 | 0.031635 |

## AtCoder 难度摘要

- 难度模型数：4814
- 范围：-10000 ~ 4383；中位：1316.5

## 本地 120 算法映射覆盖率

- CF 标签映射：120/120
- DMOJ 类型映射：120/120

## 已知近似/局限

- CF 标签是英文粗粒度，本地 120 算法频率为映射后的估算值。
- DMOJ 类型只有 21 类，points 只作难度代理，不是严格 rating。
- AtCoder 只有难度曲线，没有算法标签，因此不作为算法分类依据，只用于交叉验证难度。
- 组合统计来自 CF 官方标签；中文“线段树+贪心”这类组合会在阶段二映射展开。
