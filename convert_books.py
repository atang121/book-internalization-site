#!/usr/bin/env python3
"""
批量转换 "《书名》内化输出.txt" → "book-{id}.js"

用法:
  python3 convert_books.py                       # 转换所有 *内化输出*.txt 文件
  python3 convert_books.py "《XX》内化输出.txt"   # 转换指定文件
"""

import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'
import re
import sys
import glob
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOOKS_DIR = os.path.join(BASE_DIR, "js", "books")

ACCENT_COLORS = [
    '#d4a574', '#74b5a7', '#7aab6e', '#a78bdb', '#db8b8b',
    '#8bb5db', '#dbb88b', '#8bdbb8', '#db8bdb', '#b5a774',
]

FIELD_ICONS = {
    '量子': '⚛️', '物理': '⚛️',
    '禅': '🧘', '佛': '🧘',
    '心理治疗': '🧠', '心理学': '💊', '心理': '🧠',
    '系统': '🔄', '神经': '🧬',
    '教育': '🎓', '消费': '🛒',
    '数字': '📱', '社交媒体': '📱',
    '人际': '💔', '行为': '⏰',
    '管理': '🎯', '组织': '🎯',
    '创造': '🎨', '生态': '🌿',
}

SCENARIO_KEYWORD_ICONS = {
    '痛苦': '💔', '亲密': '💔', '伴侣': '💔',
    '嫉妒': '😤', '比较': '😤',
    '孤独': '😔', '恐惧孤独': '😔',
    '执着': '🎯', '结果': '🎯',
    '过去': '🕳️', '伤害': '🕳️', '记忆': '🕳️',
    '焦虑': '😰', '不安': '😰',
    '愤怒': '🔥', '怒': '🔥',
    '失去': '💧', '丧失': '💧',
    '无聊': '📱', '空虚': '📱',
    '冲突': '🤝', '对抗': '🤝',
    '压力': '😫', '紧张': '😫',
    '社交': '🎉', '聚会': '🎉',
    '饭后': '🍽️', '吃': '🍽️',
    '戒烟': '🚬', '烟': '🚬',
}


# ════════════════════════════════════════════
#  Utility
# ════════════════════════════════════════════

def clean(text):
    return text.strip() if text else ''


def bold_to_html(text):
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)


def esc_sq(text):
    return text.replace("\\", "\\\\").replace("'", "\\'")


def esc_tpl(text):
    return text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def assign_field_icon(field):
    for key, icon in FIELD_ICONS.items():
        if key in field:
            return icon
    return '💡'


def assign_scenario_icon(title):
    for kw, icon in SCENARIO_KEYWORD_ICONS.items():
        if kw in title:
            return icon
    return '💡'


def find_key(keys, partial):
    for k in keys:
        if partial in k:
            return k
    return ''


def generate_book_id(english_title, existing_ids=None):
    """从英文书名自动生成简短的 book ID。"""
    existing_ids = existing_ids or set()
    if not english_title:
        return ''

    parts = re.split(r'\s*/\s*', english_title)
    name = ''
    for p in reversed(parts):
        if re.search(r'[a-zA-Z]', p):
            name = p.strip()
            break
    if not name:
        name = english_title

    name = re.split(r'[:\-–—]', name)[0].strip()
    name = re.sub(r'^(The|A|An)\s+', '', name, flags=re.IGNORECASE)

    stop = {'of', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'and', 'or', 'by', 'from', 'its'}
    words = [w.replace("'", '').replace('\u2019', '') for w in re.findall(r"[a-zA-Z'\u2019]+", name)]
    words = [w for w in words if w]
    meaningful = [w.lower() for w in words if w.lower() not in stop]
    if not meaningful:
        meaningful = [w.lower() for w in words]

    candidate = '-'.join(meaningful[:3])
    if not candidate:
        return ''

    if candidate not in existing_ids:
        return candidate
    for i in range(2, 100):
        c = f"{candidate}-{i}"
        if c not in existing_ids:
            return c
    return candidate


def _is_table_row(line):
    s = line.strip()
    return s.startswith('|') and s.endswith('|') and s.count('|') >= 3

def _is_table_sep(line):
    return bool(re.match(r'^[\s|:-]+$', line.strip())) and '---' in line

def _parse_md_table(lines, start_idx):
    """Parse markdown table starting at start_idx, return (html, end_idx)."""
    rows = []
    i = start_idx
    while i < len(lines) and (_is_table_row(lines[i]) or _is_table_sep(lines[i])):
        if not _is_table_sep(lines[i]):
            cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
            rows.append(cells)
        i += 1
    if not rows:
        return '', start_idx
    sp = ' ' * 10
    html = f'{sp}<table class="md-table">\n'
    html += f'{sp}  <thead><tr>'
    for cell in rows[0]:
        html += f'<th>{bold_to_html(cell)}</th>'
    html += f'</tr></thead>\n'
    if len(rows) > 1:
        html += f'{sp}  <tbody>\n'
        for row in rows[1:]:
            html += f'{sp}    <tr>'
            for cell in row:
                html += f'<td>{bold_to_html(cell)}</td>'
            html += f'</tr>\n'
        html += f'{sp}  </tbody>\n'
    html += f'{sp}</table>'
    return html, i

def _is_line_breakpoint(line):
    s = line.strip()
    if not s:
        return True
    if re.match(r'^[-·•]\s', s):
        return True
    if s.startswith('"') or s.startswith('\u201c'):
        return True
    if re.match(r'^\*\*[^*]+\*\*[：:.]?\s*$', s):
        return True
    if _is_table_row(s):
        return True
    return False

def text_to_html(text, indent=10):
    """Convert structured plain text to HTML."""
    text = clean(text)
    if not text:
        return ''
    lines = text.split('\n')
    parts = []
    sp = ' ' * indent
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if _is_table_row(line):
            html, i = _parse_md_table(lines, i)
            if html:
                parts.append(html)
            continue

        if _is_table_sep(line):
            i += 1
            continue

        if line.startswith('"') or line.startswith('\u201c'):
            quotes = []
            while i < len(lines) and lines[i].strip() and (
                    lines[i].strip().startswith('"') or lines[i].strip().startswith('\u201c')):
                quotes.append(lines[i].strip())
                i += 1
            if len(quotes) >= 2:
                parts.append(f'{sp}<blockquote>{bold_to_html("".join(quotes))}</blockquote>')
            else:
                parts.append(f'{sp}<p>{bold_to_html(quotes[0])}</p>')
            continue

        if re.match(r'^[-·•]\s', line):
            items = []
            while i < len(lines) and lines[i].strip() and re.match(r'^[-·•]\s', lines[i].strip()):
                items.append(bold_to_html(re.sub(r'^[-·•]\s*', '', lines[i].strip())))
                i += 1
            li = ''.join(f'<li>{it}</li>' for it in items)
            parts.append(f'{sp}<ul>\n{sp}  {li}\n{sp}</ul>')
            continue

        if re.match(r'^\*\*[^*]+\*\*[：:.]?\s*$', line):
            heading = re.sub(r'^\*\*(.+?)\*\*[：:.]?\s*$', r'\1', line)
            parts.append(f'{sp}<h4>{heading}</h4>')
            i += 1
            continue

        para = []
        while i < len(lines) and lines[i].strip() and not _is_line_breakpoint(lines[i]):
            para.append(lines[i].strip())
            i += 1
        if para:
            parts.append(f'{sp}<p>{bold_to_html(" ".join(para))}</p>')

    return '\n'.join(parts)


def _find_last_insight_marker(text):
    """Find the last insight-box marker in text. Returns (position, marker_text, label)."""
    bold_markers = [
        '**核心洞察**', '**核心洞察:**', '**核心洞察：**',
        '**第一性原理**', '**第一性原理:**', '**第一性原理：**',
        '**核心**', '**洞察**',
        '**核心心法**', '**悖论**', '**追问**',
    ]
    plain_markers = [
        '核心洞察：', '核心洞察:',
        '第一性原理：', '第一性原理:',
        '更深一层：', '更深一层:',
    ]
    best_pos, best_marker, best_label = -1, '', ''
    for m in bold_markers:
        p = text.rfind(m)
        if p > best_pos:
            best_pos, best_marker = p, m
            best_label = m.strip('*').rstrip('：:')
    for m in plain_markers:
        p = text.rfind(m)
        if p > best_pos:
            actual_pos, actual_marker = p, m
            if p >= 2 and text[p-2:p] == '**':
                end_bold = p + len(m)
                if end_bold < len(text) and text[end_bold:end_bold+2] == '**':
                    actual_pos = p - 2
                    actual_marker = text[actual_pos:end_bold+2]
                else:
                    actual_pos = p - 2
                    actual_marker = '**' + m
            best_pos, best_marker = actual_pos, actual_marker
            best_label = m.rstrip('：:')
    return best_pos, best_marker, best_label


def principle_content_to_html(text, indent=10):
    """Convert principle content, detecting insight-box at the end."""
    text = clean(text)
    if not text:
        return ''

    last_pos, last_marker, label = _find_last_insight_marker(text)

    if last_pos > 0:
        main = text[:last_pos].strip()
        insight_raw = text[last_pos + len(last_marker):].strip().lstrip('：: ')
        main_html = text_to_html(main, indent)
        insight_body = bold_to_html(insight_raw.replace('\n\n', ' ').replace('\n', ' '))
        sp = ' ' * indent
        box = f'{sp}<div class="insight-box"><p><strong>{label}：</strong>{insight_body}</p></div>'
        return main_html + '\n' + box

    return text_to_html(text, indent)


# ════════════════════════════════════════════
#  Section Splitting
# ════════════════════════════════════════════

def split_sections(content):
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    pattern = re.compile(r'═{3,}\n(.+?)\n═{3,}', re.DOTALL)
    headers = [(m.group(1).strip(), m.start(), m.end()) for m in pattern.finditer(content)]
    sections = {}
    if headers:
        sections['_header'] = content[:headers[0][1]].strip()
    for i, (name, _start, end) in enumerate(headers):
        next_start = headers[i + 1][1] if i + 1 < len(headers) else len(content)
        sections[name] = content[end:next_start].strip()
    return sections


# ════════════════════════════════════════════
#  Header / Metadata
# ════════════════════════════════════════════

def parse_header(text):
    meta = {}
    m = re.search(r'书籍[：:]\s*《(.+?)》\s*\((.+?)\)', text)
    if m:
        meta['title'], meta['originalTitle'] = m.group(1), m.group(2)
    m = re.search(r'作者[：:]\s*(.+?)\s*\((.+?)\)', text)
    if m:
        meta['author'], meta['authorEn'] = m.group(1).strip(), m.group(2).strip()
    m = re.search(r'内化日期[：:]\s*(\d{4}-\d{2}-\d{2})', text)
    if m:
        meta['date'] = m.group(1)
    return meta


# ════════════════════════════════════════════
#  Core Proposition
# ════════════════════════════════════════════

def parse_core_proposition(text):
    text = clean(text)
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    result = {'question': '', 'metaAnswer': '', 'summary': ''}
    if paras:
        result['question'] = paras[0].replace('\n', ' ')
    meta_parts, summary = [], ''
    for p in paras[1:]:
        pc = p.replace('\n', ' ').strip()
        pc = re.sub(r'^元问题[：:]\s*', '', pc)
        if pc.startswith('这是一套'):
            summary = pc
        elif not summary:
            meta_parts.append(pc)
    if meta_parts:
        result['metaAnswer'] = '\n'.join(f'      <p>{bold_to_html(mp)}</p>' for mp in meta_parts)
    result['summary'] = summary
    return result


# ════════════════════════════════════════════
#  Topology (best-effort ASCII art parser)
# ════════════════════════════════════════════

def parse_topology(text):
    text = clean(text)
    split_idx = len(text)
    for kw in ['关键节点解释', '关键节点']:
        idx = text.find(kw)
        if 0 < idx < split_idx:
            split_idx = idx

    diagram = text[:split_idx].strip()
    notes_raw = text[split_idx:].strip() if split_idx < len(text) else ''
    elements = _parse_ascii_blocks(diagram)
    notes = _parse_topo_notes(notes_raw)
    return _gen_topo_html(elements, notes)


def _parse_ascii_blocks(text):
    lines = text.split('\n')
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '┌' not in line or '┴' in line or '┼' in line:
            i += 1
            continue
        num = line.count('┌')
        content_lines, is_vs = [], False
        j = i + 1
        while j < len(lines):
            if '└' in lines[j]:
                j += 1
                break
            if 'VS' in lines[j]:
                is_vs = True
            content_lines.append(lines[j])
            j += 1
        box_texts = _extract_boxes(content_lines, num)
        if num == 1:
            blocks.append({'type': 'node', 'boxes': box_texts})
        elif is_vs:
            blocks.append({'type': 'vs', 'boxes': box_texts})
        else:
            btype = 'vs' if num == 2 else 'branch'
            blocks.append({'type': btype, 'boxes': box_texts})
        i = j
    return blocks


def _extract_boxes(content_lines, num):
    boxes = [[] for _ in range(num)]
    for line in content_lines:
        pipes = [i for i, c in enumerate(line) if c == '│']
        if len(pipes) < 2:
            continue
        for bi in range(min(num, len(pipes) // 2)):
            left, right = pipes[bi * 2], pipes[bi * 2 + 1]
            seg = line[left + 1:right].strip()
            if seg and seg != 'VS':
                boxes[bi].append(seg)
    return boxes


def _parse_topo_notes(text):
    notes = []
    for m in re.finditer(r'[•·]\s*(.+?)\s*[=＝]\s*(.+?)(?=\n[•·]|\n\s*\n|\Z)', text, re.DOTALL):
        notes.append({'term': m.group(1).strip(), 'desc': m.group(2).strip().replace('\n', ' ')})
    return notes


def _gen_topo_html(elements, notes):
    h = ['    <div class="topo-flow">']
    total = len(elements)
    for idx, el in enumerate(elements):
        if idx > 0:
            h.append('      <div class="topo-connector-v"></div>')
        if el['type'] == 'node':
            box = el['boxes'][0] if el['boxes'] else []
            title, sub, bullets = '', '', []
            for ln in box:
                if ln.startswith('•') or ln.startswith('- '):
                    bullets.append(ln.lstrip('•- ').strip())
                elif ln.startswith('(') and ln.endswith(')'):
                    sub = ln
                elif not title:
                    title = ln
                elif not sub:
                    sub = ln
            pri = ' primary' if idx == 0 or idx == total - 1 or (total >= 5 and idx == total // 2) else ''
            h.append(f'      <div class="topo-node{pri}">')
            h.append(f'        <p class="topo-node-title">{title}</p>')
            if sub:
                h.append(f'        <p class="topo-node-sub">{sub}</p>')
            h.append('      </div>')
        elif el['type'] == 'branch':
            h.append('      <div class="topo-branch">')
            for box in el['boxes']:
                h.append('        <div class="topo-branch-item">')
                title_parts, bullets = [], []
                for ln in box:
                    if ln.startswith('•') or ln.startswith('- '):
                        bullets.append(ln.lstrip('•- ').strip())
                    else:
                        title_parts.append(ln)
                h.append(f'          <p class="topo-branch-title">{"".join(title_parts)}</p>')
                if bullets:
                    li = ''.join(f'<li>{b}</li>' for b in bullets)
                    h.append(f'          <ul class="topo-branch-items">{li}</ul>')
                h.append('        </div>')
            h.append('      </div>')
        elif el['type'] == 'vs':
            h.append('      <div class="topo-vs">')
            for vi, box in enumerate(el['boxes']):
                cls = 'false' if vi == 0 else 'true'
                h.append(f'        <div class="topo-vs-item {cls}">')
                label, title, bullets = '', '', []
                for ln in box:
                    if ln.startswith('•') or ln.startswith('- '):
                        bullets.append(ln.lstrip('•- ').strip())
                    elif ('(' in ln and ')' in ln) or ('（' in ln and '）' in ln):
                        label = ln if not label else label
                        if not title and label != ln:
                            title = ln
                    elif not title:
                        title = ln
                    elif not label:
                        label = ln
                if label:
                    h.append(f'          <p class="topo-vs-label">{label}</p>')
                if title:
                    h.append(f'          <p class="topo-vs-title">{title}</p>')
                if bullets:
                    li = ''.join(f'<li>{b}</li>' for b in bullets)
                    h.append(f'          <ul class="topo-branch-items">{li}</ul>')
                h.append('        </div>')
            h.append('      </div>')
    h.append('    </div>')

    if notes:
        h.append('    <div class="topo-notes">')
        h.append('      <h3>关键节点</h3>')
        for n in notes:
            h.append(f'      <div class="topo-note-item">'
                     f'<span class="topo-note-term">{n["term"]}</span>'
                     f'<span class="topo-note-desc">{n["desc"]}</span></div>')
        h.append('    </div>')

    return '\n'.join(h)


# ════════════════════════════════════════════
#  Assimilation (认知同化)
# ════════════════════════════════════════════

def parse_assimilation(text):
    text = clean(text)
    text = re.sub(r'^以用户\s*\[.*?\]\s*的视角重述[：:]\s*', '', text).strip()

    lines = text.split('\n')

    starts = []
    for li, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^\d+[.、]\s*\*\*', stripped) or re.match(r'^\d+[.、]\s*\S', stripped):
            starts.append(li)

    intro = '\n'.join(lines[:starts[0]]).strip().replace('\n', ' ') if starts else text.replace('\n', ' ')

    core_insight = ''
    ci_line_idx = len(lines)
    ci_pattern = re.compile(
        r'\*\*核心洞察[：:]*\*\*[：:]?'
        r'|\*\*核心洞察\*\*[：:]'
        r'|^核心洞察[：:]'
    )
    search_from = starts[-1] if starts else 0
    for li in range(len(lines) - 1, search_from, -1):
        if ci_pattern.search(lines[li].strip()):
            ci_line_idx = li
            after = ci_pattern.sub('', lines[li]).strip()
            remaining = [after] if after else []
            remaining.extend(lines[li + 1:])
            core_insight = ' '.join(l.strip() for l in remaining if l.strip())
            break

    principles = []
    for si, line_idx in enumerate(starts):
        title_line = lines[line_idx].strip()
        tm = re.search(r'\*\*(.+?)\*\*', title_line)
        if tm:
            title = tm.group(1)
        else:
            title = re.sub(r'^\d+[.、]\s*', '', title_line)
        c_start = line_idx + 1
        if si + 1 < len(starts):
            c_end = starts[si + 1]
        else:
            c_end = ci_line_idx
        content = '\n'.join(lines[c_start:c_end]).strip()
        principles.append({
            'title': title,
            'content': principle_content_to_html(content)
        })

    return {'intro': intro, 'principles': principles, 'coreInsight': core_insight}


# ════════════════════════════════════════════
#  Destruction (破坏与重塑)
# ════════════════════════════════════════════

def parse_destruction(text):
    text = clean(text)

    models_pos = _find_marker(text, ['必须重塑的思维模型', '重塑的思维模型'])
    cost_pos = _find_marker(text, ['**代价**', '**代价：**', '**代价:'])

    beliefs_text = text[:models_pos].strip() if models_pos < len(text) else text
    models_text = text[models_pos:cost_pos].strip() if models_pos < len(text) else ''
    cost_text = text[cost_pos:].strip() if cost_pos < len(text) else ''
    cost_text = re.sub(r'^\*\*代价[：:]*\*\*[：:]?\s*', '', cost_text).strip()

    beliefs = _parse_beliefs(beliefs_text)
    new_models = _parse_new_models(models_text)
    cost_html = text_to_html(cost_text)

    return {'beliefs': beliefs, 'newModels': new_models, 'cost': cost_html}


def _find_marker(text, markers):
    best = len(text)
    for m in markers:
        idx = text.find(m)
        if 0 < idx < best:
            best = idx
    return best


def _parse_beliefs(text):
    beliefs = []
    lines = text.split('\n')
    starts = []
    for li, line in enumerate(lines):
        if re.match(r'^\d+[.、]\s*\*\*', line.strip()):
            starts.append(li)

    for si, line_idx in enumerate(starts):
        title_line = lines[line_idx].strip()
        tm = re.search(r'\*\*[""「]?(.+?)[""」]?\*\*', title_line)
        old = tm.group(1).strip().strip('""\u201c\u201d') if tm else title_line
        c_start = line_idx + 1
        c_end = starts[si + 1] if si + 1 < len(starts) else len(lines)
        content = '\n'.join(lines[c_start:c_end]).strip()
        content = re.sub(r'^→\s*被摧毁[：:]\s*', '', content).strip()
        beliefs.append({'old': old, 'destruction': text_to_html(content)})

    return beliefs


def _parse_new_models(text):
    models = []
    for m in re.finditer(r'从["""\u201c](.+?)["""\u201d]转向["""\u201c](.+?)["""\u201d][：:]',
                         text, re.DOTALL):
        label = f'从"{m.group(1)}"转向"{m.group(2)}"'
        after = text[m.end():]
        om = re.search(r'旧模型[：:]\s*(.+?)(?=\n新模型|\n\n|\Z)', after, re.DOTALL)
        nm = re.search(r'新模型[：:]\s*(.+?)(?=\n从|\n\n|\Z)', after, re.DOTALL)
        old_m = om.group(1).strip().replace('\n', ' ') if om else ''
        new_m = nm.group(1).strip().replace('\n', ' ') if nm else ''
        models.append({'label': label, 'oldModel': old_m, 'newModel': new_m})
    return models


# ════════════════════════════════════════════
#  Practice (事上磨练)
# ════════════════════════════════════════════

def parse_practice(text):
    text = clean(text)
    parts = re.split(r'\n-{3,}\n', text)
    scenarios, toolkit_text = [], ''

    for part in parts:
        part = part.strip()
        if not part:
            continue
        if '工具包' in part or '工具箱' in part:
            toolkit_text = part
            continue
        sc = _parse_scenario(part)
        if sc:
            scenarios.append(sc)

    if not toolkit_text and parts:
        last = parts[-1].strip()
        if '工具' in last and not re.match(r'^场景', last):
            toolkit_text = last
            if scenarios and scenarios[-1]['title'] in last:
                scenarios.pop()

    toolkit_html = _parse_toolkit(toolkit_text) if toolkit_text else ''
    return {'scenarios': scenarios, 'toolkit': toolkit_html}


def _parse_scenario(text):
    text = clean(text)
    if not text:
        return None

    lines = text.split('\n')
    title_line = lines[0].strip()
    tm = re.match(r'场景[一二三四五六七八九十\d]+[：:]\s*(.+)', title_line)
    title = tm.group(1) if tm else title_line

    core_method = ''
    cm = re.search(r'\*\*核心心法\*\*[：:]\s*\n(.+?)$', text, re.DOTALL)
    if cm:
        core_method = cm.group(1).strip().replace('\n', ' ')
    else:
        cm = re.search(r'\*\*核心心法[：:]\*\*\s*\n(.+?)$', text, re.DOTALL)
        if cm:
            core_method = cm.group(1).strip().replace('\n', ' ')

    content_end = cm.start() if cm else len(text)
    first_nl = text.find('\n')
    content_text = text[first_nl + 1:content_end].strip() if first_nl > 0 else ''
    content_html = text_to_html(content_text)

    return {
        'icon': assign_scenario_icon(title),
        'title': title,
        'content': content_html,
        'coreMethod': core_method
    }


def _parse_toolkit(text):
    text = clean(text)
    text = re.sub(r'^.*?工具[包箱].*?[：:]\s*\n?', '', text).strip()

    parts_raw = re.split(r'^\d+[.、]\s*', text, flags=re.MULTILINE)
    titles = re.findall(r'^\d+[.、]\s*\*\*(.+?)\*\*', text, flags=re.MULTILINE)

    h = []
    for idx, title in enumerate(titles):
        chunk = parts_raw[idx + 1] if idx + 1 < len(parts_raw) else ''
        te = chunk.find('**')
        body = chunk[te + 2:].strip() if te >= 0 else chunk.strip()
        body = bold_to_html(body.replace('\n\n', ' ').replace('\n', ' '))
        h.append('      <div class="toolkit-item">')
        h.append(f'        <h4>{title}</h4>')
        h.append(f'        <p>{body}</p>')
        h.append('      </div>')
    return '\n'.join(h)


# ════════════════════════════════════════════
#  Cross Domain (跨界生发)
# ════════════════════════════════════════════

def parse_cross_domain(text):
    text = clean(text)
    text = re.sub(r'^[^\n]*联想[^\n]*\n', '', text).strip()
    text = re.sub(r'^-{3,}\s*\n', '', text).strip()

    parts = re.split(r'\n-{3,}\n', text)
    connections, ult_text = [], ''

    for part in parts:
        part = part.strip()
        if not part or re.match(r'^-{3,}$', part):
            continue
        if '终极洞察' in part:
            m = re.search(r'终极洞察[：:]\s*\n?(.*)', part, re.DOTALL)
            ult_text = m.group(1).strip() if m else part
            continue
        conn = _parse_connection(part)
        if conn:
            connections.append(conn)

    return {'connections': connections, 'ultimateInsight': text_to_html(ult_text)}


def _parse_connection(text):
    text = clean(text)
    if not text:
        return None
    first_line = text.split('\n')[0].strip()

    field, title = '', ''
    patterns = [
        r'\d+[.、]\s*\*\*(.+?)\s*[×xX]\s*(.+?)\*\*',
        r'\*\*(.+?)\s*[×xX]\s*(.+?)\*\*',
        r'\d+[.、]\s*(.+?)\s*[×xX]\s*(.+)',
    ]
    for pat in patterns:
        m = re.match(pat, first_line)
        if m:
            field, title = m.group(1).strip().strip('*'), m.group(2).strip().strip('*')
            break

    if not field:
        raw = re.sub(r'^\d+[.、]\s*', '', first_line).strip('*').strip()
        if '×' in raw or 'x' in raw.lower():
            parts = re.split(r'\s*[×xX]\s*', raw, maxsplit=1)
            field, title = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else parts[0].strip())
        else:
            field = title = raw

    first_nl = text.find('\n')
    content = text[first_nl + 1:].strip() if first_nl > 0 else ''
    content = re.sub(r'^相似性[：:]\s*\n?', '', content).strip()

    return {
        'icon': assign_field_icon(field),
        'field': field,
        'title': title,
        'content': text_to_html(content)
    }


# ════════════════════════════════════════════
#  Closing (内化完成)
# ════════════════════════════════════════════

def parse_closing(text):
    text = clean(text)
    parts = re.split(r'─{4,}', text)
    quotes, reflection = [], ''

    if len(parts) >= 3:
        quotes = _parse_quotes(parts[1].strip())
        reflection = text_to_html(parts[2].strip())
    elif len(parts) >= 2:
        quotes = _parse_quotes(parts[0].strip())
        reflection = text_to_html(parts[1].strip())

    return {'quotes': quotes, 'reflection': reflection}


def _parse_quotes(text):
    quotes = []
    current = []
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith('—') or s.startswith('\u2014'):
            author = s.lstrip('—\u2014 ').strip()
            if current:
                qt = ' '.join(current).strip('""\u201c\u201d ')
                quotes.append({'text': qt, 'author': author})
                current = []
        elif s.startswith('"') or s.startswith('\u201c'):
            current.append(s.strip('""\u201c\u201d'))
        elif s and current:
            current.append(s.strip('""\u201c\u201d'))
    return quotes


# ════════════════════════════════════════════
#  JS Generation
# ════════════════════════════════════════════

def generate_js(d):
    o = []
    o.append("window.BOOKS = window.BOOKS || [];")
    o.append("window.BOOKS.push({")
    o.append(f"  id: '{esc_sq(d['id'])}',")
    o.append(f"  title: '{esc_sq(d['title'])}',")
    o.append(f"  originalTitle: '{esc_sq(d['originalTitle'])}',")
    o.append(f"  author: '{esc_sq(d['author'])}',")
    o.append(f"  authorEn: '{esc_sq(d['authorEn'])}',")
    o.append(f"  date: '{d['date']}',")
    o.append(f"  accent: '{d['accent']}',")
    o.append(f"  icon: '{d['icon']}',")
    o.append("")

    cp = d['coreProposition']
    o.append("  coreProposition: {")
    o.append(f"    question: '{esc_sq(cp['question'])}',")
    o.append(f"    metaAnswer: `")
    o.append(f"{cp['metaAnswer']}")
    o.append(f"    `,")
    o.append(f"    summary: '{esc_sq(cp['summary'])}',")
    o.append("  },")
    o.append("")

    o.append(f"  topology: `")
    o.append(d['topology'])
    o.append(f"  `,")
    o.append("")

    a = d['assimilation']
    o.append("  assimilation: {")
    o.append(f"    intro: '{esc_sq(a['intro'])}',")
    o.append("    principles: [")
    for p in a['principles']:
        o.append("      {")
        o.append(f"        title: '{esc_sq(p['title'])}',")
        o.append(f"        content: `")
        o.append(p['content'])
        o.append(f"        `")
        o.append("      },")
    o.append("    ],")
    o.append(f"    coreInsight: '{esc_sq(a['coreInsight'])}'")
    o.append("  },")
    o.append("")

    de = d['destruction']
    o.append("  destruction: {")
    o.append("    beliefs: [")
    for b in de['beliefs']:
        o.append("      {")
        o.append(f"        old: '{esc_sq(b['old'])}',")
        o.append(f"        destruction: `")
        o.append(b['destruction'])
        o.append(f"        `")
        o.append("      },")
    o.append("    ],")
    o.append("    newModels: [")
    for m in de['newModels']:
        o.append(f"      {{ label: '{esc_sq(m['label'])}', "
                 f"oldModel: '{esc_sq(m['oldModel'])}', "
                 f"newModel: '{esc_sq(m['newModel'])}' }},")
    o.append("    ],")
    o.append(f"    cost: `")
    o.append(de['cost'])
    o.append(f"    `")
    o.append("  },")
    o.append("")

    pr = d['practice']
    o.append("  practice: {")
    o.append("    scenarios: [")
    for s in pr['scenarios']:
        o.append("      {")
        o.append(f"        icon: '{s['icon']}',")
        o.append(f"        title: '{esc_sq(s['title'])}',")
        o.append(f"        content: `")
        o.append(s['content'])
        o.append(f"        `,")
        o.append(f"        coreMethod: '{esc_sq(s['coreMethod'])}'")
        o.append("      },")
    o.append("    ],")
    o.append(f"    toolkit: `")
    o.append(pr['toolkit'])
    o.append(f"    `")
    o.append("  },")
    o.append("")

    cd = d['crossDomain']
    o.append("  crossDomain: {")
    o.append("    connections: [")
    for c in cd['connections']:
        o.append("      {")
        o.append(f"        icon: '{c['icon']}',")
        o.append(f"        field: '{esc_sq(c['field'])}',")
        o.append(f"        title: '{esc_sq(c['title'])}',")
        o.append(f"        content: `")
        o.append(c['content'])
        o.append(f"        `")
        o.append("      },")
    o.append("    ],")
    o.append(f"    ultimateInsight: `")
    o.append(cd['ultimateInsight'])
    o.append(f"    `")
    o.append("  },")
    o.append("")

    cl = d['closing']
    o.append("  closing: {")
    o.append("    quotes: [")
    for q in cl['quotes']:
        o.append(f"      {{ text: '{esc_sq(q['text'])}', author: '{esc_sq(q['author'])}' }},")
    o.append("    ],")
    o.append(f"    reflection: `")
    o.append(cl['reflection'])
    o.append(f"    `")
    o.append("  }")

    o.append("});")
    return '\n'.join(o) + '\n'


# ════════════════════════════════════════════
#  Main
# ════════════════════════════════════════════

def main():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    # ── 步骤1: 选择输入的 txt 文件 ──
    txt_files = filedialog.askopenfilenames(
        title="选择要转换的「内化输出」文本文件",
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
        initialdir=BASE_DIR,
    )

    if not txt_files:
        messagebox.showinfo("提示", "未选择任何文件，程序退出。")
        root.destroy()
        return

    txt_files = list(txt_files)
    print(f"\n已选择 {len(txt_files)} 个文件待转换：")
    for f in txt_files:
        print(f"  - {os.path.basename(f)}")

    color_idx = 0
    converted = []
    used_ids = set()

    for txt_path in txt_files:
        basename = os.path.basename(txt_path)
        print(f"\n{'=' * 50}")
        print(f"  处理: {basename}")
        print(f"{'=' * 50}")

        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        sections = split_sections(content)
        meta = parse_header(sections.get('_header', ''))
        title = meta.get('title', '未知')
        author = meta.get('author', '未知')
        original_title = meta.get('originalTitle', '')

        auto_id = generate_book_id(original_title, used_ids) or ('book' + str(color_idx))
        default_color = ACCENT_COLORS[color_idx % len(ACCENT_COLORS)]

        book_id = simpledialog.askstring(
            "Book ID",
            f"《{title}》({author})\n{original_title}\n\n"
            f"已根据英文书名自动生成 ID，确认或修改：",
            initialvalue=auto_id,
            parent=root,
        )
        if not book_id:
            book_id = auto_id
        used_ids.add(book_id)

        accent = simpledialog.askstring(
            "主题色",
            f"《{title}》\n\n请输入主题色（如 #d4a574）：",
            initialvalue=default_color,
            parent=root,
        )
        if not accent:
            accent = default_color

        icon = simpledialog.askstring(
            "图标",
            f"《{title}》\n\n请输入图标 emoji（如 🪞）：",
            initialvalue='📖',
            parent=root,
        )
        if not icon:
            icon = '📖'

        print(f"  书名: 《{title}》  ID: {book_id}  颜色: {accent}  图标: {icon}")

        sk = list(sections.keys())
        cp = parse_core_proposition(sections.get(find_key(sk, '核心命题'), ''))
        topo = parse_topology(sections.get(find_key(sk, '概念拓扑'), ''))
        assim = parse_assimilation(sections.get(find_key(sk, '认知同化'), ''))
        dest = parse_destruction(sections.get(find_key(sk, '破坏与重塑'), ''))
        prac = parse_practice(sections.get(find_key(sk, '事上磨练'), ''))
        cross = parse_cross_domain(sections.get(find_key(sk, '跨界生发'), ''))
        closing = parse_closing(sections.get(find_key(sk, '内化完成'), ''))

        book = {
            'id': book_id,
            'title': title,
            'originalTitle': meta.get('originalTitle', ''),
            'author': meta.get('author', ''),
            'authorEn': meta.get('authorEn', ''),
            'date': meta.get('date', ''),
            'accent': accent,
            'icon': icon,
            'coreProposition': cp,
            'topology': topo,
            'assimilation': assim,
            'destruction': dest,
            'practice': prac,
            'crossDomain': cross,
            'closing': closing,
        }

        js_content = generate_js(book)
        out_name = f"book-{book_id}.js"
        converted.append((out_name, js_content))
        color_idx += 1
        print(f"  ✓ 《{title}》转换完成 → {out_name}")

    # ── 步骤2: 选择保存位置 ──
    save_dir = filedialog.askdirectory(
        title="选择 JS 文件的保存位置",
        initialdir=BOOKS_DIR,
    )

    if not save_dir:
        save_dir = BOOKS_DIR
        print(f"\n  未选择保存位置，默认保存到: {save_dir}")

    os.makedirs(save_dir, exist_ok=True)

    saved = []
    for out_name, js_content in converted:
        out_path = os.path.join(save_dir, out_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        saved.append(out_path)
        print(f"  ✓ 已保存: {out_path}")

    summary = f"转换完成！共生成 {len(saved)} 个文件：\n\n"
    for p in saved:
        summary += f"  {os.path.basename(p)}\n"
    summary += f"\n保存位置：{save_dir}"
    summary += "\n\n提示：概念拓扑 (topology) 为自动解析，建议手动检查。"
    summary += "\n提示：生成后请运行「上传新书后点击自动修改index.py」同步 index.html。"

    messagebox.showinfo("转换完成", summary)
    root.destroy()

    print(f"\n{'=' * 50}")
    print(f"  转换完成！共生成 {len(saved)} 个文件")
    print(f"  保存位置: {save_dir}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
