"""Main-site left sidebar generator (v7, category groups). Run from the repo root: python3 scripts/build_sidebar.py .
Rewrites the sidebar CSS, aside markup, top bar and phone-drawer script on all 13 sidebar pages. Edit CATEGORIES to change the menu."""
import re, sys, pathlib

ROOT = pathlib.Path(sys.argv[1])

EXT = '<svg class="side-ext" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M8 7h9v9"/></svg>'

def icon(paths):
    return ('<svg class="side-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + paths + '</svg>')

ICONS = {
    'home': icon('<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V20h5v-6h4v6h5V9.5"/>'),
    'robotics': icon('<rect x="4" y="8" width="16" height="12" rx="2.5"/><path d="M12 8V4.5"/><circle cx="12" cy="3.5" r="1"/><path d="M9 13v1.5M15 13v1.5M9.5 17.5h5"/>'),
    'sports': icon('<path d="M7 4h10v5a5 5 0 0 1-10 0V4z"/><path d="M7 6H4.5a2.5 2.5 0 0 0 2.6 4"/><path d="M17 6h2.5a2.5 2.5 0 0 1-2.6 4"/><path d="M12 14v4M8.5 21h7M9.5 18h5"/>'),
    'gaming': icon('<rect x="2.5" y="7" width="19" height="11" rx="5"/><path d="M7 12.5h3.5M8.75 10.75v3.5"/><circle cx="15.5" cy="11.5" r=".6" fill="currentColor"/><circle cx="17.5" cy="13.75" r=".6" fill="currentColor"/>'),
    'construction': icon('<path d="M3 18h18"/><path d="M5 18v-2.5a7 7 0 0 1 14 0V18"/><path d="M10 9V5.5h4V9"/>'),
    'oilgas': icon('<path d="M12 3.5s6 6.4 6 10.8a6 6 0 0 1-12 0C6 9.9 12 3.5 12 3.5z"/><path d="M9.2 14.5a2.9 2.9 0 0 0 2.6 2.7"/>'),
}

def sub(label, href, ext=False, key=None):
    return {'label': label, 'href': href, 'ext': ext, 'key': key}

CATEGORIES = [
    ('robotics', 'Robotics &amp; Manufacturing', [
        sub('Object Detect', '/object-detect', key='od'),
        'LEVELS',
        sub('Robotic Surgery', 'https://avikravi.github.io/surgical-robotics-tissue-sim/dataset_viewer.html', ext=True),
    ]),
    ('sports', 'Sports', [
        sub('Kalshi', '/kalshi', ext=True),
        sub('Houston Texans', '/#houston-texans'),
        sub('Clutch Sports Data', '/projects.html#clutch-sports-data'),
        sub('muvve', 'https://muvve.com/', ext=True),
    ]),
    ('gaming', 'Gaming', [
        sub('AI Arcade', '/games', ext=True),
    ]),
    ('construction', 'Construction', [
        sub('TaskTag', 'https://tasktag.com/', ext=True),
    ]),
    ('oilgas', 'Oil &amp; Gas', [
        sub('Corrosion Pipeline', 'https://p66-vessel-integrity.vercel.app', ext=True),
    ]),
]


def build_aside(page):
    """page: 'home', 'projects', 'od', or 'level-N'."""
    in_od = page == 'od' or page.startswith('level-')
    out = []
    out.append('    <aside class="site-side%s" id="siteSide" aria-label="Site menu">' % (' in-od' if in_od else ''))
    out.append('        <div class="side-head">')
    out.append('            <a href="/" class="side-brand">')
    out.append('                <span class="side-brand-name">Avi Ravishankar</span>')
    out.append('                <span class="side-brand-role">AI/ML Engineer</span>')
    out.append('            </a>')
    out.append('            <button type="button" class="side-close" id="siteSideClose" aria-label="Close menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button>')
    out.append('        </div>')
    out.append('        <nav class="side-nav" aria-label="Main">')
    home_active = ' class="side-top active" aria-current="page"' if page == 'home' else ' class="side-top"'
    out.append('            <a href="/"%s>%sHome</a>' % (home_active, ICONS['home']))
    for key, label, items in CATEGORIES:
        current = ' current' if (key == 'robotics' and in_od) else ''
        out.append('            <div class="side-cat">')
        out.append('                <div class="side-cat-head%s">%s%s</div>' % (current, ICONS[key], label))
        out.append('                <div class="side-sub">')
        for item in items:
            if item == 'LEVELS':
                out.append('                    <div class="side-level-grid" aria-label="Object Detect levels">')
                for num in range(1, 11):
                    act = ' class="active" aria-current="page"' if page == 'level-%d' % num else ''
                    out.append('                        <a href="/object-detect/level-%d" title="Level %d"%s>%d</a>' % (num, num, act, num))
                out.append('                    </div>')
                continue
            cls = 'side-sub-link'
            extra = ''
            if item['key'] == 'od' and page == 'od':
                cls += ' active'
                extra = ' aria-current="page"'
            elif item['key'] == 'od' and in_od:
                cls += ' current'
            if item['ext']:
                extra += ' target="_blank" rel="noopener"'
            out.append('                    <a href="%s" class="%s"%s>%s%s</a>' % (
                item['href'], cls, extra, item['label'], EXT if item['ext'] else ''))
        out.append('                </div>')
        out.append('            </div>')
    out.append('        </nav>')
    out.append('    </aside>')
    out.append('    <div class="side-scrim" id="siteSideScrim" hidden></div>')
    return '\n'.join(out)


TOP_BAR = '''    <div class="top-bar">
        <button type="button" class="side-open" id="siteSideOpen" aria-controls="siteSide" aria-expanded="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>Menu</button>
        <a href="/AvinashResume2026.pdf" download class="nav-resume-btn">Download Resume</a>
    </div>'''

SCRIPT = '''    <script>
        /* Phone menu: the sidebar slides in as a drawer below 760px */
        (function () {
            var side = document.getElementById('siteSide');
            var openBtn = document.getElementById('siteSideOpen');
            var closeBtn = document.getElementById('siteSideClose');
            var scrim = document.getElementById('siteSideScrim');
            if (!side || !openBtn) return;
            function setOpen(open) {
                side.classList.toggle('open', open);
                scrim.hidden = !open;
                openBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
                document.body.classList.toggle('side-locked', open);
                if (open) closeBtn.focus(); else if (document.activeElement && side.contains(document.activeElement)) openBtn.focus();
            }
            openBtn.addEventListener('click', function () { setOpen(true); });
            closeBtn.addEventListener('click', function () { setOpen(false); });
            scrim.addEventListener('click', function () { setOpen(false); });
            side.addEventListener('click', function (e) {
                if (e.target.closest('a') && side.classList.contains('open')) setOpen(false);
            });
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && side.classList.contains('open')) setOpen(false);
            });
        })();
    </script>'''

CSS = '''/* Left sidebar nav (v7: category groups) */
        .site-side {
            position: fixed;
            top: 0; left: 0; bottom: 0;
            width: 248px;
            display: flex;
            flex-direction: column;
            background: #fafafa;
            border-right: 1px solid var(--line);
            padding: 20px 12px 28px;
            overflow-y: auto;
            z-index: 30;
        }

        .side-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; padding-bottom: 16px; margin-bottom: 12px; border-bottom: 1px solid var(--line); }
        .side-brand { display: block; padding: 4px 8px 0; text-decoration: none; }
        .side-brand-name { display: block; font-size: 15px; font-weight: 700; letter-spacing: -0.01em; color: #000; line-height: 1.25; }
        .side-brand-role { display: block; margin-top: 2px; font-size: 12.5px; color: var(--ink-faint); line-height: 1.35; }

        .side-nav { display: flex; flex-direction: column; gap: 14px; }

        /* Home: a main link */
        .side-top {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            color: var(--ink-soft);
            text-decoration: none;
            transition: background 0.15s, color 0.15s, box-shadow 0.15s;
        }
        .side-top:hover { background: #efefef; color: #000; }

        /* Category heading: a label, not a link */
        .side-cat-head {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 2px 8px 4px;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: -0.005em;
            color: var(--ink);
            line-height: 1.3;
        }

        .side-icon { width: 18px; height: 18px; flex-shrink: 0; color: var(--ink-faint); transition: color 0.15s; }
        .side-top:hover .side-icon,
        .side-top.active .side-icon,
        .side-cat-head.current .side-icon { color: #000; }
        .side-cat-head.current { color: #000; }
        .side-ext { width: 12px; height: 12px; margin-left: auto; flex-shrink: 0; color: var(--ink-faint); }

        /* Items inside a category: indented under a thin guide line */
        .side-sub {
            display: flex;
            flex-direction: column;
            gap: 1px;
            margin: 2px 0 0 16px;
            padding-left: 10px;
            border-left: 1px solid var(--line);
        }

        .side-sub-link {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 6px 8px;
            border-radius: 6px;
            font-size: 13.5px;
            color: var(--ink-soft);
            text-decoration: none;
            line-height: 1.3;
            transition: background 0.15s, color 0.15s;
        }
        .side-sub-link:hover { background: #efefef; color: #000; }
        .side-sub-link:hover .side-ext { color: #000; }
        .side-sub-link.current { color: #000; font-weight: 600; }

        .side-top.active,
        .side-sub-link.active {
            background: #fff;
            color: #000;
            font-weight: 600;
            box-shadow: 0 0 0 1px var(--line), 0 1px 2px rgba(0, 0, 0, 0.05);
        }

        .side-top:focus-visible,
        .side-sub-link:focus-visible,
        .side-level-grid a:focus-visible,
        .side-open:focus-visible,
        .side-close:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; }

        /* Object Detect level buttons: shown only on Object Detect pages */
        .side-level-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 5px;
            padding: 4px 2px 8px 8px;
        }
        .site-side:not(.in-od) .side-level-grid { display: none; }

        .side-level-grid a {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 26px;
            border: 1px solid var(--line);
            border-radius: 6px;
            background: #fff;
            font-size: 11.5px;
            font-weight: 600;
            color: var(--ink-soft);
            text-decoration: none;
            transition: border-color 0.15s, color 0.15s, background 0.15s;
        }
        .side-level-grid a:hover { border-color: #191919; color: #000; }
        .side-level-grid a.active { background: #191919; border-color: #191919; color: #fff; }

        /* Phone menu controls (hidden on desktop) */
        .side-open, .side-close, .side-scrim { display: none; }

        .site-main { margin-left: 248px; }

        /* Sidebar links that jump to a card (/#houston-texans) land with breathing room */
        :target { scroll-margin-top: 24px; }

        /* Top bar: resume button (plus the Menu button on phones) */
        .top-bar {
            border-bottom: 1px solid var(--line);
            padding: 14px 24px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 12px;
        }

        .nav-resume-btn {
            padding: 8px 16px;
            background: #191919;
            border-radius: 6px;
            color: #fff;
            font-size: 11.5px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            text-decoration: none;
            transition: background 0.15s;
        }

        .nav-resume-btn:hover { background: #000; }

        @media (max-width: 760px) {
            .site-side {
                width: min(300px, 86vw);
                padding: 16px 14px 28px;
                transform: translateX(-100%);
                visibility: hidden;
                transition: transform 0.22s ease, visibility 0s linear 0.22s;
                box-shadow: none;
                z-index: 50;
            }
            .site-side.open { transform: translateX(0); visibility: visible; transition: transform 0.22s ease; box-shadow: 0 0 40px rgba(0, 0, 0, 0.18); }
            .side-close {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 36px; height: 36px;
                margin: -4px -4px 0 0;
                border: none;
                border-radius: 8px;
                background: transparent;
                color: var(--ink-soft);
                cursor: pointer;
            }
            .side-close:hover { background: #efefef; color: #000; }
            .side-close svg { width: 20px; height: 20px; }
            .side-scrim { display: block; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.32); z-index: 40; }
            .side-scrim[hidden] { display: none; }
            .side-top, .side-sub-link { padding-top: 9px; padding-bottom: 9px; }
            .side-level-grid a { height: 32px; }
            body.side-locked { overflow: hidden; }

            .site-main { margin-left: 0; }
            :target { scroll-margin-top: 76px; }
            .top-bar {
                position: sticky;
                top: 0;
                z-index: 20;
                background: var(--bg);
                padding: 10px 16px;
                justify-content: space-between;
            }
            .side-open {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 7px 12px 7px 10px;
                border: 1px solid var(--line);
                border-radius: 6px;
                background: #fff;
                font: inherit;
                font-size: 13.5px;
                font-weight: 600;
                color: var(--ink);
                cursor: pointer;
            }
            .side-open svg { width: 18px; height: 18px; }
            .side-open:hover { border-color: #191919; }
        }

        @media (prefers-reduced-motion: reduce) {
            .site-side { transition: none; }
        }'''


def css_span(src):
    start = src.index('/* Left sidebar nav')
    media = src.index('@media (max-width: 760px) {', start)
    i = src.index('{', media)
    depth = 0
    for j in range(i, len(src)):
        if src[j] == '{':
            depth += 1
        elif src[j] == '}':
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    # also swallow a previously generated reduced-motion block
    rest = src[end:]
    m = re.match(r'\s*@media \(prefers-reduced-motion: reduce\) \{\s*\.site-side \{ transition: none; \}\s*\}', rest)
    if m:
        end += m.end()
    return start, end


def rewrite(path, page):
    src = path.read_text()
    start, end = css_span(src)
    src = src[:start] + CSS + src[end:]
    src, n1 = re.subn(r'    <aside class="site-side.*?</aside>\n(    <div class="side-scrim"[^\n]*\n)?', lambda m: build_aside(page) + '\n', src, count=1, flags=re.S)
    src, n2 = re.subn(r'    <div class="top-bar">.*?\n    </div>', lambda m: TOP_BAR, src, count=1, flags=re.S)
    src = re.sub(r'\n    <script>\n        /\* Phone menu: .*?</script>(?=\n)', '', src, flags=re.S)
    src, n3 = re.subn(r'\n([ \t]*)</body>', lambda m: '\n' + SCRIPT + '\n' + m.group(1) + '</body>', src, count=1)
    assert (n1, n2, n3) == (1, 1, 1), (path, n1, n2, n3)
    path.write_text(src)


PAGES = [('index.html', 'home'), ('projects.html', 'projects'), ('object-detect/index.html', 'od')]
PAGES += [('object-detect/level-%d/index.html' % n, 'level-%d' % n) for n in range(1, 11)]
for rel, page in PAGES:
    rewrite(ROOT / rel, page)
    print('ok', rel)
