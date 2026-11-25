# Personal Website — Ajan Ahmed

Multi-page academic-portfolio site (plain HTML + CSS), generated from the master CV.
Styling: dark theme, Inter font, sticky profile sidebar (`style.css`).

## Structure

- `index.html` — home: about + links to every section
- Section pages: `education.html`, `research.html`, `projects.html`, `publications.html`, `talks.html`,
  `teaching.html`, `funding.html`, `experience.html`, `honors.html`, `skills.html`
- Detail pages (one per item): `education/`, `research/`, `projects/`, `publications/`, `talks/`,
  `teaching/`, `experience/`, `skills/`
- `_build/build_site.py` — generator (not published; folders starting with `_` are ignored by GitHub Pages)

## Rebuild after editing the master CV

```powershell
cd "D:\Master CV\website"
python _build/build_site.py
```

Requires Python with `markdown` (`pip install markdown`). The site has no CV page and no CV PDF.
The generator applies the public-site rules: no GPA, phone, references, private notes, NDA result figures,
or placeholder entries; J9 excluded unless `INCLUDE_J9 = True`.

## Preview locally

```powershell
python -m http.server 8000 --directory "D:\Master CV\website"
```

Then open <http://localhost:8000>.

## Publish

Commit and push to `main`; GitHub Pages serves it at <https://ahmedajan.github.io/website/>.
