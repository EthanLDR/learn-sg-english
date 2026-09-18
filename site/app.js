(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const lessons = $$('article.lesson');
  const KEY = 'ethan-sg-english-v1';
  let state = {done: [], last: 1, dark: false, size: 16};
  try { const saved = JSON.parse(localStorage.getItem(KEY)); if (saved && typeof saved === 'object') state = {...state, ...saved}; } catch (_) {}
  const validDays = new Set(lessons.map(x => Number(x.dataset.day)));
  state.done = Array.isArray(state.done) ? [...new Set(state.done.filter(d => validDays.has(d)))] : [];
  state.size = Math.max(14, Math.min(22, Number(state.size) || 16));
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) {} }
  let toastTimer;
  function notify(message) { $('#toast').textContent = message; $('#toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 3500); }
  function paint() {
    document.body.classList.toggle('dark', Boolean(state.dark));
    document.documentElement.style.setProperty('--reading', state.size + 'px');
    $('#theme').textContent = state.dark ? '浅色' : '深色';
    $$('[data-day]').forEach(el => {
      const done = state.done.includes(Number(el.dataset.day));
      if (el.matches('.day-tile,.side-day')) el.classList.toggle('done', done);
      if (el.matches('.review-toggle')) { el.setAttribute('aria-pressed', String(done)); el.textContent = done ? '✓ 已复习' : '○ 标记已复习'; }
    });
    $('#completion-count').textContent = state.done.length + ' / ' + lessons.length;
    $('#completion').value = state.done.length;
    if (validDays.has(Number(state.last))) { $('#resume').href = '#day-' + String(state.last).padStart(2, '0'); $('#resume').textContent = state.last > 1 ? '继续上次 · Day ' + state.last : '从 Day 1 开始'; }
  }
  paint();
  $('#theme').addEventListener('click', () => { state.dark = !state.dark; paint(); save(); });
  $('#font-up').addEventListener('click', () => { state.size = Math.min(22, state.size + 1); paint(); save(); });
  $('#font-down').addEventListener('click', () => { state.size = Math.max(14, state.size - 1); paint(); save(); });
  $$('.review-toggle').forEach(button => button.addEventListener('click', () => { const d = Number(button.dataset.day); state.done = state.done.includes(d) ? state.done.filter(x => x !== d) : [...state.done, d]; paint(); save(); }));
  function openAncestors(target) { for (let el = target; el; el = el.parentElement) { if (el.tagName === 'DETAILS') el.open = true; } }
  function scrollToHash(hash, smooth = true) {
    let id; try { id = decodeURIComponent(hash.slice(1)); } catch (_) { return; }
    let target = document.getElementById(id);
    if (!target && /^day-\d+$/.test(id)) target = document.getElementById('day-' + String(Number(id.slice(4))).padStart(2, '0'));
    if (!target) return;
    openAncestors(target);
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    target.scrollIntoView({behavior: smooth && !reduce ? 'smooth' : 'instant', block: 'start'});
    const lesson = target.closest('article.lesson');
    if (lesson) { state.last = Number(lesson.dataset.day); save(); paint(); }
    if (target.matches('[data-search]')) { target.classList.add('flash'); setTimeout(() => target.classList.remove('flash'), 2200); }
  }
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href^="#"]');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    try { history.pushState(null, '', link.getAttribute('href')); } catch (_) { location.hash = link.getAttribute('href'); }
    scrollToHash(link.getAttribute('href'));
  });
  addEventListener('hashchange', () => scrollToHash(location.hash));
  if (location.hash) setTimeout(() => scrollToHash(location.hash, false), 50);
  let scrollPending = false;
  addEventListener('scroll', () => { if (scrollPending) return; scrollPending = true; requestAnimationFrame(() => { const max = document.documentElement.scrollHeight - innerHeight; $('#reading-progress').style.width = (max ? 100 * scrollY / max : 0) + '%'; scrollPending = false; }); }, {passive: true});
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { const day = Number(entry.target.dataset.day); $$('.side-day').forEach(n => n.classList.toggle('active', Number(n.dataset.day) === day)); state.last = day; save(); } }), {rootMargin: '-10% 0px -60% 0px', threshold: 0});
    lessons.forEach(el => observer.observe(el));
  }
  let index, matches = [], shown = 0, term = '', timer;
  const normalize = s => s.toLocaleLowerCase().replace(/[’‘]/g, "'").replace(/\s+/g, ' ').trim();
  function makeIndex() { return $$('.lesson-body [data-search]').map(el => ({id: el.id, text: el.textContent.replace(/\s+/g, ' ').trim(), label: el.closest('[data-label]').dataset.label})).filter(row => row.text); }
  function appendResults() {
    const fragment = document.createDocumentFragment();
    matches.slice(shown, shown + 20).forEach(row => {
      const link = document.createElement('a'); link.className = 'search-result'; link.href = '#' + row.id;
      const label = document.createElement('small'); label.textContent = row.label; link.append(label);
      const pos = normalize(row.text).indexOf(term); const start = Math.max(0, pos - 55); const snippet = (start ? '…' : '') + row.text.slice(start, start + 190) + (row.text.length > start + 190 ? '…' : '');
      const p = document.createElement('span'); const matchAt = normalize(snippet).indexOf(term);
      if (matchAt >= 0) { p.append(document.createTextNode(snippet.slice(0, matchAt))); const mark = document.createElement('mark'); mark.textContent = snippet.slice(matchAt, matchAt + term.length); p.append(mark, document.createTextNode(snippet.slice(matchAt + term.length))); } else { p.textContent = snippet; }
      link.append(p); fragment.append(link);
    });
    shown = Math.min(matches.length, shown + 20); $('#search-results').append(fragment); $('#more-results').hidden = shown >= matches.length;
  }
  function search() { term = normalize($('#query').value); $('#search-results').replaceChildren(); shown = 0; $('#more-results').hidden = true; if (!term) { $('#search-status').textContent = ''; return; } index ||= makeIndex(); matches = index.filter(row => normalize(row.text).includes(term)); $('#search-status').textContent = matches.length ? `找到 ${matches.length} 处匹配 · 点击跳到原句` : '没有找到匹配，试试更短的关键词。'; appendResults(); }
  $('#query').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(search, 160); });
  $('#search-form').addEventListener('submit', e => { e.preventDefault(); clearTimeout(timer); search(); });
  $('#clear-search').addEventListener('click', () => { clearTimeout(timer); $('#query').value = ''; search(); $('#query').focus(); });
  $('#more-results').addEventListener('click', appendResults);
  $$('.copy-lesson').forEach(button => button.addEventListener('click', async () => {
    const article = document.getElementById('day-' + button.dataset.day.padStart(2, '0')); const details = article.querySelector('details'); details.open = true;
    const text = 'Day ' + button.dataset.day + ' · ' + article.querySelector('h2').textContent + '\n\n' + article.querySelector('.lesson-body').innerText;
    try { await navigator.clipboard.writeText(text); notify('已复制本课完整正文'); } catch (_) { const range = document.createRange(); range.selectNodeContents(article.querySelector('.lesson-body')); const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range); notify('已选中本课正文，请使用浏览器的复制功能'); }
  }));
  let speaking = false;
  $('#speak').addEventListener('click', () => {
    if (!('speechSynthesis' in window)) { notify('当前浏览器不支持朗读'); return; }
    if (speaking) { speechSynthesis.cancel(); speaking = false; $('#speak').textContent = '朗读选中英文'; return; }
    const text = getSelection().toString().trim(); if (!text) { notify('先选中一句英文，再点击朗读'); return; }
    const utterance = new SpeechSynthesisUtterance(text.slice(0, 2500)); utterance.lang = 'en-SG'; utterance.rate = .9;
    utterance.voice = speechSynthesis.getVoices().find(v => v.lang === 'en-SG') || speechSynthesis.getVoices().find(v => /^en[-_]GB/i.test(v.lang)) || speechSynthesis.getVoices().find(v => /^en/i.test(v.lang)) || null;
    utterance.onend = utterance.onerror = () => { speaking = false; $('#speak').textContent = '朗读选中英文'; };
    speaking = true; $('#speak').textContent = '停止朗读'; speechSynthesis.speak(utterance);
  });
  let printStates = [];
  addEventListener('beforeprint', () => { printStates = $$('details').map(el => [el, el.open]); printStates.forEach(([el]) => { el.open = true; }); });
  addEventListener('afterprint', () => printStates.forEach(([el, open]) => { el.open = open; }));
  $('#print').addEventListener('click', () => window.print());
  // Download stays self-contained: page content, styles and interactions are embedded.
  $('#download-html').addEventListener('click', event => {
    if (location.protocol !== 'file:') return;
    event.preventDefault(); const blob = new Blob(['<!doctype html>\n' + document.documentElement.outerHTML], {type: 'text/html;charset=utf-8'}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = event.currentTarget.download; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
