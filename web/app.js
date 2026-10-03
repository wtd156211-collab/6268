// twinmark 判定页面：只读 var/report.json，高亮位置与依据全部取自引擎输出，不重判。

const STAT_LABELS = {
  total: "用例总数",
  normalize: "归一化",
  screen: "注册判定",
  compare: "比对判定",
  reject: "拒绝",
  allow: "放行",
  equivalent: "等价",
  confusable: "等价不同一",
  different: "不等价",
  pairs: "证据总数",
  flagged: "可疑条目",
};

function isFlagged(item) {
  if (!Array.isArray(item.pairs) || item.pairs.length === 0) return false;
  if (item.kind === "screen") return item.decision === "reject";
  if (item.kind === "compare") return item.equivalent === true;
  return false;
}

function renderStats(stats) {
  const host = document.getElementById("stats");
  host.textContent = "";
  for (const key of Object.keys(STAT_LABELS)) {
    const chip = document.createElement("span");
    chip.className = "stat";
    chip.dataset.key = key;
    const label = document.createElement("span");
    label.className = "stat-label";
    label.textContent = STAT_LABELS[key];
    const value = document.createElement("span");
    value.className = "stat-value";
    value.textContent = String(stats[key] ?? 0);
    chip.append(label, value);
    host.append(chip);
  }
}

// 按 pairs 的 index 把原始串的码位包成 <mark data-cp data-target data-rule>。
// index 是码点下标，用 Array.from 按码点切分，避免 UTF-16 代理对错位。
function renderString(text, pairs, side) {
  const frag = document.createDocumentFragment();
  const byIndex = new Map();
  for (const pair of pairs) {
    if (pair.side === side) byIndex.set(pair.index, pair);
  }
  Array.from(text).forEach((ch, i) => {
    const pair = byIndex.get(i);
    if (!pair) {
      frag.append(document.createTextNode(ch));
      return;
    }
    const mark = document.createElement("mark");
    mark.dataset.cp = pair.cp;
    mark.dataset.target = pair.target ?? "";
    mark.dataset.rule = pair.rule;
    mark.textContent = ch;
    if (pair.target === null) {
      mark.classList.add("invisible");
      mark.title = `${pair.cp} 不可见字符`;
    } else {
      mark.title = `${pair.cp} 像 ${pair.target}（${pair.rule}）`;
    }
    frag.append(mark);
  });
  return frag;
}

function renderPairList(pairs) {
  const list = document.createElement("ul");
  list.className = "pairs";
  for (const pair of pairs) {
    const li = document.createElement("li");
    const where = pair.side === "input" ? "输入" : pair.side === "left" ? "左串" : "右串";
    if (pair.target === null) {
      li.textContent = `${where}第 ${pair.index} 位 ${pair.cp}：不可见字符（${pair.rule}）`;
    } else {
      li.textContent = `${where}第 ${pair.index} 位 ${pair.cp}「${pair.char}」像「${pair.target}」${pair.target_cp}（${pair.rule}）`;
    }
    list.append(li);
  }
  return list;
}

function renderStringBlock(title, text, pairs, side) {
  const block = document.createElement("div");
  block.className = "string-block";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const line = document.createElement("p");
  line.className = "raw";
  line.append(renderString(text, pairs, side));
  block.append(heading, line);
  return block;
}

function renderDetail(item) {
  const host = document.getElementById("detail");
  host.textContent = "";

  const head = document.createElement("div");
  head.className = "detail-head";
  const idEl = document.createElement("span");
  idEl.className = "detail-id";
  idEl.textContent = item.id;
  const verdict = document.createElement("span");
  verdict.className = "verdict";
  if (item.kind === "screen") {
    verdict.textContent = item.decision === "reject" ? "注册：拒绝" : "注册：放行";
    verdict.classList.add(item.decision);
  } else if (item.kind === "compare") {
    verdict.textContent = item.equivalent
      ? item.identical ? "比对：同一（仅写法差别）" : "比对：等价（同形混淆）"
      : "比对：不等价";
    verdict.classList.add(item.equivalent ? "reject" : "allow");
  } else {
    verdict.textContent = "归一化";
  }
  head.append(idEl, verdict);
  host.append(head);

  if (item.kind === "screen") {
    host.append(renderStringBlock("原始用户名", item.name, item.pairs, "input"));
    host.append(renderStringBlock("归一化结果", item.normalized, [], "input"));
  } else if (item.kind === "compare") {
    host.append(renderStringBlock("左串（原始）", item.left, item.pairs, "left"));
    host.append(renderStringBlock("右串（原始）", item.right, item.pairs, "right"));
    host.append(renderStringBlock("左串归一化", item.normalized_left, [], "left"));
    host.append(renderStringBlock("右串归一化", item.normalized_right, [], "right"));
  } else {
    host.append(renderStringBlock("原始输入", item.input, [], "input"));
    host.append(renderStringBlock("归一化结果", item.normalized, [], "input"));
  }

  if (item.pairs && item.pairs.length > 0) {
    const h = document.createElement("h3");
    h.textContent = "判定依据";
    host.append(h, renderPairList(item.pairs));
  }
  if (item.rules && item.rules.length > 0) {
    const rules = document.createElement("p");
    rules.className = "rules";
    rules.textContent = "命中规则：" + item.rules.join("、");
    host.append(rules);
  }
}

function renderList(items) {
  const host = document.getElementById("list");
  host.textContent = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.dataset.id = item.id;
    const name = document.createElement("span");
    name.className = "li-name";
    name.textContent = item.kind === "compare"
      ? `${item.left} ↔ ${item.right}`
      : item.kind === "screen" ? item.name : item.input;
    const tag = document.createElement("span");
    tag.className = "li-tag";
    tag.textContent = item.kind === "screen" ? "注册" : item.kind === "compare" ? "比对" : "归一";
    li.append(tag, name);
    li.addEventListener("click", () => {
      host.querySelectorAll("li.selected").forEach((el) => el.classList.remove("selected"));
      li.classList.add("selected");
      renderDetail(item);
    });
    host.append(li);
  }
}

async function boot() {
  const res = await fetch("../var/report.json");
  if (!res.ok) throw new Error(`读取 var/report.json 失败：HTTP ${res.status}`);
  const report = await res.json();
  renderStats(report.stats);
  const flagged = report.items.filter(isFlagged).sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  renderList(flagged);
  const first = document.querySelector("#list li");
  if (first) first.click();
}

boot().catch((err) => {
  const host = document.getElementById("detail");
  host.textContent = "";
  const p = document.createElement("p");
  p.className = "error";
  p.textContent = String(err.message || err);
  host.append(p);
});
