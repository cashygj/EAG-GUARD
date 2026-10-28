# -*- coding: utf-8 -*-
"""Dump the full body of a .docx in reading order, including tables."""
import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

SRC = sys.argv[1]
doc = Document(SRC)


def iter_block_items(parent):
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn('w:p'):
            yield Paragraph(child, parent)
        elif child.tag == qn('w:tbl'):
            yield Table(child, parent)


def has_picture(p):
    return bool(p._p.findall('.//' + qn('a:blip')))


for i, block in enumerate(iter_block_items(doc)):
    if isinstance(block, Paragraph):
        t = block.text
        marks = []
        if has_picture(block):
            marks.append('IMG')
        if block.style.name != 'Normal':
            marks.append(block.style.name)
        tag = f"<<{','.join(marks)}>>" if marks else ""
        if t.strip() or tag:
            print(f"[{i:03d}]{tag} {t}")
    else:
        print(f"[{i:03d}] === TABLE {len(block.rows)}x{len(block.columns)} ===")
        for r, row in enumerate(block.rows):
            cells = [c.text.replace('\n', ' / ') for c in row.cells]
            print("   | " + " | ".join(cells))
        print("   === END TABLE ===")

print("\n---- CORE PROPERTIES ----")
cp = doc.core_properties
for a in ('title', 'subject', 'author', 'last_modified_by', 'created', 'modified', 'revision', 'comments'):
    print(a, '=', getattr(cp, a, None))
