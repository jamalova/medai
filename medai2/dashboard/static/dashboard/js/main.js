// Toggle frequency/prevalence buttons
document.querySelectorAll('.toggle').forEach(btn => {
  btn.addEventListener('click', function () {
    this.closest('.toggle-group').querySelectorAll('.toggle').forEach(b => b.classList.remove('active'));
    this.classList.add('active');
  });
});

// Animate bars on load
window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.dist-bar').forEach(bar => {
    const w = bar.style.width;
    bar.style.width = '0';
    setTimeout(() => { bar.style.width = w; }, 100);
  });
});

// Live log refresh via API
async function refreshLogs() {
  try {
    const res = await fetch('/api/logs/');
    const data = await res.json();
    const tbody = document.getElementById('logs-tbody');
    if (!tbody || !data.logs) return;

    tbody.innerHTML = data.logs.map(log => `
      <tr>
        <td class="log-id">${log.article_id}</td>
        <td><span class="domain-tag" style="background:rgba(59,111,212,0.12);color:#3b6fd4">${log.domain}</span></td>
        <td>
          <div class="confidence-wrap">
            <div class="confidence-bar-track">
              <div class="confidence-bar ${log.confidence >= 90 ? 'bar-green' : log.confidence >= 75 ? 'bar-orange' : 'bar-red'}"
                   style="width:${log.confidence}%"></div>
            </div>
            <span>${log.confidence}%</span>
          </div>
        </td>
        <td>
          ${log.status === 'verified'
            ? '<span class="status-badge verified">✔ Verified</span>'
            : '<span class="status-badge needs-review">● Needs Review</span>'}
        </td>
        <td class="log-time">${log.time}</td>
      </tr>
    `).join('');
  } catch (e) { /* silent */ }
}

setInterval(refreshLogs, 30000);

// ===========================================================
// IR ANALYTICS LOGIC
// ===========================================================

function switchTab(evt, tabName) {
  const contents = document.getElementsByClassName("tab-content");
  for (let i = 0; i < contents.length; i++) {
    contents[i].classList.remove("active");
  }

  const buttons = document.getElementsByClassName("tab-btn");
  for (let i = 0; i < buttons.length; i++) {
    buttons[i].classList.remove("active");
  }

  document.getElementById(tabName).classList.add("active");
  evt.currentTarget.classList.add("active");

  // Load data if needed
  if (tabName === 'tab-tokens') fetchTokens();
  if (tabName === 'tab-inverted') fetchInvertedIndex();
  if (tabName === 'tab-slots') fetchSlots();
}

async function fetchTokens() {
  const tbody = document.getElementById('tokens-tbody');
  tbody.innerHTML = '<tr><td colspan="4" class="empty-msg">Loading tokens...</td></tr>';
  
  try {
    const res = await fetch('/api/tokens/?limit=100');
    const data = await res.json();
    
    tbody.innerHTML = data.tokens.map(t => `
      <tr>
        <td><span class="token-badge">${t.token}</span></td>
        <td><span class="count-badge">${t.count}</span></td>
        <td>${t.doc_count} docs</td>
        <td><div class="confidence-bar-track" style="width:100px"><div class="confidence-bar" style="width:${Math.min(100, t.count/10)}%; background:#3b6fd4"></div></div></td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="4" class="empty-msg">Error loading tokens</td></tr>';
  }
}

async function fetchInvertedIndex() {
  const tbody = document.getElementById('inverted-tbody');
  tbody.innerHTML = '<tr><td colspan="2" class="empty-msg">Loading index...</td></tr>';
  
  try {
    const res = await fetch('/api/inverted-index/?limit=100');
    const data = await res.json();
    
    tbody.innerHTML = Object.entries(data.inverted_index).map(([token, docs]) => `
      <tr>
        <td><span class="token-badge" style="background:#fef3c7; color:#92400e;">${token}</span></td>
        <td style="word-break: break-all; font-family: monospace; font-size: 11px; color: #64748b;">
          ${docs.join(', ')}
        </td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="2" class="empty-msg">Error loading index</td></tr>';
  }
}

async function fetchSlots() {
  const tbody = document.getElementById('slots-tbody');
  tbody.innerHTML = '<tr><td colspan="3" class="empty-msg">Loading slots...</td></tr>';
  
  try {
    const res = await fetch('/api/slots/?limit=50');
    const data = await res.json();
    
    tbody.innerHTML = data.slots.map(s => `
      <tr>
        <td>#${s.id}</td>
        <td style="max-width:300px; font-size:12px;">${s.text}</td>
        <td>
          <div class="slot-box">
            <span class="slot-tag subject-tag">SUB: ${s.slots.subject}</span>
            <span class="slot-tag predicate-tag">PRED: ${s.slots.predicate}</span>
            <span class="slot-tag object-tag">OBJ: ${s.slots.object.substring(0, 30)}...</span>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty-msg">Error loading slots</td></tr>';
  }
}

async function performIRSearch() {
  const input = document.getElementById('irSearchInput');
  const resultsDiv = document.getElementById('irSearchResults');
  const query = input.value.trim();
  
  if (!query) return;
  
  resultsDiv.innerHTML = '<p class="empty-msg">Searching across models...</p>';
  
  try {
    const res = await fetch(`/api/search/compare/?q=${encodeURIComponent(query)}&top_k=5`);
    const data = await res.json();
    
    let html = `
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px;">
        <div class="card" style="padding:15px; background: #f8fafc;">
          <h3 style="font-size:13px; margin-bottom:12px; color:#1e293b; border-bottom:2px solid #3b6fd4; display:inline-block;">BM25 Results (Recommended)</h3>
          ${data.bm25_results.map(r => `
            <div style="margin-bottom:10px; padding:8px; border-radius:6px; background:#fff; border:1px solid #e2e8f0;">
              <div style="display:flex; justify-content:space-between; font-size:11px; font-weight:700; color:#3b6fd4;">
                <span>DOC #${r.doc_id}</span>
                <span>SCORE: ${r.score}</span>
              </div>
              <p style="font-size:12px; color:#475569; margin-top:4px;">${r.text.substring(0, 100)}...</p>
            </div>
          `).join('') || '<p class="empty-msg">No results</p>'}
        </div>
        <div class="card" style="padding:15px; background: #f8fafc;">
          <h3 style="font-size:13px; margin-bottom:12px; color:#1e293b; border-bottom:2px solid #a347ba; display:inline-block;">TF-IDF Results</h3>
          ${data.tfidf_results.map(r => `
            <div style="margin-bottom:10px; padding:8px; border-radius:6px; background:#fff; border:1px solid #e2e8f0;">
              <div style="display:flex; justify-content:space-between; font-size:11px; font-weight:700; color:#a347ba;">
                <span>DOC #${r.doc_id}</span>
                <span>SCORE: ${r.score}</span>
              </div>
              <p style="font-size:12px; color:#475569; margin-top:4px;">${r.text.substring(0, 100)}...</p>
            </div>
          `).join('') || '<p class="empty-msg">No results</p>'}
        </div>
      </div>
    `;
    resultsDiv.innerHTML = html;
  } catch (e) {
    resultsDiv.innerHTML = '<p class="empty-msg" style="color:red;">Search failed</p>';
  }
}
