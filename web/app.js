(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const pad = n => String(n).padStart(2, '0');
  const localDate = (d = new Date()) => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  const SITE = location.origin + location.pathname;

  // Yesterday/today/tomorrow (UTC) from the build; we show whichever matches the visitor's local date.
  const days = JSON.parse($('days').textContent);
  let today = null;

  /* ---------- Toast + share ---------- */
  let toastTimer;
  function toast(msg) {
    const t = $('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 1800);
  }
  async function share(url, title) {
    if (navigator.share) {
      try { await navigator.share({ title, url }); } catch { /* cancelled */ }
      return;
    }
    try { await navigator.clipboard.writeText(url); toast('Link copied'); }
    catch { prompt('Copy this link:', url); }
  }
  $('share-today').addEventListener('click', () => share(SITE, 'Wordle word of the day'));

  /* ---------- Theme toggle ---------- */
  const themeBtn = $('theme');
  const darkMq = matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => (document.documentElement.dataset.theme || (darkMq.matches ? 'dark' : 'light')) === 'dark';
  const syncTheme = () => {
    themeBtn.textContent = isDark() ? '☀️' : '\u{1F319}';
    themeBtn.title = isDark() ? 'Switch to light mode' : 'Switch to dark mode';
    document.querySelectorAll('meta[name=theme-color]').forEach(m => m.content = isDark() ? '#121212' : '#ffffff');
  };
  themeBtn.addEventListener('click', () => {
    const next = isDark() ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('theme', next);
    syncTheme();
  });
  darkMq.addEventListener('change', syncTheme);
  syncTheme();

  /* ---------- Today's word (local date) ---------- */
  const tiles = $('tiles');
  function setRevealed(show) {
    tiles.classList.toggle('hidden', !show);
    $('root').classList.toggle('revealed', show);
    tiles.title = show ? 'Click to hide' : 'Click to reveal';
    $('hint').textContent = show ? 'Click the tiles to hide it again.' : 'Spoiler. Click the tiles to reveal.';
  }
  const toggleReveal = () => setRevealed(tiles.classList.contains('hidden'));
  tiles.addEventListener('click', toggleReveal);
  tiles.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleReveal(); } });

  function pickToday() {
    const ld = localDate();
    return days.find(d => d.date === ld) || days.filter(d => d.date <= ld).pop() || days[0];
  }
  function renderToday() {
    const pick = pickToday();
    if (today && today.date === pick.date) return false;
    today = pick;
    document.body.dataset.today = pick.date;
    $('today-title').textContent = 'Wordle #' + pick.number + ' · ' + pick.date;
    tiles.innerHTML = '';
    for (const c of pick.solution.toUpperCase()) {
      const t = document.createElement('div');
      t.className = 'tile';
      t.textContent = c;
      tiles.appendChild(t);
    }
    $('editor').textContent = 'Edited by ' + (pick.editor || 'unknown');
    $('definition').textContent = pick.definition || 'No definition found.';
    setRevealed(false);
    return true;
  }

  /* ---------- Countdown to local midnight ---------- */
  function tickCountdown() {
    const now = new Date();
    const midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
    const s = Math.max(0, Math.floor((midnight - now) / 1000));
    const stale = localDate(now) > today.date;
    $('countdown').textContent = stale
      ? 'Today’s word isn’t published here yet. Check back shortly.'
      : 'Next word in ' + Math.floor(s / 3600) + 'h ' + pad(Math.floor(s / 60) % 60) + 'm ' + pad(s % 60) + 's';
    if (renderToday()) applyCutoff();
  }

  /* ---------- Definitions ---------- */
  async function lookup(word) {
    const res = await fetch('https://api.dictionaryapi.dev/api/v2/entries/en/' + word.toLowerCase());
    if (!res.ok) throw new Error('not found');
    const data = await res.json();
    return data[0].meanings.map(m =>
      m.partOfSpeech + '\n' + m.definitions.slice(0, 3).map(d => '  • ' + d.definition).join('\n')
    ).join('\n');
  }

  /* ---------- Archive ---------- */
  const body = $('archive');
  const rows = Array.from(body.querySelectorAll('tr'));
  const search = $('search');
  const blurBox = $('blur');
  const jump = $('jump');
  let eligible = [];

  const closeDefs = () => body.querySelectorAll('tr.def').forEach(r => r.remove());

  // Hide every row on/after the visitor's local today, then (re)mark repeated answers among what's left.
  function applyCutoff() {
    rows.forEach(r => r.classList.toggle('future', r.dataset.d >= today.date));
    eligible = rows.filter(r => !r.classList.contains('future'));
    const seen = {};
    eligible.forEach(r => (seen[r.dataset.w] = seen[r.dataset.w] || []).push(r.dataset.d));
    eligible.forEach(r => {
      const cell = r.children[1];
      const old = cell.querySelector('.rep');
      if (old) old.remove();
      const dates = seen[r.dataset.w];
      if (dates.length > 1) {
        const span = document.createElement('span');
        span.className = 'rep';
        span.textContent = '↻×' + dates.length;
        span.title = 'Also the answer on ' + dates.filter(d => d !== r.dataset.d).join(', ');
        cell.appendChild(span);
      }
    });
    const y = new Date(today.date + 'T00:00:00');
    y.setDate(y.getDate() - 1);
    jump.max = localDate(y);
    filter();
  }

  function filter() {
    const q = search.value.trim().toLowerCase();
    const blurred = blurBox.checked;
    let n = 0;
    closeDefs();
    eligible.forEach(r => {
      // While answers are hidden, only match on number/date so searching can't leak them.
      const hay = r.dataset.k + (blurred ? '' : ' ' + r.dataset.w);
      const hit = !q || hay.includes(q);
      r.hidden = !hit;
      if (hit) n++;
    });
    $('count').textContent = n + ' of ' + eligible.length + ' words';
  }
  search.addEventListener('input', filter);

  blurBox.checked = localStorage.getItem('blur') === '1';
  blurBox.addEventListener('change', () => {
    $('scroller').classList.toggle('blur', blurBox.checked);
    body.querySelectorAll('td.word.shown').forEach(c => c.classList.remove('shown'));
    localStorage.setItem('blur', blurBox.checked ? '1' : '0');
    filter();
  });
  $('scroller').classList.toggle('blur', blurBox.checked);

  async function toggleDef(row, forceOpen) {
    const next = row.nextElementSibling;
    if (next && next.classList.contains('def')) {
      if (!forceOpen) next.remove();
      return;
    }
    const defRow = document.createElement('tr');
    defRow.className = 'def';
    const td = document.createElement('td');
    td.colSpan = 3;
    const text = document.createElement('div');
    text.className = 'def-text';
    text.textContent = 'Loading…';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'small-btn';
    btn.textContent = 'Share link to this day';
    btn.addEventListener('click', () => share(SITE + '#' + row.dataset.d, 'Wordle #' + row.dataset.n + ' (' + row.dataset.d + ')'));
    td.append(text, btn);
    defRow.appendChild(td);
    row.after(defRow);
    try { text.textContent = await lookup(row.dataset.w); }
    catch { text.textContent = 'No definition found.'; }
  }

  body.addEventListener('click', e => {
    const cell = e.target.closest('td.word');
    if (!cell) return;
    if (blurBox.checked && !cell.classList.contains('shown')) { cell.classList.add('shown'); return; }
    toggleDef(cell.parentElement);
  });

  /* ---------- Permalinks + jump to date ---------- */
  function openFromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (!/^\d{4}-\d{2}-\d{2}$/.test(h)) return;
    // Today or later (for this visitor) would be a spoiler: just go to the top.
    if (h >= today.date) { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    const row = document.getElementById('d-' + h);
    if (!row) { toast('No word for ' + h); return; }
    if (search.value) { search.value = ''; filter(); }
    body.querySelectorAll('tr.target').forEach(r => r.classList.remove('target'));
    row.classList.add('target');
    row.querySelector('td.word').classList.add('shown');
    toggleDef(row, true);
    const scroller = $('scroller');
    scroller.scrollTop = row.offsetTop - scroller.clientHeight / 2;
    $('archive-title').scrollIntoView({ behavior: 'smooth' });
  }
  window.addEventListener('hashchange', openFromHash);
  jump.addEventListener('change', () => {
    if (!jump.value) return;
    if (location.hash === '#' + jump.value) openFromHash();
    else location.hash = jump.value;
  });

  /* ---------- Practice a random past word ---------- */
  const dlg = $('practice');
  const score = Object.assign({ solved: 0, hints: 0, streak: 0, best: 0 },
    JSON.parse(localStorage.getItem('practice') || '{}'));
  let cur = null, hints = 0, done = false, attempted = false;

  function showScore() {
    localStorage.setItem('practice', JSON.stringify(score));
    $('p-score').textContent = 'Solved ' + score.solved + ' · streak ' + score.streak +
      ' (best ' + score.best + ') · hints used ' + score.hints;
  }
  function drawTiles(show) {
    $('p-tiles').innerHTML = '';
    [...cur.word].forEach((c, i) => {
      const t = document.createElement('div');
      const visible = show || i < hints;
      t.className = 'tile' + (visible ? '' : ' hidden');
      t.textContent = visible ? c : '';
      $('p-tiles').appendChild(t);
    });
  }
  function newWord() {
    if (cur && !done && attempted) { score.streak = 0; showScore(); }
    const r = eligible[Math.floor(Math.random() * eligible.length)];
    cur = { date: r.dataset.d, number: r.dataset.n, word: r.dataset.w.toUpperCase() };
    hints = 0; done = false; attempted = false;
    $('p-title').innerHTML = '';
    $('p-title').append('Wordle #' + cur.number + ' · ');
    const a = document.createElement('a');
    a.href = '#' + cur.date; a.textContent = cur.date;
    a.addEventListener('click', () => dlg.close());
    $('p-title').append(a);
    $('p-msg').textContent = 'Guess the answer from this day.';
    $('p-def').textContent = '';
    $('p-guess').value = '';
    drawTiles(false);
    $('p-guess').focus();
  }
  async function finish(msg, solved) {
    done = true;
    if (solved) {
      score.solved++; score.streak++; score.hints += hints;
      score.best = Math.max(score.best, score.streak);
    } else {
      score.streak = 0;
    }
    showScore();
    drawTiles(true);
    $('p-msg').textContent = msg;
    $('p-def').textContent = 'Loading definition…';
    const word = cur.word;
    try { const d = await lookup(word); if (cur.word === word) $('p-def').textContent = d; }
    catch { if (cur.word === word) $('p-def').textContent = 'No definition found.'; }
  }
  function openPractice() {
    if (!dlg.open) dlg.showModal();
    newWord();
  }
  $('random').addEventListener('click', openPractice);
  $('p-next').addEventListener('click', newWord);
  $('p-reveal').addEventListener('click', () => { if (!done) finish('The answer was ' + cur.word + '.', false); });
  $('p-hint').addEventListener('click', () => {
    if (done) return;
    attempted = true;
    hints = Math.min(hints + 1, 4);
    drawTiles(false);
    $('p-msg').textContent = hints === 4 ? 'Only one letter left!' : 'Revealed ' + hints + ' letter' + (hints > 1 ? 's' : '') + '.';
  });
  $('p-form').addEventListener('submit', e => {
    e.preventDefault();
    if (done) return newWord();
    const g = $('p-guess').value.trim().toUpperCase();
    if (g.length !== 5) { $('p-msg').textContent = 'Guesses are five letters.'; return; }
    attempted = true;
    if (g === cur.word) finish('Correct! ' + (hints ? 'With ' + hints + ' hint' + (hints > 1 ? 's' : '') + '.' : 'No hints needed.'), true);
    else { $('p-msg').textContent = g + ' isn’t it. Try again, or take a hint.'; $('p-guess').select(); }
  });
  showScore();

  /* ---------- Keyboard shortcuts ---------- */
  document.addEventListener('keydown', e => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.target.closest('input, textarea, select, button, [contenteditable], #tiles') || dlg.open) return;
    switch (e.key) {
      case '/': e.preventDefault(); search.focus(); search.select(); break;
      case ' ': e.preventDefault(); toggleReveal(); break;
      case 'r': case 'R': e.preventDefault(); openPractice(); break;
      case 't': case 'T': themeBtn.click(); break;
      case 'd': case 'D':
        e.preventDefault();
        jump.focus();
        try { jump.showPicker(); } catch { /* not supported */ }
        break;
    }
  });

  /* ---------- Start ---------- */
  renderToday();
  applyCutoff();
  openFromHash();
  tickCountdown();
  setInterval(tickCountdown, 1000);

  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    navigator.serviceWorker.register('sw.js');
  }
})();
