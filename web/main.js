// 只读 var/report.json，高亮位置、目标与规则全部取自引擎输出，不在页面里重判。

const STAT_LABELS = {
  total: "用例总数",
  normalize: "归一化",
  screen: "注册判定",
  compare: "比对判定",
  reject: "拒绝",
  allow: "放行",
  equivalent: "等价",
  confusable: "等价但不同一",
  different: "不等价",
  pairs: "证据合计",
  flagged: "可疑条目",
};

function isFlagged(item) {
  if (!item.pairs || item.pairs.length === 0) return false;
  if (item.kind === "screen") return item.decision === "reject";
  if (item.kind === "compare") return item.equivalent === true;
  return false;
}

function renderStats(stats) {
  const box = document.getElementById("stats");
  for (const [key, label] of Object.entries(STAT_LABELS)) {
    const chip = document.createElement("div");
    chip.className = "stat";
    chip.dataset.stat = key;
    const value = document.createElement("b");
    value.textContent = String(stats[key] ?? 0);
    chip.append(value, document.createTextNode(label));
    box.appendChild(chip);
  }
}

// 按码点（不是 UTF-16 单元）切分，pairs 的 index 是码点下标。
function codepoints(text) {
  return Array.from(text);
}

function renderRaw(label, text, pairs) {
  const block = document.createElement("div");
  block.className = "raw";
  const side = document.createElement("span");
  side.className = "side-label";
  side.textContent = label;
  block.appendChild(side);
  const byIndex = new Map();
  for (const pair of pairs) byIndex.set(pair.index, pair);
  codepoints(text).forEach((ch, index) => {
    const pair = byIndex.get(index);
    if (!pair) {
      block.appendChild(document.createTextNode(ch));
      return;
    }
    const mark = document.createElement("mark");
    mark.dataset.cp = pair.cp;
    mark.dataset.rule = pair.rule;
    if (pair.target === null) {
      mark.dataset.target = "";
      mark.classList.add("invisible");
      mark.title = `不可见字符 ${pair.cp}（${pair.rule}）`;
    } else {
      mark.dataset.target = pair.target;
      mark.title = `${pair.cp} 像 "${pair.target}"（${pair.rule}）`;
    }
    mark.textContent = ch;
    block.appendChild(mark);
  });
  return block;
}

function renderPairsTable(pairs) {
  const table = document.createElement("table");
  table.className = "pairs";
  const head = document.createElement("tr");
  for (const col of ["侧", "位置", "字符", "码位", "像", "规则"]) {
    const th = document.createElement("th");
    th.textContent = col;
    head.appendChild(th);
  }
  table.appendChild(head);
  for (const pair of pairs) {
    const tr = document.createElement("tr");
    const cells = [
      pair.side,
      String(pair.index),
      pair.target === null ? "（不可见）" : pair.char,
      pair.cp,
      pair.target === null ? "—" : `${pair.target} (${pair.target_cp})`,
      pair.rule,
    ];
    for (const text of cells) {
      const td = document.createElement("td");
      td.className = "mono";
      td.textContent = text;
      tr.appendChild(td);
    }
    table.appendChild(tr);
  }
  return table;
}

function renderDetail(item) {
  const detail = document.getElementById("detail");
  detail.replaceChildren();
  const title = document.createElement("h2");
  const verdict = item.kind === "screen"
    ? item.decision
    : item.kind === "compare"
      ? (item.equivalent ? (item.identical ? "同一" : "等价") : "不等价")
      : "归一化";
  title.textContent = `${item.id} · ${item.kind} · ${verdict}`;
  detail.appendChild(title);
  if (item.kind === "screen") {
    detail.appendChild(renderRaw("原始输入", item.name, item.pairs));
  } else if (item.kind === "compare") {
    detail.appendChild(renderRaw("left", item.left, item.pairs.filter((p) => p.side === "left")));
    detail.appendChild(renderRaw("right", item.right, item.pairs.filter((p) => p.side === "right")));
  } else {
    detail.appendChild(renderRaw("原始输入", item.input, item.pairs ?? []));
  }
  if (item.pairs && item.pairs.length > 0) {
    detail.appendChild(renderPairsTable(item.pairs));
  }
}

function renderList(items) {
  const list = document.getElementById("list");
  const flagged = items.filter(isFlagged).sort((a, b) => (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
  for (const item of flagged) {
    const li = document.createElement("li");
    li.dataset.id = item.id;
    li.textContent = item.id;
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.textContent = item.kind === "screen" ? item.decision : "equivalent";
    li.appendChild(badge);
    li.addEventListener("click", () => {
      list.querySelectorAll("li.active").forEach((el) => el.classList.remove("active"));
      li.classList.add("active");
      renderDetail(item);
    });
    list.appendChild(li);
  }
  return flagged;
}

async function boot() {
  const detail = document.getElementById("detail");
  let report;
  try {
    const response = await fetch("../var/report.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    report = await response.json();
  } catch (err) {
    detail.replaceChildren();
    const p = document.createElement("p");
    p.className = "empty";
    p.textContent = `读不到 var/report.json（${err.message}）。先在仓库根目录跑 python -m twinmark report …，再用 python -m http.server 打开本页。`;
    detail.appendChild(p);
    return;
  }
  renderStats(report.stats);
  const flagged = renderList(report.items);
  detail.replaceChildren();
  if (flagged.length === 0) {
    const p = document.createElement("p");
    p.className = "empty";
    p.textContent = "这批用例没有可疑条目。";
    detail.appendChild(p);
  } else {
    const p = document.createElement("p");
    p.className = "empty";
    p.textContent = `共 ${flagged.length} 条可疑，点击左侧查看。`;
    detail.appendChild(p);
  }
}

boot();
