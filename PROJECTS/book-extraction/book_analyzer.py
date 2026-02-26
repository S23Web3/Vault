"""
Automated Book Analysis System
Analyzes trading/ML/finance books and generates ratings + summaries.

Usage:
    python book_analyzer.py                    # Interactive mode - scans Downloads folder
    python book_analyzer.py --folder PATH      # Scan specific folder
    python book_analyzer.py --auto             # Auto-analyze all without prompts
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

# Trading/ML keywords for relevance scoring
RELEVANCE_KEYWORDS = {
    'high': ['backtest', 'position sizing', 'risk management', 'drawdown', 'sharpe ratio',
             'stop loss', 'take profit', 'expectancy', 'r-multiple', 'MFE', 'MAE',
             'machine learning', 'xgboost', 'feature engineering', 'cross-validation',
             'overfitting', 'walk-forward', 'monte carlo', 'kelly criterion'],
    'medium': ['trading system', 'technical analysis', 'momentum', 'trend following',
               'mean reversion', 'volatility', 'ATR', 'moving average', 'stochastic',
               'neural network', 'random forest', 'gradient boosting', 'time series'],
    'low': ['candlestick', 'support resistance', 'chart pattern', 'market sentiment',
            'fundamental analysis', 'valuation', 'earnings', 'dividend']
}

TRADING_CONCEPTS = {
    'entries', 'exits', 'signals', 'indicators', 'backtesting', 'optimization',
    'commission', 'slippage', 'leverage', 'margin', 'futures', 'forex', 'crypto',
    'intraday', 'swing trading', 'breakout', 'reversal', 'VWAP', 'EMA', 'SMA'
}

ML_CONCEPTS = {
    'supervised learning', 'unsupervised learning', 'classification', 'regression',
    'decision tree', 'ensemble', 'bagging', 'boosting', 'hyperparameter',
    'training', 'validation', 'test set', 'feature selection', 'regularization',
    'bias-variance', 'confusion matrix', 'ROC', 'AUC', 'precision', 'recall'
}

class BookAnalyzer:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else Path(r"C:\Users\User\Documents\Obsidian Vault\07-TEMPLATES\book-analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Analysis log file
        self.log_file = self.output_dir / "analysis_log.json"
        self.load_log()

    def load_log(self):
        """Load previous analysis results."""
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.log = json.load(f)
        else:
            self.log = {
                'analyzed_books': {},
                'last_updated': None
            }

    def save_log(self):
        """Save analysis log."""
        self.log['last_updated'] = datetime.now().isoformat()
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log, f, indent=2, ensure_ascii=False)

    def extract_epub_text(self, epub_path):
        """Extract full text from epub."""
        print(f"  📖 Reading epub: {epub_path.name}")
        book = epub.read_epub(str(epub_path))

        chapters = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                soup = BeautifulSoup(item.get_content().decode('utf-8', errors='replace'), 'html.parser')
                text = soup.get_text()
                if len(text.strip()) > 200:
                    chapters.append({
                        'file': item.get_name(),
                        'text': text
                    })
            except:
                continue

        full_text = '\n\n'.join([c['text'] for c in chapters])
        print(f"  ✓ Extracted {len(chapters)} chapters, {len(full_text):,} characters")
        return full_text, chapters

    def extract_pdf_text(self, pdf_path):
        """Extract text from PDF (basic - pymupdf4llm if available, else skip)."""
        try:
            import pymupdf4llm
            print(f"  📄 Reading PDF: {pdf_path.name}")
            md_text = pymupdf4llm.to_markdown(str(pdf_path))
            print(f"  ✓ Extracted {len(md_text):,} characters")
            return md_text, None
        except ImportError:
            print(f"  ⚠ pymupdf4llm not installed - skipping PDF")
            return None, None
        except Exception as e:
            print(f"  ✗ Error reading PDF: {e}")
            return None, None

    def extract_book_metadata(self, text):
        """Extract title, author, TOC from book text."""
        lines = text.split('\n')

        # Try to find title (usually in first 50 lines)
        title = None
        for line in lines[:50]:
            line_clean = line.strip()
            if len(line_clean) > 10 and len(line_clean) < 100:
                if any(kw in line_clean.lower() for kw in ['trading', 'machine learning', 'python', 'financial', 'algorithmic']):
                    title = line_clean
                    break

        # Try to find author
        author = None
        for line in lines[:100]:
            if 'by ' in line.lower() or 'author' in line.lower():
                author = line.strip()
                break

        # Extract TOC
        toc = []
        in_toc = False
        for line in lines:
            line_clean = line.strip()
            if 'contents' in line_clean.lower() and len(line_clean) < 50:
                in_toc = True
                continue
            if in_toc:
                if re.match(r'^(chapter|part|\d+\.)', line_clean.lower()):
                    toc.append(line_clean)
                if len(toc) > 30:  # Assume we've captured the full TOC
                    break

        return {
            'title': title or 'Unknown',
            'author': author or 'Unknown',
            'toc': toc
        }

    def count_keywords(self, text):
        """Count relevance keywords in text."""
        text_lower = text.lower()

        scores = {
            'high': sum(text_lower.count(kw) for kw in RELEVANCE_KEYWORDS['high']),
            'medium': sum(text_lower.count(kw) for kw in RELEVANCE_KEYWORDS['medium']),
            'low': sum(text_lower.count(kw) for kw in RELEVANCE_KEYWORDS['low'])
        }

        trading_count = sum(text_lower.count(kw) for kw in TRADING_CONCEPTS)
        ml_count = sum(text_lower.count(kw) for kw in ML_CONCEPTS)

        return {
            'keyword_scores': scores,
            'trading_mentions': trading_count,
            'ml_mentions': ml_count
        }

    def analyze_content_depth(self, text):
        """Analyze if book has real code/formulas or just theory."""
        indicators = {
            'has_code': bool(re.search(r'(def |class |import |function|```)', text)),
            'has_formulas': bool(re.search(r'(\$.*\$|\\frac|\\sum|\\int|=.*\+.*\*)', text)),
            'has_examples': text.lower().count('example') > 10,
            'has_exercises': text.lower().count('exercise') > 5,
            'has_data': any(kw in text.lower() for kw in ['dataset', 'csv', 'dataframe', 'pandas']),
            'has_backtests': any(kw in text.lower() for kw in ['backtest result', 'performance metric', 'sharpe', 'drawdown'])
        }

        depth_score = sum(indicators.values())

        return {
            'indicators': indicators,
            'depth_score': depth_score,
            'depth_level': 'High' if depth_score >= 4 else 'Medium' if depth_score >= 2 else 'Low'
        }

    def generate_rating(self, keyword_analysis, depth_analysis, text_length):
        """Generate 1-10 rating based on analysis."""

        # Keyword relevance score (0-4 points)
        kw = keyword_analysis['keyword_scores']
        relevance_score = (kw['high'] * 3 + kw['medium'] * 2 + kw['low'] * 1) / 100
        relevance_score = min(relevance_score, 4)

        # Depth score (0-3 points)
        depth_score = depth_analysis['depth_score'] / 2

        # Trading/ML balance (0-2 points)
        trading = keyword_analysis['trading_mentions']
        ml = keyword_analysis['ml_mentions']
        balance_score = 2 if (trading > 20 and ml > 20) else 1 if (trading > 10 or ml > 10) else 0

        # Length penalty (reduce score if too short)
        length_score = 1 if text_length > 100000 else 0.5 if text_length > 50000 else 0

        total = relevance_score + depth_score + balance_score + length_score
        rating = round(total)

        return max(1, min(10, rating))  # Clamp to 1-10

    def extract_key_takeaways(self, text):
        """Extract 3-5 key takeaways from book."""
        # Look for summary sections
        takeaways = []

        # Search for "summary" sections
        summary_matches = re.finditer(r'summary\n+(.*?)(?:\n\n|\Z)', text.lower(), re.DOTALL)
        for match in summary_matches:
            summary_text = match.group(1)[:500]
            if len(summary_text) > 50:
                takeaways.append(summary_text.strip())
            if len(takeaways) >= 3:
                break

        # Search for "conclusion" sections if no summaries
        if not takeaways:
            conclusion_matches = re.finditer(r'conclusion\n+(.*?)(?:\n\n|\Z)', text.lower(), re.DOTALL)
            for match in conclusion_matches:
                conclusion_text = match.group(1)[:500]
                if len(conclusion_text) > 50:
                    takeaways.append(conclusion_text.strip())
                if len(takeaways) >= 3:
                    break

        return takeaways[:5] if takeaways else ["See full analysis"]

    def analyze_book(self, book_path):
        """Main analysis pipeline for a single book."""
        print(f"\n{'='*80}")
        print(f"ANALYZING: {book_path.name}")
        print(f"{'='*80}")

        # Extract text
        if book_path.suffix.lower() == '.epub':
            text, chapters = self.extract_epub_text(book_path)
        elif book_path.suffix.lower() == '.pdf':
            text, chapters = self.extract_pdf_text(book_path)
        else:
            print(f"  ✗ Unsupported format: {book_path.suffix}")
            return None

        if not text:
            return None

        # Extract metadata
        metadata = self.extract_book_metadata(text)
        print(f"  Title: {metadata['title']}")
        print(f"  Author: {metadata['author']}")
        print(f"  Chapters: {len(metadata['toc'])}")

        # Analyze content
        keyword_analysis = self.count_keywords(text)
        depth_analysis = self.analyze_content_depth(text)

        print(f"\n  Keyword Hits: High={keyword_analysis['keyword_scores']['high']} " +
              f"Medium={keyword_analysis['keyword_scores']['medium']} " +
              f"Low={keyword_analysis['keyword_scores']['low']}")
        print(f"  Trading mentions: {keyword_analysis['trading_mentions']}")
        print(f"  ML mentions: {keyword_analysis['ml_mentions']}")
        print(f"  Content depth: {depth_analysis['depth_level']} (score={depth_analysis['depth_score']}/6)")

        # Generate rating
        rating = self.generate_rating(keyword_analysis, depth_analysis, len(text))
        print(f"\n  🎯 RATING: {rating}/10")

        # Extract takeaways
        takeaways = self.extract_key_takeaways(text)

        # Compile results
        result = {
            'file_path': str(book_path),
            'file_name': book_path.name,
            'file_size_kb': book_path.stat().st_size / 1024,
            'metadata': metadata,
            'analysis': {
                'rating': rating,
                'keyword_analysis': keyword_analysis,
                'depth_analysis': depth_analysis,
                'text_length': len(text),
                'takeaways': takeaways
            },
            'analyzed_date': datetime.now().isoformat()
        }

        # Save individual book analysis
        safe_filename = re.sub(r'[^\w\s-]', '', book_path.stem).strip()[:50]
        output_file = self.output_dir / f"{safe_filename}_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Saved analysis: {output_file.name}")

        # Update log
        self.log['analyzed_books'][book_path.name] = {
            'rating': rating,
            'title': metadata['title'],
            'author': metadata['author'],
            'analyzed_date': result['analyzed_date']
        }

        return result

    def generate_summary_report(self):
        """Generate markdown summary of all analyzed books."""
        if not self.log['analyzed_books']:
            print("No books analyzed yet.")
            return

        # Sort by rating
        books = sorted(self.log['analyzed_books'].items(),
                      key=lambda x: x[1]['rating'],
                      reverse=True)

        report_file = self.output_dir / "ANALYSIS_SUMMARY.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Book Analysis Summary\n\n")
            f.write(f"**Last Updated**: {self.log['last_updated']}\n\n")
            f.write(f"**Total Books Analyzed**: {len(books)}\n\n")
            f.write("---\n\n")

            f.write("## Ratings Overview\n\n")
            f.write("| Rating | Book | Author | File |\n")
            f.write("|--------|------|--------|------|\n")

            for filename, data in books:
                f.write(f"| **{data['rating']}/10** | {data['title']} | {data['author']} | {filename} |\n")

            f.write("\n---\n\n")
            f.write("## Rating Distribution\n\n")

            # Count by rating
            rating_counts = {}
            for _, data in books:
                rating = data['rating']
                rating_counts[rating] = rating_counts.get(rating, 0) + 1

            for rating in sorted(rating_counts.keys(), reverse=True):
                count = rating_counts[rating]
                bar = '█' * count
                f.write(f"{rating}/10: {bar} ({count})\n")

            f.write("\n---\n\n")
            f.write("## Top 5 Books\n\n")

            for filename, data in books[:5]:
                f.write(f"### {data['rating']}/10 — {data['title']}\n")
                f.write(f"**Author**: {data['author']}\n\n")
                f.write(f"**File**: `{filename}`\n\n")
                f.write("---\n\n")

        print(f"\n{'='*80}")
        print(f"✓ Summary report generated: {report_file}")
        print(f"{'='*80}")

def scan_folder(folder_path, auto_mode=False):
    """Scan folder for epub/pdf files and analyze."""
    folder = Path(folder_path)

    if not folder.exists():
        print(f"ERROR: Folder not found: {folder}")
        return

    # Find all epub and pdf files
    books = list(folder.glob('*.epub')) + list(folder.glob('*.pdf'))

    if not books:
        print(f"No .epub or .pdf files found in {folder}")
        return

    print(f"\n{'='*80}")
    print(f"FOUND {len(books)} BOOKS IN: {folder}")
    print(f"{'='*80}")

    for book in books:
        print(f"  - {book.name} ({book.stat().st_size / (1024*1024):.1f} MB)")

    # Initialize analyzer
    analyzer = BookAnalyzer()

    # Process each book
    analyzed_count = 0
    skipped_count = 0

    for book in books:
        # Check if already analyzed
        if book.name in analyzer.log['analyzed_books']:
            existing_rating = analyzer.log['analyzed_books'][book.name]['rating']
            print(f"\n⏭ {book.name} — Already analyzed (rating: {existing_rating}/10)")

            if not auto_mode:
                choice = input("  Re-analyze? (y/n): ").lower()
                if choice != 'y':
                    skipped_count += 1
                    continue

        # Analyze or skip
        if not auto_mode:
            choice = input(f"\nAnalyze {book.name}? (y/n/q): ").lower()
            if choice == 'q':
                print("Quit requested.")
                break
            if choice != 'y':
                skipped_count += 1
                continue

        result = analyzer.analyze_book(book)
        if result:
            analyzed_count += 1

        analyzer.save_log()

    # Generate summary
    analyzer.generate_summary_report()

    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE")
    print(f"  Analyzed: {analyzed_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total in library: {len(analyzer.log['analyzed_books'])}")
    print(f"{'='*80}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Automated Book Analysis System')
    parser.add_argument('--folder', type=str, default=r"C:\Users\User\Downloads",
                       help='Folder to scan for books')
    parser.add_argument('--auto', action='store_true',
                       help='Auto-analyze all books without prompts')

    args = parser.parse_args()

    scan_folder(args.folder, auto_mode=args.auto)
