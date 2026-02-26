"""
Standalone Deep Book Analyzer
Runs completely locally - no API calls, no external dependencies beyond parsing libraries.
Analyzes trading/ML books and generates ratings + summaries.

Usage:
    python standalone_analyzer.py                    # Interactive mode
    python standalone_analyzer.py --auto             # Auto-analyze all
    python standalone_analyzer.py --folder PATH      # Custom folder
"""

import sys
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path
import re
import json
from datetime import datetime
from collections import Counter

# Force UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Trading concepts to detect
TRADING_CONCEPTS = {
    'entries': ['entry signal', 'entry point', 'buy signal', 'sell signal', 'trigger', 'setup'],
    'exits': ['stop loss', 'take profit', 'exit strategy', 'trailing stop', 'profit target', 'cut losses'],
    'risk': ['position size', 'risk management', 'drawdown', 'risk-reward', 'kelly', 'percent risk', 'money management'],
    'backtesting': ['backtest', 'historical test', 'walk-forward', 'optimization', 'overfitting', 'in-sample', 'out-of-sample'],
    'metrics': ['sharpe', 'sortino', 'expectancy', 'win rate', 'profit factor', 'SQN', 'R-multiple', 'max drawdown'],
    'psychology': ['discipline', 'emotion', 'bias', 'mental', 'cognitive', 'psychology', 'trader psychology'],
}

ML_CONCEPTS = {
    'supervised': ['classification', 'regression', 'labeled data', 'supervised learning'],
    'features': ['feature engineering', 'feature selection', 'feature importance', 'lag features', 'alpha factors'],
    'models': ['random forest', 'xgboost', 'gradient boost', 'neural network', 'SVM', 'logistic regression'],
    'validation': ['cross-validation', 'train test split', 'overfitting', 'k-fold', 'purging', 'walk-forward'],
    'metrics': ['accuracy', 'precision', 'recall', 'F1', 'AUC', 'confusion matrix', 'SHAP', 'feature importance'],
}

class StandaloneAnalyzer:
    def __init__(self, output_dir=None):
        # Default to ./book-analysis/ in current directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path.cwd() / "book-analysis"

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / "analysis_log.json"
        self.load_log()

    def load_log(self):
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.log = json.load(f)
        else:
            self.log = {'books': {}, 'last_updated': None}

    def save_log(self):
        self.log['last_updated'] = datetime.now().isoformat()
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log, f, indent=2, ensure_ascii=False)

    def extract_epub(self, path):
        """Extract all text from epub."""
        print(f"  📖 Reading: {path.name}")
        book = epub.read_epub(str(path))

        chapters = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                soup = BeautifulSoup(item.get_content().decode('utf-8', errors='replace'), 'html.parser')
                text = soup.get_text()
                if len(text.strip()) > 500:
                    title = self.extract_title(text)
                    chapters.append({'title': title, 'text': text})
            except:
                continue

        print(f"  ✓ Extracted {len(chapters)} chapters")
        return chapters

    def extract_pdf(self, path):
        """Extract text from PDF."""
        try:
            import pymupdf4llm
            print(f"  📄 Reading: {path.name}")
            text = pymupdf4llm.to_markdown(str(path))

            # Split by headers
            sections = []
            parts = re.split(r'\n#+\s+(.+?)\n', text)
            for i in range(1, len(parts), 2):
                if i+1 < len(parts):
                    sections.append({'title': parts[i], 'text': parts[i+1]})

            print(f"  ✓ Extracted {len(sections)} sections")
            return sections
        except ImportError:
            print(f"  ⚠ pymupdf4llm not installed - skipping PDF")
            return None
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None

    def extract_title(self, text):
        """Extract chapter title from first few lines."""
        lines = [l.strip() for l in text.split('\n')[:20] if l.strip()]
        for line in lines:
            if 10 < len(line) < 100:
                if re.match(r'^(chapter|part|\d+\.)', line.lower()):
                    return line
        return "Chapter"

    def analyze_chapter(self, text):
        """Deep analyze single chapter - count concepts and extract examples."""
        text_lower = text.lower()

        # Count trading concepts
        trading = {}
        for topic, keywords in TRADING_CONCEPTS.items():
            count = sum(text_lower.count(kw) for kw in keywords)
            if count > 0:
                examples = []
                for kw in keywords:
                    if kw in text_lower:
                        # Extract context around keyword
                        pos = text_lower.find(kw)
                        if pos >= 0:
                            start = max(0, pos - 50)
                            end = min(len(text), pos + 100)
                            examples.append(text[start:end].strip())
                            if len(examples) >= 2:
                                break
                trading[topic] = {'count': count, 'examples': examples[:2]}

        # Count ML concepts
        ml = {}
        for topic, keywords in ML_CONCEPTS.items():
            count = sum(text_lower.count(kw) for kw in keywords)
            if count > 0:
                examples = []
                for kw in keywords:
                    if kw in text_lower:
                        pos = text_lower.find(kw)
                        if pos >= 0:
                            start = max(0, pos - 50)
                            end = min(len(text), pos + 100)
                            examples.append(text[start:end].strip())
                            if len(examples) >= 2:
                                break
                ml[topic] = {'count': count, 'examples': examples[:2]}

        # Detect code
        has_code = bool(re.search(r'(def |class |import |function|```)', text))

        # Detect formulas
        has_formulas = bool(re.search(r'(\$.*\$|\\frac|\\sum|=.*\+.*\*)', text))

        # Extract key sentences
        sentences = re.split(r'[.!?]+', text)
        key_sentences = []
        keywords = ['key', 'important', 'critical', 'must', 'essential', 'note that', 'remember']
        for s in sentences:
            s = s.strip()
            if 30 < len(s) < 300 and any(kw in s.lower() for kw in keywords):
                key_sentences.append(s)
                if len(key_sentences) >= 5:
                    break

        return {
            'trading': trading,
            'ml': ml,
            'has_code': has_code,
            'has_formulas': has_formulas,
            'key_sentences': key_sentences,
            'length': len(text)
        }

    def calculate_rating(self, analyses):
        """Calculate 1-10 rating from chapter analyses."""
        # Total concepts
        total_trading = sum(len(a['trading']) for a in analyses)
        total_ml = sum(len(a['ml']) for a in analyses)
        concept_score = min(4, (total_trading + total_ml) / 15)

        # Code/formula presence
        code_chapters = sum(1 for a in analyses if a['has_code'])
        formula_chapters = sum(1 for a in analyses if a['has_formulas'])
        content_score = min(2, (code_chapters + formula_chapters) / (len(analyses) * 0.4))

        # Key sentences
        total_sentences = sum(len(a['key_sentences']) for a in analyses)
        sentence_score = min(2, total_sentences / 20)

        # Breadth
        unique_trading = len(set(topic for a in analyses for topic in a['trading'].keys()))
        unique_ml = len(set(topic for a in analyses for topic in a['ml'].keys()))
        breadth_score = min(2, (unique_trading + unique_ml) / 6)

        total = concept_score + content_score + sentence_score + breadth_score
        return max(1, min(10, round(total)))

    def get_top_concepts(self, analyses):
        """Extract most mentioned concepts."""
        trading_counts = Counter()
        ml_counts = Counter()

        for a in analyses:
            for topic, data in a['trading'].items():
                trading_counts[topic] += data['count']
            for topic, data in a['ml'].items():
                ml_counts[topic] += data['count']

        return {
            'trading': trading_counts.most_common(5),
            'ml': ml_counts.most_common(5)
        }

    def analyze_book(self, path):
        """Analyze entire book."""
        print(f"\n{'='*80}")
        print(f"ANALYZING: {path.name}")
        print(f"{'='*80}")

        # Extract chapters
        if path.suffix.lower() == '.epub':
            chapters = self.extract_epub(path)
        elif path.suffix.lower() == '.pdf':
            chapters = self.extract_pdf(path)
        else:
            print(f"  ✗ Unsupported: {path.suffix}")
            return None

        if not chapters:
            return None

        # Analyze each chapter
        print(f"  Analyzing {len(chapters)} chapters...")
        analyses = []
        for i, ch in enumerate(chapters, 1):
            print(f"    [{i}/{len(chapters)}] {ch['title'][:60]}...")
            analyses.append(self.analyze_chapter(ch['text']))

        # Calculate rating
        rating = self.calculate_rating(analyses)

        # Get stats
        total_trading = sum(len(a['trading']) for a in analyses)
        total_ml = sum(len(a['ml']) for a in analyses)
        code_chapters = sum(1 for a in analyses if a['has_code'])
        formula_chapters = sum(1 for a in analyses if a['has_formulas'])

        print(f"\n  📊 RESULTS:")
        print(f"     Trading concepts: {total_trading}")
        print(f"     ML concepts: {total_ml}")
        print(f"     Code: {code_chapters}/{len(chapters)}")
        print(f"     Formulas: {formula_chapters}/{len(chapters)}")
        print(f"  🎯 RATING: {rating}/10")

        # Get top concepts
        top = self.get_top_concepts(analyses)

        # Save results
        result = {
            'file': str(path),
            'name': path.name,
            'size_mb': path.stat().st_size / (1024*1024),
            'chapters': len(chapters),
            'rating': rating,
            'stats': {
                'trading_concepts': total_trading,
                'ml_concepts': total_ml,
                'code_chapters': code_chapters,
                'formula_chapters': formula_chapters
            },
            'top_concepts': top,
            'analyzed': datetime.now().isoformat()
        }

        # Save JSON
        safe_name = re.sub(r'[^\w\s-]', '', path.stem)[:50]
        json_file = self.output_dir / f"{safe_name}_analysis.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Save markdown
        self.save_markdown(result, chapters, analyses, safe_name)

        # Update log
        self.log['books'][path.name] = {
            'rating': rating,
            'chapters': len(chapters),
            'analyzed': result['analyzed']
        }

        print(f"  ✓ Saved: {json_file.name}")
        return result

    def save_markdown(self, result, chapters, analyses, filename):
        """Generate markdown summary."""
        md_file = self.output_dir / f"{filename}_summary.md"

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Analysis: {result['name']}\n\n")
            f.write(f"**Rating**: {result['rating']}/10\n\n")
            f.write(f"**Size**: {result['size_mb']:.1f} MB | **Chapters**: {result['chapters']}\n\n")

            # Add links to related files
            json_file = f"{filename}_analysis.json"
            f.write(f"**Files**: [[{json_file}]] (JSON data) | [[MASTER_SUMMARY]] (all books)\n\n")
            f.write(f"**Source**: `{result['file']}`\n\n")
            f.write("---\n\n")

            f.write("## Summary\n\n")
            stats = result['stats']
            f.write(f"- Trading concepts: {stats['trading_concepts']}\n")
            f.write(f"- ML concepts: {stats['ml_concepts']}\n")
            f.write(f"- Code: {stats['code_chapters']}/{result['chapters']}\n")
            f.write(f"- Formulas: {stats['formula_chapters']}/{result['chapters']}\n\n")

            f.write("## Top Concepts\n\n")
            f.write("### Trading:\n")
            for topic, count in result['top_concepts']['trading']:
                f.write(f"- **{topic}**: {count} mentions\n")

            f.write("\n### ML:\n")
            for topic, count in result['top_concepts']['ml']:
                f.write(f"- **{topic}**: {count} mentions\n")

            f.write("\n---\n\n")
            f.write("## Chapters\n\n")

            for i, (ch, analysis) in enumerate(zip(chapters, analyses), 1):
                f.write(f"### {i}. {ch['title']}\n\n")

                if analysis['trading']:
                    f.write("**Trading:**\n")
                    for topic, data in analysis['trading'].items():
                        f.write(f"- {topic}: {data['count']}\n")

                if analysis['ml']:
                    f.write("\n**ML:**\n")
                    for topic, data in analysis['ml'].items():
                        f.write(f"- {topic}: {data['count']}\n")

                if analysis['key_sentences']:
                    f.write("\n**Key Quotes:**\n")
                    for s in analysis['key_sentences'][:3]:
                        f.write(f"> {s[:150]}...\n\n")

                f.write("\n")

    def generate_master_summary(self):
        """Create master summary of all books."""
        if not self.log['books']:
            return

        books = sorted(self.log['books'].items(), key=lambda x: x[1]['rating'], reverse=True)

        summary = self.output_dir / "MASTER_SUMMARY.md"
        with open(summary, 'w', encoding='utf-8') as f:
            f.write("# Book Analysis - Master Summary\n\n")
            f.write(f"**Updated**: {self.log['last_updated']}\n\n")
            f.write(f"**Total**: {len(books)} books\n\n")
            f.write("---\n\n")

            f.write("| Rating | Book | Chapters |\n")
            f.write("|--------|------|----------|\n")
            for name, data in books:
                f.write(f"| **{data['rating']}/10** | {name} | {data['chapters']} |\n")

        print(f"\n✓ Master summary: {summary}")

def scan_and_analyze(folder=None, auto=False):
    """Main entry point with interactive folder selection."""

    # Ask for folder if not provided
    if not folder:
        print("\n" + "="*80)
        print("BOOK ANALYZER - Standalone (No API Credits)")
        print("="*80)
        print("\nEnter folder path to scan for books:")
        print("(Press Enter for current directory)")
        folder_input = input("> ").strip()
        folder = folder_input if folder_input else str(Path.cwd())

    folder = Path(folder)
    if not folder.exists():
        print(f"ERROR: {folder} not found")
        return

    # Scan for books
    print(f"\nScanning: {folder}")
    books = list(folder.glob('*.epub')) + list(folder.glob('*.pdf'))

    if not books:
        print(f"No .epub or .pdf files found in {folder}")
        return

    # Display found books with numbering
    print(f"\n{'='*80}")
    print(f"FOUND {len(books)} BOOKS")
    print(f"{'='*80}")

    analyzer = StandaloneAnalyzer()

    for i, book in enumerate(books, 1):
        size_mb = book.stat().st_size / (1024*1024)
        status = ""
        if book.name in analyzer.log['books']:
            rating = analyzer.log['books'][book.name]['rating']
            status = f" [Already analyzed: {rating}/10]"
        print(f"{i:2d}. {book.name} ({size_mb:.1f} MB){status}")

    # Selection prompt
    if not auto:
        print(f"\n{'='*80}")
        print("Select books to analyze:")
        print("  - Enter numbers: 1,3,5 (analyze books 1, 3, 5)")
        print("  - Enter range: 1-5 (analyze books 1 through 5)")
        print("  - Enter 'all' (analyze all books)")
        print("  - Enter 'new' (analyze only new books)")
        print("  - Enter 'q' (quit)")
        print("="*80)

        selection = input("\n> ").strip().lower()

        if selection == 'q':
            print("Cancelled.")
            return

        # Parse selection
        selected_indices = set()

        if selection == 'all':
            selected_indices = set(range(len(books)))
        elif selection == 'new':
            selected_indices = {i for i, book in enumerate(books) if book.name not in analyzer.log['books']}
            if not selected_indices:
                print("All books already analyzed!")
                return
        else:
            # Parse comma-separated numbers and ranges
            parts = selection.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # Range: 1-5
                    try:
                        start, end = part.split('-')
                        start_idx = int(start.strip()) - 1
                        end_idx = int(end.strip()) - 1
                        selected_indices.update(range(start_idx, end_idx + 1))
                    except:
                        print(f"Invalid range: {part}")
                else:
                    # Single number
                    try:
                        idx = int(part) - 1
                        if 0 <= idx < len(books):
                            selected_indices.add(idx)
                    except:
                        print(f"Invalid number: {part}")

        if not selected_indices:
            print("No valid selection made.")
            return

        # Filter books by selection
        books_to_analyze = [books[i] for i in sorted(selected_indices)]
    else:
        # Auto mode - analyze all
        books_to_analyze = books

    # Analyze selected books
    print(f"\n{'='*80}")
    print(f"ANALYZING {len(books_to_analyze)} BOOKS")
    print(f"{'='*80}")

    analyzed = 0
    skipped = 0

    for book in books_to_analyze:
        result = analyzer.analyze_book(book)
        if result:
            analyzed += 1
        else:
            skipped += 1

        analyzer.save_log()

    # Generate master summary
    analyzer.generate_master_summary()

    print(f"\n{'='*80}")
    print(f"COMPLETE")
    print(f"  Analyzed: {analyzed}")
    print(f"  Skipped: {skipped}")
    print(f"  Total library: {len(analyzer.log['books'])}")
    print(f"  Output: {analyzer.output_dir}")
    print(f"{'='*80}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Standalone Book Analyzer')
    parser.add_argument('--folder', default=None, help='Folder to scan (will prompt if not provided)')
    parser.add_argument('--auto', action='store_true', help='Auto-analyze all without prompts')
    args = parser.parse_args()

    scan_and_analyze(args.folder, args.auto)
