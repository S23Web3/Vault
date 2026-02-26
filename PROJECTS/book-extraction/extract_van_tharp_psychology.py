"""
Van Tharp Psychology Extraction Script
Extracts ALL psychology-related chapters from the epub.
Run standalone: python extract_van_tharp_psychology.py
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
from pathlib import Path

# Psychology-focused chapters (based on TOC analysis)
PSYCHOLOGY_CHAPTERS = {
    'ch01': 'Chapter 1: The Holy Grail',
    'ch02': 'Chapter 2: Judgmental Biases',
    'ch03': 'Chapter 3: Setting Your Objectives',
    'ch04': 'Chapter 4: Steps to Developing a System',
    'ch10': 'Chapter 10: How to Take Profits and Losses',
    'ch14': 'Chapter 14: Position Sizing',
    'ch15': 'Chapter 15: Conclusion'
}

def clean_text(text):
    """Remove excessive whitespace and format nicely."""
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Remove excessive spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()

def extract_epub(epub_path, output_path):
    """Extract psychology chapters from Van Tharp epub."""

    import sys
    # Force UTF-8 for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print(f"Reading epub: {epub_path}")
    book = epub.read_epub(str(epub_path))

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("VAN THARP — TRADE YOUR WAY TO FINANCIAL FREEDOM\n")
        f.write("PSYCHOLOGY EXTRACTION\n")
        f.write("=" * 80 + "\n\n")

        extracted_count = 0

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                # Get file name to identify chapter
                file_name = item.get_name().lower()

                # Extract text
                soup = BeautifulSoup(item.get_content().decode('utf-8', errors='replace'), 'html.parser')
                text = soup.get_text()

                # Skip tiny files (TOC, cover, etc.)
                if len(text.strip()) < 500:
                    continue

                # Check if this is a psychology chapter
                is_psychology_chapter = False
                chapter_title = None

                for ch_key, ch_name in PSYCHOLOGY_CHAPTERS.items():
                    if ch_key in file_name or ch_name.lower() in text[:2000].lower():
                        is_psychology_chapter = True
                        chapter_title = ch_name
                        break

                # Also extract if it contains key psychology keywords
                if not is_psychology_chapter:
                    keywords = ['cognitive bias', 'holy grail', 'position sizing', 'expectancy',
                                'self-sabotage', 'discipline', 'risk management', 'mental']
                    if any(kw in text.lower() for kw in keywords):
                        is_psychology_chapter = True
                        chapter_title = f"Psychology Content from {file_name}"

                if is_psychology_chapter:
                    extracted_count += 1
                    print(f"  ✓ Extracting: {chapter_title or file_name}")

                    f.write("\n" + "=" * 80 + "\n")
                    f.write(f"{chapter_title or file_name}\n")
                    f.write(f"Source file: {item.get_name()}\n")
                    f.write("=" * 80 + "\n\n")

                    cleaned = clean_text(text)
                    f.write(cleaned)
                    f.write("\n\n")

            except Exception as e:
                print(f"  ✗ Error processing {item.get_name()}: {e}")
                continue

        f.write("\n" + "=" * 80 + "\n")
        f.write(f"EXTRACTION COMPLETE — {extracted_count} sections extracted\n")
        f.write("=" * 80 + "\n")

    print(f"\n✓ Extraction complete: {output_file}")
    print(f"  {extracted_count} psychology sections extracted")
    print(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")
    return output_file

if __name__ == "__main__":
    epub_path = Path(r"C:\Users\User\Downloads\Van Tharp - Trade Your Way to Financial Freedom.epub")
    output_path = Path(r"C:\Users\User\Documents\Obsidian Vault\07-TEMPLATES\van-tharp-psychology-extraction.txt")

    if not epub_path.exists():
        print(f"ERROR: epub not found at {epub_path}")
        exit(1)

    extract_epub(epub_path, output_path)
