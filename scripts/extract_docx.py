#!/usr/bin/env python3
"""Extrae texto de un archivo .docx (OpenXML) sin dependencias externas.

Uso: python scripts/extract_docx.py path/to/file.docx
Imprime el texto extraído por consola.
"""
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

WPNS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def extract_text_from_docx(path: Path) -> str:
    texts = []
    with zipfile.ZipFile(path, 'r') as z:
        # document main body
        names = [n for n in z.namelist() if n.startswith('word/')]
        targets = []
        if 'word/document.xml' in names:
            targets.append('word/document.xml')
        # include headers and footers if present
        targets += [n for n in names if n.startswith('word/header') and n.endswith('.xml')]
        targets += [n for n in names if n.startswith('word/footer') and n.endswith('.xml')]

        for t in targets:
            data = z.read(t)
            texts.append(extract_text_from_xml(data))
    return '\n\n'.join([t for t in texts if t.strip()])


def extract_text_from_xml(xml_bytes: bytes) -> str:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return ''
    paragraphs = []
    for p in root.findall('.//' + WPNS + 'p'):
        parts = []
        for t in p.findall('.//' + WPNS + 't'):
            if t.text:
                parts.append(t.text)
        if parts:
            paragraphs.append(''.join(parts))
    return '\n'.join(paragraphs)


def main():
    if len(sys.argv) < 2:
        print('Uso: python scripts/extract_docx.py file.docx', file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f'No existe: {path}', file=sys.stderr)
        sys.exit(2)
    text = extract_text_from_docx(path)
    if not text.strip():
        print('(No se extrajo texto legible del .docx)')
    else:
        print(text)


if __name__ == '__main__':
    main()
