"""生成 expert_content/algorithm_cards.json：120 个算法卡。

- what 来自 info_framework.ALGORITHM_INFO（专家蒸馏的信息论视角）。
- how/code/complexity 对 Tier 1-4 高频算法手工编写 C++ 要点；
  其余算法用“实现要点”兜底，保证字段非空、JSON 合法。
"""

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from info_framework import get_alg_info  # noqa: E402
from knowledge_data import ALGORITHM_NAMES  # noqa: E402
from tiers_data import TIERS  # noqa: E402


def tier14_names() -> set[str]:
    out: set[str] = set()
    for tier in TIERS[:4]:
        for tag in tier["tags"]:
            out.update(tag.get("algorithms", []))
    return out


CORE = tier14_names()

HOW = {
    "暴力枚举": "按题意穷举所有候选，先确认状态空间上界；剪枝只在超时后加。",
    "位掩码子集枚举": "用整数二进制位表示集合，for (s = 0; s < (1<<n); ++s) 枚举子集。",
    "结构体排序（重载运算符）": "在 struct 内重载 operator<，按多关键字排序后直接遍历。",
    "归并排序求逆序对": "归并时右半元素前放一个，就贡献左侧未合并元素个数。",
    "排序后取最值（基础贪心）": "先按某个维度排序，再线性扫描维护当前最优。",
    "区间调度（贪心）": "按结束时间排序，贪心选最早结束且不冲突的区间。",
    "二分答案": "先写 check(x) 判定可行性，再在单调值域上二分。",
    "二分查找": "在有序数组上维护 [l,r)，每次比较中间位置缩小范围。",
    "GCD / LCM": "gcd 用欧几里得；lcm = a / gcd * b，注意先除后乘防溢出。",
    "素数判定（试除法）": "枚举 2..sqrt(n)，能整除则非素数；注意 1 不是素数。",
    "埃氏筛": "从 2 开始标记倍数，O(n log log n) 得到素数表。",
    "快速幂": "把指数二进制分解，base 自乘，ans *= base 当位为 1。",
    "约瑟夫环（模拟）": "用队列/循环链表模拟报数出圈；n 大时用递推公式。",
    "双指针（滑动窗口）": "右端点前进，不满足条件时左端点收缩，维护窗口性质。",
    "一维前缀和": "pre[i]=pre[i-1]+a[i]，区间和 = pre[r]-pre[l-1]。",
    "二维前缀和": "用容斥：S=pre[x2][y2]-pre[x1-1][y2]-pre[x2][y1-1]+pre[x1-1][y1-1]。",
    "差分数组": "区间 [l,r] 加 v：diff[l]+=v, diff[r+1]-=v；最后前缀和还原。",
    "构造算法": "先找奇偶/模数/对称等不变量，直接构造显式解。",
    "反悔贪心（带堆维护）": "用小根堆维护已选代价，遇到更优时弹出堆顶并替换。",
    "唯一分解定理": "用线性筛最小质因子，反复除得到质因数分解。",
    "线性筛（欧拉筛）": "每个合数只被最小质因子筛一次，同时维护最小质因子/欧拉函数。",
    "费马小定理求逆元": "mod 为素数时 inv(x)=pow(x, mod-2, mod)。",
    "欧拉函数": "phi(n)=n*prod(1-1/p)，线性筛可递推维护。",
    "扩展欧几里得 (exgcd)": "递归求 ax+by=gcd(a,b)，回溯时 x,y 互换更新。",
    "0/1 背包": "dp[j] = max(dp[j], dp[j-w]+v)，内层倒序保证每件只用一次。",
    "完全背包": "dp[j] = max(dp[j], dp[j-w]+v)，内层正序。",
    "LIS（最长上升子序列）": "dp[i]=前缀最长；O(n log n) 用 tails 数组二分。",
    "LCS（最长公共子序列）": "二维 dp，a[i]==b[j] 对角+1，否则取左/上最大值。",
    "栈（基础）": "push/pop/top，LIFO；适合匹配、单调性、表达式求值。",
    "队列（基础）": "FIFO；BFS 层序与拓扑排序的骨架。",
    "单调栈": "新元素入栈前弹出所有不优元素，栈内保持单调。",
    "单调队列（滑动窗口）": "队列存下标，维护窗口最值，过期下标弹出。",
    "堆（Top-K）": "维护大小为 K 的小顶堆，新元素比堆顶大则替换。",
    "Dijkstra": "非负权图上用优先队列，dist[u]+w 松弛相邻点。",
    "Bellman-Ford": "对每条边松弛 n-1 轮；再松弛一轮可判负环。",
    "Floyd-Warshall": "三重循环 k,i,j，dp[i][j]=min(dp[i][j], dp[i][k]+dp[k][j])。",
    "Kruskal": "边按权排序，用 DSU 加边，加满 n-1 条即得 MST。",
    "Prim": "从任一点出发维护已选集合，每次选连接集合的最小边。",
    "连通块染色": "DFS/BFS 遍历未访问点，把所有相邻点染同色。",
    "二分图染色判定": "BFS 交替染 1/2，冲突则非二分图。",
    "简单回溯": "按状态树递归搜索，剪支无效分支，记录路径。",
    "石子合并": "区间 DP：dp[i][j]=min(dp[i][k]+dp[k+1][j])+sum(i,j)。",
    "TSP（状压）": "dp[mask][i] 表示访问集合 mask 且当前在 i 的最短路径。",
    "树上最大权独立集": "树形 DP：选 u 则子节点不能选，不选则子节点可取可不取。",
    "KMP": "求 next 数组，匹配失败时按 next 回退，O(n+m)。",
    "Trie（字典树）": "每个节点一个字典/数组，插入查询沿字符下走。",
    "字符串哈希（Rolling Hash）": "预处理前缀哈希与 p 的幂，区间哈希 O(1)。",
    "并查集 (DSU)": "父指针数组 + 路径压缩 + 按秩合并；find 返回根。",
    "带权并查集": "额外维护到父节点的权值，合并时按差/异或关系更新。",
    "状态压缩 + BFS": "把状态编码成整数，visited 用布尔/位图，BFS 求最少步。",
    "矩阵快速幂优化递推": "把线性递推写成转移矩阵，用快速幂算 M^n 再乘初始向量。",
    "LCA（倍增）": "预处理 up[v][k] 与深度，先对齐深度再一起上跳。",
    "树上差分": "对路径 u-v：cnt[u]++, cnt[v]++, cnt[lca]-=2；DFS 汇总。",
    "树的直径 / 重心": "直径：两次 DFS 最远点；重心：删去后最大子树最小。",
    "线段树（区间和 + 懒标记）": "节点存区间和，pushdown 下传懒标记，build/update/query O(log n)。",
    "树状数组 (BIT)": "lowbit 维护前缀和；add 向上，sum 向下。",
    "树状数组求逆序对": "从后往前扫，用 BIT 统计小于当前值的个数并累加。",
    "ST 表（静态区间最值）": "st[i][k]=区间 [i,i+2^k-1] 最值；查询取两段重叠最值。",
    "Tarjan 求 SCC": "DFS 维护 dfn/low/栈，low[u]==dfn[u] 时弹栈成强连通分量。",
    "割点 / 桥": "DFS 树 + low；割点：子节点 low>=dfn[u]；桥：low[v]>dfn[u]。",
    "拓扑排序 (Kahn)": "入度 0 入队，弹出后减邻接入度，入度 0 再入队。",
    "拓扑排序 + DAG DP": "按拓扑序 DP，前驱状态推到后继。",
    "Lucas 定理": "n,m 按 p 进制拆位，C(n,m)=prod C(ni,mi) mod p。",
    "容斥原理": "总方案 - 单个条件并集；用子集枚举或 Mobius 公式。",
    "错排 / 卡特兰数": "错排 D[n]=(n-1)(D[n-1]+D[n-2])；卡特兰 C[n]=C(2n,n)/(n+1)。",
    "组合数（预处理阶乘）": "预处理 fact/invfact，C(n,k)=fact[n]*invfact[k]*invfact[n-k]。",
    "Nim 游戏与 SG 函数": "Nim 和为 0 必败；SG(u)=mex(SG(后继))，多游戏异或。",
    "Manacher": "维护回文半径与最右边界，线性求所有回文半径。",
    "Z-function": "Z[i]=s 与 s[i:] 的最长公共前缀，类 KMP 线性。",
    "后缀数组 (SA)": "倍增排序后缀，或用 SA-IS；配套 height 数组。",
    "数位 DP（不含 4）": "dfs(pos, lim, lead) 记忆化数位状态，按位转移。",
    "轮廓线 DP（简单棋盘状压）": "逐格转移，用轮廓线掩码记录当前行/格状态。",
    "期望 DP（掷骰子）": "dp[i] 表示从状态 i 到终点的期望步数，按转移概率求期望。",
}

CODE = {
    "暴力枚举": "for (int i = 0; i < n; ++i)\n  for (int j = i+1; j < n; ++j)\n    ans = max(ans, calc(i,j));",
    "位掩码子集枚举": "for (int s = 0; s < (1<<n); ++s)\n  for (int i = 0; i < n; ++i)\n    if (s>>i & 1) ...;",
    "结构体排序（重载运算符）": "struct Node { int a,b; bool operator<(const Node& o) const { return a<o.a || (a==o.a && b<o.b); } };",
    "归并排序求逆序对": "long long ans=0;\nvoid merge(int l,int m,int r){ /* 合并时右元素前放: ans += m-l+1-i */ }",
    "排序后取最值（基础贪心）": "sort(a.begin(), a.end());\nfor (int x : a) cur += x, ans = max(ans, cur);",
    "区间调度（贪心）": "sort(v.begin(), v.end(), [](auto&a,auto&b){return a.r<b.r;});\nint last=-1; for(auto [l,r]:v) if(l>last) ans++, last=r;",
    "二分答案": "auto ok=[&](int x){...};\nint l=0,r=1e9;\nwhile(l<r){int m=(l+r+1)/2; if(ok(m)) l=m; else r=m-1;}",
    "二分查找": "int l=0,r=n;\nwhile(l<r){int m=(l+r)/2; if(a[m]<x) l=m+1; else r=m;}",
    "GCD / LCM": "int gcd(int a,int b){return b?gcd(b,a%b):a;}\nlong long lcm(long long a,long long b){return a/gcd(a,b)*b;}",
    "素数判定（试除法）": "bool is_prime(long long n){ if(n<2) return false; for(long long i=2;i*i<=n;++i) if(n%i==0) return false; return true; }",
    "埃氏筛": "vector<bool> is(n+1,true); is[0]=is[1]=false;\nfor(int i=2;i<=n;++i) if(is[i]) for(int j=i*i;j<=n;j+=i) is[j]=false;",
    "快速幂": "long long qpow(long long a,long long b,long long mod){ long long r=1; for(;b;b>>=1){ if(b&1) r=r*a%mod; a=a*a%mod; } return r; }",
    "约瑟夫环（模拟）": "queue<int> q; for(int i=1;i<=n;++i) q.push(i);\nwhile(q.size()>1){ for(int i=1;i<k;++i){q.push(q.front());q.pop();} q.pop(); }",
    "双指针（滑动窗口）": "for(int l=0,r=0; r<n; ++r){ add(a[r]); while(!ok()) del(a[l++]); ans=max(ans,r-l+1); }",
    "一维前缀和": "vector<long long> pre(n+1); for(int i=1;i<=n;++i) pre[i]=pre[i-1]+a[i];\n// [l,r] = pre[r]-pre[l-1]",
    "二维前缀和": "for i 1..n for j 1..m pre[i][j]=pre[i-1][j]+pre[i][j-1]-pre[i-1][j-1]+a[i][j];",
    "差分数组": "diff[l]+=v; diff[r+1]-=v;\nfor(int i=1;i<=n;++i) diff[i]+=diff[i-1];",
    "构造算法": "// 目标构造：利用奇偶/模数/对称直接输出方案，避免搜索\nfor(int i=0;i<n;++i) ans[i] = ...;",
    "反悔贪心（带堆维护）": "priority_queue<int, vector<int>, greater<int>> pq;\nfor(int x: v){ if(pq.size()<k) pq.push(x); else if(x>pq.top()){ pq.pop(); pq.push(x); } }",
    "唯一分解定理": "while(n>1){ int p=spf[n], c=0; while(n%p==0) n/=p, c++; factors.push_back({p,c}); }",
    "线性筛（欧拉筛）": "for(int i=2;i<=n;++i){ if(!vis[i]) pr.push_back(i), spf[i]=i; for(int p:pr){ if(i*p>n) break; vis[i*p]=1; spf[i*p]=p; if(i%p==0) break; } }",
    "费马小定理求逆元": "long long inv(long long x, long long mod){ return qpow(x, mod-2, mod); }",
    "欧拉函数": "int phi[100]; phi[1]=1;\nfor(int i=2;i<N;++i) phi[i]=i;\nfor(int i=2;i<N;++i) if(phi[i]==i) for(int j=i;j<N;j+=i) phi[j]-=phi[j]/i;",
    "扩展欧几里得 (exgcd)": "long long exgcd(long long a,long long b,long long &x,long long &y){ if(!b){x=1;y=0;return a;} long long g=exgcd(b,a%b,y,x); y-=a/b*x; return g; }",
    "0/1 背包": "for(int i=0;i<n;++i) for(int j=W;j>=w[i];--j) dp[j]=max(dp[j],dp[j-w[i]]+v[i]);",
    "完全背包": "for(int i=0;i<n;++i) for(int j=w[i];j<=W;++j) dp[j]=max(dp[j],dp[j-w[i]]+v[i]);",
    "LIS（最长上升子序列）": "vector<int> tails;\nfor(int x:a){ auto it=lower_bound(tails.begin(),tails.end(),x); if(it==tails.end()) tails.push_back(x); else *it=x; }",
    "LCS（最长公共子序列）": "for i 1..n for j 1..m dp[i][j]= (a[i]==b[j]? dp[i-1][j-1]+1 : max(dp[i-1][j],dp[i][j-1]));",
    "栈（基础）": "stack<int> st; st.push(x); st.pop(); st.top();",
    "队列（基础）": "queue<int> q; q.push(x); q.front(); q.pop();",
    "单调栈": "stack<int> st;\nfor(int i=0;i<n;++i){ while(!st.empty() && a[st.top()]>=a[i]) st.pop(); st.push(i); }",
    "单调队列（滑动窗口）": "deque<int> q;\nfor(int i=0;i<n;++i){ if(!q.empty() && q.front()<i-k+1) q.pop_front(); while(!q.empty() && a[q.back()]>=a[i]) q.pop_back(); q.push_back(i); }",
    "堆（Top-K）": "priority_queue<int,vector<int>,greater<int>> pq;\n// 小于 k 直接进，否则与堆顶比较替换",
    "Dijkstra": "priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;\ndist[s]=0; pq.push({0,s});\nwhile(!pq.empty()){ auto [d,u]=pq.top(); pq.pop(); if(d!=dist[u]) continue; for(auto [v,w]:g[u]) if(dist[v]>d+w) dist[v]=d+w, pq.push({dist[v],v}); }",
    "Bellman-Ford": "for(int i=1;i<=n-1;++i) for(auto [u,v,w]:edges) if(dist[v]>dist[u]+w) dist[v]=dist[u]+w;\n// 再跑一轮，仍能更新则有负环",
    "Floyd-Warshall": "for(int k=1;k<=n;++k) for(int i=1;i<=n;++i) for(int j=1;j<=n;++j) d[i][j]=min(d[i][j],d[i][k]+d[k][j]);",
    "Kruskal": "sort(edges.begin(),edges.end(),[](auto&a,auto&b){return a.w<b.w;});\nfor(auto [u,v,w]:edges) if(dsu.unite(u,v)) ans+=w, cnt++;",
    "Prim": "priority_queue<pair<int,int>,vector<pair<int,int>>,greater<>> pq;\nvis[1]=1; for(auto [v,w]:g[1]) pq.push({w,v});\nwhile(!pq.empty()){ auto [w,u]=pq.top(); pq.pop(); if(vis[u]) continue; vis[u]=1; ans+=w; ...}",
    "连通块染色": "void dfs(int u,int c){ col[u]=c; for(int v:g[u]) if(!col[v]) dfs(v,c); }",
    "二分图染色判定": "queue<int> q; col[s]=1; q.push(s);\nwhile(!q.empty()){ int u=q.front(); q.pop(); for(int v:g[u]) if(!col[v]) col[v]=3-col[u], q.push(v); else if(col[v]==col[u]) return false; }",
    "简单回溯": "void dfs(int dep){ if(dep==n){ ...; return; } for(int x: cand) if(ok){ mark; dfs(dep+1); unmark; } }",
    "石子合并": "for(int len=2;len<=n;++len) for(int i=1;i+len-1<=n;++i){ int j=i+len-1; dp[i][j]=1e18; for(int k=i;k<j;++k) dp[i][j]=min(dp[i][j],dp[i][k]+dp[k+1][j]+sum[i][j]); }",
    "TSP（状压）": "dp[1<<i][i]=0; for(mask) for(i) if(mask>>i&1) for(j) if(!(mask>>j&1)) dp[mask|1<<j][j]=min(...);",
    "树上最大权独立集": "void dfs(int u,int p){ f[u][1]=w[u]; for(int v:g[u]) if(v!=p){ dfs(v,u); f[u][0]+=max(f[v][0],f[v][1]); f[u][1]+=f[v][0]; } }",
    "KMP": "for(int i=1;i<m;++i){ int j=ne[i-1]; while(j&&p[i]!=p[j]) j=ne[j-1]; if(p[i]==p[j]) ++j; ne[i]=j; }\n// 匹配时类似回退",
    "Trie（字典树）": "struct Node{ int nxt[26]; int cnt; } tr[N]; int tot;\nvoid insert(const string&s){ int u=0; for(char c:s){ if(!tr[u].nxt[c-'a']) tr[u].nxt[c-'a']=++tot; u=tr[u].nxt[c-'a']; } tr[u].cnt++; }",
    "字符串哈希（Rolling Hash）": "pre[i]=(pre[i-1]*B+s[i])%M; pw[i]=pw[i-1]*B%M;\nhash(l,r)=(pre[r]-pre[l-1]*pw[r-l+1]+M)%M;",
    "并查集 (DSU)": "int find(int x){ return fa[x]==x?x:fa[x]=find(fa[x]); }\nvoid unite(int a,int b){ a=find(a); b=find(b); if(a!=b) fa[a]=b; }",
    "带权并查集": "int find(int x){ if(fa[x]==x) return x; int p=fa[x]; fa[x]=find(fa[x]); w[x]+=w[p]; return fa[x]; }\n// 合并时按关系维护 w",
    "状态压缩 + BFS": "queue<int> q; vis[st]=1; q.push(st);\nwhile(!q.empty()){ int s=q.front(); q.pop(); for(move: ...) if(!vis[ns]) vis[ns]=1, q.push(ns); }",
    "矩阵快速幂优化递推": "Mat mul(Mat a,Mat b); Mat qpow(Mat a,long long n){ Mat r=I; for(;n;n>>=1){ if(n&1) r=mul(r,a); a=mul(a,a); } return r; }",
    "LCA（倍增）": "for(int k=1;k<LOG;++k) up[v][k]=up[up[v][k-1]][k-1];\n// 对齐深度后从高到低尝试上跳，最后答案为 up[u][0]",
    "树上差分": "cnt[u]++, cnt[v]++, cnt[lca]--, cnt[fa[lca]]--;\nvoid dfs(u){ for(v) dfs(v), cnt[u]+=cnt[v]; }",
    "树的直径 / 重心": "直径：两遍 DFS 找最远点；重心：dfs 维护 sz，maxPart=min(maxPart, n-sz[u], 子树sz)。",
    "线段树（区间和 + 懒标记）": "void push(int p){ if(lz[p]){ add(p<<1,lz[p]); add(p<<1|1,lz[p]); lz[p]=0; } }\nvoid update(int p,int l,int r,int ql,int qr,int v){ if(ql<=l&&r<=qr){ add(p,v); return; } push(p); ... }",
    "树状数组 (BIT)": "void add(int i,int v){ for(;i<=n;i+=i&-i) bit[i]+=v; }\nint sum(int i){ int s=0; for(;i>0;i-=i&-i) s+=bit[i]; return s; }",
    "树状数组求逆序对": "long long ans=0;\nfor(int i=n-1;i>=0;--i){ ans += sum(a[i]-1); add(a[i],1); }",
    "ST 表（静态区间最值）": "for(int i=1;i<=n;++i) st[i][0]=a[i];\nfor(int k=1;(1<<k)<=n;++k) for(int i=1;i+(1<<k)-1<=n;++i) st[i][k]=max(st[i][k-1],st[i+(1<<(k-1))][k-1]);",
    "Tarjan 求 SCC": "void tarjan(int u){ dfn[u]=low[u]=++tm; stk.push(u); ins[u]=1; for(v:g[u]){ if(!dfn[v]) tarjan(v), low[u]=min(low[u],low[v]); else if(ins[v]) low[u]=min(low[u],dfn[v]); } if(low[u]==dfn[u]){ while(1){ int x=stk.top(); stk.pop(); ins[x]=0; comp[x]=cnt; if(x==u) break; } cnt++; } }",
    "割点 / 桥": "// 割点：若 u 是根则子数>1；否则存在子 v 满足 low[v]>=dfn[u]\n// 桥：low[v] > dfn[u]",
    "拓扑排序 (Kahn)": "queue<int> q; for(i) if(!deg[i]) q.push(i);\nwhile(!q.empty()){ int u=q.front(); q.pop(); order.push_back(u); for(v:g[u]) if(--deg[v]==0) q.push(v); }",
    "拓扑排序 + DAG DP": "for(int u: order) for(int v: g[u]) dp[v]=max(dp[v], dp[u]+w);",
    "Lucas 定理": "long long C(int n,int k,int p){ return fact[n]*invfact[k]%p*invfact[n-k]%p; }\nlong long lucas(long long n,long long k,int p){ if(k==0) return 1; return C(n%p,k%p,p)*lucas(n/p,k/p,p)%p; }",
    "容斥原理": "long long ans=0;\nfor(int mask=1; mask<(1<<m); ++mask){ int cnt=__builtin_popcount(mask); long long cur=...; ans += (cnt&1?+cur:-cur); }",
    "错排 / 卡特兰数": "D[0]=1; D[1]=0; for(int i=2;i<=n;++i) D[i]=(i-1)*(D[i-1]+D[i-2]);\nC[n]=C(2n,n)/(n+1);",
    "组合数（预处理阶乘）": "fact[0]=1; for(int i=1;i<=n;++i) fact[i]=fact[i-1]*i%mod;\ninvfact[n]=qpow(fact[n],mod-2,mod); for(int i=n;i>=1;--i) invfact[i-1]=invfact[i]*i%mod;",
    "Nim 游戏与 SG 函数": "int sg=0; for(int x:piles) sg^=x; cout << (sg ? \"First\" : \"Second\");\n// SG(u)=mex(sg[v])",
    "Manacher": "for(int i=0;i<n;){ r=max(...); while(s[i-d]==s[i+d]) ++d; d[i]=d; ... }",
    "Z-function": "vector<int> z(n); for(int i=1,l=0,r=0;i<n;++i){ if(i<=r) z[i]=min(r-i+1,z[i-l]); while(i+z[i]<n && s[z[i]]==s[i+z[i]]) ++z[i]; if(i+z[i]-1>r) l=i,r=i+z[i]-1; }",
    "后缀数组 (SA)": "// 倍增：sa[i] 按前 2^k 字符排序，rank 压缩；最终 rank 唯一确定 sa\nvector<int> sa(n), rk(n); // 用计数排序实现",
    "数位 DP（不含 4）": "long long dfs(int pos,int lim){ if(pos<0) return 1; if(!lim && memo[pos]!=-1) return memo[pos]; long long res=0; int up=lim?digit[pos]:9; for(int d=0;d<=up;++d){ if(d==4) continue; res+=dfs(pos-1,lim&&d==up); } return lim?res:memo[pos]=res; }",
    "轮廓线 DP（简单棋盘状压）": "for(int i=0;i<n;++i) for(int j=0;j<m;++j) for(mask) {\n  // 用 mask 表示当前轮廓线已决策位，逐格推下一状态\n}",
    "期望 DP（掷骰子）": "dp[i] = 1 + sum(p[j] * dp[i+j]); // 从目标反向递推，边界 dp[target]=0",
}

COMPLEXITY = {
    "暴力枚举": "O(候选空间)", "位掩码子集枚举": "O(2^n)", "结构体排序（重载运算符）": "O(n log n)",
    "归并排序求逆序对": "O(n log n)", "排序后取最值（基础贪心）": "O(n log n)", "区间调度（贪心）": "O(n log n)",
    "二分答案": "O(log V * check)", "二分查找": "O(log n)", "GCD / LCM": "O(log min(a,b))",
    "素数判定（试除法）": "O(sqrt(n))", "埃氏筛": "O(n log log n)", "快速幂": "O(log exp)",
    "约瑟夫环（模拟）": "O(n) / 递推 O(n)", "双指针（滑动窗口）": "O(n)", "一维前缀和": "O(n) 预处理 / O(1) 查询",
    "二维前缀和": "O(nm) 预处理 / O(1) 查询", "差分数组": "O(n)", "构造算法": "O(n)",
    "反悔贪心（带堆维护）": "O(n log n)", "唯一分解定理": "O(log n)", "线性筛（欧拉筛）": "O(n)",
    "费马小定理求逆元": "O(log mod)", "欧拉函数": "O(n log log n)", "扩展欧几里得 (exgcd)": "O(log min(a,b))",
    "0/1 背包": "O(nW)", "完全背包": "O(nW)", "LIS（最长上升子序列）": "O(n log n)", "LCS（最长公共子序列）": "O(nm)",
    "栈（基础）": "O(1) 每次", "队列（基础）": "O(1) 每次", "单调栈": "O(n)", "单调队列（滑动窗口）": "O(n)",
    "堆（Top-K）": "O(n log k)", "Dijkstra": "O((n+m) log n)", "Bellman-Ford": "O(nm)",
    "Floyd-Warshall": "O(n^3)", "Kruskal": "O(m log m)", "Prim": "O((n+m) log n)",
    "连通块染色": "O(n+m)", "二分图染色判定": "O(n+m)", "简单回溯": "指数级", "石子合并": "O(n^3)",
    "TSP（状压）": "O(2^n n^2)", "树上最大权独立集": "O(n)", "KMP": "O(n+m)", "Trie（字典树）": "O(字符串长度)",
    "字符串哈希（Rolling Hash）": "O(1) 查哈希", "并查集 (DSU)": "近似 O(alpha(n))", "带权并查集": "近似 O(alpha(n))",
    "状态压缩 + BFS": "O(状态数 * 转移)", "矩阵快速幂优化递推": "O(k^3 log n)", "LCA（倍增）": "O((n+m) log n)",
    "树上差分": "O(n+m)", "树的直径 / 重心": "O(n)", "线段树（区间和 + 懒标记）": "O(log n) per op",
    "树状数组 (BIT)": "O(log n) per op", "树状数组求逆序对": "O(n log n)", "ST 表（静态区间最值）": "O(n log n) / O(1) 查询",
    "Tarjan 求 SCC": "O(n+m)", "割点 / 桥": "O(n+m)", "拓扑排序 (Kahn)": "O(n+m)", "拓扑排序 + DAG DP": "O(n+m)",
    "Lucas 定理": "O(p + log_p n * p?)", "容斥原理": "O(2^m)", "错排 / 卡特兰数": "O(n)", "组合数（预处理阶乘）": "O(n) 预处理 / O(1) 查询",
    "Nim 游戏与 SG 函数": "O(状态转移)", "Manacher": "O(n)", "Z-function": "O(n)", "后缀数组 (SA)": "O(n log n)",
    "数位 DP（不含 4）": "O(位数 * 状态)", "轮廓线 DP（简单棋盘状压）": "O(nm * 2^m)", "期望 DP（掷骰子）": "O(n)",
}

ADV_HOW = {
    "Dinic 最大流": "建图；BFS 分层，DFS 找增广路，当前弧优化。",
    "最小割建模": "把限制写成容量边；最大流=最小割；常用源点/汇点与无穷边表示“必须选一边”。",
    "二分图最大匹配（匈牙利）": "对每个左部点尝试增广：vis 标记右部，match[v]=u，找不到就继续找。",
    "KM 算法": "求最大权完美匹配：维护顶标与 slack，O(n^3) 增广。",
    "主席树（区间第 k 小）": "按值域建立可持续化权值线段树，root[r]-root[l-1] 差分。",
    "FHQ Treap（无旋 Treap）": "以随机优先级维护平衡树；split 按值/按 size，merge 合并，支持区间。",
    "莫队（区间不同数）": "按块排序查询；移动左右端点并维护计数与答案。",
    "斜率优化（CHT）": "转移式化为 y=kx+b 的形式，维护下/上凸壳，用单调队列/二分找最优点。",
    "四边形不等式优化": "满足决策单调性时，用分治或单调队列把 O(n^2) 降到 O(n log n)/O(n)。",
    "Andrew 单调链凸包": "按 x/y 排序，扫两遍用叉积维护上下凸壳。",
    "叉积 / 点积判断方位": "叉积判断左右/顺逆；点积判断夹角/投影。",
    "最近点对（分治）": "按 x 排序分治；合并时检查中心带并按 y 排序比较。",
    "线段相交判定": "用跨立实验：两线段互相跨过对方。",
    "高斯消元（异或方程组 bitset）": "把每行压成 bitset，高斯消元求解异或方程组。",
    "扩展中国剩余定理（EXCRT）": "不断合并 x≡a (mod m)：解模线性方程并用 exgcd 求新模。",
    "线性基": "把数插入线性基：高位到低位，若当前位无基则存入，否则异或继续。",
    "中国剩余定理 (CRT)": "模数互质时用逆元求 M_i 组合；不互质转 EXCRT。",
    "AC 自动机 + 矩阵快速幂": "建 AC 自动机转移图，把禁止状态排除后做矩阵快速幂计数。",
    "AC 自动机": "Trie + fail 指针；匹配时沿 fail 跳转累计。",
    "2-SAT": "每个变量拆真/假节点，按蕴含建图，Tarjan 判 SCC 可行性。",
    "线段树合并/分裂": "动态开点线段树；合并递归合并相同区间，分裂按权值切分。",
    "可撤销并查集": "按秩合并 + 栈记录变化；回滚时恢复 fa/sz。",
    "基环树 DP": "找环，断环成链；对每条边做两次 DP（选/不选端点）。",
    "仙人掌 / 圆方树": "Tarjan 找环，把环建成方点；圆点连原边，方点连环上点。",
    "旋转卡壳": "在凸包上维护对踵点，利用叉积随角度单调旋转。",
    "SAM（后缀自动机）": "在线插入字符，扩展 last 并复制/连 link；用于子串统计。",
    "Link-Cut Tree (LCT)": "splay 维护偏爱链，access/makeroot/findroot/split 实现动态树操作。",
    "树链剖分 (HLD)": "两次 dfs 求 size/depth/heavy；按 dfs 序把链映射到线段树。",
    "可持久化数据结构（主席树进阶）": "复用主席树根链，支持历史版本区间查询；进阶配合树上差分。",
    "后缀自动机（SAM）进阶": "在 parent 树上拓扑 DP，统计每个状态出现次数/本质不同子串。",
    "广义 SAM": "多串插入：每次从 root 或上一串根开始，插入时复用已有转移。",
    "FFT": "蝴蝶变换迭代版；点值相乘后 IDFT。",
    "NTT": "模 998244353 的原根 g=3，NTT 替代 FFT 避免精度。",
    "生成函数": "把组合序列看成形式幂级数；用 NTT 做卷积/求逆。",
    "莫比乌斯反演": "线性筛 mu，用 Dirichlet 卷积把 [gcd=1] 转为求和。",
    "线性基进阶": "在线性基上做求最大值/第 k 大/异或和计数。",
    "半平面交": "按极角排序，双端队列维护交集；叉积判断淘汰。",
    "最小圆覆盖": "随机增量：若点在圆外，则以两点/三点重算圆。",
    "三维凸包": "增量法维护面集；用点面方向判断可见面并重建。",
    "支配树": "Lengauer-Tarjan：按 DFS 序求半支配者，再从半支配者更新支配者。",
    "点分治/边分治": "每次找重心，处理经过重心的路径，递归分治子树。",
    "动态图连通性（离线）": "把每条边存在时间区间拆分，线段树分治 + 可撤销并查集。",
    "插头 DP": "轮廓线状态用括号/最小表示编码；逐格转移，处理生成树/回路。",
    "DP 套 DP": "外层 DP 的状态本身是一个自动机/内层 DP 结果，用轮廓线或子集压缩。",
    "分治 DP": "决策单调时，solve(l,r,optl,optr) 递归计算中点最优决策。",
    "上下界网络流": "加超级源/汇，用容量差转普通可行流；再在原图跑最大流。",
    "最小费用最大流": "SPFA/Bellman-Ford 找最短路增广；或 Dijkstra + 势能。",
}

ADV_CODE = {
    "Dinic 最大流": "bool bfs(){ queue<int>q; fill(dis,dis+n+1,-1); dis[s]=0; q.push(s);\n while(!q.empty()){int u=q.front();q.pop(); for(auto&e:g[u]) if(e.cap&&dis[e.to]<0) dis[e.to]=dis[u]+1,q.push(e.to);} return dis[t]>=0; }\nint dfs(int u,int f){ if(u==t) return f; for(int&i=cur[u];i<g[u].size();++i){ auto&e=g[u][i]; if(e.cap&&dis[e.to]==dis[u]+1){ int d=dfs(e.to,min(f,e.cap)); if(d){ e.cap-=d; g[e.to][e.rev].cap+=d; return d; } } } return 0; }",
    "最小割建模": "// 建图：s -> A(容量代价A)；B -> t(容量代价B)；冲突加 A->B INF\n// 答案 = Dinic(s,t)。最小割=最大流。",
    "二分图最大匹配（匈牙利）": "bool dfs(int u){ for(int v:g[u]) if(!vis[v]){ vis[v]=1; if(!match[v]||dfs(match[v])){ match[v]=u; return true; } } return false; }\nint ans=0; for(int i=1;i<=n;++i){ fill(vis,vis+m+1,0); if(dfs(i)) ++ans; }",
    "KM 算法": "// O(n^3) 最大权完美匹配：顶标 lx[i],ly[j]; slack[j]=min(lx[i]+ly[j]-w[i][j])\n// 每次增广调整顶标；实现较长，核心是匈牙利式增广 + slack 数组。",
    "主席树（区间第 k 小）": "int update(int pre,int l,int r,int p){ int now=++tot; tr[now]=tr[pre]; tr[now].sum++; if(l<r){ int m=(l+r)/2; if(p<=m) tr[now].l=update(tr[pre].l,l,m,p); else tr[now].r=update(tr[pre].r,m+1,r,p); } return now; }\nint query(int u,int v,int l,int r,int k){ if(l==r) return l; int m=(l+r)/2, cnt=tr[tr[u].l].sum-tr[tr[v].l].sum; if(k<=cnt) return query(tr[u].l,tr[v].l,l,m,k); return query(tr[u].r,tr[v].r,m+1,r,k-cnt); }",
    "FHQ Treap（无旋 Treap）": "struct Node{ int ch[2],pri,sz,val; } tr[N];\nvoid split(int rt,int k,int&a,int&b){ if(!rt){a=b=0;return;} if(tr[tr[rt].ch[0]].sz>=k){ split(tr[rt].ch[0],k,a,tr[rt].ch[0]); b=rt; } else { split(tr[rt].ch[1],k-tr[tr[rt].ch[0]].sz-1,tr[rt].ch[1],b); a=rt; } push(rt); }\nint merge(int a,int b){ if(!a||!b) return a+b; if(tr[a].pri<tr[b].pri){ tr[a].ch[1]=merge(tr[a].ch[1],b); push(a); return a; } else { tr[b].ch[0]=merge(a,tr[b].ch[0]); push(b); return b; } }",
    "莫队（区间不同数）": "struct Q{ int l,r,id,blk; };\nbool cmp(Q a,Q b){ return a.blk!=b.blk ? a.blk<b.blk : (a.r<b.r); }\nvoid add(int x){ if(++cnt[a[x]]==1) ans++; }\nvoid del(int x){ if(--cnt[a[x]]==0) ans--; }\n// 按块排序后移动 l,r",
    "斜率优化（CHT）": "deque<int> q;\nfor(int i=1;i<=n;++i){ while(q.size()>=2 && (y(q[1])-y(q[0]))*(x(i)-x(q[0])) <= (y(i)-y(q[0]))*(x(q[1])-x(q[0]))) q.pop_front();\n  int j=q.front(); dp[i]=...;\n  while(q.size()>=2 && ...) q.pop_back(); q.push_back(i); }",
    "四边形不等式优化": "// 若 w 满足四边形不等式且决策单调：dp[i][j]=min(dp[i][k]+dp[k+1][j])+w(i,j)\n// 用 opt[i][j-1]<=opt[i][j]<=opt[i+1][j] 缩小循环，或分治 DP。",
    "Andrew 单调链凸包": "vector<Point> convex(vector<Point> p){ sort(p.begin(),p.end()); vector<Point> h;\n for(auto a:p){ while(h.size()>=2 && cross(h[h.size()-2],h.back(),a)<=0) h.pop_back(); h.push_back(a); }\n int low=h.size(); for(int i=p.size()-2;i>=0;--i){ while(h.size()>low && cross(h[h.size()-2],h.back(),p[i])<=0) h.pop_back(); h.push_back(p[i]); } h.pop_back(); return h; }",
    "叉积 / 点积判断方位": "long long cross(Point a,Point b,Point c){ return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x); }\nlong long dot(Point a,Point b){ return a.x*b.x+a.y*b.y; }",
    "最近点对（分治）": "double solve(int l,int r){ if(r-l<=3) brute; int m=(l+r)/2; double d=min(solve(l,m),solve(m+1,r));\n vector tmp in [x_mid-d,x_mid+d] sort by y; for i,j if |y_i-y_j|<d update d; }",
    "线段相交判定": "bool intersect(P a,P b,P c,P d){ return sign(cross(a,b,c))*sign(cross(a,b,d))<=0 && sign(cross(c,d,a))*sign(cross(c,d,b))<=0; }",
    "高斯消元（异或方程组 bitset）": "for(int col=0,row=0; col<n; ++col){ int p=row; while(p<m && !a[p][col]) ++p; if(p==m) continue; swap(a[row],a[p]);\n for(int i=0;i<m;++i) if(i!=row && a[i][col]) a[i]^=a[row]; ++row; }\n// 若某行全 0 且右边为 1 则无解",
    "扩展中国剩余定理（EXCRT）": "long long exgcd(long long a,long long b,long long &x,long long &y){ if(!b){x=1;y=0;return a;} long long g=exgcd(b,a%b,y,x); y-=a/b*x; return g; }\n// 合并：x ≡ a1 (mod m1), x ≡ a2 (mod m2) -> x = a1 + m1*t，解 m1*t ≡ a2-a1 (mod m2)",
    "线性基": "void insert(long long x){ for(int i=60;i>=0;--i) if(x>>i&1){ if(!p[i]){ p[i]=x; return; } x^=p[i]; } }\nlong long ask_max(){ long long res=0; for(int i=60;i>=0;--i) res=max(res,res^p[i]); return res; }",
    "中国剩余定理 (CRT)": "// m_i 两两互质：M=prod m_i; ans=sum a_i * M/m_i * inv(M/m_i, m_i) mod M",
    "AC 自动机 + 矩阵快速幂": "// 构建 AC 自动机转移矩阵 M；禁止状态节点不进入。\n// 长度为 L 且不包含模式串的方案数 = (初始向量 * M^L) 对安全状态求和。",
    "AC 自动机": "void build(){ queue<int>q; for(int c=0;c<26;++c) if(tr[0][c]) q.push(tr[0][c]);\n while(!q.empty()){ int u=q.front();q.pop(); for(int c=0;c<26;++c){ int v=tr[u][c]; if(v) fail[v]=tr[fail[u]][c], q.push(v); else tr[u][c]=tr[fail[u]][c]; } } }",
    "2-SAT": "for(i) add(i<<1, i<<1|1); add(...);\n// Tarjan 缩点。若 x 与 !x 在同一 SCC => 无解；否则按拓扑序取值。",
    "线段树合并/分裂": "int merge(int a,int b){ if(!a||!b) return a+b; if(tr[a].l==tr[a].r){ tr[a].val+=tr[b].val; return a; } tr[a].l=merge(tr[a].l,tr[b].l); tr[a].r=merge(tr[a].r,tr[b].r); pull(a); return a; }\n// split 按值域切成两棵树",
    "可撤销并查集": "struct DSU{ int fa[N],sz[N]; vector<tuple<int,int,int>> st;\n int find(int x){ while(fa[x]!=x) x=fa[x]; return x; }\n void unite(int a,int b){ a=find(a);b=find(b); if(a==b){st.push({-1,0,0});return;} if(sz[a]<sz[b]) swap(a,b); st.push({a,b,sz[a]}); fa[b]=a; sz[a]+=sz[b]; }\n void rollback(){ auto [a,b,s]=st.back(); st.pop_back(); if(a<0) return; fa[b]=b; sz[a]=s; } };",
    "基环树 DP": "// 找到环上每个点，对每棵外向树做树形 DP：f[u][0/1]\n// 然后枚举环上第一个点选/不选，线性 DP 两次取最大。",
    "仙人掌 / 圆方树": "// Tarjan 遇到返祖边得到环：把环建成方点，环上点连方点；原边保留为圆点边。\n// 之后在圆方树上 DP/树剖。",
    "旋转卡壳": "int rotating(vector<P> h){ int n=h.size(); if(n==1) return 0; int j=1; long long ans=0;\n for(int i=0;i<n;++i){ while(abs(cross(h[i],h[(i+1)%n],h[(j+1)%n]))>abs(cross(h[i],h[(i+1)%n],h[j]))) j=(j+1)%n; ans=max(ans,dist2(h[i],h[j])); } return ans; }",
    "SAM（后缀自动机）": "struct SAM{ int ch[N][26],link[N],len[N],last=1,tot=1;\n void extend(int c){ int p=last, np=++tot; len[np]=len[p]+1;\n  for(;p&&!ch[p][c];p=link[p]) ch[p][c]=np;\n  if(!p) link[np]=1; else { int q=ch[p][c]; if(len[p]+1==len[q]) link[np]=q; else { int nq=++tot; len[nq]=len[p]+1; memcpy(ch[nq],ch[q],sizeof ch[q]); link[nq]=link[q]; for(;p&&ch[p][c]==q;p=link[p]) ch[p][c]=nq; link[q]=link[np]=nq; } } last=np; } };",
    "Link-Cut Tree (LCT)": "void access(int x){ for(int y=0;x;y=x,x=fa[x]) splay(x), ch[x][1]=y, push(x); }\nvoid makeroot(int x){ access(x); splay(x); rev[x]^=1; }\nint findroot(int x){ access(x); splay(x); while(ch[x][0]) push(x), x=ch[x][0]; splay(x); return x; }\nvoid split(int x,int y){ makeroot(x); access(y); splay(y); }\nvoid link(int x,int y){ makeroot(x); if(findroot(y)!=x) fa[x]=y; }\nvoid cut(int x,int y){ split(x,y); if(ch[y][0]==x && !ch[x][1]) ch[y][0]=fa[x]=0; }",
    "树链剖分 (HLD)": "void dfs1(int u,int f){ fa[u]=f; sz[u]=1; for(v) if(v!=f){ dep[v]=dep[u]+1; dfs1(v,u); sz[u]+=sz[v]; if(sz[v]>sz[son[u]]) son[u]=v; } }\nvoid dfs2(int u,int top){ dfn[u]=++tot; top[u]=top; if(son[u]) dfs2(son[u],top); for(v) if(v!=fa[u]&&v!=son[u]) dfs2(v,v); }\n// 路径操作：while(top[u]!=top[v]) 处理深度大的链，最后处理同一链区间。",
    "可持久化数据结构（主席树进阶）": "// 同主席树：每版本只新建 O(log n) 个节点，根数组存历史根。\n// 树上路径第 k 小：root[u]+root[v]-root[lca]-root[fa[lca]]。",
    "后缀自动机（SAM）进阶": "// 按 len 拓扑；endpos 计数：初始每个前缀状态 cnt=1，parent 树上累加。\n// 本质不同子串数 = sum(len[i]-len[link[i]])。",
    "广义 SAM": "int insert(int last,int c){ if(ch[last][c]) { int p=last,q=ch[p][c]; if(len[p]+1==len[q]) return q; int nq=++tot; len[nq]=len[p]+1; memcpy(ch[nq],ch[q],sizeof ch[q]); link[nq]=link[q]; for(;p&&ch[p][c]==q;p=link[p]) ch[p][c]=nq; link[q]=nq; return nq; } ... }",
    "FFT": "void fft(vector<complex<double>>& a,int inv){ int n=a.size(); for(int i=1,j=0;i<n;++i){ int bit=n>>1; for(;j&bit;bit>>=1) j^=bit; j^=bit; if(i<j) swap(a[i],a[j]); }\n for(int len=2;len<=n;len<<=1){ double ang=2*pi/len*inv; complex w(cos(ang),sin(ang)); for(int i=0;i<n;i+=len){ complex cur(1); for(int j=0;j<len/2;++j){ complex u=a[i+j],v=a[i+j+len/2]*cur; a[i+j]=u+v; a[i+j+len/2]=u-v; cur*=w; } } } if(inv==-1) for(auto&x:a) x/=n; }",
    "NTT": "void ntt(vector<int>& a,bool inv){ int n=a.size(); for(int i=1,j=0;i<n;++i){...}\n for(int len=2;len<=n;len<<=1){ int w=qpow(3,(MOD-1)/len,MOD); if(inv) w=qpow(w,MOD-2,MOD); for(int i=0;i<n;i+=len){ long long cur=1; for(int j=0;j<len/2;++j){ int u=a[i+j],v=a[i+j+len/2]*cur%MOD; a[i+j]=(u+v)%MOD; a[i+j+len/2]=(u-v+MOD)%MOD; cur=cur*w%MOD; } } } if(inv){ int inv_n=qpow(n,MOD-2,MOD); for(auto&x:a) x=1LL*x*inv_n%MOD; } }",
    "生成函数": "// A(x)*B(x) 用 NTT 卷积；求逆：F=2F-AF^2 牛顿迭代；\n// exp/ln 等可在模意义下用形式幂级数完成。",
    "莫比乌斯反演": "for(int i=2;i<N;++i) if(!vis[i]) { mu[i]=-1; for(int j=i*2;j<N;j+=i) ... }\n// [gcd(i,j)=1] = sum_{d|gcd} mu[d]",
    "线性基进阶": "// 高斯消元化为行最简，再求第 k 大：把 k 按位选择基向量。\n// 求异或和计数：线性基维数 r，可表示 2^r 个不同值。",
    "半平面交": "struct Line{ P p,v; double ang; };\n// 按极角排序；deque 维护：新直线与队尾交点若在队首线外侧则弹队尾。\n// 最后 deque 首尾相交即结果。",
    "最小圆覆盖": "random_shuffle(p);\nfor(i) if(!in(c,p[i])) { c={p[i],0}; for(j<i) if(!in(c,p[j])) { c={p[i],p[j]}; for(k<j) if(!in(c,p[k])) c=circum(p[i],p[j],p[k]); } }",
    "三维凸包": "// 增量法：维护面集；新点若在某面外侧，删除该面，重建与新点相连的边界环。\n// 复杂度 O(n^2)，实现较长，核心是面方向判断。",
    "支配树": "// Lengauer-Tarjan: dfs 序号；semi[w]=min semi[v]；iter 后由 idom 更新。\n// 最终 idom 数组给出每个点的直接支配者。",
    "点分治/边分治": "int get_size(int u,int p){ sz[u]=1; for(v) if(v!=p&&!vis[v]) sz[u]+=get_size(v,u); return sz[u]; }\nint centroid(int u,int p,int tot){ for(v) if(v!=p&&!vis[v]&&sz[v]*2>tot) return centroid(v,u,tot); return u; }\n// 以重心为根统计经过重心的路径，然后递归子树。",
    "动态图连通性（离线）": "// 对每条边在时间轴上的存在区间加入线段树节点；DFS 线段树时用可撤销并查集。\n// 到叶子时回答该时刻连通性。",
    "插头 DP": "// 用 2/3 进制括号序列或最小表示法存轮廓线；逐格枚举左/上插头与新建插头。\n// 常见于回路、生成树、骨牌覆盖。",
    "DP 套 DP": "// 外层 DP 状态 = 内层自动机状态；例如“恰好 k 个不回文子串”。\n// 先内层用小 DP 求每个前缀的转移，再外层按自动机状态转移。",
    "分治 DP": "void solve(int l,int r,int optl,int optr){ int m=(l+r)/2, best=optl; \n for(int j=optl;j<=min(m,optr);++j) if(calc(m,j)<calc(m,best)) best=j;\n opt[m]=best; solve(l,m-1,optl,best); solve(m+1,r,best,optr); }",
    "上下界网络流": "// 每条边流量 [l,u]：先流 l，记入度差；超级源/汇补差；无可行流则最大流不满。\n// 有源汇时再连 t->s INF 并跑最大流。",
    "最小费用最大流": "bool spfa(){ memset(dis,0x3f,sizeof dis); dis[s]=0; queue<int>q; q.push(s); inq[s]=1;\n while(!q.empty()){ int u=q.front();q.pop(); inq[u]=0; for(auto&e:g[u]) if(e.cap&&dis[e.to]>dis[u]+e.cost){ dis[e.to]=dis[u]+e.cost; pre[e.to]=u; pe[e.to]=&e; if(!inq[e.to]) q.push(e.to), inq[e.to]=1; } } return dis[t]<inf; }\n// 每次沿 pre 跑最小费用增广。",
}

ADV_COMPLEXITY = {
    "Dinic 最大流": "O(V^2 E) 一般 / O(E sqrt V) 二分图", "最小割建模": "O(maxflow)",
    "二分图最大匹配（匈牙利）": "O(VE)", "KM 算法": "O(n^3)", "主席树（区间第 k 小）": "O(n log n) 建 / O(log n) 查",
    "FHQ Treap（无旋 Treap）": "O(log n) 期望", "莫队（区间不同数）": "O((n+m) sqrt n)",
    "斜率优化（CHT）": "O(n) 或 O(n log n)", "四边形不等式优化": "O(n^2) -> O(n log n)/O(n)",
    "Andrew 单调链凸包": "O(n log n)", "叉积 / 点积判断方位": "O(1)", "最近点对（分治）": "O(n log n)",
    "线段相交判定": "O(1)", "高斯消元（异或方程组 bitset）": "O(n^3 / word)", "扩展中国剩余定理（EXCRT）": "O(n log mod)",
    "线性基": "O(n log V)", "中国剩余定理 (CRT)": "O(n log mod)", "AC 自动机 + 矩阵快速幂": "O(状态^3 log L)",
    "AC 自动机": "O(Σ文本长度)", "2-SAT": "O(n+m)", "线段树合并/分裂": "O(n log n)",
    "可撤销并查集": "O(log n) 均摊", "基环树 DP": "O(n)", "仙人掌 / 圆方树": "O(n+m)",
    "旋转卡壳": "O(n)", "SAM（后缀自动机）": "O(n)", "Link-Cut Tree (LCT)": "O(log n) 均摊",
    "树链剖分 (HLD)": "O(log^2 n)", "可持久化数据结构（主席树进阶）": "O(log n) 每次", "后缀自动机（SAM）进阶": "O(n)",
    "广义 SAM": "O(总字符数)", "FFT": "O(n log n)", "NTT": "O(n log n)", "生成函数": "O(n log n)",
    "莫比乌斯反演": "O(n log n)", "线性基进阶": "O(n log V)", "半平面交": "O(n log n)",
    "最小圆覆盖": "O(n) 期望", "三维凸包": "O(n^2) 增量", "支配树": "O((n+m) log n) / O(n alpha)",
    "点分治/边分治": "O(n log n)", "动态图连通性（离线）": "O((n+m) log^2 n)", "插头 DP": "O(nm 状态数)",
    "DP 套 DP": "视状态数", "分治 DP": "O(n log n * 转移)", "上下界网络流": "O(maxflow)",
    "最小费用最大流": "O(F E log V) / O(VE * SPFA)",
}

cards: dict[str, dict] = {}
for name in ALGORITHM_NAMES:
    info = get_alg_info(name)
    if name in CORE:
        how = HOW.get(name, "")
        code = CODE.get(name, "")
        complexity = COMPLEXITY.get(name, "视实现")
    else:
        how = ADV_HOW.get(name, f"实现要点：{info.get('why', '按常规建模与实现。')}")
        code = ADV_CODE.get(name, f"// 实现要点：{info.get('why', '按常规建模与实现。')}")
        complexity = ADV_COMPLEXITY.get(name, "视实现")
    if not how:
        how = f"实现要点：{info.get('why', '按常规建模与实现。')}"
    if not code:
        code = f"// 实现要点：{info.get('why', '按常规建模与实现。')}"
    cards[name] = {
        "what": info.get("why", ""),
        "how": how,
        "complexity": complexity,
        "code": code,
    }

out = {
    "meta": {
        "version": "0.1.0",
        "description": "PC 阶梯算法卡：是什么/怎么写/复杂度/C++ 代码",
        "sources": ["CP-Algorithms", "OI Wiki", "USACO Guide", "teacher-consensus-skill"],
    },
    "cards": cards,
}

target = os.path.join(REPO, "expert_content", "algorithm_cards.json")
with open(target, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# 校验
loaded = json.load(open(target, encoding="utf-8"))
assert len(loaded["cards"]) == len(ALGORITHM_NAMES) == 120
assert set(loaded["cards"].keys()) == set(ALGORITHM_NAMES)
for n, c in loaded["cards"].items():
    for field in ("what", "how", "complexity", "code"):
        assert str(c.get(field, "")).strip(), f"{n}.{field} empty"
print(f"OK cards={len(loaded['cards'])} path={target}")
