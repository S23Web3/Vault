"""
Deep Book Analysis System
Does FULL chapter-by-chapter analysis of trading/ML/finance books.
Not just keyword counting — actually reads and understands content.

Usage:
    python deep_book_analyzer.py                    # Interactive mode - scans Downloads
    python deep_book_analyzer.py --folder PATH      # Scan specific folder
    python deep_book_analyzer.py --auto             # Auto-analyze all without prompts
"""

import sys
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path
import re
import json
from datetime import datetime

# Force UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Core concepts to extract per chapter
TRADING_TOPICS = {
    'entries': ['entry signal', 'entry point', 'trigger', 'buy signal', 'setup', 'pattern'],
    'exits': ['stop loss', 'take profit', 'exit strategy', 'trailing stop', 'profit target'],
    'risk': ['position size', 'risk management', 'drawdown', 'risk-reward', 'kelly', 'percent risk'],
    'backtesting': ['backtest', 'historical test', 'walk-forward', 'optimization', 'overfitting'],
    'metrics': ['sharpe', 'sortino', 'expectancy', 'win rate', 'profit factor', 'SQN', 'R-multiple'],
    'psychology': ['discipline', 'emotion', 'bias', 'mental', 'cognitive', 'psychology'],
}

ML_TOPICS = {
    'supervised': ['classification', 'regression', 'labeled data', 'supervised learning'],
    'features': ['feature engineering', 'feature selection', 'feature importance', 'lag features'],
    'models': ['random forest', 'xgboost', 'gradient boost', 'neural network', 'SVM', 'logistic'],
    'validation': ['cross-validation', 'train test split', 'overfitting', 'k-fold', 'purging'],
    'metrics': ['accuracy', 'precision', 'recall', 'F1', 'AUC', 'confusion matrix', 'SHAP'],
}

class DeepBookAnalyzer:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else Path(r"C:\Users\User\Documents\Obsidian Vault\07-TEMPLATES\book-analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.output_dir / "deep_analysis_log.json"
        self.load_log()

    def load_log(self):
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.log = json.load(f)
        else:
            self.log = {'analyzed_books': {}, 'last_updated': None}

    def save_log(self):
        self.log['last_updated'] = datetime.now().isoformat()
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log, f, indent=2, ensure_ascii=False)

    def extract_epub_chapters(self, epub_path):
        """Extract chapters as separate text blocks."""
        print(f"  📖 Reading epub: {epub_path.name}")
        book = epub.read_epub(str(epub_path))

        chapters = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                soup = BeautifulSoup(item.get_content().decode('utf-8', errors='replace'), 'html.parser')
                text = soup.get_text()

                if len(text.strip()) > 500:  # Skip tiny files
                    # Try to identify chapter title
                    lines = text.split('\n')
                    title = None
                    for line in lines[:20]:
                        if re.match(r'^(chapter|part|\d+\.)', line.strip().lower()):
                            title = line.strip()
                            break

                    chapters.append({
                        'file': item.get_name(),
                        'title': title or item.get_name(),
                        'text': text,
                        'length': len(text)
                    })
            except:
                continue

        print(f"  ✓ Extracted {len(chapters)} chapters")
        return chapters

    def extract_pdf_chapters(self, pdf_path):
        """Extract PDF as chapters (split by page or section)."""
        try:
            import pymupdf4llm
            print(f"  📄 Reading PDF: {pdf_path.name}")
            md_text = pymupdf4llm.to_markdown(str(pdf_path))

            # Split by # headers (markdown headings)
            chapter_pattern = r'^#+\s+(.+?)$'
            matches = list(re.finditer(chapter_pattern, md_text, re.MULTILINE))

            chapters = []
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i+1].start() if i+1 < len(matches) else len(md_text)
                chapter_text = md_text[start:end]

                if len(chapter_text.strip()) > 500:
                    chapters.append({
                        'file': f'section_{i}',
                        'title': match.group(1),
                        'text': chapter_text,
                        'length': len(chapter_text)
                    })

            print(f"  ✓ Extracted {len(chapters)} sections")
            return chapters

        except ImportError:
            print(f"  ⚠ pymupdf4llm not installed - skipping PDF")
            return None
        except Exception as e:
            print(f"  ✗ Error reading PDF: {e}")
            return None

    def deep_analyze_chapter(self, chapter_text):
        """Deep analysis of a single chapter - extract actual concepts."""
        text_lower = chapter_text.lower()

        # Find trading concepts
        trading_concepts_found = {}
        for topic, keywords in TRADING_TOPICS.items():
            mentions = []
            for keyword in keywords:
                if keyword in text_lower:
                    # Extract surrounding context (50 chars before/after)
                    pattern = f'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                    contexts = re.findall(pattern, text_lower, re.IGNORECASE)
                    mentions.extend(contexts[:2])  # Limit to 2 examples per keyword

            if mentions:
                trading_concepts_found[topic] = {
                    'count': len(mentions),
                    'examples': mentions[:3]  # Top 3 examples
                }

        # Find ML concepts
        ml_concepts_found = {}
        for topic, keywords in ML_TOPICS.items():
            mentions = []
            for keyword in keywords:
                if keyword in text_lower:
                    pattern = f'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                    contexts = re.findall(pattern, text_lower, re.IGNORECASE)
                    mentions.extend(contexts[:2])

            if mentions:
                ml_concepts_found[topic] = {
                    'count': len(mentions),
                    'examples': mentions[:3]
                }

        # Check for code/formulas
        has_code = bool(re.search(r'(def |class |import |function|```python)', chapter_text))
        has_formulas = bool(re.search(r'(\$.*\$|\\frac|\\sum|=.*\+.*\*)', chapter_text))

        # Extract key sentences (those with important keywords)
        key_sentences = []
        sentences = re.split(r'[.!?]+', chapter_text)
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean) > 30 and len(sentence_clean) < 300:
                # Check if sentence contains important concepts
                important_keywords = ['key', 'important', 'critical', 'must', 'essential',
                                     'fundamental', 'note that', 'remember', 'always', 'never']
                if any(kw in sentence_clean.lower() for kw in important_keywords):
                    key_sentences.append(sentence_clean)

        return {
            'trading_concepts': trading_concepts_found,
            'ml_concepts': ml_concepts_found,
            'has_code': has_code,
            'has_formulas': has_formulas,
            'key_sentences': key_sentences[:5],  # Top 5
            'length': len(chapter_text)
        }

    def analyze_book_deep(self, book_path):
        """Deep analysis of entire book."""
        print(f"\n{'='*80}")
        print(f"DEEP ANALYSIS: {book_path.name}")
        print(f"{'='*80}")

        # Extract chapters
        if book_path.suffix.lower() == '.epub':
            chapters = self.extract_epub_chapters(book_path)
        elif book_path.suffix.lower() == '.pdf':
            chapters = self.extract_pdf_chapters(book_path)
        else:
            print(f"  ✗ Unsupported format: {book_path.suffix}")
            return None

        if not chapters:
            return None

        # Analyze each chapter
        print(f"\n  Analyzing {len(chapters)} chapters...")
        chapter_analyses = []

        for i, chapter in enumerate(chapters, 1):
            print(f"    [{i}/{len(chapters)}] {chapter['title'][:60]}...")
            analysis = self.deep_analyze_chapter(chapter['text'])
            chapter_analyses.append({
                'title': chapter['title'],
                'file': chapter['file'],
                'analysis': analysis
            })

        # Aggregate results
        total_trading_concepts = sum(
            len(ch['analysis']['trading_concepts']) for ch in chapter_analyses
        )
        total_ml_concepts = sum(
            len(ch['analysis']['ml_concepts']) for ch in chapter_analyses
        )
        chapters_with_code = sum(
            ch['analysis']['has_code'] for ch in chapter_analyses
        )
        chapters_with_formulas = sum(
            ch['analysis']['has_formulas'] for ch in chapter_analyses
        )

        # Calculate rating based on depth
        rating = self.calculate_deep_rating(chapter_analyses, total_trading_concepts, total_ml_concepts)

        print(f"\n  📊 DEEP ANALYSIS RESULTS:")
        print(f"     Trading concepts found: {total_trading_concepts}")
        print(f"     ML concepts found: {total_ml_concepts}")
        print(f"     Chapters with code: {chapters_with_code}/{len(chapters)}")
        print(f"     Chapters with formulas: {chapters_with_formulas}/{len(chapters)}")
        print(f"  🎯 RATING: {rating}/10")

        # Extract top concepts
        top_concepts = self.extract_top_concepts(chapter_analyses)

        # Compile results
        result = {
            'file_path': str(book_path),
            'file_name': book_path.name,
            'file_size_mb': book_path.stat().st_size / (1024*1024),
            'total_chapters': len(chapters),
            'rating': rating,
            'aggregate_stats': {
                'total_trading_concepts': total_trading_concepts,
                'total_ml_concepts': total_ml_concepts,
                'chapters_with_code': chapters_with_code,
                'chapters_with_formulas': chapters_with_formulas,
            },
            'top_concepts': top_concepts,
            'chapter_analyses': chapter_analyses,
            'analyzed_date': datetime.now().isoformat()
        }

        # Save detailed analysis
        safe_filename = re.sub(r'[^\w\s-]', '', book_path.stem).strip()[:50]
        output_file = self.output_dir / f"{safe_filename}_DEEP.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Saved deep analysis: {output_file.name}")

        # Generate markdown summary
        self.generate_book_markdown(result, safe_filename)

        # Update log
        self.log['analyzed_books'][book_path.name] = {
            'rating': rating,
            'chapters': len(chapters),
            'analyzed_date': result['analyzed_date']
        }

        return result

    def calculate_deep_rating(self, chapter_analyses, total_trading, total_ml):
        """Calculate rating based on deep analysis."""

        # Concept coverage (0-4 points)
        concept_score = min(4, (total_trading + total_ml) / 15)

        # Code/formula presence (0-2 points)
        chapters_with_content = sum(
            1 for ch in chapter_analyses
            if ch['analysis']['has_code'] or ch['analysis']['has_formulas']
        )
        content_score = min(2, chapters_with_content / (len(chapter_analyses) * 0.3))

        # Key sentences extracted (0-2 points)
        total_key_sentences = sum(
            len(ch['analysis']['key_sentences']) for ch in chapter_analyses
        )
        sentence_score = min(2, total_key_sentences / 20)

        # Breadth (0-2 points) - covers multiple topics
        unique_trading_topics = len(set(
            topic for ch in chapter_analyses
            for topic in ch['analysis']['trading_concepts'].keys()
        ))
        unique_ml_topics = len(set(
            topic for ch in chapter_analyses
            for topic in ch['analysis']['ml_concepts'].keys()
        ))
        breadth_score = min(2, (unique_trading_topics + unique_ml_topics) / 6)

        total = concept_score + content_score + sentence_score + breadth_score
        return max(1, min(10, round(total)))

    def extract_top_concepts(self, chapter_analyses):
        """Extract most frequently mentioned concepts."""
        trading_counts = {}
        ml_counts = {}

        for ch in chapter_analyses:
            for topic, data in ch['analysis']['trading_concepts'].items():
                trading_counts[topic] = trading_counts.get(topic, 0) + data['count']
            for topic, data in ch['analysis']['ml_concepts'].items():
                ml_counts[topic] = ml_counts.get(topic, 0) + data['count']

        # Sort and return top 5
        top_trading = sorted(trading_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_ml = sorted(ml_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'trading': [{'topic': t, 'mentions': c} for t, c in top_trading],
            'ml': [{'topic': t, 'mentions': c} for t, c in top_ml]
        }

    def generate_book_markdown(self, result, filename):
        """Generate human-readable markdown summary."""
        md_file = self.output_dir / f"{filename}_SUMMARY.md"

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Deep Analysis: {result['file_name']}\n\n")
            f.write(f"**Rating**: {result['rating']}/10\n\n")
            f.write(f"**Analyzed**: {result['analyzed_date']}\n\n")
            f.write(f"**Size**: {result['file_size_mb']:.1f} MB | **Chapters**: {result['total_chapters']}\n\n")
            f.write("---\n\n")

            f.write("## Summary Stats\n\n")
            stats = result['aggregate_stats']
            f.write(f"- Trading concepts found: **{stats['total_trading_concepts']}**\n")
            f.write(f"- ML concepts found: **{stats['total_ml_concepts']}**\n")
            f.write(f"- Chapters with code: **{stats['chapters_with_code']}/{result['total_chapters']}**\n")
            f.write(f"- Chapters with formulas: **{stats['chapters_with_formulas']}/{result['total_chapters']}**\n\n")

            f.write("## Top Concepts\n\n")
            f.write("### Trading:\n")
            for item in result['top_concepts']['trading']:
                f.write(f"- **{item['topic']}**: {item['mentions']} mentions\n")

            f.write("\n### Machine Learning:\n")
            for item in result['top_concepts']['ml']:
                f.write(f"- **{item['topic']}**: {item['mentions']} mentions\n")

            f.write("\n---\n\n")
            f.write("## Chapter-by-Chapter Breakdown\n\n")

            for i, ch in enumerate(result['chapter_analyses'], 1):
                f.write(f"### {i}. {ch['title']}\n\n")

                if ch['analysis']['trading_concepts']:
                    f.write("**Trading Concepts:**\n")
                    for topic, data in ch['analysis']['trading_concepts'].items():
                        f.write(f"- {topic}: {data['count']} mentions\n")

                if ch['analysis']['ml_concepts']:
                    f.write("\n**ML Concepts:**\n")
                    for topic, data in ch['analysis']['ml_concepts'].items():
                        f.write(f"- {topic}: {data['count']} mentions\n")

                if ch['analysis']['key_sentences']:
                    f.write("\n**Key Takeaways:**\n")
                    for sentence in ch['analysis']['key_sentences']:
                        f.write(f"> {sentence}\n\n")

                f.write("\n")

        print(f"  ✓ Saved markdown summary: {md_file.name}")

    def generate_master_summary(self):
        """Generate master summary of all analyzed books."""
        if not self.log['analyzed_books']:
            print("No books analyzed yet.")
            return

        books = sorted(self.log['analyzed_books'].items(),
                      key=lambda x: x[1]['rating'],
                      reverse=True)

        summary_file = self.output_dir / "MASTER_ANALYSIS_SUMMARY.md"

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Deep Book Analysis — Master Summary\n\n")
            f.write(f"**Last Updated**: {self.log['last_updated']}\n\n")
            f.write(f"**Total Books**: {len(books)}\n\n")
            f.write("---\n\n")

            f.write("## All Books (Sorted by Rating)\n\n")
            f.write("| Rating | File | Chapters | Date |\n")
            f.write("|--------|------|----------|------|\n")

            for filename, data in books:
                date_short = data['analyzed_date'][:10]
                f.write(f"| **{data['rating']}/10** | {filename} | {data['chapters']} | {date_short} |\n")

        print(f"\n✓ Master summary: {summary_file}")

def scan_and_analyze(folder_path, auto_mode=False):
    """Scan folder and perform deep analysis."""
    folder = Path(folder_path)

    if not folder.exists():
        print(f"ERROR: Folder not found: {folder}")
        return

    books = list(folder.glob('*.epub')) + list(folder.glob('*.pdf'))

    if not books:
        print(f"No .epub or .pdf files found in {folder}")
        return

    print(f"\n{'='*80}")
    print(f"FOUND {len(books)} BOOKS IN: {folder}")
    print(f"{'='*80}")

    for book in books:
        print(f"  - {book.name} ({book.stat().st_size / (1024*1024):.1f} MB)")

    analyzer = DeepBookAnalyzer()

    analyzed_count = 0
    skipped_count = 0

    for book in books:
        if book.name in analyzer.log['analyzed_books']:
            existing_rating = analyzer.log['analyzed_books'][book.name]['rating']
            print(f"\n⏭ {book.name} — Already analyzed (rating: {existing_rating}/10)")

            if not auto_mode:
                choice = input("  Re-analyze? (y/n): ").lower()
                if choice != 'y':
                    skipped_count += 1
                    continue

        if not auto_mode:
            choice = input(f"\nDeep analyze {book.name}? (y/n/q): ").lower()
            if choice == 'q':
                break
            if choice != 'y':
                skipped_count += 1
                continue

        result = analyzer.analyze_book_deep(book)
        if result:
            analyzed_count += 1

        analyzer.save_log()

    analyzer.generate_master_summary()

    print(f"\n{'='*80}")
    print(f"DEEP ANALYSIS COMPLETE")
    print(f"  Analyzed: {analyzed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total in library: {len(analyzer.log['analyzed_books'])}")
    print(f"{'='*80}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Deep Book Analysis System')
    parser.add_argument('--folder', type=str, default=r"C:\Users\User\Downloads",
                       help='Folder to scan for books')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-analyze all books without prompts')

    args = parser.parse_args()

    scan_and_analyze(args.folder, auto_mode=args.auto)
