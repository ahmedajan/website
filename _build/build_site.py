"""Generate the multi-page personal website from Master CV/master_cv.md.

Run:  python _build/build_site.py   (from the website folder)
Everything is regenerated except avatar.jpg, style.css, README.md.
Public-site rules: no private notes, no GPA, no phone number, no references,
no NDA result figures, no unpublished-placeholder entries, J9 excluded unless INCLUDE_J9 = True.
"""
import html, pathlib, re, shutil
import markdown

INCLUDE_J9 = True

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT.parent / "Master CV" / "master_cv.md"
BASE_TITLE = "Ajan Ahmed, PhD"

# ---------------------------------------------------------------- helpers
def slug(text):
    text = re.sub(r"<[^>]+>|\*|_|`", "", text)
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return text[:70].strip("-") or "item"

def fix_indent(md):
    out = []
    for line in md.split("\n"):
        m = re.match(r"^( +)([-*]|\d+\.) ", line)
        if m:
            line = " " * (len(m.group(1)) * 2) + line[len(m.group(1)):]
        out.append(line)
    md = "\n".join(out)
    md = re.sub(r"^([^|\s-][^\n]*)\n(- |\| |1\. )", r"\1\n\n\2", md, flags=re.M)
    return md

def linkify(h):
    h = re.sub(r"(?<![\w/\"=])(10\.\d{4,9}/[^\s<,;)]+[^\s<,;.)])",
               r'<a href="https://doi.org/\1">\1</a>', h)
    h = re.sub(r"(?<![\w/\"=>])arXiv:(\d{4}\.\d{4,5})", r'<a href="https://arxiv.org/abs/\1">arXiv:\1</a>', h)
    h = re.sub(r"(?<![\w/\"=>])(github\.com/[\w\-./]+[\w/])", r'<a href="https://\1">\1</a>', h)
    return h

def md2html(md):
    return linkify(markdown.markdown(fix_indent(md), extensions=["tables", "sane_lists"]))

def inline(md):
    h = markdown.markdown(md.strip())
    return re.sub(r"^<p>|</p>$", "", h)

def clean_public(md):
    md = re.sub(r"<!--.*?-->\n?", "", md, flags=re.S)
    md = re.sub(r"^\s*- \*\*Tags:\*\*.*\n", "", md, flags=re.M)
    md = re.sub(r"^\s*- \*\*Industry framing:\*\*.*\n", "", md, flags=re.M)
    md = re.sub(r"^\s*- \*\*GPA.*\n", "", md, flags=re.M)
    md = re.sub(r"^\s*- [^\n]*(\|r\||under 8%)[^\n]*\n", "", md, flags=re.M)  # NDA result figures (VSEA)
    md = re.sub(r"3\.905\s*/\s*4\.0 cumulative graduate GPA,?\s*(with )?", "", md)  # never publish GPA
    md = re.sub(r"^\s*- [^\n]*\(to add[^\n]*\n", "", md, flags=re.M)
    md = re.sub(r"^\s*-\s*$\n", "", md, flags=re.M)
    md = re.sub(r"\*\*Resume bullets?[^*]*:\*\*", "**Highlights:**", md)
    md = md.replace("**Limitations & future work (for interviews and research statements):**", "**Limitations & future work:**")
    md = md.replace("Status:** completed; final technical report delivered to the sponsor; results not publishable under a non-disclosure agreement (NDA)",
                    "Status:** completed; final technical report delivered to the sponsor (results under a non-disclosure agreement)")
    return md

def sections(md, level):
    """Split md into (heading, body) at the given heading level."""
    pat = re.compile(rf"^{'#' * level} (.+)$", re.M)
    parts, idx = [], [m for m in pat.finditer(md)]
    for i, m in enumerate(idx):
        end = idx[i + 1].start() if i + 1 < len(idx) else len(md)
        parts.append((m.group(1).strip(), md[m.end():end].strip("\n")))
    pre = md[: idx[0].start()] if idx else md
    return pre.strip(), parts

def first_meta(body):
    """One-line teaser: Dates / Reference / Status / first bullet."""
    for key in ("Dates", "Date", "Dates / Semesters", "Reference", "Status"):
        m = re.search(rf"^- \*\*{re.escape(key)}:\*\*\s*(.+)$", body, re.M)
        if m:
            return m.group(1)
    m = re.search(r"^- (.+)$", body, re.M)
    return m.group(1) if m else ""

# ---------------------------------------------------------------- page shell
NAV = [
    ("index.html", "Home"), ("education.html", "Education"), ("research.html", "Research Experience"),
    ("projects.html", "Projects"), ("publications.html", "Publications"), ("talks.html", "Invited Talks"),
    ("teaching.html", "Teaching"), ("funding.html", "Research Funding"), ("experience.html", "Work Experience"),
    ("honors.html", "Honors & Certifications"), ("skills.html", "Skills"), ("cv.html", "CV"),
]
ICONS = """<ul class="icons">
  <li><a href="https://github.com/ahmedajan" aria-label="GitHub"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56 0-.27-.01-1-.02-1.96-3.2.69-3.87-1.54-3.87-1.54-.52-1.32-1.27-1.67-1.27-1.67-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.69 1.24 3.34.95.1-.74.4-1.24.72-1.53-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.28 1.18-3.08-.12-.29-.51-1.46.11-3.04 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.58.23 2.75.11 3.04.74.8 1.18 1.82 1.18 3.08 0 4.42-2.69 5.39-5.26 5.68.41.36.78 1.06.78 2.13 0 1.54-.01 2.78-.01 3.16 0 .31.21.68.8.56C20.22 21.39 23.5 17.08 23.5 12 23.5 5.65 18.35.5 12 .5z"/></svg></a></li>
  <li><a href="https://scholar.google.com/citations?user=BlD713QAAAAJ" aria-label="Google Scholar"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 24a7 7 0 1 1 0-14 7 7 0 0 1 0 14zm0-24L0 9.5l4.84 3.94A8 8 0 0 1 12 9a8 8 0 0 1 7.16 4.44L24 9.5z"/></svg></a></li>
  <li><a href="https://orcid.org/0009-0002-7000-7809" aria-label="ORCID"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zM7.37 17.97H5.85V7.41h1.52v10.56zm-.76-11.91a.95.95 0 1 1 0-1.9.95.95 0 0 1 0 1.9zm10.13 11.91h-3.49V7.41h3.39c3.22 0 4.7 2.3 4.7 5.28 0 3.24-2.03 5.28-4.6 5.28zm-.18-9.18h-1.79v7.8h1.69c2.39 0 3.32-1.73 3.32-3.9 0-2.36-1.5-3.9-3.22-3.9z"/></svg></a></li>
  <li><a href="https://www.linkedin.com/in/ajan-ahmed" aria-label="LinkedIn"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/></svg></a></li>
  <li><a href="mailto:aahmed@clarkson.edu" aria-label="Email"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5zm2.4.4L12 11l7.6-5.6H4.4zM20 7.2l-7.4 5.5a1 1 0 0 1-1.2 0L4 7.2V19h16V7.2z"/></svg></a></li>
</ul>"""

BIO = """<p class="bio">
  <span>Dr. Ahmed holds a Ph.D. in Electrical and Computer Engineering from Clarkson University, an M.Eng. in Electrical and Computer Engineering from Southern Illinois University Carbondale, and a B.Sc. in Electrical and Electronic Engineering from North South University, Bangladesh.</span>
  <span>His research makes voice biometrics reliable in the real world &mdash; speaker recognition, biometric quality assessment and standardization, deepfake audio, and trustworthy AI. Based in Edmonton, Alberta.</span>
</p>"""

def page(title, content, depth=0, active=""):
    up = "../" * depth
    nav = "\n".join(
        f'<li><a href="{up}{href}"{" class=\"active\"" if href == active else ""}>{label}</a></li>'
        for href, label in NAV)
    icons = ICONS
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="color-scheme" content="dark" />
  <title>{html.escape(title)}{'' if title == BASE_TITLE else ' | ' + BASE_TITLE}</title>
  <meta name="description" content="Ajan Ahmed, PhD: voice biometrics, speaker recognition, biometric quality, deepfake audio, trustworthy AI" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?display=swap&family=Inter:ital,wght@0,400;0,500;0,600;1,400" rel="stylesheet" />
  <link rel="stylesheet" href="{up}style.css" />
</head>
<body>
  <div id="main">
    <div class="inner">
     <aside class="profile">
      <a href="{up}index.html"><img class="avatar" src="{up}avatar.jpg" alt="Ajan Ahmed, PhD" /></a>
      <h1><a class="plain" href="{up}index.html">Ajan Ahmed, PhD</a></h1>
      <p class="role">Electrical &amp; Computer Engineering &middot; Voice Biometrics &amp; Trustworthy AI</p>
      {BIO}
      {icons}
      <nav class="site-nav"><ul>
{nav}
      </ul></nav>
     </aside>
     <section class="content">
{content}
      <footer class="foot">&copy; 2026 Ajan Ahmed, PhD &middot; Open Work Permit (Canada)</footer>
     </section>
    </div>
  </div>
</body>
</html>
"""

def write(rel, title, content, depth=0, active=""):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(page(title, content, depth, active), encoding="utf-8")

def crumb(section_href, section_label):
    return f'<p class="crumb"><a href="../{section_href}">&larr; {section_label}</a></p>'

# ---------------------------------------------------------------- load master
raw = SRC.read_text(encoding="utf-8")
_, top = sections(raw, 2)
S = {h: clean_public(b) for h, b in top}

USED = set()
def item_list(items, folder, section_href, section_label, active):
    """items: list of (heading, body). Writes detail pages; returns list HTML."""
    lis = []
    for h, body in items:
        s = slug(re.sub(r"^[A-Z]+\d+\.\s*", "", h))
        rel = f"{folder}/{s}.html"
        n = 2
        while rel in USED:
            rel = f"{folder}/{s}-{n}.html"; n += 1
        USED.add(rel)
        title_txt = re.sub(r"\*", "", h)
        detail = f"{crumb(section_href, section_label)}\n<h2>{inline(h)}</h2>\n<div class=\"prose\">\n{md2html(body)}\n</div>"
        write(rel, title_txt, detail, depth=1, active=active)
        meta = first_meta(body)
        meta_html = f'<br /><span class="meta">{inline(meta)}</span>' if meta else ""
        lis.append(f'<li><p><a href="{rel}">{inline(h)}</a>{meta_html}</p></li>')
    return '<ul class="list">\n' + "\n".join(lis) + "\n</ul>"

# ---------------------------------------------------------------- Home
edu_pre, edu_items = sections(S["Education"], 3)
summary = sections(S["Summary Variants"], 3)[1]
research_summary = dict(summary).get("Research", "")
cards = [
    ("education.html", "Education", "Ph.D. (Clarkson), M.Eng. (SIUC), B.Sc. (NSU)"),
    ("research.html", "Research Experience", "Clarkson, Southern Illinois University, North South University"),
    ("projects.html", "Projects", "22 research projects and 6 human-subjects data collections"),
    ("publications.html", "Publications", "Journal articles, conference papers, datasets, software"),
    ("talks.html", "Invited Talks", "Invited seminars and workshop talks, 2024–2026"),
    ("teaching.html", "Teaching", "~665 students, co-instructor, 2 course booklets, mentoring"),
    ("funding.html", "Research Funding", "11 funded proposals co-written, over $1.1M (NSF, FBI, DHS, CITeR)"),
    ("experience.html", "Work Experience", "BlackBerry (RIM), McGill University, and more"),
    ("honors.html", "Honors & Certifications", "3MT 1st Prize, Best Oral Presentation, scholarships"),
    ("skills.html", "Skills", "Technical and professional skills"),
]
card_html = '<ul class="cards">' + "".join(
    f'<li><a href="{h}"><span class="card-title">{t}</span><span class="card-sub">{d}</span></a></li>' for h, t, d in cards) + "</ul>"
home = f"""<h2>About</h2>
<div class="prose"><p>{inline(research_summary)}</p></div>
<h2>Explore</h2>
{card_html}"""
write("index.html", BASE_TITLE, home, active="index.html")

# ---------------------------------------------------------------- Education
write("education.html", "Education", "<h2>Education</h2>\n" + item_list(edu_items, "education", "education.html", "Education", "education.html"), active="education.html")

# ---------------------------------------------------------------- Research Experience
_, res_items = sections(S["Research Experience"], 3)
write("research.html", "Research Experience", "<h2>Research Experience</h2>\n" + item_list(res_items, "research", "research.html", "Research Experience", "research.html"), active="research.html")

# ---------------------------------------------------------------- Work Experience
_, work_items = sections(S["Work Experience"], 3)
work_items = [(h, b) for h, b in work_items if "Technical Position — ImransLab" not in h]
write("experience.html", "Work Experience", "<h2>Work Experience</h2>\n" + item_list(work_items, "experience", "experience.html", "Work Experience", "experience.html"), active="experience.html")

# ---------------------------------------------------------------- Projects (grouped)
proj_pre, proj_groups = sections(S["Projects"], 3)
blocks = []
for gh, gbody in proj_groups:
    gpre, gitems = sections(gbody, 4)
    blocks.append(f"<h3 class=\"group\">{inline(gh)}</h3>")
    if gpre and not gitems:
        blocks.append(md2html(gpre))
    elif gpre:
        blocks.append(f'<div class="prose">{md2html(gpre)}</div>')
    if gitems:
        blocks.append(item_list(gitems, "projects", "projects.html", "Projects", "projects.html"))
write("projects.html", "Projects", "<h2>Projects</h2>\n" + "\n".join(blocks), active="projects.html")

# ---------------------------------------------------------------- Publications & Talks
pub_pre, pub_groups = sections(S["Publications & Presentations"], 3)
pub_blocks, talk_html = [], ""
for gh, gbody in pub_groups:
    gpre, gitems = sections(gbody, 4)
    if not INCLUDE_J9:
        gitems = [(h, b) for h, b in gitems if not h.startswith("J9.")]
    if gh.startswith("Invited Talks"):
        talk_html = "<h2>Invited Talks &amp; Seminars</h2>\n" + item_list(gitems, "talks", "talks.html", "Invited Talks", "talks.html")
        continue
    pub_blocks.append(f"<h3 class=\"group\">{inline(gh)}</h3>")
    if gitems:
        pub_blocks.append(item_list(gitems, "publications", "publications.html", "Publications", "publications.html"))
    elif gpre:
        pub_blocks.append(f'<div class="prose">{md2html(gpre)}</div>')
pub_intro = f'<div class="prose">{md2html(pub_pre)}</div>' if pub_pre else ""
if not INCLUDE_J9:
    pub_intro = pub_intro.replace("9 journal articles", "8 journal articles").replace("(24)", "(23)")
write("publications.html", "Publications", "<h2>Publications</h2>\n" + pub_intro + "\n".join(pub_blocks), active="publications.html")
write("talks.html", "Invited Talks", talk_html, active="talks.html")

# ---------------------------------------------------------------- Teaching
teach_pre, teach_items = sections(S["Teaching Experience"], 3)
t_blocks = [f'<div class="prose">{md2html(teach_pre)}</div>'] if teach_pre else []
roles = []
for h, b in teach_items:
    if h == "Course Materials Developed":
        _, books = sections(b, 4)
        t_blocks.append("<h3 class=\"group\">Course Materials Developed</h3>")
        t_blocks.append(item_list(books, "teaching", "teaching.html", "Teaching", "teaching.html"))
    elif h in ("Pedagogy Training",):
        continue
    elif h == "Teaching Interests":
        t_blocks.append("<h3 class=\"group\">Teaching Interests</h3>")
        t_blocks.append(f'<div class="prose">{md2html(b)}</div>')
    else:
        roles.append((h, b))
t_html = "<h2>Teaching</h2>\n" + t_blocks[0] + "<h3 class=\"group\">Teaching & Mentoring Roles</h3>\n" + \
    item_list(roles, "teaching", "teaching.html", "Teaching", "teaching.html") + "\n".join(t_blocks[1:])
write("teaching.html", "Teaching", t_html, active="teaching.html")

# ---------------------------------------------------------------- Funding (single page)
fund = S["Research Funding & Grant Proposals"]
fund = re.sub(r"### Other Proposals.*?(?=### |\Z)", "", fund, flags=re.S)
fund = re.sub(r"### Resume bullets \(grant writing\).*?(?=### |\Z)", "", fund, flags=re.S)
write("funding.html", "Research Funding", "<h2>Research Funding</h2>\n<p class=\"lead\">Funded research proposals I co-wrote with faculty principal investigators.</p>\n<div class=\"prose\">" + md2html(fund) + "</div>", active="funding.html")

# ---------------------------------------------------------------- Honors (awards + certifications + memberships)
hon = "<h2>Honors &amp; Awards</h2>\n<div class=\"prose\">" + md2html(S["Awards, Honors & Scholarships"]) + "</div>"
certs = S["Certifications & Training"]
hon += "\n<h2>Certifications &amp; Training</h2>\n<div class=\"prose\">" + md2html(certs) + "</div>"
hon += "\n<h2>Professional Memberships</h2>\n<div class=\"prose\">" + md2html(S["Professional Memberships"]) + "</div>"
write("honors.html", "Honors & Certifications", hon, active="honors.html")

# ---------------------------------------------------------------- Skills (summary + full)
tech = S["Technical Skills"]
tpre, tgroups = sections(tech, 3)
summary_block = dict(tgroups).get("Summary (core stack; rebuilt from the sections below)", "")
sk = "<h2>Skills</h2>\n<h3 class=\"group\">Core Stack</h3>\n<div class=\"prose\">" + md2html(summary_block) + "</div>"
sk += "\n<h3 class=\"group\">Technical Skills (detailed)</h3>\n"
sk += item_list([(h, b) for h, b in tgroups if not h.startswith("Summary")], "skills", "skills.html", "Skills", "skills.html")
spre, sgroups = sections(S["Soft Skills"], 3)
sk += "\n<h3 class=\"group\">Professional Skills</h3>\n" + item_list(sgroups, "skills", "skills.html", "Skills", "skills.html")
write("skills.html", "Skills", sk, active="skills.html")

# ---------------------------------------------------------------- CV page
cv = """<h2>Curriculum Vitae</h2>
<div class="prose"><p>Dr. Ahmed's complete, detailed CV (all sections) is available as a PDF.</p>
<p><a href="Ajan_Ahmed_CV.pdf">Download the CV (PDF)</a></p>
<p>Contact: <a href="mailto:aahmed@clarkson.edu">aahmed@clarkson.edu</a> &middot; Edmonton, Alberta, Canada &middot; Open Work Permit (Canada), no sponsorship required.</p></div>"""
write("cv.html", "CV", cv, active="cv.html")

print("site built in", ROOT)

# ---------------------------------------------------------------- public CV PDF (for cv.html)
import subprocess
pub = clean_public(raw)
pub = pub.replace("# Master CV — Ajan Ahmed, PhD", "# Ajan Ahmed, PhD", 1)
pub = re.sub(r"^> .*\n(>.*\n)*", "", pub, flags=re.M)
for sec in ("Summary Variants", "References", "Notes / Achievement Bank"):
    pub = re.sub(rf"^## {re.escape(sec)}\n.*?(?=^## |\Z)", "", pub, flags=re.S | re.M)
pub = re.sub(r"^- \*\*Phone:\*\*.*\n", "", pub, flags=re.M)
pub = re.sub(r"^### Other Proposals\n.*?(?=^### |^## |\Z)", "", pub, flags=re.S | re.M)
pub = re.sub(r"^### Technical Position — ImransLab.*?(?=^### |^## |\Z)", "", pub, flags=re.S | re.M)
if not INCLUDE_J9:
    pub = re.sub(r"^#### J9\..*?(?=^#### |^### |\Z)", "", pub, flags=re.S | re.M)
    pub = pub.replace("9 journal articles", "8 journal articles").replace("(24)", "(23)")
pub = re.sub(r"^#{2,4} \[(Project Name|Job Title)\].*?(?=^#{2,4} |\Z)", "", pub, flags=re.S | re.M)
pub_html = markdown.markdown(fix_indent(pub), extensions=["tables", "sane_lists"])
PDF_CSS = """
@page { size: Letter; margin: 0.65in 0.7in 0.75in 0.7in;
  @bottom-center { content: "Ajan Ahmed, PhD | CV | Page " counter(page) " of " counter(pages);
                   font-family: 'Segoe UI', Arial, sans-serif; font-size: 8pt; color: #666; } }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Segoe UI', Calibri, Arial, sans-serif; font-size: 9.6pt; line-height: 1.38; color: #1d1d1f; }
h1 { font-size: 24pt; color: #35393D; margin: 0 0 2pt 0; }
h2 { font-size: 13.5pt; color: #fff; background: #35393D; padding: 4pt 8pt; margin: 16pt 0 8pt 0; border-radius: 3px; break-after: avoid; }
h3 { font-size: 11pt; color: #35393D; margin: 12pt 0 4pt 0; padding-bottom: 2pt; border-bottom: 1px solid #ccc; break-after: avoid; }
h4 { font-size: 10pt; color: #444; margin: 10pt 0 3pt 0; break-after: avoid; }
p { margin: 3pt 0 5pt 0; } ul, ol { margin: 2pt 0 5pt 0; padding-left: 16pt; } li { margin: 1.2pt 0; }
table { border-collapse: collapse; width: 100%; font-size: 8.8pt; } th, td { border: 1px solid #ccc; padding: 3pt 5pt; vertical-align: top; }
tr { break-inside: avoid; } a { color: #1d1d1f; text-decoration: none; }
"""
tmp_html = ROOT / "_build" / "cv_public.html"
tmp_html.write_text(f'<!doctype html><html><head><meta charset="utf-8"><title>Ajan Ahmed, PhD — CV</title><style>{PDF_CSS}</style></head><body>{pub_html}</body></html>', encoding="utf-8")
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={ROOT / 'Ajan_Ahmed_CV.pdf'}", tmp_html.as_uri()], check=True, timeout=180)
tmp_html.unlink()
print("public CV PDF written")