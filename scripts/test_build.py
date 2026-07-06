"""Smoke test: run the static site builder against the migrated content
and check that key output files exist. Run from the classmemorial/ root."""
import os, sys

os.environ.setdefault("CONTENT_DIR", os.path.abspath("content"))
os.environ.setdefault("DATA_DIR", os.path.abspath("data"))
os.environ.setdefault("SITE_DIR", os.path.abspath("data/site"))
os.environ.setdefault("FRONTEND_DIR", os.path.abspath("frontend"))

sys.path.insert(0, "backend")
from app import builder

n = builder.build_site()
print("built pages:", n)

from pathlib import Path
site = Path(os.environ["SITE_DIR"])
must = ["index.html", "archives/index.html", "gallery/index.html",
        "404.html", "sitemap.xml", "static/css/style.css", "static/js/main.js"]
for f in must:
    p = site / f
    print(("OK " if p.exists() else "MISS ") + f)

# a couple of post pages
posts = [d for d in (site / "p").iterdir()] if (site / "p").exists() else []
print("post dirs:", len(posts))
for d in posts[:3]:
    print("  post:", d.name, "->", (d / "index.html").exists())

# legacy permalink check
legacy = list((site).glob("20*/*/*/*/index.html"))
print("legacy permalink pages:", len(legacy))
for d in legacy[:3]:
    print("  legacy:", d.parent.relative_to(site))

# check agreement pages render
for name in ["用户协议", "免责声明", "about"]:
    p = site / name / "index.html"
    print(("OK " if p.exists() else "MISS ") + name + "/index.html")
