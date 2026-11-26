"""Add the localized lesson video guide without disturbing other course content."""
import html
import json
import re
from pathlib import Path

GUIDE = json.loads(
    (Path(__file__).resolve().parents[1] / "data/yurally-course-videos.json").read_text()
)
FIGURE = re.compile(r'<figure class="course-video">.*?</figure>', re.S)
VIDEO_ID = re.compile(r'youtube-nocookie\.com/embed/([\w-]{11})')
GROUP = '<div class="wp-block-group yurally-video-guide has-text-color has-background has-border-color" style="margin-top:20px;margin-bottom:0;padding-top:22px;padding-right:22px;padding-bottom:22px;padding-left:22px;color:#F3FAFB;background-color:#082B38;border-radius:14px;border-color:#28505A;border-width:1px;border-style:solid">'


def esc(value):
    return html.escape(value, quote=True)


def link(ident):
    return f'href="https://www.youtube.com/watch?v={ident}" target="_blank" rel="noopener noreferrer"'


def figure(ident):
    meta = GUIDE["videos"][ident]
    title = esc(meta["author"] + " — " + meta["title"])
    credit = esc(meta["author"] + "｜" + meta["title"])
    return (f'<figure class="course-video"><iframe src="https://www.youtube-nocookie.com/embed/{ident}" title="{title}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" '
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
            f'<figcaption>{credit} · <a {link(ident)}>YouTube</a></figcaption></figure>')


def video(ident, lang):
    label = esc(GUIDE["labels"][lang]["link"])
    return figure(ident) + f'\n<p style="font-size:15px;line-height:1.8"><a {link(ident)}>{label}</a></p>\n'


def notes(slug, lang):
    label = GUIDE["labels"][lang]
    note = GUIDE["lessons"][slug]["notes"][lang]
    punctuation = "：" if lang == "zh" else ": "
    return "".join(f'<p class="yurally-video-{key}"><strong>{esc(label[key])}{punctuation}</strong>{esc(note[key])}</p>\n'
                   for key in ("watch", "practice"))


def add_video_html(content, slug, lang):
    """Idempotent static HTML insertion; keep the original BWF videos and text."""
    planned = GUIDE["lessons"][slug]["ids"]
    existing = [VIDEO_ID.search(m.group()).group(1) for m in FIGURE.finditer(content)]
    assert len(set(existing)) == len(existing) and set(existing).issubset(planned), slug
    if 'class="yurally-video-watch"' in content:
        assert existing == planned, slug
        return content
    if existing:
        content = FIGURE.sub(lambda m: figure(VIDEO_ID.search(m.group()).group(1)), content)
        last = list(FIGURE.finditer(content))[-1].end()
        new = "\n" + "".join(video(i, lang) for i in planned if i not in existing) + notes(slug, lang)
        return content[:last] + new + content[last:]
    anchor = content.index('<h2 id="self-check">')
    position = content.rfind('<div class="wp-block-group', 0, anchor)
    assert position >= 0 and '</div>' not in content[position:anchor], slug
    heading = esc(GUIDE["labels"][lang]["heading"])
    new = (GROUP + f'<h2 class="wp-block-heading" id="lesson-video" style="margin-top:0;margin-bottom:18px;font-size:27px;font-weight:650;line-height:1.35">{heading}</h2>\n'
           + "".join(video(i, lang) for i in planned) + notes(slug, lang) + '</div>\n')
    return content[:position] + new + content[position:]
