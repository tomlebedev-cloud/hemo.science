(() => {
  'use strict';

  const { LANG, norm, fmtDuration, fmtClock, fmtDate, plural, el, getJSON, embedUrl, thumb, PLAY_ICON } = window.HS;

  const $ = (id) => document.getElementById(id);
  const els = {
    list: $('list'), chips: $('chips'), q: $('q'), lang: $('lang'), onlyVideo: $('only-video'),
    count: $('result-count'), empty: $('empty'), reset: $('reset'), guides: $('guides-list'),
    player: $('player'), playerTitle: $('player-title'), playerFrame: $('player-frame'),
    playerMeta: $('player-meta'), playerClose: $('player-close'),
  };

  const state = { items: [], category: '', q: '', lang: '', onlyVideo: false };

  const pageUrl = (item) => `pranesimas.html?nr=${item.id}`;

  function card(item) {
    const hasVideo = Boolean(item.youtube);
    const open = () => openPlayer(item);

    let media;
    if (hasVideo) {
      media = el('button', { type: 'button', class: 'thumb', 'aria-label': `Žiūrėti: ${item.title}`, onclick: open }, [
        el('span', { class: 'play', html: PLAY_ICON }),
        item.duration ? el('span', { class: 'dur', text: fmtClock(item.duration) }) : null,
      ]);
      media.prepend(thumb(item.youtube, () => media.classList.add('no-img')));
    } else {
      media = el('div', { class: 'placeholder' }, [
        el('span', {}, [
          el('span', { class: 'ph-cat', text: item.category }),
          document.createTextNode('Vaizdo įrašas ruošiamas'),
        ]),
        item.duration ? el('span', { class: 'dur', text: fmtClock(item.duration) }) : null,
      ]);
    }

    const title = el('h3', { class: 'card-title' }, el('a', { href: pageUrl(item), text: item.title }));

    const meta = el('div', { class: 'meta' }, [
      fmtDate(item) ? el('span', { text: fmtDate(item) }) : null,
      item.duration ? el('span', { text: fmtDuration(item.duration) }) : null,
      item.lang ? el('span', { class: 'lang-tag', title: `Skaitymo kalba: ${LANG[item.lang]}`, text: item.lang }) : null,
      item.conference ? el('span', { text: 'Keli pranešėjai' }) : null,
      item.konspektas ? el('a', { class: 'badge', href: pageUrl(item), text: 'Konspektas' }) : null,
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
    els.count.textContent = `${n} ${plural(n, 'pranešimas', 'pranešimai', 'pranešimų')}`;
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
    els.playerMeta.replaceChildren(
      document.createTextNode([fmtDate(item), fmtDuration(item.duration), item.lang && LANG[item.lang]].filter(Boolean).join(' · ')),
      el('a', { class: 'player-link', href: pageUrl(item), text: item.konspektas ? 'Konspektas ir turinys →' : 'Pranešimo puslapis →' }));
    els.playerFrame.replaceChildren(el('iframe', {
      src: embedUrl(item.youtube, 0, true),
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

  function renderGuides(guides) {
    els.guides.replaceChildren(...guides.map((g) => el('a', { class: 'guide-card', href: `gidas.html?id=${g.id}` }, [
      el('h3', { text: g.title }),
      el('p', { text: g.lead }),
      el('span', { class: 'guide-n', text: `${g.nrs.length} ${plural(g.nrs.length, 'pranešimas', 'pranešimai', 'pranešimų')}` }),
    ])));
  }

  getJSON('data/gidai-sarasas.json').then(renderGuides).catch(() => { els.guides.closest('section').hidden = true; });

  getJSON('data/pranesimai.json')
    .then((items) => { state.items = items; renderStats(); update(); })
    .catch(() => { els.list.replaceChildren(el('p', { class: 'empty', text: 'Nepavyko įkelti pranešimų sąrašo. Pabandykite perkrauti puslapį.' })); });
})();
