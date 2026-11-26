"""Build the four-language full courses from the published WordPress content."""
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = '/future-tech-forum'
SITE = 'https://kra-boop.github.io' + BASE
VERSION = '20261120-gold-1'
LANGS = {'zh': '中文', 'en': 'ENG', 'ja': '日本語', 'ko': '한국어'}
TEXT = {
    'zh': dict(home='首頁', courses='課程總覽', faq='常見問答', menu='課程分類', all='全部課程', selfcheck='自我檢核', source='WordPress 課程原文', categories=['基礎技術', '進攻技巧', '防守技巧', '裝備指南', '賽事觀察']),
    'en': dict(home='Home', courses='All courses', faq='FAQ', menu='Course categories', all='All courses', selfcheck='Self-check', source='Original WordPress course', categories=['Basic techniques', 'Attack', 'Defense', 'Equipment', 'Match observation']),
    'ja': dict(home='ホーム', courses='講座一覧', faq='よくある質問', menu='講座カテゴリー', all='すべての講座', selfcheck='セルフチェック', source='WordPress の元の講座', categories=['基本技術', '攻撃', '守備', '用具ガイド', '試合観察']),
    'ko': dict(home='홈', courses='전체 강좌', faq='자주 묻는 질문', menu='강좌 분류', all='전체 강좌', selfcheck='자가 점검', source='WordPress 원문 강좌', categories=['기초 기술', '공격 기술', '수비 기술', '장비 가이드', '경기 관찰']),
}
CATEGORIES = ['basics', 'attack', 'defense', 'gear', 'match']
CODE_CATEGORY = dict(zip('BADGM', CATEGORIES))
records = json.loads((ROOT / 'data/yurally-courses-source.json').read_text())
assert len(records) == 196
by_key = {(r['lang'], r['slug']): r for r in records}
assert len(by_key) == 196
urls = {urlsplit(r['link']).path.rstrip('/'): f"{SITE}/yurally-courses/{r['lang']}/{r['slug']}/" for r in records}

def esc(value):
    return html.escape(value, quote=True)

def course_url(lang, slug):
    return f'{BASE}/yurally-courses/{lang}/{slug}/'

def directory_url(lang, category=None):
    return f'{BASE}/yurally-courses/{lang}/' + (f'{category}/' if category else '')

def home(lang):
    return 'https://yurally.wordpress.com/' + ('' if lang == 'zh' else lang + '/')

def rewrite_link(match):
    value = html.unescape(match.group(1))
    parsed = urlsplit(value)
    if parsed.hostname == 'yurally.wordpress.com':
        target = urls.get(parsed.path.rstrip('/'))
        if target:
            return 'href="' + esc(target + ('#' + parsed.fragment if parsed.fragment else '')) + '"'
        parts = parsed.path.strip('/').split('/')
        link_lang = parts[0] if parts[0] in LANGS else 'zh'
        section = parts[-1]
        categories = {'basics-lessons': 'basics', 'attack-lessons': 'attack', 'defense-lessons': 'defense', 'gear-lessons': 'gear', 'match-lessons': 'match'}
        if section == 'articles' or section in categories:
            return 'href="https://kra-boop.github.io' + directory_url(link_lang, categories.get(section)) + '"'
        if parsed.path.rstrip('/').endswith('/faq'):
            lang = next((l for l in LANGS if parsed.path.startswith('/' + l + '/')), 'zh')
            return f'href="{SITE}/yurally-faq/?lang={lang}"'
    return match.group(0)

def embed(match):
    attrs = json.loads(match.group(1))
    url = attrs.get('url', '')
    parsed = urlsplit(url)
    video_id = parse_qs(parsed.query).get('v', [''])[0] or (parsed.path.lstrip('/') if parsed.hostname == 'youtu.be' else '')
    if attrs.get('providerNameSlug') == 'youtube' and re.fullmatch(r'[\w-]{11}', video_id):
        return f'<figure class="course-video"><iframe src="https://www.youtube-nocookie.com/embed/{video_id}" title="BWF YouTube" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe><figcaption><a href="{esc(url)}">YouTube</a></figcaption></figure>'
    return re.sub(r'<!--.*?-->', '', match.group(0), flags=re.S)

def body(record):
    text = record['content']
    text = re.sub(r'<!-- wp:embed (\{.*?\}) -->.*?<!-- /wp:embed -->', embed, text, flags=re.S)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    details = re.findall(r'<details\b[^>]*>\s*<summary[^>]*>(.*?)</summary>(.*?)</details>', text, re.S)
    assert len(details) == 1, record['id']
    question, answer = details[0]
    answer = re.sub(r'^\s*<div[^>]*class="[^"]*answer[^"]*"[^>]*>(.*)</div>\s*$', r'\1', answer, flags=re.S)
    replacement = '<details class="yurally-self-check" data-self-check><summary>' + question.strip() + '</summary><div class="answer">' + answer.strip() + '</div></details>'
    text = re.sub(r'<details\b[^>]*>.*?</details>', lambda _: replacement, text, count=1, flags=re.S)
    label = TEXT[record['lang']]['selfcheck']
    text, count = re.subn(r'<h2\b[^>]*id="self-check"[^>]*>.*?</h2>', '<h2 id="self-check">' + label + '</h2>', text, count=1, flags=re.S)
    assert count == 1, record['id']
    return re.sub(r'href="([^"]+)"', rewrite_link, text)

def category(record):
    first = re.search(r'<p\b[^>]*>(.*?)</p>', record['content'], re.S).group(1)
    code = re.search(r'([BADGM]\d{2})', first)
    assert code, record['id']
    return CODE_CATEGORY[code.group(1)[0]], code.group(1)

def social():
    return '<footer class="social-links"><a href="https://www.instagram.com/kraven_hun/" target="_blank" rel="noopener noreferrer"><img src="https://yurally.wordpress.com/wp-content/uploads/2026/11/yurally-instagram.png" alt="Instagram"></a><a href="https://www.threads.com/@kraven_hun" target="_blank" rel="noopener noreferrer"><img src="https://yurally.wordpress.com/wp-content/uploads/2026/11/yurally-threads.png" alt="Threads"></a></footer>'

def navigation(lang, slug=None, selected=None):
    t = TEXT[lang]
    nav = f'<nav class="site-nav" aria-label="YuRally"><a href="{home(lang)}">YuRally · {t["home"]}</a><a href="{directory_url(lang)}">{t["courses"]}</a><a href="{BASE}/yurally-faq/?lang={lang}">{t["faq"]}</a></nav>'
    links = []
    for other, label in LANGS.items():
        url = course_url(other, slug) if slug else directory_url(other, selected)
        links.append(f'<a href="{url}" lang="{("zh-Hant" if other == "zh" else other)}" data-language="{other}"' + (' aria-current="page"' if other == lang else '') + f'>{label}</a>')
    nav += '<nav class="languages" aria-label="Language">' + ''.join(links) + '</nav>'
    nav += '<details class="course-menu"><summary>' + t['menu'] + '</summary><nav class="answer">'
    for cat, label in [(None, t['all']), *zip(CATEGORIES, t['categories'])]:
        nav += f'<a href="{directory_url(lang, cat)}"' + (' aria-current="page"' if selected == cat else '') + f'>{label}</a>'
    return nav + '</nav></details>'

def document(lang, title, content, slug=None, selected=None):
    canonical = course_url(lang, slug) if slug else directory_url(lang, selected)
    return f'''<!doctype html>
<html lang="{'zh-Hant' if lang == 'zh' else lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}｜YuRally</title><link rel="canonical" href="https://kra-boop.github.io{canonical}">
<link rel="stylesheet" href="{BASE}/assets/courses.css?v={VERSION}"><script defer src="{BASE}/assets/disclosures.js?v={VERSION}"></script><script defer src="{BASE}/assets/courses.js?v={VERSION}"></script>
</head><body><main data-course="{esc(slug or '')}" data-language="{lang}">{navigation(lang, slug, selected)}<h1>{esc(title)}</h1>{content}{social()}</main></body></html>'''

manifest = []
for record in records:
    lang, slug = record['lang'], record['slug']
    title = html.unescape(record['title'])
    cat, code = category(record)
    rendered = body(record)
    content = f'<article class="lesson-body">{rendered}</article>'
    out = ROOT / 'yurally-courses' / lang / slug / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(document(lang, title, content, slug, cat))
    question = re.search(r'<summary>(.*?)</summary>', rendered, re.S).group(1)
    manifest.append(dict(id=record['id'], lang=lang, slug=slug, title=title, category=cat, code=code, url=course_url(lang, slug), wordpress_url=record['link'], question=html.unescape(re.sub('<[^>]*>', '', question))))

for lang in LANGS:
    for selected in [None, *CATEGORIES]:
        items = sorted((r for r in manifest if r['lang'] == lang and (selected is None or r['category'] == selected)), key=lambda r: (CATEGORIES.index(r['category']), r['code']))
        content = '<p>' + str(len(items)) + ' · YuRally</p><ul class="course-list">'
        for item in items:
            content += f'<li><a href="{item["url"]}"><small>{item["code"]}</small>{esc(item["title"])}</a></li>'
        content += '</ul>'
        title = TEXT[lang]['courses'] if selected is None else TEXT[lang]['categories'][CATEGORIES.index(selected)]
        out = ROOT / 'yurally-courses' / lang
        if selected:
            out /= selected
        out.mkdir(parents=True, exist_ok=True)
        (out / 'index.html').write_text(document(lang, title, content, selected=selected))
        if lang == 'zh' and selected is None:
            (ROOT / 'yurally-courses/index.html').write_text(document(lang, title, content))

(ROOT / 'yurally-courses/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
faq = ROOT / 'yurally-faq/index.html'
faq.write_text(re.sub(r'href="([^"]+)"', rewrite_link, faq.read_text()))
# Legacy self-check links now open the complete course, with the check in place.
(ROOT / 'self-check.html').write_text('''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>羽你同行課程</title></head><body><p><a href="./yurally-courses/">羽你同行課程 · YuRally</a></p><script>
const slug = decodeURIComponent(location.hash.slice(1));
const requested = new URLSearchParams(location.search).get('lang') || 'zh';
const lang = ['zh','en','ja','ko'].includes(requested) ? requested : 'zh';
fetch('./yurally-courses/manifest.json').then(r => r.json()).then(rows => {
  const lesson = rows.find(row => row.slug === slug && row.lang === lang);
  location.replace(lesson ? lesson.url + '#self-check' : './yurally-courses/' + lang + '/');
});</script></body></html>''')
print(json.dumps({'courses': len(manifest), 'languages': {l: sum(r['lang'] == l for r in manifest) for l in LANGS}, 'source_questions': len(set((r['lang'], r['slug']) for r in manifest))}))
