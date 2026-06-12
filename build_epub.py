#!/usr/bin/env python3
"""Build ePub for No Thoughts, Just Fluff — robust version."""

import os, re, zipfile, uuid
from datetime import datetime

NOVEL_DIR = r"C:\Users\Administrator\novels\No Thoughts Just Fluff"
CHAPTERS_DIR = os.path.join(NOVEL_DIR, "chapters")
OUTPUT = os.path.join(NOVEL_DIR, "No_Thoughts_Just_Fluff.epub")

# Collect chapters
ch_files = sorted(f for f in os.listdir(CHAPTERS_DIR) if f.endswith(".md") and f.startswith("ch0"))
print(f"Found {len(ch_files)} chapters")

def md_to_html(text):
    """Simple markdown → HTML conversion."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic  
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Paragraphs
    paragraphs = text.strip().split('\n\n')
    parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith('<'):
            parts.append(p)
        else:
            p = p.replace('\n', '<br/>')
            parts.append(f'<p>{p}</p>')
    return '\n'.join(parts)

def escape_xml(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

# Build OEBPS content
book_id = str(uuid.uuid4())
now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

chapters_html = []
manifest_items = []
spine_items = []
toc_entries = []

for ch_file in ch_files:
    ch_num = int(re.search(r'ch(\d+)', ch_file).group(1))
    with open(os.path.join(CHAPTERS_DIR, ch_file), 'r', encoding='utf-8') as f:
        raw = f.read()
    
    # Extract title
    title_match = re.search(r'^#\s+(.+)', raw, re.MULTILINE)
    if title_match:
        ch_title = title_match.group(1).strip()
        content = re.sub(r'^#\s+.+\n?', '', raw, count=1)
    else:
        ch_title = f"Chapter {ch_num}"
        content = raw
    
    html_body = md_to_html(content)
    if not html_body.strip():
        html_body = '<p>&#160;</p>'
    
    fname = f"chapter{ch_num:03d}.xhtml"
    ch_html = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head><meta charset="UTF-8"/><title>{escape_xml(ch_title)}</title></head>
<body>
<h2>Chapter {ch_num}: {escape_xml(ch_title)}</h2>
{html_body}
</body></html>"""
    
    chapters_html.append((fname, ch_html))
    item_id = f"ch{ch_num:03d}"
    manifest_items.append(f'<item id="{item_id}" href="{fname}" media-type="application/xhtml+xml"/>')
    spine_items.append(f'<itemref idref="{item_id}"/>')
    toc_entries.append(f'<navPoint id="nav_{item_id}" playOrder="{ch_num}"><navLabel><text>Chapter {ch_num}: {escape_xml(ch_title)}</text></navLabel><content src="{fname}"/></navPoint>')

# Create ePub (ZIP)
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    # mimetype must be first, uncompressed
    zf.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
    
    # META-INF/container.xml
    zf.writestr('META-INF/container.xml', """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""")
    
    # OEBPS/content.opf
    opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">urn:uuid:{book_id}</dc:identifier>
    <dc:title>No Thoughts, Just Fluff</dc:title>
    <dc:creator>K. Chen</dc:creator>
    <dc:language>en</dc:language>
    <dc:date>{now}</dc:date>
    <dc:description>A burned-out PR worker transforms into a giant capybara and discovers that choosing peace might be the bravest thing she's ever done.</dc:description>
    <meta property="dcterms:modified">{now}</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    {''.join(manifest_items)}
  </manifest>
  <spine toc="ncx">
    <itemref idref="nav"/>
    {''.join(spine_items)}
  </spine>
</package>"""
    zf.writestr('OEBPS/content.opf', opf)
    
    # OEBPS/toc.ncx
    ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{book_id}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>No Thoughts, Just Fluff</text></docTitle>
  <navMap>
    {''.join(toc_entries)}
  </navMap>
</ncx>"""
    zf.writestr('OEBPS/toc.ncx', ncx)
    
    # OEBPS/nav.xhtml
    nav_links = []
    for i, (fname, ch_html) in enumerate(chapters_html):
        ch_num = i + 1
        title_match = re.search(r'<h2>(.*?)</h2>', ch_html)
        title = title_match.group(1) if title_match else f"Chapter {ch_num}"
        nav_links.append(f'<li><a href="{fname}">{escape_xml(title)}</a></li>')
    
    nav = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">
<head><meta charset="UTF-8"/><title>Table of Contents</title></head>
<body>
<nav epub:type="toc" id="toc">
  <h1>Table of Contents</h1>
  <ol>
    {''.join(nav_links)}
  </ol>
</nav>
</body></html>"""
    zf.writestr('OEBPS/nav.xhtml', nav)
    
    # Chapter files
    for fname, ch_html in chapters_html:
        zf.writestr(f'OEBPS/{fname}', ch_html)

print(f"\nePub written to: {OUTPUT}")
print(f"Size: {os.path.getsize(OUTPUT):,} bytes")
print(f"Chapters: {len(ch_files)}")
