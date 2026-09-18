"""Gidus (gidai/*.md) paverčia puslapio duomenimis data/gidai.json.

Gido failo pradžioje – antraštė tarp „---“ eilučių:
  id, pavadinimas, aprasas, raktai (kableliais; pagal juos randamos susijusios
  pranešimų dalys), perziureta (taip/ne).
Tekste nuoroda į pranešimą rašoma [[14@11:53]] arba [[14]] – ji tampa nuoroda į
pranešimo puslapį, atidarantį įrašą nuo tos vietos.

Paleidimas: python tools/build_gidai.py  (po build_konspektai.py)
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'gidai'
OUT = ROOT / 'data' / 'gidai.json'
INDEX = ROOT / 'data' / 'gidai-sarasas.json'
KONSP = ROOT / 'data' / 'konspektai'
LIST = ROOT / 'data' / 'pranesimai.json'

REF_RE = re.compile(r'\[\[(\d+)(?:@([\d:]+))?\]\]')
TAG_RE = re.compile(r'<[^>]+>')

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='replace')


def secs(stamp):
    p = [int(x) for x in stamp.split(':')]
    while len(p) < 3:
        p.insert(0, 0)
    return p[0] * 3600 + p[1] * 60 + p[2]


def clock(s):
    h, m, s = s // 3600, s % 3600 // 60, s % 60
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


class Renderer:
    def __init__(self, items):
        self.items = items
        self.refs = {}  # nr -> set(sekundės)

    def ref(self, m):
        nr, stamp = int(m.group(1)), m.group(2)
        it = self.items.get(nr)
        if not it:
            raise SystemExit(f'Nėra pranešimo Nr. {nr}')
        t = secs(stamp) if stamp else None
        self.refs.setdefault(nr, set())
        if t is not None:
            self.refs[nr].add(t)
        href = f'pranesimas.html?nr={nr}' + (f'&amp;t={t}' if t is not None else '')
        label = f'{nr}' + (f' · {clock(t)}' if t is not None else '')
        title = html.escape(it['title'], quote=True)
        return f'<a class="ref" href="{href}" title="{title}">{label}</a>'

    def inline(self, text):
        t = html.escape(text.strip(), quote=False)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])', r'<em>\1</em>', t)
        return REF_RE.sub(self.ref, t)

    def blocks(self, md):
        out, lines, i = [], md.splitlines(), 0
        while i < len(lines):
            l = lines[i].rstrip()
            if not l.strip():
                i += 1
                continue
            if l.startswith('## '):
                title = l[3:].strip()
                slug = re.sub(r'[^\w]+', '-', title.lower()).strip('-')
                out.append(f'<h2 id="{slug}">{self.inline(title)}</h2>')
                i += 1
            elif l.startswith('### '):
                out.append(f'<h3>{self.inline(l[4:])}</h3>')
                i += 1
            elif l.startswith('|'):
                rows = []
                while i < len(lines) and lines[i].startswith('|'):
                    rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                    i += 1
                head, body = rows[0], rows[2:]
                th = ''.join(f'<th scope="col">{self.inline(c)}</th>' for c in head)
                tb = ''.join('<tr>' + ''.join(f'<td>{self.inline(c)}</td>' for c in r) + '</tr>' for r in body)
                out.append(f'<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')
            elif re.match(r'^(\d+\.|-)\s', l):
                ordered = l[0].isdigit()
                items = []
                while i < len(lines) and lines[i].strip():
                    m = re.match(r'^(\d+\.|-)\s+(.*)$', lines[i])
                    if m:
                        items.append(m.group(2))
                    elif items:
                        items[-1] += ' ' + lines[i].strip()
                    i += 1
                tag = 'ol' if ordered else 'ul'
                out.append(f'<{tag}>' + ''.join(f'<li>{self.inline(x)}</li>' for x in items) + f'</{tag}>')
            elif l.startswith('> '):
                buf = []
                while i < len(lines) and lines[i].startswith('>'):
                    buf.append(lines[i].lstrip('> ').strip())
                    i += 1
                out.append(f'<aside class="callout">{self.inline(" ".join(buf))}</aside>')
            else:
                buf = []
                while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||-\s|\d+\.\s|>)', lines[i]):
                    buf.append(lines[i].strip())
                    i += 1
                out.append(f'<p>{self.inline(" ".join(buf))}</p>')
        return '\n'.join(out)


def front(md):
    m = re.match(r'^---\n(.*?)\n---\n', md, re.S)
    meta = dict(re.findall(r'^(\w+):\s*(.*)$', m.group(1), re.M))
    return meta, md[m.end():]


def related(keys, items):
    """Pranešimų dalys, kurių pavadinime ar tekste minimi gido raktai."""
    found = {}
    for f in KONSP.glob('*.json'):
        nr = int(f.stem)
        d = json.loads(f.read_text(encoding='utf-8'))
        for s in d['sections']:
            title = TAG_RE.sub('', s['title'])
            hay = (title + ' ' + ' '.join(TAG_RE.sub('', b) for b in s['bullets'])).lower()
            hits_title = sum(bool(re.search(r'(?<!\w)' + re.escape(k), title.lower())) for k in keys)
            hits_body = sum(len(re.findall(r'(?<!\w)' + re.escape(k), hay)) for k in keys)
            if hits_title or hits_body >= 2:
                found.setdefault(nr, []).append({'title': title, 'start': s['start'],
                                                 'score': hits_title * 3 + hits_body})
    return found


def main():
    items = {it['id']: it for it in json.loads(LIST.read_text(encoding='utf-8'))}
    guides = []
    for path in sorted(SRC.glob('*.md')):
        meta, body = front(path.read_text(encoding='utf-8'))
        r = Renderer(items)
        content = r.blocks(body)
        keys = [k.strip().lower() for k in meta.get('raktai', '').split(',') if k.strip()]
        rel = related(keys, items)
        # necituojami pranešimai rodomi tik jei tema juose aptariama plačiau
        extra = sorted((nr for nr in rel if nr not in r.refs),
                       key=lambda nr: -sum(x['score'] for x in rel[nr]))
        extra = [nr for nr in extra if sum(x['score'] for x in rel[nr]) >= 5][:6]
        nrs = set(r.refs) | set(extra)
        sources = []
        for nr in nrs:
            it = items[nr]
            secs_ = sorted(rel.get(nr, []), key=lambda s: -s['score'])[:4]
            secs_.sort(key=lambda s: (s['start'] is None, s['start'] or 0))
            sources.append({
                'nr': nr, 'title': it['title'], 'year': it['year'], 'lang': it['lang'],
                'youtube': bool(it['youtube']), 'cited': nr in r.refs,
                'weight': len(r.refs.get(nr, ())) * 3 + sum(s['score'] for s in rel.get(nr, [])),
                'sections': [{'title': s['title'], 'start': s['start']} for s in secs_],
            })
        sources.sort(key=lambda s: (not s['cited'], -s['weight']))
        headings = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', content)
        guides.append({
            'id': meta['id'], 'title': meta['pavadinimas'], 'lead': meta['aprasas'],
            'reviewed': meta.get('perziureta', 'ne').lower() == 'taip',
            'toc': [{'id': a, 'title': TAG_RE.sub('', b)} for a, b in headings],
            'html': content, 'sources': sources,
        })
        print(f'{meta["id"]}: cituojama pranešimų {len(r.refs)}, susijusių iš viso {len(sources)}')
    OUT.write_text(json.dumps(guides, ensure_ascii=False, indent=1), encoding='utf-8')
    # trumpas sąrašas pradžios ir pranešimų puslapiams
    index = [{'id': g['id'], 'title': g['title'], 'lead': g['lead'],
              'nrs': sorted(s['nr'] for s in g['sources'] if s['cited'])} for g in guides]
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n{len(guides)} gidai → {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)')


if __name__ == '__main__':
    main()
