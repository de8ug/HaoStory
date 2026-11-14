const state = {
  sources: [],
  conversations: [],
  formats: [],
  selected: new Set(),
  selectedConversations: new Set(),
  sourceMode: "project",
  angle: "",
  analysis: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "请求失败，请稍后重试。");
  return data;
}

function humanSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);
}

function renderSources() {
  const container = $("#source-list");
  if (state.sourceMode === "conversations") {
    if (!state.conversations.length) {
      container.innerHTML = '<div class="loading-row">当前智能体没有提供可选择的近期会话。可回到智能体直接指定聊天，或导出为 Markdown。</div>';
      return;
    }
    container.innerHTML = state.conversations.map((conversation) => `
      <label class="source-item">
        <input type="checkbox" value="${escapeHtml(conversation.id)}" ${state.selectedConversations.has(conversation.id) ? "checked" : ""}>
        <span class="file-icon">CHAT</span>
        <span class="file-name"><strong>${escapeHtml(conversation.title)}</strong><small>${escapeHtml(conversation.project || "未归属工程")} · ${escapeHtml(conversation.updated_at || "近期")}</small></span>
        <span class="file-size">选择后读取</span>
      </label>
    `).join("");
    $$(".source-item input").forEach((input) => input.addEventListener("change", () => {
      if (input.checked) state.selectedConversations.add(input.value);
      else state.selectedConversations.delete(input.value);
      state.analysis = null;
      state.angle = "";
      updateSummary();
    }));
    return;
  }
  if (!state.sources.length) {
    container.innerHTML = '<div class="loading-row">没有发现可选的说明文档或图片。你仍可通过当前对话告诉智能体需要使用的材料。</div>';
    return;
  }
  container.innerHTML = state.sources.map((source) => `
    <label class="source-item">
      <input type="checkbox" value="${escapeHtml(source.path)}" ${state.selected.has(source.path) ? "checked" : ""}>
      <span class="file-icon">${source.kind === "image" ? "IMG" : "TXT"}</span>
      <span class="file-name"><strong>${escapeHtml(source.name)}</strong><small>${escapeHtml(source.path)}</small></span>
      <span class="file-size">${humanSize(source.size)}</span>
    </label>
  `).join("");
  $$(".source-item input").forEach((input) => input.addEventListener("change", () => {
    if (input.checked) state.selected.add(input.value);
    else state.selected.delete(input.value);
    state.analysis = null;
    state.angle = "";
    updateSummary();
  }));
}

function renderFormats(catalog) {
  $("#format-grid").innerHTML = catalog.formats.map((format) => `
    <label class="format-card">
      <input type="checkbox" value="${format.id}">
      <span class="format-check">✓</span>
      <b>${escapeHtml(format.title)}</b>
      <p>${escapeHtml(format.description)}</p>
    </label>
  `).join("");
  $$(".format-card input").forEach((input) => input.addEventListener("change", () => {
    state.formats = $$(".format-card input:checked").map((item) => item.value);
    state.analysis = null;
    state.angle = "";
    updateSummary();
  }));
}

function updateSummary() {
  const selectedSources = state.sources.filter((source) => state.selected.has(source.path));
  const textCount = selectedSources.filter((source) => source.kind === "text").length;
  const imageCount = selectedSources.filter((source) => source.kind === "image").length;
  $("#selection-count").textContent = `已选 ${selectedSources.length} 项`;
  const values = [textCount, imageCount, state.selectedConversations.size, state.formats.length];
  $$("#material-summary b").forEach((element, index) => { element.textContent = values[index]; });
  const hasMaterial = selectedSources.length || state.selectedConversations.size;
  const percent = Math.min(100, (hasMaterial ? 35 : 0) + (imageCount ? 20 : 0) + (state.formats.length ? 30 : 0) + (state.angle ? 15 : 0));
  $("#meter-value").style.width = `${percent}%`;
  $("#meter-label").textContent = percent >= 80 ? "可以开始制作" : percent >= 50 ? "已经具备基础材料" : hasMaterial ? "继续选择内容形式" : "等待选择材料";
  $("#create-button").disabled = !(state.angle && $("#consent").checked);
}

function renderAnalysis(result) {
  const container = $("#recommendations");
  container.className = "recommendations";
  container.innerHTML = result.recommendations.map((item, index) => `
    <button class="angle-card" type="button" data-angle="${escapeHtml(item.id)}">
      <small>推荐 ${index + 1} · ${escapeHtml(item.format)}</small>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.description)}</p>
      <p>${escapeHtml(item.reason)}</p>
      <span class="angle-score">适合度 ${item.score}</span>
    </button>
  `).join("");
  $$(".angle-card").forEach((card) => card.addEventListener("click", () => {
    $$(".angle-card").forEach((item) => item.classList.remove("selected"));
    card.classList.add("selected");
    state.angle = card.dataset.angle;
    updateSummary();
    $("#produce").scrollIntoView({ behavior: "smooth", block: "start" });
  }));
  const gaps = $("#gaps");
  gaps.hidden = false;
  gaps.innerHTML = `
    <h3>如果愿意，可以再补充</h3>
    ${result.gaps.length ? result.gaps.map((item, index) => `
      <div class="gap-row"><b>0${index + 1}</b><div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.why)}</p></div></div>
    `).join("") : '<div class="gap-row"><b>✓</b><div><strong>现有材料已经足够</strong><p>可以直接交给智能体生成第一版。</p></div></div>'}
  `;
}

async function analyze() {
  const error = $("#form-error");
  error.textContent = "";
  if (!state.selected.size && !state.selectedConversations.size) { error.textContent = "请至少选择一项材料。"; return; }
  if (!state.formats.length) { error.textContent = "请至少选择一种内容形式。"; return; }
  const button = $("#analyze-button");
  button.disabled = true;
  button.querySelector("span").textContent = "正在寻找故事线索…";
  try {
    state.analysis = await api("/api/analyze", {
      method: "POST",
      body: JSON.stringify({
        selections: [...state.selected],
        conversation_refs: state.conversations.filter((item) => state.selectedConversations.has(item.id)),
        formats: state.formats,
        goal: $("#goal").value,
        audience: $("#audience").value,
      }),
    });
    renderAnalysis(state.analysis);
    $("#angles").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (failure) {
    error.textContent = failure.message;
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "分析材料并推荐方向";
  }
}

async function createJob() {
  const button = $("#create-button");
  button.disabled = true;
  button.querySelector("span").textContent = "正在准备制作任务…";
  try {
    const result = await api("/api/jobs", {
      method: "POST",
      body: JSON.stringify({
        selected_paths: [...state.selected],
        conversation_refs: state.conversations.filter((item) => state.selectedConversations.has(item.id)),
        formats: state.formats,
        angle: state.angle,
        goal: $("#goal").value,
        audience: $("#audience").value,
        supplements: $("#supplements").value,
        generate_with_current_material: true,
        research_current_examples: $("#research-current").checked,
      }),
    });
    const success = $("#job-success");
    success.hidden = false;
    success.innerHTML = `<strong>制作任务已经准备好</strong><p>任务编号 ${escapeHtml(result.job_id)}。回到调用 HaoStory 的智能体，它会只读取你选中的材料并继续生成。</p>`;
    success.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (failure) {
    $("#form-error").textContent = failure.message;
  } finally {
    button.querySelector("span").textContent = "创建制作任务";
    updateSummary();
  }
}

async function init() {
  try {
    const [capabilities, sources, catalog, hostContext] = await Promise.all([
      api("/api/capabilities"), api("/api/sources"), api("/api/templates"), api("/api/host-context"),
    ]);
    $("#project-name").textContent = capabilities.project;
    state.sources = sources.sources;
    state.conversations = hostContext.conversations || [];
    if (state.conversations.length) $("#conversation-tab").disabled = false;
    const sponsor = capabilities.sponsor;
    if (!sponsor.enabled) {
      $("#sponsor-footer").hidden = true;
      $("#sponsor-links").hidden = true;
    } else {
      $("#sponsor-lab").textContent = sponsor.lab_name;
      $("#sponsor-lab-note").textContent = sponsor.lab_note;
      $("#sponsor-wechat").textContent = sponsor.wechat;
      $("#sponsor-wechat-note").textContent = sponsor.wechat_note;
      $("#sponsor-onetake").textContent = sponsor.onetake_name;
      $("#sponsor-onetake-note").textContent = sponsor.onetake_note;
    }
    renderSources();
    renderFormats(catalog);
    updateSummary();
  } catch (failure) {
    $("#source-list").innerHTML = `<div class="loading-row">${escapeHtml(failure.message)}</div>`;
  }
}

$("#analyze-button").addEventListener("click", analyze);
$("#create-button").addEventListener("click", createJob);
$("#consent").addEventListener("change", updateSummary);
$("#project-tab").addEventListener("click", () => {
  state.sourceMode = "project";
  $("#project-tab").classList.add("active");
  $("#conversation-tab").classList.remove("active");
  renderSources();
});
$("#conversation-tab").addEventListener("click", () => {
  if ($("#conversation-tab").disabled) return;
  state.sourceMode = "conversations";
  $("#conversation-tab").classList.add("active");
  $("#project-tab").classList.remove("active");
  renderSources();
});
init();
