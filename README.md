# Personal Website

A minimal academic-portfolio static site (plain HTML + CSS), modeled on
<https://tim.affects.ai/>.

## Files

- `index.html` — page content with `[PLACEHOLDERS]` to fill in
- `style.css` — styling (light + dark mode)
- `avatar.jpg` — **you need to add this** (your profile photo, square crop, ~400×400 works well)

## Fill in your content

Open `index.html` and replace every `[BRACKETED]` value:

- `[YOUR NAME]`, `[CREDENTIALS]`, `[ROLE / AFFILIATION]`
- `[BIO]` paragraph
- Links: `[USERNAME]`, `[ORCID-ID]`, `[YOU]@example.com`
- Publication entries (`[AUTHORS]`, `[TITLE]`, `[VENUE]`, `[YEAR]`)
- Project entries
- `[YEAR]` in the footer

Delete any section you don't need (e.g. *Under Review*).

## Preview locally

Just double-click `index.html`, or run a tiny server:

```powershell
cd E:\website
python -m http.server 8000
```

Then open <http://localhost:8000>.

## Deploy to GitHub Pages

1. Create a new GitHub repo. For a personal site at
   `https://<username>.github.io`, name the repo **`<username>.github.io`**.
   Otherwise any repo name works and the site will be at
   `https://<username>.github.io/<repo>/`.
2. Push these files:

   ```powershell
   cd E:\website
   git init
   git add .
   git commit -m "Initial site"
   git branch -M main
   git remote add origin https://github.com/<username>/<repo>.git
   git push -u origin main
   ```
3. On GitHub: **Settings → Pages → Source: Deploy from a branch →
   Branch: `main` / `(root)` → Save**.
4. Wait ~1 minute, then visit the URL Pages shows you.

## Custom domain (optional)

Add a `CNAME` file containing just your domain
(e.g. `you.example.com`), then configure DNS at your registrar per
<https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site>.
