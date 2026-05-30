const API_BASE_URL = 'http://localhost:8001';
const STORAGE_KEY = 'ai-pr-review-history';

const $ = (id) => document.getElementById(id);

const show = (el) => el.classList.remove('hidden');
const hide = (el) => el.classList.add('hidden');

function getLocalHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveLocalHistory(record) {
  const history = getLocalHistory();
  history.unshift(record);
  if (history.length > 50) history.pop();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

function renderLocalHistory() {
  const list = $('history-list');
  const history = getLocalHistory();

  if (history.length === 0) {
    list.innerHTML = '<li class="history-empty">暂无历史记录</li>';
    return;
  }

  list.innerHTML = history.map((item, index) => {
    const time = item.timestamp
      ? new Date(item.timestamp).toLocaleString('zh-CN')
      : '';
    return `<li data-index="${index}">
      <div class="hl-pr">${item.url || item.pr_url}</div>
      ${item.summary ? `<div class="hl-summary">${item.summary.length > 100 ? item.summary.slice(0, 100) + '…' : item.summary}</div>` : ''}
      ${time ? `<span class="hl-time">${time}</span>` : ''}
    </li>`;
  }).join('');
}

async function loadHistoryFromServer() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/history`);
    if (!res.ok) return;
    const list = await res.json();
    if (list.length === 0) return;
    list.forEach((item) => {
      saveLocalHistory({
        id: item.id,
        url: item.pr_url,
        summary: item.summary,
        timestamp: new Date(item.created_at).getTime(),
      });
    });
    renderLocalHistory();
  } catch {
    // offline, use local cache
  }
}

function confidenceClass(score) {
  if (score >= 90) return 'confidence-high';
  if (score >= 70) return 'confidence-medium';
  if (score >= 50) return 'confidence-low';
  return 'confidence-info';
}

function confidenceLabel(score) {
  if (score >= 90) return '高风险';
  if (score >= 70) return '中等风险';
  if (score >= 50) return '低风险';
  return '仅供参考';
}

function renderItem(text, confidence) {
  const cls = confidenceClass(confidence);
  const label = confidenceLabel(confidence);
  return `<span class="item-text">${text}</span>
    <span class="confidence-badge ${cls}" title="置信度: ${confidence}% - ${label}">${confidence}%</span>`;
}

function renderList(el, items) {
  el.innerHTML = '';
  if (items && items.length) {
    items.forEach((item) => {
      const li = document.createElement('li');
      if (typeof item === 'string') {
        li.innerHTML = renderItem(item, 50);
      } else {
        li.innerHTML = renderItem(item.text, item.confidence);
      }
      el.appendChild(li);
    });
  }
}

async function displayResult(data) {
  show($('result-area'));
  hide($('placeholder'));
  hide($('loading'));

  $('pr-meta').textContent = `${data.pr_url}  ·  ID: ${data.id}`;
  $('summary').textContent = data.summary;

  renderList($('risks-list'), data.risks);
  renderList($('suggestions-list'), data.suggestions);
}

async function handleAnalyze() {
  const url = $('pr-url').value.trim();
  if (!url) {
    $('pr-url').focus();
    return;
  }

  hide($('error'));
  hide($('result-area'));
  hide($('placeholder'));
  show($('loading'));

  $('analyze-btn').disabled = true;
  $('analyze-btn').textContent = '分析中...';

  try {
    const res = await fetch(`${API_BASE_URL}/api/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pr_url: url }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `服务器错误 (${res.status})`);
    }

    const data = await res.json();

    saveLocalHistory({
      id: data.id,
      url: data.pr_url,
      summary: data.summary,
      data: { risks: data.risks, suggestions: data.suggestions },
      timestamp: Date.now(),
    });

    await displayResult(data);
    renderLocalHistory();
  } catch (err) {
    hide($('loading'));
    show($('error'));
    if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
      $('error').innerHTML = '❌ 无法连接后端，请确保后端服务已启动（端口 8001）';
    } else {
      $('error').textContent = '❌ ' + err.message;
    }
  } finally {
    $('analyze-btn').disabled = false;
    $('analyze-btn').textContent = '分析';
  }
}

function loadFromLocalHistory(index) {
  const history = getLocalHistory();
  const item = history[index];
  if (!item) return;
  $('pr-url').value = item.url || item.pr_url;

  if (item.data) {
    show($('result-area'));
    hide($('placeholder'));
    $('pr-meta').textContent = (item.url || item.pr_url) + '  ·  本地缓存';
    $('summary').textContent = item.summary || '';

    renderList($('risks-list'), item.data.risks);
    renderList($('suggestions-list'), item.data.suggestions);
  } else if (item.id) {
    loadDetailFromServer(item.id);
  }
}

async function loadDetailFromServer(id) {
  hide($('error'));
  hide($('result-area'));
  hide($('placeholder'));
  show($('loading'));

  try {
    const res = await fetch(`${API_BASE_URL}/api/review/${id}`);
    if (!res.ok) {
      hide($('loading'));
      show($('error'));
      $('error').textContent = `无法加载记录 (${res.status})`;
      return;
    }
    const data = await res.json();
    await displayResult(data);
  } catch (err) {
    hide($('loading'));
    show($('error'));
    if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
      $('error').innerHTML = '❌ 无法连接后端，请确保后端服务已启动（端口 8001）';
    } else {
      $('error').textContent = '❌ ' + err.message;
    }
  } finally {
    hide($('loading'));
  }
}

document.addEventListener('DOMContentLoaded', () => {
  $('analyze-btn').addEventListener('click', handleAnalyze);

  $('pr-url').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleAnalyze();
  });

  $('history-list').addEventListener('click', (e) => {
    const li = e.target.closest('li');
    if (!li || li.dataset.index === undefined) return;
    loadFromLocalHistory(parseInt(li.dataset.index, 10));
  });

  loadHistoryFromServer().then(renderLocalHistory);
});
