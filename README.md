# hemo.science

Prof. dr. Juliaus Ptašeko pranešimų archyvas: hemostazė, krešėjimo sistemos biožymenys,
venų tromboembolija, antikoaguliantų ir antiagregantų terapijos kontrolė.

Statinis puslapis (HTML, CSS, JS be priklausomybių), talpinamas GitHub Pages.

## Struktūra

- `index.html` – pradžia: gidai ir pranešimų sąrašas
- `pranesimas.html?nr=N` – pranešimo puslapis: įrašas ir konspektas su laiko žymomis
- `gidas.html?id=…` – gidas pagal temą su nuorodomis į pranešimų vietas
- `assets/` – išvaizda ir puslapių skriptai (`common.js` bendros funkcijos)
- `data/pranesimai.json` – pranešimų sąrašas
- `data/konspektai/N.json` – konspektai
- `data/gidai.json`, `data/gidai-sarasas.json` – gidai
- `gidai/*.md` – gidų tekstai (redaguojami ranka)
- `tools/build_data.py` – JSON generavimas iš Excel sąrašo (lapas „Puslapiui“)
- `tools/build_konspektai.py` – konspektai iš `konspektavimas/*/konspektas.md`
- `tools/build_gidai.py` – gidai iš `gidai/*.md`
- `data/paieska.json` – konspektų tekstų paieškos indeksas (kuria `build_konspektai.py`)
- `tools/perziuros_dokumentas.py` – Word dokumentas autoriui peržiūrėti (`perziura/`, nekeliama)

## Sąrašo atnaujinimas

```bash
python tools/build_data.py "kelias/iki/Pranešimų sąrašas.xlsx"
```

Be argumento skaitomas `../DS/PRESENTATIONS/Pranešimų sąrašas 2026-09-17.xlsx`.

## Konspektai ir gidai

```bash
python tools/build_konspektai.py
python tools/build_gidai.py
```

Konspektų šaltiniai (`konspektavimas/`) į repozitoriją nekeliami. Konspektas laikomas
autoriaus peržiūrėtu, jei jame yra eilutė `Peržiūrėta: taip`; gidas – jei antraštėje
`perziureta: taip`. Neperžiūrėti rodomi su pastaba.

Gido tekste nuoroda į pranešimą rašoma `[[14@11:53]]` (pranešimas Nr. 14, nuo 11:53)
arba `[[14]]`.

## Vietinė peržiūra

```bash
python -m http.server 8117
```

Video rodomi per `youtube-nocookie.com`. Privatūs YouTube video puslapyje neatsidaro –
jiems reikia matomumo „Neįtrauktas į sąrašą“ (unlisted).
