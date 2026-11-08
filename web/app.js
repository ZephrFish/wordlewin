(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const today = document.body.dataset.today;

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

  /* ---------- Today's reveal ---------- */
  const tiles = $('tiles');
  const reveal = () => {
    const show = tiles.classList.toggle('hidden') === false;
    $('root').classList.toggle('revealed', show);
    tiles.title = show ? 'Click to hide' : 'Click to reveal';
    $('hint').textContent = show ? 'Click the tiles to hide it again.' : 'Spoiler. Click the tiles to reveal.';
  };
  tiles.addEventListener('click', reveal);
  tiles.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); reveal(); } });

  /* ---------- Definitions ---------- */
  async function lookup(word) {
    const res = await fetch('https://api.dictionaryapi.dev/api/v2/entries/en/' + word.toLowerCase());
    if (!res.ok) throw new Error('not found');
    const data = await res.json();
    return data[0].meanings.map(m =>
      m.partOfSpeech + '\n' + m.definitions.slice(0, 3).map(d => '  • ' + d.definition).join('\n')
    ).join('\n');
  }

  /* ---------- Archive: search, blur, definitions ---------- */
  const body = $('archive');
  const rows = Array.from(body.querySelectorAll('tr'));
  const count = $('count');
  const search = $('search');
  const blurBox = $('blur');
  const showCount = n => count.textContent = n + ' of ' + rows.length + ' words';

  const closeDefs = () => body.querySelectorAll('tr.def').forEach(r => r.remove());

  function filter() {
    const q = search.value.trim().toLowerCase();
    const blurred = blurBox.checked;
    let n = 0;
    closeDefs();
    rows.forEach(r => {
      // While answers are hidden, only match on number/date so searching can't leak them.
      const hay = r.dataset.k + (blurred ? '' : ' ' + r.dataset.w);
      const hit = !q || hay.includes(q);
      r.hidden = !hit;
      if (hit) n++;
    });
    showCount(n);
  }
  search.addEventListener('input', filter);

  blurBox.checked = localStorage.getItem('blur') === '1';
  const applyBlur = () => {
    body.parentElement.parentElement.classList.toggle('blur', blurBox.checked);
    body.querySelectorAll('td.word.shown').forEach(c => c.classList.remove('shown'));
    localStorage.setItem('blur', blurBox.checked ? '1' : '0');
    filter();
  };
  blurBox.addEventListener('change', applyBlur);
  applyBlur();

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
    td.textContent = 'Loading…';
    defRow.appendChild(td);
    row.after(defRow);
    try { td.textContent = await lookup(row.dataset.w); }
    catch { td.textContent = 'No definition found.'; }
  }

  body.addEventListener('click', e => {
    const cell = e.target.closest('td.word');
    if (!cell) return;
    if (blurBox.checked && !cell.classList.contains('shown')) { cell.classList.add('shown'); return; }
    toggleDef(cell.parentElement);
  });

  /* ---------- Permalinks: #YYYY-MM-DD ---------- */
  function openFromHash() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (!/^\d{4}-\d{2}-\d{2}$/.test(h)) return;
    if (h === today) { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    const row = document.getElementById('d-' + h);
    if (!row) return;
    if (search.value) { search.value = ''; filter(); }
    body.querySelectorAll('tr.target').forEach(r => r.classList.remove('target'));
    row.classList.add('target');
    row.querySelector('td.word').classList.add('shown');
    toggleDef(row, true);
    // Scroll the archive box to the row, then bring the box into view.
    const scroller = $('scroller');
    scroller.scrollTop = row.offsetTop - scroller.clientHeight / 2;
    $('archive-title').scrollIntoView({ behavior: 'smooth' });
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  /* ---------- Practice a random past word ---------- */
  const dlg = $('practice');
  const past = rows.map(r => ({ date: r.dataset.d, number: r.dataset.n, word: r.dataset.w.toUpperCase() }));
  let cur = null, hints = 0, done = false;

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
    cur = past[Math.floor(Math.random() * past.length)];
    hints = 0; done = false;
    $('p-title').innerHTML = '';
    $('p-title').append('Wordle #' + cur.number + ' · ');
    const a = document.createElement('a');
    a.href = '#' + cur.date; a.textContent = cur.date;
    a.addEventListener('click', () => dlg.close());
    $('p-title').append(a);
    $('p-msg').textContent = 'Guess the answer from this day.';
    $('p-guess').value = '';
    drawTiles(false);
    $('p-guess').focus();
  }
  function finish(msg) {
    done = true;
    drawTiles(true);
    $('p-msg').textContent = msg;
  }
  $('random').addEventListener('click', () => { dlg.showModal(); newWord(); });
  $('p-next').addEventListener('click', newWord);
  $('p-reveal').addEventListener('click', () => finish('The answer was ' + cur.word + '.'));
  $('p-hint').addEventListener('click', () => {
    if (done) return;
    hints = Math.min(hints + 1, 4);
    drawTiles(false);
    $('p-msg').textContent = hints === 4 ? 'Only one letter left!' : 'Revealed ' + hints + ' letter' + (hints > 1 ? 's' : '') + '.';
  });
  $('p-form').addEventListener('submit', e => {
    e.preventDefault();
    if (done) return newWord();
    const g = $('p-guess').value.trim().toUpperCase();
    if (g.length !== 5) { $('p-msg').textContent = 'Guesses are five letters.'; return; }
    if (g === cur.word) finish('Correct! ' + (hints ? 'With ' + hints + ' hint' + (hints > 1 ? 's' : '') + '.' : 'No hints needed.'));
    else { $('p-msg').textContent = g + ' isn’t it. Try again, or take a hint.'; $('p-guess').select(); }
  });

  /* ---------- Offline / installable ---------- */
  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    navigator.serviceWorker.register('sw.js');
  }
})();
