# 标识符归一与同形字检测（从 0 实现）

仓库里只有本说明、`samples/**` 与 `.gitignore`，没有实现代码。交付 `twinmark` 包（Python 3.13 标准库，库 + `python -m twinmark` 入口）、`web/` 下的判定页面与 `tests/`（`unittest`）；页面是原生 HTML/ES module，无构建、无依赖。

## 一、范围

**要做**：归一化标识符；注册时判名字可不可疑，比对时判两个名字算不算同一个；每条判定给出依据（哪两个字符看着像、命中哪条规则）；批量跑 `samples/cases/**` 并渲染页面；同一输入两遍结果一致。

**不做**：不接入注册流程或账号库，不做查重、模糊搜索、子串匹配、相似度打分、双向文本、emoji 与整形（IDN）；不联网、不读时钟与随机数、不写时间戳。

## 二、口径与公式

### 2.1 归一化（四步，迭代到不动点）

一轮按序四步，与上一轮结果相同就停：① 大小写 `str.casefold()`；② 全半角与兼容字符 `unicodedata.normalize("NFKC", s)`（全角转半角）；③ 零宽字符：删掉类别为 `Cf` 的码位（`U+200B`、`U+2060`、`U+FEFF`、`U+00AD` 等）；④ 组合字符 `unicodedata.normalize("NFC", s)`（分解写法合成预组合）。

**最多 4 轮**：②可能引入新的大写字母，`㎒` 第 1 轮得 `MHz`、第 2 轮才得 `mhz`；第 4 轮还在变按输入不可用处理（退出码 1）。**幂等**：`normalize(normalize(x)) == normalize(x)` 恒成立。空白与标点不动，首尾空格照算。

### 2.2 映射表与查表

一行是「可疑码位 → 它看起来像的字符」，查表用归一化之后的码位；多份 `--map` 按序合并，同一可疑码位出现两次（值相同也算）判输入不可用。加载逐行校验：码位写成 `U+XXXX`（4–6 位大写十六进制）且不同；目标是 ASCII 可打印字符（`U+0021`–`U+007E`）且过 `normalize` 不变；可疑码位满足 `normalize(码位) == 码位`。

**内存**：`confusables-large.tsv` 12042 条，加载后堆增量 ≤ 24 MiB；等价关系按目标归并（本表 36 组），不得展开成两两组合。**折叠** `fold(s)`：逐码位查表，有就换成目标、没有就原样保留，只替换一次、不级联。

### 2.3 场景一：注册判定

逐码位扫**原始输入**取证：命中映射表的码位给一条同形证据；`Cf` 不可见字符给一条证据，目标为空，规则固定为 `invisible.zero-width`。

`reject` 当且仅当：①有同形证据且归一化结果里至少有一个 ASCII 字母（`a`–`z`）；②有不可见证据。其余 `allow`；纯外文名（整串没有 ASCII 字母）会留下证据但判 `allow`。

### 2.4 场景二：比对判定

`equivalent` = `fold(normalize(left)) == fold(normalize(right))`；`identical` = 两边归一化结果逐码位相同，`true` 表示差别只在写法（大小写、全半角、零宽、组合字符）上。`equivalent=false` 也可能带证据（如 `kefu-01` 对 `kefu-о1`）。

### 2.5 证据与排序

证据条目七个键：`side`（`input`/`left`/`right`）、`index`（**原始串**里的码点下标）、`cp`、`char`、`target`、`target_cp`、`rule`；不可见字符的后两键为 `null`。排序先 `left` 后 `right`、同侧按 `index` 升序；`rules` 为规则 ID 去重后按字典序。

## 三、数据结构与流程

索引 `{可疑码位: (目标码位, 规则 ID)}` 即可。结果记录都带 `id`、`kind`，按 kind 加字段：`normalize` 加 `normalized`；`screen` 加 `normalized`、`decision`、`pairs`、`rules`；`compare` 加 `normalized_left`、`normalized_right`、`equivalent`、`identical`、`pairs`、`rules`。流程：读表校验 → 逐行读用例（`id` 唯一、字段齐全、无 `Cc`）→ 逐条判定 → 按序写结果行；报告在结果上加统计与原串。

## 四、输入输出与文件格式

一律 UTF-8 无 BOM、LF、末行有换行；JSON 键按字典序、分隔符后不带空格、非 ASCII 不转义；`Cc`/`Cf` 字符写成 `\uXXXX`（大写十六进制）转义，素材与期望就这么写，验收逐字节比。

**4.1 映射表** `samples/maps/*.tsv`：四列 TSV——可疑码位、目标码位、规则 ID、说明；空行与 `#` 行跳过；规则 ID 用小写字母、数字、连字符并用句点分段（如 `homoglyph.cyrillic`）。

**4.2 用例与期望** `samples/cases/*.jsonl` 一行一条 `{"id","kind",...}`，`id` 形如 `n-01-00001`（文件号 + 行号）且全局唯一，`kind` 为 `normalize`（`text`）/`screen`（`name`）/`compare`（`left`、`right`）；`samples/expected/*.jsonl` 与 cases 同名、同序、等长，字段见第三节。

**4.3 命令行**（仓库根目录）：

```
python -m twinmark evaluate --map samples/maps/confusables-large.tsv --cases samples/cases/b-01-batch.jsonl --out var/results.jsonl
python -m twinmark report --map samples/maps/confusables-large.tsv --cases samples/cases/w-01-web.jsonl --out var/report.json
```

`--map`/`--cases` 可多次给并按序处理，`--out` 省略写 stdout（报告那条必须落到 `var/report.json`）。退出码 0 成功 / 1 输入不可用（缺文件、格式不合法、`id` 重复或字段缺失、四轮不收敛）/ 2 用法错误；非 0 不写输出。

**4.4 报告** `var/report.json` 用 `json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)` 加末行换行。`items` 与结果行逐条一致，另带原始串；`stats` 十一键：`total`/`normalize`/`screen`/`compare`/`reject`/`allow`/`equivalent`/`confusable`/`different`/`pairs`/`flagged`，其中 `confusable` 为等价但不同一、`pairs` 为证据合计、`flagged` 为有证据且可疑（screen 判 `reject` 或 compare 判 `equivalent`）。

**4.5 页面** `web/index.html` + 原生 ES module，无外部资源，起 `python -m http.server` 打开，只读 `var/report.json`：顶部 `id="stats"` 显示 `stats`；左栏 `id="list"` 每个可疑条目一个 `<li data-id>`（按 `id` 升序）；右栏 `id="detail"` 显示原始串，按 `pairs` 的 `index` 把码位包成 `<mark data-cp data-target data-rule>`，`target` 为空标不可见字符。位置、目标与规则只能取自 JSON，不重判。

## 五、性能与验收口径

预算（Windows、Python 3.13、单进程、含读表）：12042 条表 + 12000 条用例，`evaluate` ≤ 10 s、`tracemalloc` 峰值 ≤ 48 MiB；隐藏规模 5 万条表 + 20 万条用例 ≤ 90 s、峰值 ≤ 128 MiB。

验收：

1. 每个 `samples/cases/*.jsonl` 跑一遍，输出与同名 `samples/expected/*.jsonl` 逐字节相同；`w-01-web` 的 `report` 与 `expected/w-01-web.report.json` 逐字节相同。
2. 幂等与可重复：样例里每个串满足 `normalize(normalize(x)) == normalize(x)`，跑两遍、换 `PYTHONHASHSEED` 也一样。
3. 内存与耗时须在预算内。
4. 判定带依据：`reject` 每条都有非空 `pairs`，每个同形/不可见码位各留一条证据。
5. 页面左栏条目数 = `stats.flagged`，高亮与 `pairs` 逐条对得上。
6. `python -m unittest` 通过，测试只读 `samples/`。

## 六、样例说明

`maps/confusables-core.tsv` 42 条手写映射（西里尔、希腊、拉丁扩展、标点、数字）；`confusables-large.tsv` 12042 条 = core + 12000 条 CJK 区压测条目。用例 12092 条：`n-01-normalize` 24（大小写、全半角、零宽、组合字符、两轮收敛）、`s-01-screen` 26（同形混用、纯外文名放行、零宽与 BOM、全角与大小写）、`x-01-compare` 26（同形等价、组合字符等价、零宽插入、无关名字不等价）、`w-01-web` 16（页面用混合批次）、`b-01-batch` 12000（批量规模）。`expected/` 与 cases 同名同序，逐行给出归一结果、判定、证据与规则，另有 `w-01-web.report.json` 给页面用；`notes.md` 是现场记录，不是规格。两份表只差压测条目（CJK 区码位、样例不出现），用哪一份结果都一样。

## 七、待补的文档

隐藏验收的放大映射表与批量用例不提供；真实语料、页面版式、模块划分、索引落盘与否自定，其余范围见第一节。
