(() => {
  'use strict';

  const { LANG, fmtClock, el, getJSON } = window.HS;

  const root = document.getElementById('page');
  const id = new URLSearchParams(location.search).get('id');

  const NOTICE = 'Gidas sudarytas iš pranešimų konspektų ir autoriaus dar neperžiūrėtas. '
    + 'Tai edukacinė santrauka, ne klinikinės gairės: prieš taikydami skaičius sutikrinkite įraše ir galiojančiose gairėse.';

  function fail(text) {
    document.title = 'Gidas nerastas — hemo.science';
    root.replaceChildren(el('div', { class: 'empty' }, [
      el('p', { text }),
      el('a', { class: 'link-btn', href: './#gidai', text: 'Grįžti į gidų sąrašą' }),
    ]));
  }

  function source(s) {
    const page = `pranesimas.html?nr=${s.nr}`;
    return el('li', { class: 'src' }, [
      el('div', { class: 'src-head' }, [
        el('span', { class: 'src-nr', text: s.nr }),
        el('a', { href: page, text: s.title }),
      ]),
      el('p', { class: 'src-meta', text: [s.year, s.lang && `${LANG[s.lang]} k.`, s.youtube ? null : 'įrašas dar neskelbiamas'].filter(Boolean).join(' · ') }),
      s.sections.length ? el('ul', { class: 'src-secs' }, s.sections.map((x) => el('li', {}, el('a', {
        href: x.start !== null ? `${page}&t=${x.start}` : page,
      }, [x.start !== null ? el('span', { class: 'time', text: fmtClock(x.start) }) : null, document.createTextNode(x.title)])))) : null,
    ]);
  }

  function render(g) {
    document.title = `${g.title} — hemo.science`;
    const cited = g.sources.filter((s) => s.cited);
    const more = g.sources.filter((s) => !s.cited);

    const head = el('header', { class: 'page-head' }, [
      el('p', { class: 'eyebrow', text: 'Gidas' }),
      el('h1', { class: 'page-title', text: g.title }),
      el('p', { class: 'lead', text: g.lead }),
    ]);

    const main = el('div', { class: 'page-main' }, [
      g.reviewed ? null : el('aside', { class: 'notice', text: NOTICE }),
      el('p', { class: 'ref-help' }, [
        document.createTextNode('Nuorodos '),
        el('span', { class: 'ref ref-demo', text: '14 · 11:53' }),
        document.createTextNode(' veda į pranešimą Nr. 14 ir atidaro įrašą nuo 11:53.'),
      ]),
      el('article', { class: 'guide-body', html: g.html }),
      el('section', { class: 'sources', id: 'saltiniai', 'aria-labelledby': 'saltiniai-h' }, [
        el('h2', { id: 'saltiniai-h', text: 'Kur apie tai kalbama' }),
        el('ol', { class: 'src-list' }, cited.map(source)),
        more.length ? el('h3', { text: 'Taip pat minima' }) : null,
        more.length ? el('ol', { class: 'src-list' }, more.map(source)) : null,
      ]),
    ]);

    const toc = el('nav', { class: 'toc', 'aria-label': 'Gido turinys' }, [
      el('h2', { text: 'Turinys' }),
      el('ol', { class: 'toc-list' }, [
        ...g.toc.map((t) => el('li', {}, el('a', { href: `#${t.id}`, text: t.title }))),
        el('li', {}, el('a', { href: '#saltiniai', text: 'Kur apie tai kalbama' })),
      ]),
    ]);

    root.replaceChildren(head, el('div', { class: 'page-grid' }, [main, el('aside', { class: 'page-side' }, toc)]));
    if (location.hash) document.querySelector(location.hash)?.scrollIntoView();
  }

  if (!id) { fail('Gidas nenurodytas.'); return; }

  getJSON('data/gidai.json')
    .then((guides) => {
      const g = guides.find((x) => x.id === id);
      if (g) render(g); else fail('Tokio gido nėra.');
    })
    .catch(() => fail('Nepavyko įkelti gido. Pabandykite perkrauti puslapį.'));
})();
