import asyncio
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "https://bytebytego.com"
OUTPUT_DIR = Path(r"C:\Users\modia\bytebytego-courses")
SESSION_FILE = OUTPUT_DIR / "session.json"
EMAIL = "ashutosh94g@gmail.com"
MIN_CONTENT_SIZE = 6000

COURSES = [
    ("01-tech-resume", "tech-resume", "How to Write a Good Resume"),
    ("02-coding-patterns", "coding-patterns", "Coding Interview Patterns"),
    ("03-system-design-interview", "system-design-interview", "System Design Interview"),
    ("04-object-oriented-design-interview", "object-oriented-design-interview", "Object-Oriented Design Interview"),
    ("05-ml-system-design-interview", "machine-learning-system-design-interview", "Machine Learning System Design Interview"),
    ("06-mobile-system-design-interview", "mobile-system-design-interview", "Mobile System Design Interview"),
    ("07-genai-system-design-interview", "genai-system-design-interview", "Generative AI System Design Interview"),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - {course_name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: Georgia, 'Times New Roman', serif;
    line-height: 1.8; color: #1a1a1a;
    max-width: 820px; margin: 0 auto; padding: 2rem 1.5rem; background: #fff;
  }}
  h1 {{ font-size: 2rem; margin: 1.5rem 0 1rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  h2 {{ font-size: 1.6rem; margin: 1.8rem 0 0.8rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  h3 {{ font-size: 1.3rem; margin: 1.5rem 0 0.6rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  h4, h5, h6 {{ margin: 1.2rem 0 0.5rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  p {{ margin: 0.8rem 0; }}
  img {{ max-width: 100%; height: auto; margin: 1rem 0; border-radius: 4px; }}
  pre {{ background: #f5f5f5; padding: 1rem; border-radius: 6px; overflow-x: auto; margin: 1rem 0; font-size: 0.9rem; }}
  code {{ background: #f0f0f0; padding: 0.15rem 0.4rem; border-radius: 3px; font-size: 0.9em; }}
  pre code {{ background: none; padding: 0; }}
  ul, ol {{ margin: 0.8rem 0; padding-left: 2rem; }}
  li {{ margin: 0.3rem 0; }}
  blockquote {{ border-left: 4px solid #10b981; padding: 0.5rem 1rem; margin: 1rem 0; background: #f0fdf4; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; }}
  th {{ background: #f5f5f5; font-weight: 600; }}
  hr {{ border: none; border-top: 1px solid #e5e5e5; margin: 2rem 0; }}
  .breadcrumb {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 0.85rem; color: #666; margin-bottom: 1.5rem;
    padding-bottom: 1rem; border-bottom: 1px solid #e5e5e5;
  }}
  .breadcrumb a {{ color: #10b981; text-decoration: none; }}
  .breadcrumb a:hover {{ text-decoration: underline; }}
  .nav-footer {{
    margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #e5e5e5;
    display: flex; justify-content: space-between;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 0.9rem;
  }}
  .nav-footer a {{ color: #10b981; text-decoration: none; }}
  .nav-footer a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<div class="breadcrumb">
  <a href="../index.html">All Courses</a> &rsaquo; <a href="index.html">{course_name}</a> &rsaquo; {title}
</div>
{content}
<div class="nav-footer">
  <span>{prev_link}</span>
  <span>{next_link}</span>
</div>
</body>
</html>"""

COURSE_INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{course_name} - ByteByteGo</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6; color: #1a1a1a;
    max-width: 820px; margin: 0 auto; padding: 2rem 1.5rem; background: #fff;
  }}
  h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
  .subtitle {{ color: #666; margin-bottom: 2rem; }}
  .breadcrumb {{ font-size: 0.85rem; color: #666; margin-bottom: 1.5rem; }}
  .breadcrumb a {{ color: #10b981; text-decoration: none; }}
  ol {{ padding-left: 0; list-style: none; }}
  ol li {{
    padding: 0.75rem 1rem; margin: 0.4rem 0;
    border: 1px solid #e5e5e5; border-radius: 6px; transition: background 0.15s;
  }}
  ol li:hover {{ background: #f0fdf4; }}
  ol li a {{ color: #1a1a1a; text-decoration: none; display: block; }}
  ol li a:hover {{ color: #10b981; }}
</style>
</head>
<body>
<div class="breadcrumb"><a href="../index.html">All Courses</a> &rsaquo; {course_name}</div>
<h1>{course_name}</h1>
<p class="subtitle">{lesson_count} lessons</p>
<ol>
{lessons_html}
</ol>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

async def is_login_page(page) -> bool:
    """Check if the current page is a login/auth wall."""
    return await page.evaluate("""() => {
        const body = document.body?.innerText || '';
        return body.includes('To access premium content, please log in first')
            || body.includes('Welcome to ByteByteGo')
            && (document.querySelector('input[placeholder="Email"]') !== null);
    }""")


async def do_login(page):
    """Perform the Magic.link email+code login. Returns True on success.
    
    Opens the login form, fills in the email, submits it, then waits
    for the user to type the 6-digit code **directly in the Chromium
    window** that Playwright opened (no stdin needed).
    """
    print("[LOGIN] Navigating to bytebytego.com ...")
    await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    await asyncio.sleep(2)

    login_btn = page.locator("button:has-text('Login')")
    if await login_btn.count() == 0:
        if await page.locator("text=My Courses").count() > 0:
            print("[LOGIN] Already logged in!")
            return True
        email_input = page.locator("input[placeholder='Email']")
        if await email_input.count() == 0:
            print("[LOGIN] No Login button or email field found.")
            return False
    else:
        print("[LOGIN] Clicking Login ...")
        await login_btn.first.click()
        await asyncio.sleep(2)

    email_input = page.locator("input[placeholder='Email']")
    await email_input.wait_for(state="visible", timeout=10000)
    await email_input.fill(EMAIL)
    await asyncio.sleep(0.5)

    submit = page.locator("button:has-text('Log In / Sign Up')")
    await submit.click()
    print(f"[LOGIN] Code sent to {EMAIL}")
    print("[LOGIN]")
    print("[LOGIN] =====================================================")
    print("[LOGIN]  TYPE THE 6-DIGIT CODE IN THE CHROMIUM BROWSER WINDOW")
    print("[LOGIN]  (the code entry boxes visible on screen)")
    print("[LOGIN]  Waiting up to 120 seconds ...")
    print("[LOGIN] =====================================================")

    # Poll until "My Courses" appears (meaning login succeeded)
    for tick in range(120):
        await asyncio.sleep(1)
        try:
            if await page.locator("text=My Courses").count() > 0:
                print("[LOGIN] Login successful!")
                return True
        except Exception:
            pass
        if tick % 15 == 14:
            print(f"[LOGIN] Still waiting ... ({tick+1}s)")

    print("[LOGIN] Timed out waiting for login.")
    return False


async def ensure_logged_in(page, context):
    """If the page is showing a login wall, re-authenticate and save session."""
    if not await is_login_page(page):
        return True

    print("[AUTH] Session expired -- re-authenticating ...")
    ok = await do_login(page)
    if ok:
        await context.storage_state(path=str(SESSION_FILE))
        print("[AUTH] Session refreshed and saved.")
    return ok


# ---------------------------------------------------------------------------
# Lesson discovery
# ---------------------------------------------------------------------------

async def discover_lessons(page, context, course_slug):
    url = f"{BASE_URL}/courses/{course_slug}"
    print(f"  Discovering lessons at {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(4)

    if await is_login_page(page):
        await ensure_logged_in(page, context)
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)

    if course_slug == "coding-patterns":
        print("  Expanding all collapsible sections ...")
        await page.evaluate("""() => {
            document.querySelectorAll('button[aria-expanded="false"]').forEach(b => b.click());
        }""")
        await asyncio.sleep(2)

    # Strategy 1: __NEXT_DATA__
    nd = await page.evaluate("""(cs) => {
        const el = document.querySelector('#__NEXT_DATA__');
        if (!el) return null;
        const data = JSON.parse(el.textContent);
        const props = data.props?.pageProps || {};
        function norm(s) { return Array.isArray(s) ? s.join('/') : String(s); }
        let results = [];
        function walk(items) {
            if (!Array.isArray(items)) return;
            for (const c of items) {
                if (c.slug) results.push({ slug: norm(c.slug), title: c.title || c.name || norm(c.slug) });
                ['lessons','chapters','children','items'].forEach(k => { if (c[k]) walk(c[k]); });
            }
        }
        ['chapters','lessons','sections','toc','tableOfContents'].forEach(k => { if (props[k]) walk(props[k]); });
        return results;
    }""", course_slug)

    if nd and len(nd) > 2:
        seen, lessons = set(), []
        for item in nd:
            s = str(item["slug"])
            if s not in seen:
                seen.add(s)
                lessons.append({"slug": s, "title": str(item.get("title", s)),
                                "url": f"{BASE_URL}/courses/{course_slug}/{s}"})
        print(f"  Found {len(lessons)} lessons (via __NEXT_DATA__)")
        return lessons

    # Strategy 2: <a> hrefs in DOM
    links = await page.evaluate("""(cs) => {
        const prefix = '/courses/' + cs + '/';
        return [...document.querySelectorAll('a')].filter(a => {
            const h = a.getAttribute('href') || '';
            return h.startsWith(prefix) && a.innerText.trim();
        }).map(a => ({
            slug: (a.getAttribute('href')||'').substring(('/courses/'+cs+'/').length).replace(/\\/$/,''),
            title: a.innerText.trim()
        }));
    }""", course_slug)
    if links:
        seen, lessons = set(), []
        for lnk in links:
            if lnk["slug"] and lnk["slug"] not in seen:
                seen.add(lnk["slug"])
                lessons.append({"slug": lnk["slug"], "title": lnk["title"],
                                "url": f"{BASE_URL}/courses/{course_slug}/{lnk['slug']}"})
        if lessons:
            print(f"  Found {len(lessons)} lessons (via DOM links)")
            return lessons

    print("  WARNING: no lessons discovered")
    return []


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def sanitize_filename(name):
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '-', name).strip('-')
    return name[:100].lower()


def download_image(img_url, images_dir, session):
    try:
        ext = Path(urlparse(img_url).path).suffix or ".png"
        if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.avif'):
            ext = ".png"
        filename = f"img-{hashlib.md5(img_url.encode()).hexdigest()[:12]}{ext}"
        filepath = images_dir / filename
        if filepath.exists():
            return f"images/{filename}"
        resp = session.get(img_url, timeout=20)
        if resp.status_code == 200 and len(resp.content) > 100:
            filepath.write_bytes(resp.content)
            return f"images/{filename}"
    except Exception:
        pass
    return img_url


async def extract_content(page):
    """Pull the main lesson content HTML from the page (excluding nav/sidebar)."""
    return await page.evaluate("""() => {
        const remove = ['nav','header','footer','button',
            '[class*="sidebar"]','[class*="Sidebar"]',
            '[class*="banner"]','[class*="Banner"]',
            '[class*="topbar"]','[class*="TopBar"]'];
        const try_sel = ['article','[class*="prose"]',
            '[class*="content"]','[class*="Content"]',
            '[class*="lesson"]','[class*="Lesson"]',
            '[class*="chapter"]','[class*="Chapter"]','main'];
        for (const sel of try_sel) {
            const el = document.querySelector(sel);
            if (el && el.innerText.length > 200) {
                const c = el.cloneNode(true);
                remove.forEach(r => c.querySelectorAll(r).forEach(n => n.remove()));
                return c.innerHTML;
            }
        }
        let best=null, bLen=0;
        for (const d of document.querySelectorAll('div')) {
            const t = d.innerText||'';
            if (t.length>bLen && d.querySelectorAll('p,h1,h2,h3').length>1) { best=d; bLen=t.length; }
        }
        if (best) {
            const c = best.cloneNode(true);
            remove.forEach(r => c.querySelectorAll(r).forEach(n => n.remove()));
            return c.innerHTML;
        }
        return document.body.innerHTML;
    }""")


async def download_lesson(page, context, lesson, course_dir, course_name,
                          idx, total, all_lessons, http_session):
    title = lesson["title"]
    safe = sanitize_filename(title)
    filename = f"{idx:02d}-{safe}.html"
    filepath = course_dir / filename
    lesson["filename"] = filename

    if filepath.exists() and filepath.stat().st_size > MIN_CONTENT_SIZE:
        print(f"    [{idx+1}/{total}] OK (cached): {safe}")
        return True

    print(f"    [{idx+1}/{total}] Downloading: {safe}")

    async def safe_goto(url, retries=3):
        for attempt in range(retries):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                return True
            except Exception:
                if attempt < retries - 1:
                    print(f"    Retry {attempt+1} ...")
                    await asyncio.sleep(3)
        print(f"    ERROR: could not load {url}")
        return False

    if not await safe_goto(lesson["url"]):
        return False

    if await is_login_page(page):
        print(f"    [!] Login wall -- re-authenticating ...")
        ok = await ensure_logged_in(page, context)
        if not ok:
            print(f"    SKIP (auth failed): {safe}")
            return False
        if not await safe_goto(lesson["url"]):
            return False
        if await is_login_page(page):
            print(f"    SKIP (still login wall): {safe}")
            return False

    content_html = await extract_content(page)

    if len(content_html) < 300:
        print(f"    SKIP (content too short: {len(content_html)} chars)")
        return False

    images_dir = course_dir / "images"
    images_dir.mkdir(exist_ok=True)
    soup = BeautifulSoup(content_html, "html.parser")

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        local = download_image(urljoin(lesson["url"], src), images_dir, http_session)
        img["src"] = local
        for attr in ("srcset", "loading", "decoding"):
            if img.get(attr):
                del img[attr]

    prev_link = next_link = ""
    if idx > 0:
        p = all_lessons[idx-1]
        pf = p.get("filename", f"{idx-1:02d}-{sanitize_filename(p['title'])}.html")
        prev_link = f'<a href="{pf}">Prev</a>'
    if idx < total - 1:
        n = all_lessons[idx+1]
        nf = n.get("filename", f"{idx+1:02d}-{sanitize_filename(n['title'])}.html")
        next_link = f'<a href="{nf}">Next</a>'

    final = HTML_TEMPLATE.format(
        title=title, course_name=course_name,
        content=str(soup), prev_link=prev_link, next_link=next_link)

    filepath.write_text(final, encoding="utf-8")
    return True


# ---------------------------------------------------------------------------
# Index generators
# ---------------------------------------------------------------------------

def generate_course_index(course_dir, course_name, lessons):
    items = []
    for i, les in enumerate(lessons):
        fn = les.get("filename", f"{i:02d}-{sanitize_filename(les['title'])}.html")
        items.append(f'  <li><a href="{fn}">{les["title"]}</a></li>')
    html = COURSE_INDEX_TEMPLATE.format(
        course_name=course_name, lesson_count=len(lessons),
        lessons_html="\n".join(items))
    (course_dir / "index.html").write_text(html, encoding="utf-8")


def generate_master_index(all_course_data):
    cards = ""
    for folder, _, name, lessons in all_course_data:
        cards += f'<div class="course-card">\n  <h2><a href="{folder}/index.html">{name}</a></h2>\n'
        cards += f'  <p class="meta">{len(lessons)} lessons</p>\n  <ol>\n'
        for i, les in enumerate(lessons[:5]):
            fn = les.get("filename", f"{i:02d}-{sanitize_filename(les['title'])}.html")
            cards += f'    <li><a href="{folder}/{fn}">{les["title"]}</a></li>\n'
        if len(lessons) > 5:
            cards += f'    <li class="more"><a href="{folder}/index.html">... and {len(lessons)-5} more</a></li>\n'
        cards += '  </ol>\n</div>\n'
    total = sum(len(ls) for *_, ls in all_course_data)
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ByteByteGo Courses</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.6;color:#1a1a1a;max-width:900px;margin:0 auto;padding:2rem 1.5rem;background:#fff}}
h1{{font-size:2.2rem;margin-bottom:.3rem}}
.tagline{{color:#666;margin-bottom:2rem;font-size:1.05rem}}
.course-card{{border:1px solid #e5e5e5;border-radius:8px;padding:1.5rem;margin-bottom:1.2rem;transition:box-shadow .15s}}
.course-card:hover{{box-shadow:0 2px 12px rgba(0,0,0,.08)}}
.course-card h2{{font-size:1.3rem;margin-bottom:.3rem}}
.course-card h2 a{{color:#1a1a1a;text-decoration:none}}
.course-card h2 a:hover{{color:#10b981}}
.meta{{color:#888;font-size:.9rem;margin-bottom:.8rem}}
ol{{padding-left:1.5rem}} ol li{{margin:.2rem 0;font-size:.95rem}}
ol li a{{color:#555;text-decoration:none}} ol li a:hover{{color:#10b981}}
.more a{{color:#10b981!important;font-style:italic}}
</style></head><body>
<h1>ByteByteGo Courses</h1>
<p class="tagline">{len(all_course_data)} courses, {total} lessons -- Offline archive</p>
{cards}
</body></html>"""
    (OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
    print(f"\n[INDEX] Master index.html created ({len(all_course_data)} courses, {total} lessons)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print("=" * 60)
    print("  ByteByteGo Course Downloader  (v2 -- with login detection)")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        if SESSION_FILE.exists():
            print("[SESSION] Loading saved session ...")
            context = await browser.new_context(storage_state=str(SESSION_FILE))
        else:
            context = await browser.new_context()

        page = await context.new_page()

        # --- initial auth check ---
        print("[SESSION] Checking login state ...")
        await page.goto(f"{BASE_URL}/my-courses", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)

        if await is_login_page(page) or await page.locator("text=My Courses").count() == 0:
            print("[SESSION] Not logged in. Starting fresh login ...")
            ok = await do_login(page)
            if not ok:
                print("Login failed. Exiting.")
                await browser.close()
                return
            await context.storage_state(path=str(SESSION_FILE))
            print("[SESSION] Session saved.")
        else:
            print("[SESSION] Logged in!")
            await context.storage_state(path=str(SESSION_FILE))

        # http session for image downloads
        http_session = requests.Session()
        for c in await context.cookies():
            http_session.cookies.set(c["name"], c["value"], domain=c.get("domain", ""))

        all_course_data = []
        total_downloaded = 0
        total_skipped = 0

        for folder, slug, name in COURSES:
            print(f"\n{'='*60}")
            print(f"  COURSE: {name}")
            print(f"{'='*60}")

            course_dir = OUTPUT_DIR / folder
            course_dir.mkdir(exist_ok=True)
            (course_dir / "images").mkdir(exist_ok=True)

            lessons = await discover_lessons(page, context, slug)
            if not lessons:
                print(f"  SKIP: no lessons for {name}")
                continue

            for i, les in enumerate(lessons):
                ok = await download_lesson(page, context, les, course_dir, name,
                                           i, len(lessons), lessons, http_session)
                if ok:
                    total_downloaded += 1
                else:
                    total_skipped += 1
                await asyncio.sleep(1.2)

            generate_course_index(course_dir, name, lessons)
            all_course_data.append((folder, slug, name, lessons))
            print(f"  Done: {name} ({len(lessons)} lessons)")

        generate_master_index(all_course_data)
        await browser.close()

    print(f"\n{'='*60}")
    print(f"  COMPLETE  --  {total_downloaded} downloaded, {total_skipped} skipped")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
