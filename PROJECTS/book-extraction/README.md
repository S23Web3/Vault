# Book Analyzer

This is made by me and Claude, no ripoffachino (like the famous frappucino with ice cubes)

> Deep analysis of books with concept extraction — 100% local, no API credits

Automated chapter-by-chapter concept extraction from epub and PDF books. Runs entirely on your machine.
Asks for the folder where the books are, scans it and analyses them. Select the books with a comma as separator.
Pre-configured for finance and machine learning content, but fully customizable for any domain.

Maybe I will build a gui if I get reactions to this repo.

## Features

- 🔍 **Deep Analysis** — Chapter-by-chapter concept extraction
- 📊 **Smart Rating** — 1-10 rating based on content depth
- 💾 **100% Local** — No API calls, no external services
- 📝 **Rich Output** — JSON data + Markdown summaries
- 🔄 **Smart Logging** — Won't re-analyze books unless requested
- 🎯 **Interactive** — Choose which books to analyze

## Quick Start

```bash
git clone https://github.com/S23Web3/BooksAnalyzer.git
cd BooksAnalyzer
pip install -r requirements.txt
python standalone_analyzer.py
```

## How It Works

1. **Scan** — Point it at a folder with .epub or .pdf files
2. **Select** — Choose which books to analyze (1,3,5 or 1-10 or all)
3. **Analyze** — Extracts chapters, finds concepts, detects code/formulas
4. **Rate** — Generates 1-10 rating based on depth
5. **Export** — Creates JSON + Markdown summaries

## Output

All results saved to `./book-analysis/`:

```
book-analysis/
├── Book_A_analysis.json        # Full data
├── Book_A_summary.md           # Human-readable
├── MASTER_SUMMARY.md           # All books ranked
└── analysis_log.json           # Prevents duplicates
```

## What It Extracts

### Built-in Concept Categories
The analyzer comes pre-configured with two concept dictionaries that you can customize:

**Category 1** (example keywords):
- Keywords like: entry point, signal, pattern, strategy
- Risk-related terms: position sizing, drawdown, risk management
- Performance metrics: expectancy, win rate, profit factor
- Psychological factors: discipline, bias, emotion

**Category 2** (example keywords):
- Supervised learning: classification, regression, labeled data
- Feature work: feature engineering, selection, importance
- Models: random forest, XGBoost, neural networks
- Validation: cross-validation, k-fold, train-test split
- Metrics: accuracy, precision, F1, AUC, SHAP

### Plus
- Code detection (Python, formulas)
- Key sentence extraction
- Concept frequency analysis
- Fully customizable - edit concept dictionaries for ANY domain

## Rating System

| Points | Criteria |
|--------|----------|
| 0-4 | Concept coverage (both categories) |
| 0-2 | Code & formula presence |
| 0-2 | Key actionable sentences |
| 0-2 | Topic breadth |
| **1-10** | **Total rating** |

## Usage Modes

### Interactive (Recommended)
```bash
python standalone_analyzer.py
```
- Asks for folder
- Lists all books
- You choose which to analyze

### Auto Mode
```bash
python standalone_analyzer.py --auto
```
- Analyzes everything in current directory
- No prompts

### Specify Folder
```bash
python standalone_analyzer.py --folder "/path/to/books"
```

### Windows
Double-click `analyze_books.bat`

## Customization

Edit the two concept dictionaries in `standalone_analyzer.py` to track any keywords you want:

```python
CONCEPT_CATEGORY_1 = {
    'your_topic': ['keyword1', 'keyword2', 'keyword3'],
    'another_topic': ['keyword4', 'keyword5'],
}

CONCEPT_CATEGORY_2 = {
    'different_domain': ['keyword6', 'keyword7'],
}
```

The default configuration extracts financial and machine learning concepts, but you can customize for any domain (history, science, medicine, etc.).

## Requirements

- Python 3.7+
- ebooklib (epub parsing)
- beautifulsoup4 (HTML extraction)
- pymupdf4llm (PDF conversion)

Install: `pip install -r requirements.txt`

## Example Output

```
FOUND 5 BOOKS
================================================================================
 1. Book_A.epub (8.6 MB)
 2. Book_B.epub (27.1 MB) [Already analyzed: 10/10]
 3. Book_C.pdf (13.1 MB)

Select books to analyze:
> 1,3

[1/2] Analyzing Book_A...
  📖 Reading: Book_A.epub
  ✓ Extracted 30 chapters
  📊 RESULTS:
     Category 1 concepts: 109
     Category 2 concepts: 15
  🎯 RATING: 10/10
  ✓ Saved: Book_A_analysis.json
```

## License

MIT License — see [LICENSE](LICENSE)

## Author

S23Web3

## Contributing

Issues and PRs welcome!
