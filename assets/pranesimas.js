(() => {
  'use strict';

  const { LANG, fmtDuration, fmtClock, fmtDate, el, getJSON, embedUrl, thumb, PLAY_ICON } = window.HS;

  const root = document.getElementById('page');
  const params = new URLSearchParams(location.search);
  const nr = Number(params.get('nr'));
  const startAt = Number(params.get('t')) || 0;

  const NOTICE = 'Konspektas parengtas pagal pranešimo įrašą ir autoriaus dar neperžiūrėtas. '
    + 'Skaičius ir rekomendacijas sutikrinkite įraše ir galiojančiose gairėse.';

  function fail(text) {
    document.title = 'Pranešimas nerastas — hemo.science';
    root.replaceChildren(el('div', { class: 'empty' }, [
      el('p', { text }),
      el('a', { class: 'link-btn', href: './#sarasas', text: 'Grįžti į pranešimų sąrašą' }),
    ]));
  }

  /* Vaizdo įrašas: iš pradžių miniatiūra, iframe įkeliamas paspaudus arba atėjus su ?t= */
  function makeVideo(item) {
    const box = el('div', { class: 'video', id: 'video' });
    if (!item.youtube) {
      box.classList.add('video-none');
      box.append(el('p', { text: 'Šio pranešimo vaizdo įrašas dar neskelbiamas.' }));
      return { box, play: null };
    }
    const play = (t, autoplay = true) => {
      box.replaceChildren(el('iframe', {
        src: embedUrl(item.youtube, t, autoplay), title: item.title,
        allow: 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture',
        allowfullscreen: true,
      }));
      const u = new URL(location.href);
      if (t) u.searchParams.set('t', t); else u.searchParams.delete('t');
      history.replaceState(null, '', u);
    };
    const poster = el('button', { type: 'button', class: 'thumb', 'aria-label': `Žiūrėti: ${item.title}`, onclick: () => play(startAt) }, [
      el('span', { class: 'play', html: PLAY_ICON }),
      startAt ? el('span', { class: 'dur', text: `nuo ${fmtClock(startAt)}` }) : null,
    ]);
    poster.prepend(thumb(item.youtube, () => poster.classList.add('no-img')));
    box.append(poster);
    if (startAt) play(startAt, false);
    return { box, play };
  }

  function timeButton(sec, play, label) {
    if (sec === null || sec === undefined) return null;
    if (!play) return el('span', { class: 'time time-off', text: fmtClock(sec) });
    return el('button', {
      type: 'button', class: 'time', 'aria-label': `Žiūrėti nuo ${fmtClock(sec)}${label ? `: ${label}` : ''}`,
      onclick: () => {
        play(sec);
        document.getElementById('video').scrollIntoView({ behavior: 'smooth', block: 'start' });
      },
    }, [el('span', { class: 'time-icon', html: PLAY_ICON }), document.createTextNode(fmtClock(sec))]);
  }

  const plain = (html) => { const d = document.createElement('div'); d.innerHTML = html; return d.textContent; };

  function renderKonspektas(k, play) {
    const parts = [];
    if (!k.reviewed) parts.push(el('aside', { class: 'notice', text: NOTICE }));

    if (k.summary.length) {
      parts.push(el('section', { class: 'k-block', 'aria-labelledby': 'apie-h' }, [
        el('h2', { id: 'apie-h', text: 'Apie ką pranešimas' }),
        ...k.summary.map((p) => el('p', { class: 'k-summary', html: p })),
      ]));
    }

    if (k.sections.length) {
      const list = [];
      let part = null;
      k.sections.forEach((s, i) => {
        if (s.part && s.part !== part) {
          part = s.part;
          list.push(el('h3', { class: 'k-part', text: part }));
        }
        list.push(el('article', { class: 'k-sec', id: `d${i + 1}` }, [
          el('div', { class: 'k-sec-head' }, [
            el('h3', { html: s.title }),
            timeButton(s.start, play, plain(s.title)),
          ]),
          s.bullets.length ? el('ul', {}, s.bullets.map((b) => el('li', { html: b }))) : null,
        ]));
      });
      parts.push(el('section', { class: 'k-block', 'aria-labelledby': 'mintys-h' }, [
        el('h2', { id: 'mintys-h', text: 'Pagrindinės mintys' }), ...list,
      ]));
    }

    if (k.takeaways.length) {
      parts.push(el('section', { class: 'k-block takeaways', id: 'isvados', 'aria-labelledby': 'isvados-h' }, [
        el('h2', { id: 'isvados-h', text: 'Praktinės išvados' }),
        el('ol', {}, k.takeaways.map((t) => el('li', { html: t }))),
      ]));
    }

    if (k.table && k.table.rows.length) {
      parts.push(el('section', { class: 'k-block', id: 'ribos', 'aria-labelledby': 'ribos-h' }, [
        el('h2', { id: 'ribos-h', text: 'Rodmenys ir ribos' }),
        el('div', { class: 'table-wrap' }, el('table', {}, [
          el('thead', {}, el('tr', {}, k.table.head.map((h) => el('th', { scope: 'col', html: h })))),
          el('tbody', {}, k.table.rows.map((r) => el('tr', {}, r.map((c) => el('td', { html: c }))))),
        ])),
      ]));
    }
    return parts;
  }

  function renderToc(k, play) {
    const items = [];
    let part = null;
    k.sections.forEach((s, i) => {
      if (s.part && s.part !== part) {
        part = s.part;
        items.push(el('li', { class: 'toc-part', text: part }));
      }
      items.push(el('li', {}, [
        el('a', { href: `#d${i + 1}`, html: s.title }),
        timeButton(s.start, play, plain(s.title)),
      ]));
    });
    const extra = [];
    if (k.takeaways.length) extra.push(el('li', {}, el('a', { href: '#isvados', text: 'Praktinės išvados' })));
    if (k.table && k.table.rows.length) extra.push(el('li', {}, el('a', { href: '#ribos', text: 'Rodmenys ir ribos' })));
    return el('nav', { class: 'toc', 'aria-label': 'Pranešimo turinys' }, [
      el('h2', { text: 'Turinys' }),
      el('ol', { class: 'toc-list' }, items),
      extra.length ? el('ul', { class: 'toc-extra' }, extra) : null,
    ]);
  }

  function renderGuides(guides) {
    const mine = guides.filter((g) => g.nrs.includes(nr));
    if (!mine.length) return null;
    return el('div', { class: 'side-guides' }, [
      el('h2', { text: 'Susiję gidai' }),
      el('ul', {}, mine.map((g) => el('li', {}, el('a', { href: `gidas.html?id=${g.id}`, text: g.title })))),
    ]);
  }

  function render(item, k, guides) {
    document.title = `${item.title} — hemo.science`;
    const { box, play } = makeVideo(item);
    const meta = [
      fmtDate(item), fmtDuration(item.duration), item.lang && `${LANG[item.lang]} k.`,
      item.slides && item.slides !== LANG[item.lang]
        ? (item.slides.startsWith('Įvairios') ? 'skaidrės įvairiomis kalbomis' : `skaidrės: ${item.slides.toLowerCase()} k.`)
        : null,
      item.conference ? 'keli pranešėjai' : null,
    ].filter(Boolean);

    const head = el('header', { class: 'page-head' }, [
      el('p', { class: 'eyebrow', text: item.category }),
      el('h1', { class: 'page-title', text: item.title }),
      el('p', { class: 'page-meta', text: meta.join(' · ') }),
    ]);

    const main = el('div', { class: 'page-main' }, [box]);
    const side = el('aside', { class: 'page-side' });

    if (k) {
      main.append(...renderKonspektas(k, play));
      if (k.sections.length) side.append(renderToc(k, play));
    } else {
      main.append(el('p', { class: 'notice', text: 'Šio pranešimo konspektas dar ruošiamas.' }));
    }
    const g = renderGuides(guides);
    if (g) side.append(g);

    root.replaceChildren(head, el('div', { class: side.childElementCount ? 'page-grid' : 'page-grid single' }, [main, side]));
    if (location.hash) document.querySelector(location.hash)?.scrollIntoView();
  }

  if (!nr) { fail('Pranešimas nenurodytas.'); return; }

  Promise.all([
    getJSON('data/pranesimai.json'),
    getJSON(`data/konspektai/${nr}.json`).catch(() => null),
    getJSON('data/gidai-sarasas.json').catch(() => []),
  ]).then(([items, k, guides]) => {
    const item = items.find((x) => x.id === nr);
    if (!item) { fail('Tokio pranešimo nėra.'); return; }
    render(item, k, guides);
  }).catch(() => fail('Nepavyko įkelti pranešimo. Pabandykite perkrauti puslapį.'));
})();
