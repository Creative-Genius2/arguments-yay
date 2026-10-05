#!/usr/bin/env python3
"""
Story reader tool. Extracts and displays chapters from the Ashes of the Past
EPUB and the user's own stories (Inklings of a Legacy, Greyscale).

Usage:
    python reader.py list                    # list all available chapters
    python reader.py ashes 1                 # read Ashes chapter 1 (Prologue)
    python reader.py ashes 25               # read Ashes chapter 25 (Mewtwo Strikes Back)
    python reader.py ashes 1-3              # read Ashes chapters 1 through 3
    python reader.py ashes prologue         # search by name
    python reader.py ashes mewtwo           # search by name (partial match)
    python reader.py inklings               # read Inklings of a Legacy (full)
    python reader.py greyscale              # read Greyscale (full)
"""

import sys
import os
import re
import zipfile
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EPUB_PATH = os.path.join(SCRIPT_DIR, "Ashes_of_the_Past_-.epub")
INKLINGS_PATH = os.path.join(SCRIPT_DIR, "Inklings Of A Legacy.md")
GREYSCALE_PATH = os.path.join(SCRIPT_DIR, "Pokémon_ Greyscale (5).md")


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False
        self.in_em = False
        self.in_blockquote = False

    def handle_starttag(self, tag, attrs):
        if tag == "em" or tag == "i":
            self.result.append("*")
            self.in_em = True
        elif tag == "strong" or tag == "b":
            self.result.append("**")
        elif tag == "hr":
            self.result.append("\n---\n")
        elif tag == "br":
            self.result.append("\n")
        elif tag == "p":
            pass
        elif tag == "blockquote":
            self.in_blockquote = True

    def handle_endtag(self, tag):
        if tag == "em" or tag == "i":
            self.result.append("*")
            self.in_em = False
        elif tag == "strong" or tag == "b":
            self.result.append("**")
        elif tag == "p":
            self.result.append("\n\n")
        elif tag == "blockquote":
            self.in_blockquote = False

    def handle_data(self, data):
        self.result.append(data)

    def get_text(self):
        return "".join(self.result).strip()


def parse_toc(epub_zip):
    """Parse the NCX table of contents to get chapter ordering and titles."""
    toc_xml = epub_zip.read("toc.ncx").decode("utf-8")
    chapters = []
    nav_points = re.findall(
        r'<navPoint[^>]*>.*?<text>(.*?)</text>.*?<content src="(.*?)"',
        toc_xml,
        re.DOTALL,
    )
    for title, src in nav_points:
        title = title.strip()
        if title in ("Preface", "Afterword"):
            continue
        chapters.append({"title": title, "file": src})
    return chapters


def extract_chapter_text(epub_zip, filename):
    """Extract readable text from a chapter's xhtml."""
    html = epub_zip.read(filename).decode("utf-8")
    content_match = re.search(
        r'<div class="userstuff2">(.*?)</div>', html, re.DOTALL
    )
    if not content_match:
        content_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL)
    if not content_match:
        return "(Could not extract chapter content)"

    extractor = HTMLTextExtractor()
    extractor.feed(content_match.group(1))
    text = extractor.get_text()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def list_chapters():
    """List all available content."""
    with zipfile.ZipFile(EPUB_PATH, "r") as z:
        chapters = parse_toc(z)

    print("=" * 60)
    print("ASHES OF THE PAST — Kanto Arc")
    print("=" * 60)
    for i, ch in enumerate(chapters, 1):
        print(f"  {i:3d}. {ch['title']}")
    print(f"\n  Total: {len(chapters)} chapters")

    print("\n" + "=" * 60)
    print("USER'S STORIES")
    print("=" * 60)
    print("  inklings  — Inklings of a Legacy")
    print("  greyscale — Pokémon: Greyscale")
    print()


def read_ashes(query):
    """Read one or more Ashes chapters by number, range, or name search."""
    with zipfile.ZipFile(EPUB_PATH, "r") as z:
        chapters = parse_toc(z)

        range_match = re.match(r"^(\d+)-(\d+)$", query)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            for num in range(start, end + 1):
                if 1 <= num <= len(chapters):
                    ch = chapters[num - 1]
                    print(f"\n{'=' * 60}")
                    print(f"Chapter {num}: {ch['title']}")
                    print(f"{'=' * 60}\n")
                    print(extract_chapter_text(z, ch["file"]))
            return

        if query.isdigit():
            num = int(query)
            if 1 <= num <= len(chapters):
                ch = chapters[num - 1]
                print(f"\n{'=' * 60}")
                print(f"Chapter {num}: {ch['title']}")
                print(f"{'=' * 60}\n")
                print(extract_chapter_text(z, ch["file"]))
            else:
                print(f"Chapter {num} out of range (1-{len(chapters)})")
            return

        query_lower = query.lower()
        matches = [
            (i, ch)
            for i, ch in enumerate(chapters, 1)
            if query_lower in ch["title"].lower()
        ]
        if matches:
            for num, ch in matches:
                print(f"\n{'=' * 60}")
                print(f"Chapter {num}: {ch['title']}")
                print(f"{'=' * 60}\n")
                print(extract_chapter_text(z, ch["file"]))
        else:
            print(f"No chapters matching '{query}'")
            print("Use 'python reader.py list' to see all chapters")


def read_user_story(which):
    """Read one of the user's stories in full."""
    if which == "inklings":
        path = INKLINGS_PATH
        title = "Inklings of a Legacy"
    elif which == "greyscale":
        path = GREYSCALE_PATH
        title = "Pokémon: Greyscale"
    else:
        print(f"Unknown story: {which}")
        return

    print(f"\n{'=' * 60}")
    print(title)
    print(f"{'=' * 60}\n")
    with open(path, "r", encoding="utf-8") as f:
        print(f.read())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "list":
        list_chapters()
    elif cmd == "ashes":
        if len(sys.argv) < 3:
            print("Usage: python reader.py ashes <chapter_number|name|range>")
            return
        query = " ".join(sys.argv[2:])
        read_ashes(query)
    elif cmd == "inklings":
        read_user_story("inklings")
    elif cmd == "greyscale":
        read_user_story("greyscale")
    else:
        print(f"Unknown command: {cmd}")
        print("Commands: list, ashes <num>, inklings, greyscale")


if __name__ == "__main__":
    main()
