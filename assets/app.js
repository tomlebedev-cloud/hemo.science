(() => {
  'use strict';

  const LANG = { lt: 'Lietuvių', en: 'Anglų', ru: 'Rusų', uk: 'Ukrainiečių' };
  const MONTHS = ['sausio', 'vasario', 'kovo', 'balandžio', 'gegužės', 'birželio', 'liepos', 'rugpjūčio', 'rugsėjo', 'spalio', 'lapkričio', 'gruodžio'];

  const $ = (id) => document.getElementById(id);
  const els = {
    list: $('list'), chips: $('chips'), q: $('q'), lang: $('lang'), onlyVideo: $('only-video'),
    count: $('result-count'), empty: $('empty'), reset: $('reset'),
    player: $('player'), playerTitle: $('player-title'), playerFrame: $('player-frame'),
    playerMeta: $('player-meta'), playerClose: $('player-close'),
  };

  const state = { items: [], category: '', q: '', lang: '', onlyVideo: false };

  const norm = (s) => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

  function fmtDuration(sec) {
    if (!sec) return '';
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    if (h) return `${h} val. ${m} min.`;
    return `${m} min.`;
  }

  function fmtClock(sec) {
    if (!sec) return '';
    const h = Math.floor(sec / 3600);
    const m = String(Math.floor((sec % 3600) / 60)).padStart(h ? 2 : 1, '0');
    const s = String(sec % 60).padStart(2, '0');
    return h ? `${h}:${m}:${s}` : `${m}:${s}`;
  }

  function fmtDate(item) {
    if (item.date) {
      const [y, mo, d] = item.date.split('-').map(Number);
      return `${y} m. ${MONTHS[mo - 1]} ${d} d.`;
    }
    return item.year ? `${item.year} m.` : '';
  }

  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === undefined || v === null || v === false) continue;
      if (k === 'class') node.className = v;
      else if (k === 'text') node.textContent = v;
      else if (k === 'html') node.innerHTML = v;
      else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? '' : v);
    }
    for (const c of [].concat(children)) if (c) node.append(c);
    return node;
  }

  const PLAY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';

  function card(item) {
    const hasVideo = Boolean(item.youtube);
    const open = () => openPlayer(item);

    let media;
    if (hasVideo) {
      const img = el('img', {
        src: `https://i.ytimg.com/vi/${item.youtube}/hqdefault.jpg`,
        alt: '', loading: 'lazy', decoding: 'async', width: 480, height: 360,
      });
      media = el('button', { type: 'button', class: 'thumb', 'aria-label': `Žiūrėti: ${item.title}`, onclick: open }, [
        img,
        el('span', { class: 'play', html: PLAY_ICON }),
        item.duration ? el('span', { class: 'dur', text: fmtClock(item.duration) }) : null,
      ]);
      // privatiems video YouTube grąžina 404 su pilku 120×90 paveikslėliu
      const noImg = () => { img.remove(); media.classList.add('no-img'); };
      img.addEventListener('error', noImg, { once: true });
      img.addEventListener('load', () => { if (img.naturalWidth <= 120) noImg(); }, { once: true });
    } else {
      media = el('div', { class: 'placeholder' }, [
        el('span', {}, [
          el('span', { class: 'ph-cat', text: item.category }),
          document.createTextNode('Vaizdo įrašas ruošiamas'),
        ]),
        item.duration ? el('span', { class: 'dur', text: fmtClock(item.duration) }) : null,
      ]);
    }

    const title = el('h3', { class: 'card-title' },
      hasVideo ? el('button', { type: 'button', onclick: open, text: item.title }) : document.createTextNode(item.title));

    const meta = el('div', { class: 'meta' }, [
      fmtDate(item) ? el('span', { text: fmtDate(item) }) : null,
      item.duration ? el('span', { text: fmtDuration(item.duration) }) : null,
      item.lang ? el('span', { class: 'lang-tag', title: `Skaitymo kalba: ${LANG[item.lang]}`, text: item.lang }) : null,
      item.conference ? el('span', { text: 'Keli pranešėjai' }) : null,
    ]);

    return el('article', { class: 'card' }, [
      media,
      el('div', { class: 'card-body' }, [el('span', { class: 'card-cat', text: item.category }), title, meta]),
    ]);
  }

  function filtered() {
    const q = norm(state.q.trim());
    return state.items.filter((it) =>
      (!state.category || it.category === state.category) &&
      (!state.lang || it.lang === state.lang) &&
      (!state.onlyVideo || it.youtube) &&
      (!q || norm(`${it.title} ${it.category} ${it.year || ''}`).includes(q)));
  }

  function renderChips() {
    const counts = new Map();
    for (const it of state.items) counts.set(it.category, (counts.get(it.category) || 0) + 1);
    const cats = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], 'lt'));
    const make = (value, label, n) => el('button', {
      type: 'button', class: 'chip', 'aria-pressed': String(state.category === value),
      onclick: () => { state.category = state.category === value && value ? '' : value; update(); },
    }, [document.createTextNode(label), el('span', { class: 'n', text: n })]);
    els.chips.replaceChildren(make('', 'Visos temos', state.items.length), ...cats.map(([c, n]) => make(c, c, n)));
  }

  function render() {
    const items = filtered();
    const groups = new Map();
    for (const it of items) {
      const key = it.year || 'Data nenurodyta';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(it);
    }
    const frag = document.createDocumentFragment();
    for (const [year, list] of groups) {
      frag.append(el('section', { class: 'year', 'aria-label': String(year) }, [
        el('h3', { class: 'year-h', text: String(year) }),
        el('div', { class: 'year-grid' }, list.map(card)),
      ]));
    }
    els.list.replaceChildren(frag);
    els.empty.hidden = items.length > 0;
    const n = items.length;
    const word = n % 10 === 1 && n % 100 !== 11 ? 'pranešimas' : (n % 10 === 0 || (n % 100 >= 11 && n % 100 <= 19) ? 'pranešimų' : 'pranešimai');
    els.count.textContent = `${n} ${word}`;
  }

  function renderStats() {
    const set = (k, v) => { const d = document.querySelector(`[data-stat="${k}"]`); if (d) d.textContent = v; };
    set('count', state.items.length);
    set('hours', Math.round(state.items.reduce((s, it) => s + (it.duration || 0), 0) / 3600));
    set('topics', new Set(state.items.map((it) => it.category)).size);
    set('langs', new Set(state.items.map((it) => it.lang).filter(Boolean)).size);
  }

  function update() {
    renderChips();
    render();
    const p = new URLSearchParams();
    if (state.category) p.set('tema', state.category);
    if (state.lang) p.set('kalba', state.lang);
    if (state.q) p.set('q', state.q);
    if (state.onlyVideo) p.set('video', '1');
    const qs = p.toString();
    history.replaceState(null, '', qs ? `?${qs}${location.hash}` : location.pathname + location.hash);
  }

  function openPlayer(item) {
    els.playerTitle.textContent = item.title;
    els.playerMeta.textContent = [fmtDate(item), fmtDuration(item.duration), item.lang && LANG[item.lang]].filter(Boolean).join(' · ');
    els.playerFrame.replaceChildren(el('iframe', {
      src: `https://www.youtube-nocookie.com/embed/${item.youtube}?autoplay=1&rel=0`,
      title: item.title,
      allow: 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture',
      allowfullscreen: true,
    }));
    if (typeof els.player.showModal === 'function') els.player.showModal();
    else window.open(`https://youtu.be/${item.youtube}`, '_blank', 'noopener');
  }

  function closePlayer() {
    els.player.close();
  }

  els.player.addEventListener('close', () => els.playerFrame.replaceChildren());
  els.playerClose.addEventListener('click', closePlayer);
  els.player.addEventListener('click', (e) => { if (e.target === els.player) closePlayer(); });

  let t;
  els.q.addEventListener('input', () => { clearTimeout(t); t = setTimeout(() => { state.q = els.q.value; update(); }, 150); });
  els.lang.addEventListener('change', () => { state.lang = els.lang.value; update(); });
  els.onlyVideo.addEventListener('change', () => { state.onlyVideo = els.onlyVideo.checked; update(); });
  els.reset.addEventListener('click', () => {
    Object.assign(state, { category: '', q: '', lang: '', onlyVideo: false });
    els.q.value = ''; els.lang.value = ''; els.onlyVideo.checked = false;
    update();
  });

  const params = new URLSearchParams(location.search);
  state.category = params.get('tema') || '';
  state.lang = params.get('kalba') || '';
  state.q = params.get('q') || '';
  state.onlyVideo = params.get('video') === '1';
  els.q.value = state.q; els.lang.value = state.lang; els.onlyVideo.checked = state.onlyVideo;

  fetch('data/pranesimai.json', { cache: 'no-cache' })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((items) => { state.items = items; renderStats(); update(); })
    .catch(() => { els.list.replaceChildren(el('p', { class: 'empty', text: 'Nepavyko įkelti pranešimų sąrašo. Pabandykite perkrauti puslapį.' })); });
})();
