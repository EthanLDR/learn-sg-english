#!/usr/bin/env python3
"""Render every committed lesson without editing its source; fail on archive loss."""
from __future__ import annotations
import hashlib
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import mistune
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
MD = mistune.create_markdown(escape=True, hard_wrap=True, plugins=['table', 'strikethrough', 'url'])
HEAD = re.compile(r'^h[1-6]$')
DATE = re.compile(r'<!--\s*lesson-date:\s*(\d{4}-\d{2}-\d{2})\s*-->')
REVIEW = re.compile(r'compact\s*review|今日.*复习|今日速记|今日复习卡|今日\s*\d+\s*句.*复习', re.I)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def git_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def normalized(text: str) -> str:
    return re.sub(r'\s+', '', text)


def render(raw: str, key: str, transcript: bool = False) -> tuple[str, str, str, str]:
    """Return body, local TOC, review HTML and review anchor. Only markup changes."""
    cleaned = DATE.sub('', raw)
    if transcript:
        cleaned = re.sub(r'(?m)^(Ethan:|Coach:)', r'\n\1', cleaned)
    soup = BeautifulSoup(MD(cleaned), 'html.parser')
    original_text = normalized(soup.get_text())
    heads = soup.find_all(HEAD)
    minimum = min((int(h.name[1]) for h in heads), default=1)
    toc = []
    for number, heading in enumerate(heads, 1):
        heading['id'] = f'{key}-s{number:02}'
        heading.name = f'h{min(5, 3 + int(heading.name[1]) - minimum)}'
        heading['data-search'] = ''
        text = heading.get_text(' ', strip=True)
        if heading.name == 'h3' or re.search(r'\d+\s*[–—-]\s*\d+\s*(min|分钟)', text, re.I):
            toc.append(f'<a href="#{heading["id"]}">{html.escape(text)}</a>')
    for i, node in enumerate(soup.select('p, li, th, td'), 1):
        node['id'] = f'{key}-p{i:03}'
        if not node.select('p, li, th, td'):
            node['data-search'] = ''
        text = node.get_text(' ', strip=True)
        if node.name == 'p' and re.match(r'^(?:A|B|You|Staff|Manager|PM|Driver|Colleague|Engineer|Backend Engineer|Ethan|Coach):', text):
            node['class'] = ['dialogue']
            if text.startswith('Ethan:'):
                node['class'].append('learner')
        if node.name == 'p' and text.startswith(('❌', '✅')):
            node['class'] = ['correction']
    for table in soup.find_all('table'):
        wrapper = soup.new_tag('div', attrs={'class': 'table-scroll', 'role': 'region', 'tabindex': '0', 'aria-label': '可横向滚动的表格'})
        table.wrap(wrapper)
    for link in soup.find_all('a', href=True):
        if link['href'].startswith(('https://', 'http://')):
            link['rel'] = 'noopener noreferrer'
    require(normalized(soup.get_text()) == original_text, f'Render changed source text: {key}')
    review_html, review_anchor = '', key
    candidates = [h for h in soup.find_all(HEAD) if REVIEW.search(h.get_text(' ', strip=True))]
    if candidates:
        heading = candidates[-1]
        review_anchor = heading['id']
        nodes = []
        for node in heading.next_siblings:
            if isinstance(node, Tag) and HEAD.match(node.name) and int(node.name[1]) <= int(heading.name[1]):
                break
            nodes.append(str(node))
        fragment = BeautifulSoup(''.join(nodes), 'html.parser')
        for node in fragment.find_all(True):
            node.attrs.pop('id', None)
            node.attrs.pop('data-search', None)
        review_html = str(fragment)
    toc_html = '<nav class="local-toc" aria-label="本课小节">' + ''.join(toc) + '</nav>' if toc else ''
    return str(soup), toc_html, review_html, review_anchor


def main() -> None:
    config = json.loads((ROOT / 'site-config.json').read_text())
    lock = json.loads((ROOT / 'content-lock.json').read_text())
    for path, expected in lock['files'].items():
        require((ROOT / path).is_file(), f'Historical file missing: {path}')
        require(git_sha((ROOT / path).read_bytes()) == expected, f'Historical source changed: {path}; preserve it and add errata separately')
    files = sorted((ROOT / 'lessons').glob('day-*.md'))
    require(all(re.fullmatch(r'day-\d{3,}\.md', p.name) for p in files), 'Invalid lesson filename')
    files.sort(key=lambda p: int(p.stem.split('-')[1]))
    days = [int(p.stem.split('-')[1]) for p in files]
    require(len(days) >= config['minimum_lessons'], 'Archive incomplete; refusing to publish')
    require(days == list(range(1, max(days) + 1)), 'Duplicate or missing lesson numbers')
    archives = [('live-review', '现场口语复盘', 'Day 1 实练 · 逐条保留原话与反馈'), ('errata', '语法勘误与补充', '区分语法错误、语境差异与表达选择'), ('setup', '课程设置与收录说明', '原始指令、学习偏好与历史归档说明')]
    for key, _, _ in archives:
        require((ROOT / 'archive' / (key + '.md')).is_file(), f'Missing appendix: {key}')
    OUT.mkdir(exist_ok=True)
    # Only the dedicated generated output directory is cleared.
    for child in OUT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    lesson_cards, tiles, side, review_cards, meta, dates = [], [], [], [], [], {}
    for path, day in zip(files, days):
        raw = path.read_text(encoding='utf-8')
        require(len(raw.strip()) > 500, f'Lesson looks truncated: {path.name}')
        matches = DATE.findall(raw)
        require(len(matches) <= 1, f'Multiple lesson dates: {path.name}')
        date = matches[0] if matches else None
        if date:
            datetime.strptime(date, '%Y-%m-%d')
            require(date not in dates, f'Duplicate lesson date: {date}')
            dates[date] = day
        if day > config['historical_last_day']:
            require(bool(date), f'New lesson needs lesson-date: {path.name}')
        key = f'day-{day:02}'
        configured = config.get('titles', {}).get(str(day))
        first = re.search(r'^#{1,6}\s+(.+)$', raw, re.M)
        title = configured or (first.group(1).strip() if first else f'Day {day} · Singapore English')
        body, toc, review, review_anchor = render(raw, key)
        stamp = date or '历史归档 · 未补造日期'
        safe_title = html.escape(title)
        source = 'sources/lessons/' + path.name
        tiles.append(f'<a class="day-tile" href="#{key}" data-day="{day}"><span>DAY {day:02}<i aria-hidden="true"></i></span><strong>{safe_title}</strong><small>{html.escape(stamp)}</small><b aria-hidden="true">↗</b></a>')
        side.append(f'<a class="side-day" href="#{key}" data-day="{day}"><span>{day:02}</span>{safe_title}<i aria-hidden="true"></i></a>')
        previous = f'<a href="#day-{day-1:02}">← 上一课</a>' if day > 1 else '<a href="#directory">← 课程目录</a>'
        following = f'<a href="#day-{day+1:02}">下一课 →</a>' if day < max(days) else '<a href="#review-hub">复习卡总览 →</a>'
        lesson_cards.append(f'''<article id="{key}" class="lesson" data-day="{day}" data-label="Day {day} · {safe_title}">
<header class="lesson-header"><div class="eyebrow">DAY {day:02} <span>{html.escape(stamp)}</span></div><h2>{safe_title}</h2><div class="lesson-actions"><button class="review-toggle" data-day="{day}" aria-pressed="false">○ 标记已复习</button><a href="#{review_anchor}">本课复习区 ↓</a><button class="copy-lesson" data-day="{day}">复制本课</button><a href="{source}" download>Markdown 原文</a></div></header>
<details class="lesson-detail" open><summary>完整课程 <span>对话 / 句型 / 替换训练 / 纠错</span></summary>{toc}<div class="lesson-body">{body}</div></details>
<footer class="lesson-footer">{previous}<a href="#directory">目录 ↑</a>{following}</footer></article>''')
        if review:
            review_cards.append(f'<details class="review-card"><summary><span>DAY {day:02}</span>{safe_title}</summary><div class="review-content">{review}<p><a href="#{review_anchor}">返回本课原始复习区 ↗</a></p></div></details>')
        else:
            review_cards.append(f'<details class="review-card"><summary><span>DAY {day:02}</span>{safe_title}</summary><p><a href="#{key}">本课没有独立命名的复习卡，点击查看完整课程。</a></p></details>')
        meta.append({'day': day, 'title': title, 'date': date, 'anchor': '#' + key, 'source': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'git_blob_sha': git_sha(path.read_bytes()), 'review_anchor': '#' + review_anchor})
    appendix_html, appendix_meta = [], []
    for key, title, subtitle in archives:
        path = ROOT / 'archive' / (key + '.md')
        raw = path.read_text()
        body, toc, _, _ = render(raw, key, transcript=key == 'live-review')
        appendix_html.append(f'<article id="{key}" class="appendix" data-label="{title}"><header class="lesson-header"><div class="eyebrow">REFERENCE / ARCHIVE</div><h2>{title}</h2><p class="muted">{subtitle}</p><a href="sources/archive/{key}.md" download>下载完整原文 ↗</a></header>{toc}<div class="lesson-body">{body}</div></article>')
        appendix_meta.append({'source': 'archive/' + path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size})
    transcript = (ROOT / 'archive/live-review.md').read_text()
    turns = len(re.findall(r'(?m)^(Ethan|Coach):', transcript))
    build_date = datetime.now(timezone.utc).isoformat(timespec='seconds')
    manifest = {'schema_version': 1, 'repository': config['repository'], 'commit': os.getenv('GITHUB_SHA', 'local-preview'), 'built_at': build_date, 'lesson_count': len(days), 'latest_day': max(days), 'latest_lesson_date': max(dates) if dates else None, 'historical_archive_verified': True, 'historical_files_verified': len(lock['files']), 'practice_message_count': turns, 'lessons': meta, 'appendices': appendix_meta}
    page = (ROOT / 'site/template.html').read_text()
    replacements = {'STYLE': (ROOT/'site/style.css').read_text(), 'SCRIPT': (ROOT/'site/app.js').read_text(), 'COUNT': str(len(days)), 'LAST': str(max(days)), 'LATEST_ANCHOR': f'day-{max(days):02}', 'LATEST_TITLE': html.escape(meta[-1]['title']), 'LAST_DATE': manifest['latest_lesson_date'] or '日期未注明', 'TURNS': str(turns), 'TILES': ''.join(tiles), 'SIDEBAR': ''.join(side), 'LESSONS': '\n'.join(lesson_cards), 'REVIEWS': ''.join(review_cards), 'APPENDICES': '\n'.join(appendix_html), 'BUILD_DATE': build_date, 'REPO': html.escape(config['repository'])}
    for key, value in replacements.items():
        page = page.replace('@@' + key + '@@', value)
    require(not re.search(r'@@[A-Z_]+@@', page), 'Unexpanded template variable')
    soup = BeautifulSoup(page, 'html.parser')
    ids = [node['id'] for node in soup.find_all(id=True)]
    require(len(ids) == len(set(ids)), 'Duplicate HTML anchors')
    id_set = set(ids)
    for link in soup.select('a[href^="#"]'):
        require(link['href'][1:] in id_set, f'Broken internal anchor: {link["href"]}')
    require(len(soup.select('article.lesson')) == len(days), 'Rendered lesson count mismatch')
    for path in files + [ROOT/'archive'/(key+'.md') for key, _, _ in archives]:
        destination = OUT / 'sources' / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        require(destination.read_bytes() == path.read_bytes(), f'Source copy changed: {path}')
    (OUT/'index.html').write_text(page, encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT/'.nojekyll').touch()
    print(f'PASS: {len(days)} full lessons; {turns} practice messages; {len(lock["files"])} historical files locked; {len(ids)} valid anchors.')
    print(f'Latest lesson: Day {max(days)}, date: {manifest["latest_lesson_date"]}')


if __name__ == '__main__':
    main()
