"""
Adds navigation to all System Design HTM files:
  1. Generates an index.html with grouped chapter cards
  2. Injects a sticky top navbar with dropdown menu into each .htm file
  3. Injects prev/next chapter links at the bottom of each page
"""
import os, re

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# ── Chapter definitions: (title, filename) in order ──────────────────────────

CATEGORIES = [
    ("Fundamentals", [
        ("Scale from Zero to Million Users",           "Scale-from-zero-to-million-users.htm"),
        ("Back of Envelope Estimation",                "back-of-envelope-estimation.htm"),
        ("Framework for System Design",                "Framework-for-system-design.htm"),
        ("Design Content Hashing",                     "Design-content-hashing.htm"),
        ("Design Key-Value Store",                     "Design-Key-Value-Store.htm"),
        ("Design a Unique ID Generator",               "Design-a-unique-id-gemnerator-in-distributed-systems.htm"),
        ("Design Rate Limiter",                        "Design-rate-limiter.htm"),
    ]),
    ("Core Applications", [
        ("Design a URL Shortener",                     "Design-a-url-shortner.htm"),
        ("Design a Web Crawler",                       "Design-a-web-crawler.htm"),
        ("Design a Notification System",               "Design-a-notification-system.htm"),
        ("Design a News Feed System",                  "Design-news-feed-system.htm"),
        ("Design a Chat System",                       "Design-chat-system.htm"),
        ("Design Search Autocomplete",                 "Design-search-automatic-complete.htm"),
        ("Design YouTube",                             "Design-youtube.htm"),
        ("Design Google Drive",                        "Design-google-drive.htm"),
    ]),
    ("Location & Proximity", [
        ("Proximity Service",                          "Proximity-Service.htm"),
        ("Nearby Friends",                             "Nearby-friends.htm"),
        ("Google Maps",                                "Google-maps.htm"),
    ]),
    ("Distributed Infrastructure", [
        ("Distributed Message Queue",                  "Distributed-Messege-queue.htm"),
        ("Metrics Monitoring & Alerting System",       "Metrics-Monitoring-and-Alerting-System.htm"),
        ("Ad Click Event Aggregation",                 "Ad-Click-Event-Aggregation.htm"),
        ("Hotel Reservation System",                   "Hotel-reservation-System.htm"),
        ("Distributed Email Service",                  "Distributed-Email-Service.htm"),
        ("S3-like Object Storage",                     "S3-like-object-storage.htm"),
        ("Real-time Gaming Leaderboard",               "Real-time-gaming-leaderboard.htm"),
        ("Payment System",                             "Payment-System.htm"),
        ("Digital Wallet",                             "Digital-Wallet.htm"),
        ("Stock Exchange",                             "Stock-Exchange.htm"),
    ]),
    ("Appendix", [
        ("Learning Continues",                         "Learning-Continues.htm"),
    ]),
]

# Flat ordered list for prev/next
FLAT_CHAPTERS = []
ch_num = 1
for _, chapters in CATEGORIES:
    for title, filename in chapters:
        FLAT_CHAPTERS.append((ch_num, title, filename))
        ch_num += 1


# ── Shared CSS for navbar + prev/next (scoped with sdnav- prefix) ────────────

NAV_CSS = """
<style id="sdnav-styles">
.sdnav-bar {
    position: sticky; top: 0; z-index: 10000;
    display: flex; align-items: center; justify-content: space-between;
    background: #1a1a2e; color: #fff;
    padding: 0 24px; height: 52px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.sdnav-bar a { color: #fff; text-decoration: none; }
.sdnav-brand { font-weight: 700; font-size: 16px; letter-spacing: 0.5px; }
.sdnav-links { display: flex; align-items: center; gap: 20px; }
.sdnav-links a:hover { color: #35ddac; }
.sdnav-dropdown { position: relative; }
.sdnav-dropdown-btn {
    background: none; border: 1px solid rgba(255,255,255,0.25);
    color: #fff; padding: 6px 14px; border-radius: 6px; cursor: pointer;
    font-size: 13px; font-family: inherit;
}
.sdnav-dropdown-btn:hover { border-color: #35ddac; color: #35ddac; }
.sdnav-dropdown-panel {
    display: none; position: absolute; right: 0; top: 42px;
    background: #fff; color: #333; border-radius: 8px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.18); width: 340px;
    max-height: 80vh; overflow-y: auto; padding: 12px 0;
    z-index: 10001;
}
.sdnav-dropdown-panel.sdnav-open { display: block; }
.sdnav-cat-label {
    padding: 8px 18px 4px; font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px; color: #999;
}
.sdnav-dropdown-panel a {
    display: block; padding: 7px 18px; color: #333;
    font-size: 13px; text-decoration: none; line-height: 1.4;
}
.sdnav-dropdown-panel a:hover { background: #f0faf5; color: #0a8f38; }
.sdnav-dropdown-panel a.sdnav-active { color: #0a8f38; font-weight: 600; }

/* Hamburger for mobile */
.sdnav-hamburger {
    display: none; background: none; border: none; color: #fff;
    font-size: 22px; cursor: pointer; padding: 4px 8px; line-height: 1;
}
.sdnav-mobile-menu {
    display: none; position: fixed; top: 52px; left: 0; right: 0; bottom: 0;
    background: #fff; z-index: 10001; overflow-y: auto; padding: 12px 0;
}
.sdnav-mobile-menu.sdnav-open { display: block; }
.sdnav-mobile-menu .sdnav-cat-label {
    padding: 12px 20px 4px; font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px; color: #999;
}
.sdnav-mobile-menu a {
    display: block; padding: 10px 20px; color: #333;
    font-size: 15px; text-decoration: none; border-bottom: 1px solid #f0f0f0;
}
.sdnav-mobile-menu a:hover { background: #f0faf5; }
.sdnav-mobile-menu a.sdnav-active { color: #0a8f38; font-weight: 600; }

/* Prev/Next navigation */
.sdnav-prevnext {
    display: flex; justify-content: space-between; gap: 16px;
    margin: 40px 0 20px; padding: 20px 0;
    border-top: 1px solid #e0e0e0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.sdnav-prevnext a {
    display: flex; flex-direction: column; gap: 4px;
    padding: 12px 16px; border-radius: 8px; text-decoration: none;
    color: #333; background: #f7f7f7; transition: background 0.2s;
    max-width: 48%; min-width: 0;
}
.sdnav-prevnext a:hover { background: #e8f5ee; }
.sdnav-prevnext-label { font-size: 12px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }
.sdnav-prevnext-title { font-size: 14px; font-weight: 600; color: #1a1a2e; }
.sdnav-prevnext .sdnav-next { margin-left: auto; text-align: right; }

@media screen and (max-width: 768px) {
    .sdnav-links { display: none; }
    .sdnav-hamburger { display: block; }
    .sdnav-prevnext { flex-direction: column; }
    .sdnav-prevnext a { max-width: 100%; }
    .sdnav-prevnext .sdnav-next { text-align: left; }
}
</style>
"""

NAV_JS = """
<script>
(function(){
    var db = document.querySelector('.sdnav-dropdown-btn');
    var dp = document.querySelector('.sdnav-dropdown-panel');
    if(db && dp) {
        db.addEventListener('click', function(e){
            e.stopPropagation();
            dp.classList.toggle('sdnav-open');
        });
        document.addEventListener('click', function(){ dp.classList.remove('sdnav-open'); });
    }
    var hb = document.querySelector('.sdnav-hamburger');
    var mm = document.querySelector('.sdnav-mobile-menu');
    if(hb && mm) {
        hb.addEventListener('click', function(){
            var open = mm.classList.toggle('sdnav-open');
            hb.textContent = open ? '\\u2715' : '\\u2630';
        });
    }
})();
</script>
"""


def build_dropdown_links(current_file=None):
    """Build the HTML for the chapter links in the dropdown and mobile menu."""
    html = ""
    for cat_name, chapters in CATEGORIES:
        html += f'<div class="sdnav-cat-label">{cat_name}</div>\n'
        for ch_num, title, filename in FLAT_CHAPTERS:
            if any(filename == f for _, f in chapters):
                active = ' class="sdnav-active"' if filename == current_file else ''
                html += f'<a href="{filename}"{active}>{ch_num}. {title}</a>\n'
    return html


def build_navbar_html(current_file):
    """Build the full navbar HTML for a chapter page."""
    dropdown_links = build_dropdown_links(current_file)
    return f"""
{NAV_CSS}
<nav class="sdnav-bar">
    <a href="index.html" class="sdnav-brand">System Design</a>
    <div class="sdnav-links">
        <a href="index.html">Home</a>
        <div class="sdnav-dropdown">
            <button class="sdnav-dropdown-btn">Chapters &#9662;</button>
            <div class="sdnav-dropdown-panel">
{dropdown_links}
            </div>
        </div>
    </div>
    <button class="sdnav-hamburger" aria-label="Menu">&#9776;</button>
</nav>
<div class="sdnav-mobile-menu">
    <a href="index.html" style="font-weight:600;">Home</a>
{dropdown_links}
</div>
{NAV_JS}
"""


def build_prevnext_html(chapter_index):
    """Build prev/next navigation HTML for a chapter at the given flat index."""
    prev_html = ""
    next_html = ""
    if chapter_index > 0:
        pn, pt, pf = FLAT_CHAPTERS[chapter_index - 1]
        prev_html = f"""<a href="{pf}" class="sdnav-prev">
    <span class="sdnav-prevnext-label">&larr; Previous</span>
    <span class="sdnav-prevnext-title">{pn}. {pt}</span>
</a>"""
    if chapter_index < len(FLAT_CHAPTERS) - 1:
        nn, nt, nf = FLAT_CHAPTERS[chapter_index + 1]
        next_html = f"""<a href="{nf}" class="sdnav-next">
    <span class="sdnav-prevnext-label">Next &rarr;</span>
    <span class="sdnav-prevnext-title">{nn}. {nt}</span>
</a>"""
    return f'<div class="sdnav-prevnext">{prev_html}{next_html}</div>'


def generate_index_html():
    """Generate the index.html homepage."""
    cards = ""
    ch = 1
    for cat_name, chapters in CATEGORIES:
        cards += f'<h2 class="sdidx-cat">{cat_name}</h2>\n<div class="sdidx-grid">\n'
        for title, filename in chapters:
            cards += f"""<a href="{filename}" class="sdidx-card">
    <span class="sdidx-ch">{ch}</span>
    <span class="sdidx-title">{title}</span>
</a>\n"""
            ch += 1
        cards += '</div>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<title>System Design - Study Notes</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f5; color: #333;
}}
.sdidx-header {{
    background: #1a1a2e; color: #fff; padding: 48px 24px 40px; text-align: center;
}}
.sdidx-header h1 {{ font-size: 2em; font-weight: 800; margin-bottom: 8px; }}
.sdidx-header p {{ font-size: 1.05em; color: rgba(255,255,255,0.7); }}
.sdidx-main {{ max-width: 1000px; margin: 0 auto; padding: 24px; }}
.sdidx-cat {{
    font-size: 1.15em; font-weight: 700; color: #1a1a2e;
    margin: 32px 0 14px; padding-bottom: 8px;
    border-bottom: 2px solid #35ddac;
}}
.sdidx-grid {{
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
}}
.sdidx-card {{
    display: flex; align-items: center; gap: 14px;
    background: #fff; border-radius: 10px; padding: 16px 18px;
    text-decoration: none; color: #333;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: box-shadow 0.2s, transform 0.2s;
}}
.sdidx-card:hover {{
    box-shadow: 0 4px 16px rgba(0,0,0,0.1); transform: translateY(-2px);
}}
.sdidx-ch {{
    flex-shrink: 0; width: 36px; height: 36px; border-radius: 50%;
    background: #1a1a2e; color: #35ddac; font-weight: 700; font-size: 14px;
    display: flex; align-items: center; justify-content: center;
}}
.sdidx-title {{ font-size: 14px; font-weight: 600; line-height: 1.35; }}
.sdidx-footer {{
    text-align: center; padding: 24px; color: #999; font-size: 13px;
    margin-top: 32px;
}}

@media screen and (max-width: 768px) {{
    .sdidx-grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }}
    .sdidx-header {{ padding: 32px 16px 28px; }}
    .sdidx-header h1 {{ font-size: 1.5em; }}
    .sdidx-main {{ padding: 16px; }}
}}
@media screen and (max-width: 480px) {{
    .sdidx-grid {{ grid-template-columns: 1fr; }}
    .sdidx-card {{ padding: 14px; }}
}}
</style>
</head>
<body>
<div class="sdidx-header">
    <h1>System Design</h1>
    <p>29 chapters covering fundamentals to advanced distributed systems</p>
</div>
<main class="sdidx-main">
{cards}
</main>
<div class="sdidx-footer">System Design Study Notes</div>
</body>
</html>
"""


def inject_into_file(filepath, current_filename, chapter_index):
    """Inject navbar and prev/next into a single .htm file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already injected
    if 'id="sdnav-styles"' in content:
        print(f"  SKIP (already has nav): {current_filename}")
        return False

    navbar_html = build_navbar_html(current_filename)
    prevnext_html = build_prevnext_html(chapter_index)

    # Inject navbar right after <body> tag
    body_match = re.search(r'<body[^>]*>', content)
    if body_match:
        insert_pos = body_match.end()
        content = content[:insert_pos] + navbar_html + content[insert_pos:]

    # Inject prev/next before the last </article>
    last_article = content.rfind('</article>')
    if last_article >= 0:
        content = content[:last_article] + prevnext_html + content[last_article:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  INJECTED: {current_filename}")
    return True


def main():
    # Generate index.html
    index_path = os.path.join(DIRECTORY, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(generate_index_html())
    print(f"Generated index.html\n")

    # Inject nav into each chapter file
    injected = 0
    for i, (ch_num, title, filename) in enumerate(FLAT_CHAPTERS):
        filepath = os.path.join(DIRECTORY, filename)
        if not os.path.exists(filepath):
            print(f"  MISSING: {filename}")
            continue
        if inject_into_file(filepath, filename, i):
            injected += 1

    print(f"\nDone! Injected navigation into {injected}/{len(FLAT_CHAPTERS)} files.")


if __name__ == '__main__':
    main()
