"""Konspektus (konspektavimas/*/konspektas.md) paverčia struktūrizuotais duomenimis puslapiui.

Rezultatas: data/konspektai/N.json – {summary, sections, takeaways, table, reviewed}
ir pranešimų sąraše (data/pranesimai.json) pažymima, kuris pranešimas turi konspektą.
Į viešus duomenis nepatenka vidinės skiltys („Ką dar pasitikrinti“, „Šaltiniai“)
ir citatos blokai (> …) su pastabomis sąrašui tvarkyti.

Konspektas laikomas autoriaus peržiūrėtu, jei jame yra eilutė „Peržiūrėta: taip“.

Paleidimas: python tools/build_konspektai.py
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'konspektavimas'
OUT = ROOT / 'data' / 'konspektai'
LIST = ROOT / 'data' / 'pranesimai.json'
SEARCH = ROOT / 'data' / 'paieska.json'

SKIP_SECTIONS = {'Ką dar pasitikrinti', 'Šaltiniai šiame aplanke'}
GROUP_RE = re.compile(r'^\*\*(.+?)\*\*\s*(?:\[([\d:]+)(?:[–-]([\d:]+))?\])?\s*$')
BULLET_RE = re.compile(r'^\s*(?:[-*]|\d+\.)\s+(.*)$')
REVIEWED_RE = re.compile(r'^Peržiūrėta:\s*taip\s*$', re.M | re.I)

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')


def secs(stamp):
    if not stamp:
        return None
    p = [int(x) for x in stamp.split(':')]
    while len(p) < 3:
        p.insert(0, 0)
    return p[0] * 3600 + p[1] * 60 + p[2]


def inline(text):
    """Saugus minimalus Markdown → HTML: **paryškinta**, *kursyvas*, `kodas`."""
    t = html.escape(text.strip(), quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])', r'<em>\1</em>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t


def split_sections(md):
    sections, name, buf = {}, None, []
    for line in md.splitlines():
        m = re.match(r'^##\s+(.+)$', line)
        if m and not line.startswith('###'):
            if name:
                sections[name] = buf
            name, buf = m.group(1).strip(), []
        elif name:
            buf.append(line)
    if name:
        sections[name] = buf
    return sections


def parse_paragraphs(lines):
    paras, cur = [], []
    for l in lines:
        if l.strip().startswith('>'):
            continue
        if l.strip():
            cur.append(l.strip())
        elif cur:
            paras.append(inline(' '.join(cur)))
            cur = []
    if cur:
        paras.append(inline(' '.join(cur)))
    return paras


def parse_groups(lines):
    groups, part, cur = [], None, None
    for l in lines:
        s = l.rstrip()
        if not s.strip() or s.strip().startswith('>'):
            continue
        h3 = re.match(r'^###\s+(.+)$', s)
        if h3:
            part = h3.group(1).strip()
            continue
        g = GROUP_RE.match(s.strip())
        if g:
            cur = {'title': inline(g.group(1)), 'start': secs(g.group(2)), 'end': secs(g.group(3)),
                   'part': part, 'bullets': []}
            groups.append(cur)
            continue
        b = BULLET_RE.match(s)
        if b and cur is not None:
            cur['bullets'].append(inline(b.group(1)))
        elif cur is not None and cur['bullets']:
            cur['bullets'][-1] += ' ' + inline(s)
    return groups


def parse_list(lines):
    return [inline(m.group(1)) for m in (BULLET_RE.match(l) for l in lines) if m]


def parse_table(lines):
    rows = [l.strip() for l in lines if l.strip().startswith('|')]
    if len(rows) < 2:
        return None
    cells = lambda r: [inline(c) for c in r.strip('|').split('|')]
    return {'head': cells(rows[0]), 'rows': [cells(r) for r in rows[2:]]}


def parse(path):
    md = path.read_text(encoding='utf-8')
    sec = split_sections(md)
    about = next((v for k, v in sec.items() if k.startswith('Apie ką')), [])
    main = next((v for k, v in sec.items() if k.startswith('Pagrindinės mintys')), [])
    out = {
        'summary': parse_paragraphs(about),
        'sections': parse_groups(main),
        'takeaways': parse_list(next((v for k, v in sec.items() if k.startswith('Praktinės išvados')), [])),
        'table': parse_table(next((v for k, v in sec.items() if k.startswith('Rodmenys')), [])),
        'reviewed': bool(REVIEWED_RE.search(md)),
    }
    # pranešimai, kurių pagrindinė dalis suskirstyta į klausimus (###) be **grupių**
    if not out['sections']:
        out['sections'] = [{'title': inline(k), 'start': None, 'end': None, 'part': None,
                            'bullets': parse_list(v)} for k, v in sec.items()
                           if k not in SKIP_SECTIONS and not k.startswith(('Apie ką', 'Praktinės', 'Rodmenys'))]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    for folder in sorted(SRC.iterdir()):
        k = folder / 'konspektas.md'
        if folder.is_dir() and k.exists():
            nr = int(folder.name[:2])
            d = parse(k)
            (OUT / f'{nr}.json').write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
            done.add(nr)
            print(f'{nr:2d}: santrauka {len(d["summary"])}, dalių {len(d["sections"])}, '
                  f'išvadų {len(d["takeaways"])}, lentelė {"taip" if d["table"] else "ne"}'
                  f'{", peržiūrėta" if d["reviewed"] else ""}')
    for old in OUT.glob('*.json'):
        if int(old.stem) not in done:
            old.unlink()

    # paieškos indeksas pradžios puslapiui: {nr: [[dalies pavadinimas, pradžia, tekstas, inkaras], ...]}
    tag = re.compile(r'<[^>]+>')
    index = {}
    for nr in sorted(done):
        d = json.loads((OUT / f'{nr}.json').read_text(encoding='utf-8'))
        rows = [['Apie ką pranešimas', None, tag.sub('', ' '.join(d['summary'])), '']]
        rows += [[tag.sub('', s['title']), s['start'], tag.sub('', ' '.join(s['bullets'])), f'd{i + 1}']
                 for i, s in enumerate(d['sections'])]
        rows += [['Praktinės išvados', None, tag.sub('', ' '.join(d['takeaways'])), 'isvados']]
        if d['table']:
            rows += [['Rodmenys ir ribos', None,
                      tag.sub('', ' · '.join(' '.join(r) for r in d['table']['rows'])), 'ribos']]
        index[nr] = [r for r in rows if r[2]]
    SEARCH.write_text(json.dumps(index, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'Paieškos indeksas → {SEARCH.relative_to(ROOT)} ({SEARCH.stat().st_size // 1024} KB)')

    items = json.loads(LIST.read_text(encoding='utf-8'))
    for it in items:
        it['konspektas'] = it['id'] in done
    LIST.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n{len(done)} konspektai → {OUT.relative_to(ROOT)}/, žymos atnaujintos {LIST.name}')


if __name__ == '__main__':
    main()
