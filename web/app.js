// 메시지 코치 데모 프론트 (바닐라 JS, 빌드 없음)
// TODO(DAY-OF): customize/schemas의 필드 이름을 바꾸면 아래 run*() 함수의 화면 표시 부분도 맞추기
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

// ---------- 공통 ----------

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function store(key, value) {
  // localStorage는 막혀 있을 수 있으니 실패해도 무시
  try {
    if (value === undefined) return localStorage.getItem(key) || "";
    localStorage.setItem(key, value);
  } catch { return ""; }
}

async function api(path, { method = "GET", json, form } = {}) {
  const headers = {};
  const key = store("teamKey");
  if (key) headers["X-Team-Key"] = key;
  let body;
  if (json !== undefined) { headers["Content-Type"] = "application/json"; body = JSON.stringify(json); }
  else if (form) body = form;
  const res = await fetch(path, { method, headers, body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail ?? data);
    throw new Error(`${res.status} ${detail}`);
  }
  return data;
}

function toast(message, isError = false) {
  const el = $("#toast");
  el.textContent = message;
  el.className = "toast" + (isError ? " error" : "");
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (el.hidden = true), 3500);
}

// 버튼을 잠그고 작업 실행, 실패하면 오류 토스트
async function busy(button, label, work) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  try { return await work(); }
  catch (error) { toast(error.message, true); }
  finally { button.disabled = false; button.textContent = original; }
}

const orNull = (v) => (v === "" || v == null ? null : v);
const contactId = (sel) => orNull($(sel).value) && Number($(sel).value);

// 이번 요청의 HCX 호출 정보 칩
function metaChips(meta) {
  if (!meta) return "";
  const chips = meta.calls.map((c) => {
    const kind = c.mock ? "mock" : c.cached ? "cached" : "";
    const tag = c.mock ? "MOCK" : c.cached ? "캐시" : `${c.total_tokens ?? "?"} tok · ${(c.latency_ms / 1000).toFixed(1)}s`;
    return `<span class="chip ${kind}">${esc(c.model)} · ${tag}</span>`;
  });
  return `<div class="chips">${chips.join("")}</div>`;
}

function refChips(refs) {
  if (!refs?.length) return "";
  return `<p class="muted">참고 자료: ${refs.map((r) => `<span class="chip">${esc(r.title)}</span>`).join(" ")}</p>`;
}

// 점수 게이지. invert=true면 낮을수록 좋음(오해 위험도)
function gauge(label, value, invert = false) {
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  const good = invert ? 100 - v : v;
  const color = good >= 70 ? "var(--good)" : good >= 40 ? "var(--warn)" : "var(--bad)";
  return `<div class="gauge-wrap"><div class="gauge" style="--v:${v};--c:${color}"><span>${v}</span></div>${esc(label)}</div>`;
}

function list(items) {
  return items?.length ? `<ul class="plain">${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
}

// ---------- 초기화: 도메인 선택지, 상태 ----------

let domain = {};

async function loadDomain() {
  domain = await api("/api/domain");
  $("#service-name").textContent = domain.service?.name || "메시지 코치";
  $("#service-target").textContent = domain.service?.target ? `대상: ${domain.service.target}` : "";
  document.title = domain.service?.name || document.title;

  const options = (items, empty) =>
    `<option value="">${empty}</option>` + (items || []).map((i) => `<option value="${esc(i.id)}">${esc(i.label || i.id)}</option>`).join("");
  $$(".relation-select").forEach((s) => (s.innerHTML = options(domain.relations, "선택 안 함")));
  $$(".purpose-select").forEach((s) => (s.innerHTML = options(domain.purposes, "선택 안 함")));
  $("#scenario-select").innerHTML = (domain.scenarios || []).map((s) => `<option value="${esc(s.id)}">${esc(s.title || s.id)}</option>`).join("");
  showScenario();
}

function showScenario() {
  const s = (domain.scenarios || []).find((x) => x.id === $("#scenario-select").value);
  $("#scenario-desc").textContent = s ? [s.ai_role && `상대 역할: ${s.ai_role}`, s.situation, s.goal && `목표: ${s.goal}`].filter(Boolean).join(" · ") : "";
}

async function loadHealth() {
  const h = await api("/api/health");
  const badge = $("#mode-badge");
  badge.textContent = h.mock ? `MOCK (${h.mock_reason})` : "HyperCLOVA X 연결됨";
  badge.className = "badge " + (h.mock ? "mock" : "live");
}

// ---------- 탭 ----------

function switchTab(name) {
  $$(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  $$(".tab").forEach((t) => t.classList.toggle("active", t.id === `tab-${name}`));
  if (name === "usage") loadUsage();
  if (name === "contacts") loadContacts();
}

// ---------- 자유 입력 → 기능 연결 ----------

async function routeInput() {
  const text = $("#route-input").value.trim();
  if (!text) return;
  await busy($("#route-btn"), "분류 중…", async () => {
    const r = await api("/api/route", { method: "POST", json: { text } });
    if (!r.feature) return toast("어떤 기능인지 고르지 못했어요. 탭을 직접 선택해 주세요.");
    const target = { compose: "#compose-input", coach: "#coach-input", interpret: "#interpret-input" }[r.feature];
    if (target) $(target).value = text;
    switchTab(r.feature);
    toast(`'${$(`.tabs button[data-tab=${r.feature}]`).textContent.trim()}' 기능으로 연결했어요.`);
  });
}

// ---------- ① 작성 ----------

async function runCompose() {
  const key_points = $("#compose-input").value.trim();
  if (!key_points) return toast("핵심 내용을 입력해 주세요.", true);
  await busy($("#compose-btn"), "작성 중…", async () => {
    const r = await api("/api/compose", { method: "POST", json: {
      key_points, relation: orNull($("#compose-relation").value), purpose: orNull($("#compose-purpose").value),
      contact_id: contactId("#compose-contact"),
    } });
    $("#compose-result").innerHTML = `
      <div class="card">
        <div class="result-head"><h3>메시지 초안</h3>${metaChips(r.meta)}</div>
        <div class="draft" id="draft-text">${esc(r.draft)}</div>
        ${list(r.notes)}
        ${refChips(r.references)}
        <div class="row" style="margin-top:12px">
          <button id="copy-draft">복사</button>
          <button id="draft-to-coach">이 초안 코칭 받기</button>
        </div>
      </div>`;
    $("#copy-draft").onclick = () => navigator.clipboard?.writeText(r.draft).then(() => toast("복사했어요."));
    $("#draft-to-coach").onclick = () => { $("#coach-input").value = r.draft; switchTab("coach"); };
  });
}

// ---------- ② 코칭 ----------

// 원문에 문제 구간을 <mark>로 표시 (겹치는 구간은 앞의 것만)
function highlight(text, issues) {
  const spans = issues.map((issue, i) => ({ ...issue, n: i + 1 }))
    .filter((i) => i.start != null && i.end != null)
    .sort((a, b) => a.start - b.start);
  let html = "", pos = 0;
  for (const s of spans) {
    if (s.start < pos) continue;
    html += esc(text.slice(pos, s.start));
    html += `<mark class="${esc(s.severity)}" title="${esc(s.problem)}">${esc(text.slice(s.start, s.end))}<sup>${s.n}</sup></mark>`;
    pos = s.end;
  }
  return html + esc(text.slice(pos));
}

async function runCoach() {
  const text = $("#coach-input").value.trim();
  if (!text) return toast("메시지를 입력해 주세요.", true);
  await busy($("#coach-btn"), "분석 중…", async () => {
    const r = await api("/api/coach", { method: "POST", json: {
      text, relation: orNull($("#coach-relation").value), purpose: orNull($("#coach-purpose").value),
      contact_id: contactId("#coach-contact"),
    } });
    const label = { high: "높음", medium: "보통", low: "낮음" };
    $("#coach-result").innerHTML = `
      <div class="card">
        <div class="result-head"><h3>점수</h3>${metaChips(r.meta)}</div>
        <div class="gauges">
          ${gauge("공손도", r.scores.politeness)}
          ${gauge("명확성", r.scores.clarity)}
          ${gauge("오해 위험도", r.scores.misunderstanding_risk, true)}
        </div>
        <p style="text-align:center">${esc(r.summary)}</p>
      </div>
      <div class="card">
        <h3>문제 구간</h3>
        <div class="highlighted">${highlight(r.original, r.issues)}</div>
        <div class="issues">${r.issues.map((i, n) => `
          <div class="issue ${esc(i.severity)}">
            <b>${n + 1}.</b> <q>${esc(i.quote)}</q> <span class="chip">${label[i.severity] || esc(i.severity)}</span>
            <div>${esc(i.problem)}</div>
            <div class="fix">→ ${esc(i.suggestion)}</div>
          </div>`).join("")}</div>
      </div>
      <div class="card">
        <h3>전후 비교</h3>
        <div class="compare">
          <div class="before"><h4>원문</h4>${esc(r.original)}</div>
          <div class="after"><h4>수정본</h4>${esc(r.revised)}</div>
        </div>
        ${refChips(r.references)}
      </div>`;
  });
}

// ---------- ③ 해석 ----------

function previewImage() {
  const file = $("#interpret-image").files[0];
  const img = $("#interpret-preview");
  img.hidden = !file;
  if (file) img.src = URL.createObjectURL(file);
}

async function runInterpret() {
  const text = $("#interpret-input").value.trim();
  const file = $("#interpret-image").files[0];
  if (!text && !file) return toast("받은 메시지나 캡처를 넣어 주세요.", true);
  const form = new FormData();
  form.append("text", text);
  if (file) form.append("image", file);
  if ($("#interpret-relation").value) form.append("relation", $("#interpret-relation").value);
  if ($("#interpret-contact").value) form.append("contact_id", $("#interpret-contact").value);

  await busy($("#interpret-btn"), file ? "캡처 읽는 중…" : "해석 중…", async () => {
    const r = await api("/api/interpret", { method: "POST", form });
    const urgency = { high: "급함", medium: "보통", low: "여유" }[r.urgency] || r.urgency;
    $("#interpret-result").innerHTML = `
      <div class="card">
        <div class="result-head"><h3>해석</h3>${metaChips(r.meta)}</div>
        ${r.extracted_text ? `<p class="muted">캡처에서 읽은 글</p><div class="highlighted">${esc(r.extracted_text)}</div>` : ""}
        <dl class="kv" style="margin-top:12px">
          <dt>의도</dt><dd>${esc(r.intent)}</dd>
          <dt>감정</dt><dd>${esc(r.emotion)}</dd>
          <dt>긴급도</dt><dd>${esc(urgency)}</dd>
          <dt>핵심</dt><dd>${list(r.key_points)}</dd>
        </dl>
      </div>
      <div class="card">
        <h3>답장 초안</h3>
        <div class="draft">${esc(r.reply_draft)}</div>
        ${refChips(r.references)}
        <div class="row" style="margin-top:12px"><button id="reply-to-coach">이 답장 코칭 받기</button></div>
      </div>`;
    $("#reply-to-coach").onclick = () => { $("#coach-input").value = r.reply_draft; switchTab("coach"); };
  });
}

// ---------- ④ 리허설 ----------

let sessionId = null;

function bubble(role, text, extra = "") {
  const div = document.createElement("div");
  div.className = `bubble ${role} ${extra}`;
  div.textContent = text;
  $("#chat-log").appendChild(div);
  $("#chat-log").scrollTop = $("#chat-log").scrollHeight;
  return div;
}

async function startRehearsal() {
  await busy($("#rehearsal-start"), "준비 중…", async () => {
    const r = await api("/api/rehearsal/start", { method: "POST", json: {
      scenario_id: $("#scenario-select").value, contact_id: contactId("#rehearsal-contact"),
    } });
    sessionId = r.session_id;
    $("#chat-log").innerHTML = "";
    $("#rehearsal-result").innerHTML = "";
    $("#rehearsal-box").hidden = false;
    r.messages.forEach((m) => bubble(m.role, m.content));
    if (!r.messages.length) bubble("assistant", `(${r.scenario.ai_role || "상대"}에게 먼저 말을 걸어 보세요)`, "typing");
    $("#chat-text").focus();
  });
}

async function sendRehearsal(event) {
  event.preventDefault();
  const text = $("#chat-text").value.trim();
  if (!text || !sessionId) return;
  $("#chat-text").value = "";
  bubble("user", text);
  const typing = bubble("assistant", "…", "typing");
  try {
    const r = await api(`/api/rehearsal/${sessionId}/message`, { method: "POST", json: { text } });
    typing.remove();
    bubble("assistant", r.reply);
  } catch (error) {
    typing.remove();
    toast(error.message, true);
  }
}

async function endRehearsal() {
  if (!sessionId) return;
  await busy($("#rehearsal-end"), "평가 중…", async () => {
    const r = await api(`/api/rehearsal/${sessionId}/end`, { method: "POST" });
    const f = r.report;
    $("#rehearsal-result").innerHTML = `
      <div class="card">
        <div class="result-head"><h3>피드백 리포트 ${f.goal_achieved ? "🎯 목표 달성" : ""}</h3>${metaChips(r.meta)}</div>
        <div class="gauges">
          ${gauge("종합", f.overall_score)}
          ${gauge("공손도", f.scores.politeness)}
          ${gauge("명확성", f.scores.clarity)}
          ${gauge("자연스러움", f.scores.naturalness)}
        </div>
        <p style="text-align:center">${esc(f.summary)}</p>
        <div class="grid-2">
          <div><h3>잘한 점</h3>${list(f.good_points)}</div>
          <div><h3>고칠 점</h3><div class="issues">${f.improvements.map((i) => `
            <div class="issue"><q>${esc(i.quote)}</q><div class="fix">→ ${esc(i.suggestion)}</div></div>`).join("")}</div></div>
        </div>
      </div>`;
    sessionId = null;
    $("#rehearsal-box").hidden = true;
  });
}

// ---------- ⑤ 상대 ----------

let contacts = [];

async function loadContacts() {
  contacts = await api("/api/contacts");
  const relLabel = (id) => (domain.relations || []).find((r) => r.id === id)?.label || id || "";
  $("#contact-list").innerHTML = contacts.length ? contacts.map((c) => `
    <li>
      <div><b>${esc(c.name)}</b> <span class="chip">${esc(relLabel(c.relation))}</span><br><span class="muted">${esc(c.profile || "")}</span></div>
      <div class="row">
        <button data-act="history" data-id="${c.id}">기록</button>
        <button data-act="edit" data-id="${c.id}">수정</button>
        <button data-act="delete" data-id="${c.id}">삭제</button>
      </div>
    </li>`).join("") : `<li class="muted">아직 없어요. 왼쪽에서 추가해 보세요.</li>`;
  const options = `<option value="">선택 안 함</option>` + contacts.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
  $$(".contact-select").forEach((s) => { const v = s.value; s.innerHTML = options; s.value = v; });
}

function resetContactForm() {
  $("#contact-id").value = "";
  $("#contact-name").value = "";
  $("#contact-relation").value = "";
  $("#contact-profile").value = "";
  $("#contact-form-title").textContent = "새 상대 추가";
}

async function saveContact() {
  const body = { name: $("#contact-name").value.trim(), relation: orNull($("#contact-relation").value), profile: $("#contact-profile").value.trim() };
  if (!body.name) return toast("이름을 입력해 주세요.", true);
  const id = $("#contact-id").value;
  await busy($("#contact-save"), "저장 중…", async () => {
    await api(id ? `/api/contacts/${id}` : "/api/contacts", { method: id ? "PUT" : "POST", json: body });
    resetContactForm();
    await loadContacts();
    toast("저장했어요.");
  });
}

async function contactAction(event) {
  const btn = event.target.closest("button[data-act]");
  if (!btn) return;
  const c = contacts.find((x) => x.id === Number(btn.dataset.id));
  if (btn.dataset.act === "edit") {
    $("#contact-id").value = c.id;
    $("#contact-name").value = c.name;
    $("#contact-relation").value = c.relation || "";
    $("#contact-profile").value = c.profile || "";
    $("#contact-form-title").textContent = `${c.name} 수정`;
  } else if (btn.dataset.act === "delete") {
    if (!confirm(`${c.name}과(와)의 기록을 모두 삭제할까요?`)) return;
    await api(`/api/contacts/${c.id}`, { method: "DELETE" }).catch((e) => toast(e.message, true));
    $("#contact-history").innerHTML = "";
    loadContacts();
  } else if (btn.dataset.act === "history") {
    const items = await api(`/api/contacts/${c.id}/interactions`);
    $("#contact-history").innerHTML = `
      <div class="card"><h3>${esc(c.name)} 대화 기록</h3>
        <table><tr><th>기능</th><th>입력</th><th>결과</th><th>시각</th></tr>
        ${items.map((i) => `<tr><td><span class="chip">${esc(i.feature)}</span></td><td>${esc(i.input)}</td><td>${esc(i.output)}</td>
          <td class="muted">${new Date(i.created * 1000).toLocaleString()}</td></tr>`).join("") || `<tr><td colspan="4" class="muted">기록 없음</td></tr>`}
        </table></div>`;
  }
}

// ---------- 토큰 ----------

async function loadUsage() {
  const u = await api("/api/usage").catch((e) => toast(e.message, true));
  if (!u) return;
  const t = u.total, lim = u.limits;
  const pct = (a, b) => (b ? Math.min(100, (a / b) * 100) : 0);
  const table = (groups, title) => {
    const rows = Object.entries(groups);
    const max = Math.max(1, ...rows.map(([, g]) => g.total_tokens));
    return `<div class="card"><h3>${title}</h3><table>
      <tr><th></th><th>호출</th><th>실제</th><th>캐시</th><th>토큰</th><th style="width:30%"></th><th>평균 지연</th></tr>
      ${rows.map(([name, g]) => `<tr><td>${esc(name)}</td><td class="num">${g.calls}</td><td class="num">${g.live_calls}</td>
        <td class="num">${g.cached_calls}</td><td class="num">${g.total_tokens.toLocaleString()}</td>
        <td><div class="bar" style="width:${pct(g.total_tokens, max)}%"></div></td><td class="num">${g.avg_latency_ms}ms</td></tr>`).join("")
        || `<tr><td colspan="7" class="muted">아직 호출 없음</td></tr>`}
    </table></div>`;
  };
  $("#usage-result").innerHTML = `
    <div class="stats">
      <div class="stat"><small>총 토큰</small><b>${t.total_tokens.toLocaleString()}</b><small>입력 ${t.prompt_tokens.toLocaleString()} · 출력 ${t.completion_tokens.toLocaleString()}</small></div>
      <div class="stat"><small>실제 호출</small><b>${t.live_calls}</b><small>오류 ${t.errors}</small></div>
      <div class="stat"><small>캐시로 아낀 호출</small><b>${t.cached_calls}</b></div>
      <div class="stat"><small>MOCK 호출</small><b>${t.mock_calls}</b></div>
    </div>
    <div class="card"><h3>한도</h3>
      <small>호출 ${lim.used_live_calls} / ${lim.max_live_calls}</small><div class="progress"><div style="width:${pct(lim.used_live_calls, lim.max_live_calls)}%"></div></div>
      <small>토큰 ${lim.used_tokens.toLocaleString()} / ${lim.token_stop_threshold.toLocaleString()}</small><div class="progress"><div style="width:${pct(lim.used_tokens, lim.token_stop_threshold)}%"></div></div>
    </div>
    ${table(u.by_feature, "기능별")}
    ${table(u.by_model, "모델별")}
    <div class="card"><h3>최근 호출</h3><table>
      <tr><th>시각</th><th>기능</th><th>모델</th><th>상태</th><th>토큰</th><th>지연</th></tr>
      ${u.recent.map((r) => `<tr><td class="muted">${esc(r.ts.slice(11, 19))}</td><td>${esc(r.feature)}</td><td>${esc(r.model)}</td>
        <td>${r.mock ? '<span class="chip mock">MOCK</span>' : r.cached ? '<span class="chip cached">캐시</span>' : esc(r.status)}</td>
        <td class="num">${r.total_tokens ?? "-"}</td><td class="num">${r.latency_ms}ms</td></tr>`).join("")}
    </table></div>`;
}

// ---------- 이벤트 연결 ----------

$$(".tabs button").forEach((b) => (b.onclick = () => switchTab(b.dataset.tab)));
$("#route-btn").onclick = routeInput;
$("#route-input").addEventListener("keydown", (e) => e.key === "Enter" && routeInput());
$("#compose-btn").onclick = runCompose;
$("#coach-btn").onclick = runCoach;
$("#interpret-image").onchange = previewImage;
$("#interpret-btn").onclick = runInterpret;
$("#scenario-select").onchange = showScenario;
$("#rehearsal-start").onclick = startRehearsal;
$("#chat-form").onsubmit = sendRehearsal;
$("#rehearsal-end").onclick = endRehearsal;
$("#contact-save").onclick = saveContact;
$("#contact-reset").onclick = resetContactForm;
$("#contact-list").onclick = contactAction;
$("#usage-refresh").onclick = loadUsage;
$("#team-key").value = store("teamKey");
$("#team-key").onchange = (e) => { store("teamKey", e.target.value.trim()); init(); };

async function init() {
  try {
    await Promise.all([loadHealth(), loadDomain()]);
    await loadContacts();
  } catch (error) {
    toast(error.message, true);
  }
}
init();
