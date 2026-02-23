#!/usr/bin/env python3
"""
扫描 js/books/ 目录下所有 book-*.js 文件，
自动检测重复、按日期排序，同步到 index.html 的 <script> 标签区域。

用法：在项目根目录运行  python3 上传新书后点击自动修改index.py
"""

import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
BOOKS_DIR = os.path.join(BASE_DIR, "js", "books")


def extract_meta(filepath):
    """从 book-*.js 文件中提取 title 和 date。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        head = f.read(2000)
    title_m = re.search(r"title:\s*'([^']*)'", head)
    date_m = re.search(r"date:\s*'(\d{4}-\d{2}-\d{2})'", head)
    title = title_m.group(1) if title_m else ''
    date = date_m.group(1) if date_m else '9999-99-99'
    return title, date


def get_book_files_with_meta():
    """获取所有 book-*.js 文件及其元信息。"""
    pattern = os.path.join(BOOKS_DIR, "book-*.js")
    result = []
    for fpath in glob.glob(pattern):
        name = os.path.basename(fpath)
        title, date = extract_meta(fpath)
        mtime = os.path.getmtime(fpath)
        result.append({'name': name, 'path': fpath, 'title': title, 'date': date, 'mtime': mtime})
    return result


def deduplicate(books):
    """检测标题重复的书，保留最新的文件，删除旧的。返回去重后的列表。"""
    by_title = {}
    for b in books:
        by_title.setdefault(b['title'], []).append(b)

    keep = []
    for title, group in by_title.items():
        if len(group) > 1:
            group.sort(key=lambda x: x['mtime'], reverse=True)
            newest = group[0]
            print(f"\n  ⚠ 检测到重复书籍《{title}》，共 {len(group)} 个文件：")
            for i, b in enumerate(group):
                tag = "保留" if i == 0 else "删除"
                print(f"    [{tag}] {b['name']}  (date: {b['date']})")
            for dup in group[1:]:
                os.remove(dup['path'])
                print(f"    ✗ 已删除: {dup['name']}")
            keep.append(newest)
        else:
            keep.append(group[0])
    return keep


def build_script_block(filenames):
    lines = []
    for name in filenames:
        lines.append(f'  <script src="js/books/{name}"></script>')
    return "\n".join(lines)


def sync():
    if not os.path.exists(INDEX_PATH):
        print(f"错误：找不到 {INDEX_PATH}")
        return

    all_books = get_book_files_with_meta()
    if not all_books:
        print("警告：js/books/ 下没有找到 book-*.js 文件")
        return

    print(f"\n扫描到 {len(all_books)} 个文件...")
    books = deduplicate(all_books)
    books.sort(key=lambda x: x['date'])

    book_files = [b['name'] for b in books]

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"(    ={40,}\n  -->)\n(.*?)\n(  <script src=\"js/app\.js\"></script>)",
        re.DOTALL,
    )

    match = pattern.search(content)
    if not match:
        print("错误：在 index.html 中找不到 script 标记区域")
        return

    old_block = match.group(2).strip()
    new_block = build_script_block(book_files)

    if old_block == new_block:
        print(f"\n无需更新，index.html 已包含全部 {len(book_files)} 本书：")
        for i, b in enumerate(books, 1):
            print(f"  {i:02d}. 《{b['title']}》 ({b['date']})  →  {b['name']}")
        return

    new_content = pattern.sub(
        rf"\g<1>\n{new_block}\n\g<3>",
        content,
    )

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    old_names = set(re.findall(r'book-[\w-]+\.js', old_block))
    new_names = set(book_files)
    added = new_names - old_names
    removed = old_names - new_names

    print(f"\n已同步 index.html，共 {len(book_files)} 本书（按日期排序）：")
    for i, b in enumerate(books, 1):
        mark = ''
        if b['name'] in added:
            mark = '  [新增]'
        print(f"  {i:02d}. 《{b['title']}》 ({b['date']})  →  {b['name']}{mark}")
    if removed:
        print("\n  已移除的引用：")
        for name in sorted(removed):
            print(f"    ✗ {name}")


if __name__ == "__main__":
    sync()
