# AI4薄肌

Public repository: <https://github.com/Selen-Suyue/ai4boji>

Website: <https://selen-suyue.github.io/ai4boji/>

## 发布结构 / Publishing structure

GitHub Pages hosts the bilingual introduction, a read-only synthetic dashboard and the 60-second product film. The Python service and personal SQLite store run locally. Pages does not host the personal backend.

`site/` contains the landing page. `python3 scripts/build_site.py` assembles `dist/`, copies the dashboard UI and generates a 14-day synthetic snapshot in a fresh temporary database. The builder never reads the user's `data/` or `.demo/` store. The static preview disables form writes and calls no model API.

`.github/workflows/pages.yml` tests the app, builds the site and deploys via GitHub Actions. Enable **Settings → Pages → Source → GitHub Actions**. Each push to `main` triggers deployment. No repository secret is needed.

```bash
python3 scripts/build_site.py
python3 -m http.server 18767 --bind 127.0.0.1 --directory dist
```

The preview is built with relative paths to work under `/ai4boji/`. The project title remains **AI4薄肌**; only the repository URL uses the ASCII slug `ai4boji`.
