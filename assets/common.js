/* Bendros funkcijos visiems puslapiams: formatavimas, elementų kūrimas, duomenų įkėlimas. */
window.HS = (() => {
  'use strict';

  const LANG = { lt: 'Lietuvių', en: 'Anglų', ru: 'Rusų', uk: 'Ukrainiečių' };
  const MONTHS = ['sausio', 'vasario', 'kovo', 'balandžio', 'gegužės', 'birželio', 'liepos', 'rugpjūčio', 'rugsėjo', 'spalio', 'lapkričio', 'gruodžio'];

  const norm = (s) => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

  function fmtDuration(sec) {
    if (!sec) return '';
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    if (h) return `${h} val. ${m} min.`;
    return `${m} min.`;
  }

  function fmtClock(sec) {
    if (sec === null || sec === undefined) return '';
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

  function plural(n, one, few, many) {
    if (n % 10 === 1 && n % 100 !== 11) return one;
    if (n % 10 === 0 || (n % 100 >= 11 && n % 100 <= 19)) return many;
    return few;
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

  function getJSON(url) {
    return fetch(url, { cache: 'no-cache' }).then((r) => {
      if (!r.ok) throw new Error(`${url}: ${r.status}`);
      return r.json();
    });
  }

  function embedUrl(id, start, autoplay) {
    const p = new URLSearchParams({ rel: '0' });
    if (start) p.set('start', String(start));
    if (autoplay) p.set('autoplay', '1');
    return `https://www.youtube-nocookie.com/embed/${id}?${p}`;
  }

  const PLAY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>';

  /* YouTube miniatiūra; privatiems video grąžinamas pilkas 120×90 paveikslėlis */
  function thumb(id, onMissing) {
    const img = el('img', {
      src: `https://i.ytimg.com/vi/${id}/hqdefault.jpg`,
      alt: '', loading: 'lazy', decoding: 'async', width: 480, height: 360,
    });
    const missing = () => { img.remove(); onMissing(); };
    img.addEventListener('error', missing, { once: true });
    img.addEventListener('load', () => { if (img.naturalWidth <= 120) missing(); }, { once: true });
    return img;
  }

  return { LANG, norm, fmtDuration, fmtClock, fmtDate, plural, el, getJSON, embedUrl, thumb, PLAY_ICON };
})();
