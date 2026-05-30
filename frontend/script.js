const API_BASE_URL = 'http://localhost:8000';

const $ = (id) => document.getElementById(id);

const show = (el) => el.classList.remove('hidden');
const hide = (el) => el.classList.add('hidden');

$('submitBtn').addEventListener('click', submitReview);
$('prUrl').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') submitReview();
});

async function submitReview() {
  const url = $('prUrl').value.trim();
  if (!url) return;

  hide($('error'));
  hide($('result'));
  show($('loading'));

  try {
    const res = await fetch(`${API_BASE_URL}/api/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pr_url: url }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Server error (${res.status})`);
    }

    const data = await res.json();
    renderResult(data);
  } catch (err) {
    show($('error'));
    $('error').textContent = 'Error: ' + err.message;
  } finally {
    hide($('loading'));
  }
}

function renderResult(data) {
  $('prMeta').textContent = `${data.pr_url}  ·  ID: ${data.id}`;

  $('summary').textContent = data.summary;

  const risksEl = $('risks');
  risksEl.innerHTML = '';
  if (data.risks && data.risks.length) {
    data.risks.forEach((r) => {
      const li = document.createElement('li');
      li.textContent = r;
      risksEl.appendChild(li);
    });
  } else {
    const li = document.createElement('li');
    li.textContent = 'None';
    risksEl.appendChild(li);
  }

  const suggEl = $('suggestions');
  suggEl.innerHTML = '';
  if (data.suggestions && data.suggestions.length) {
    data.suggestions.forEach((s) => {
      const li = document.createElement('li');
      li.textContent = s;
      suggEl.appendChild(li);
    });
  } else {
    const li = document.createElement('li');
    li.textContent = 'None';
    suggEl.appendChild(li);
  }

  show($('result'));
  loadHistory();
}

async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/history`);
    if (!res.ok) return;

    const list = await res.json();
    const ul = $('historyList');
    const empty = $('historyEmpty');

    ul.innerHTML = '';

    if (!list.length) {
      show(empty);
      return;
    }

    hide(empty);

    list.forEach((item) => {
      const li = document.createElement('li');
      li.dataset.id = item.id;

      const prLine = document.createElement('div');
      prLine.className = 'hl-pr';
      prLine.textContent = item.pr_url;

      const summaryLine = document.createElement('div');
      summaryLine.className = 'hl-summary';
      summaryLine.textContent =
        item.summary.length > 100
          ? item.summary.slice(0, 100) + '…'
          : item.summary;

      const timeLine = document.createElement('div');
      timeLine.className = 'hl-time';
      timeLine.textContent = new Date(item.created_at).toLocaleString();

      li.appendChild(prLine);
      li.appendChild(summaryLine);
      li.appendChild(timeLine);
      li.addEventListener('click', () => loadDetail(item.id));
      ul.appendChild(li);
    });
  } catch {
    // silently ignore history load failures
  }
}

async function loadDetail(id) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/review/${id}`);
    if (!res.ok) return;
    const data = await res.json();
    renderResult(data);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch {
    // silently ignore
  }
}

loadHistory();
