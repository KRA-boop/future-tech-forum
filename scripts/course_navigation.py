"""Keep lesson return buttons pointing to the full YuRally category pages."""
import html
import re

WP_SITE = "https://yurally.wordpress.com"
PAGES_SITE = "https://kra-boop.github.io"
BASE = "/future-tech-forum"
LANGUAGES = {"zh", "en", "ja", "ko"}
CATEGORIES = {"attack", "defense", "basics", "gear", "match"}
BUTTON = re.compile(r'<a\b[^>]*class="[^"]*\bwp-block-button__link\b[^"]*"[^>]*>[^<]*</a>')
HREF = re.compile(r'href="([^"]+)"')


def wordpress_category_url(lang, category):
    assert lang in LANGUAGES and category in CATEGORIES
    prefix = "" if lang == "zh" else lang + "/"
    return f"{WP_SITE}/{prefix}{category}-lessons/"


def return_to_category(content, lang, category):
    """Change only the category-return button, preserving all other content."""
    old = f"{PAGES_SITE}{BASE}/yurally-courses/{lang}/{category}/"
    target = wordpress_category_url(lang, category)
    changed = 0

    def replace(match):
        nonlocal changed
        button = match.group(0)
        link = HREF.search(button)
        if link and html.unescape(link.group(1)) in (old, target):
            changed += 1
            return button[:link.start(1)] + target + button[link.end(1):]
        return button

    result = BUTTON.sub(replace, content)
    assert changed == 1, f"Expected exactly one category-return button for {lang}/{category}, found {changed}"
    return result
