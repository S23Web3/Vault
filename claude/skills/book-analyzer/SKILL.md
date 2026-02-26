---
name: book-analyzer
description: Standalone book analysis tool for trading/ML/finance books. Analyzes epub/PDF files locally without API credits. Deep chapter-by-chapter analysis with concept extraction, code detection, and 1-10 ratings. Use when user wants to analyze books, rate books, extract concepts, or needs reading recommendations.
---

# Book Analyzer Skill

## Location
`PROJECTS/book-extraction/standalone_analyzer.py`

## What It Does
- Analyzes trading/ML/finance books completely locally (no API credits)
- Deep chapter-by-chapter concept extraction
- Detects code, formulas, key sentences
- Generates 1-10 ratings
- Creates JSON + Markdown summaries
- Tracks analyzed books (won't re-analyze unless requested)

## Usage

### Interactive Mode (Recommended)
```bash
cd "c:\Users\User\Documents\Obsidian Vault\PROJECTS\book-extraction"
python standalone_analyzer.py
```

**Workflow:**
1. Asks for folder path (default: Downloads)
2. Scans and lists books with size + status
3. User selects which to analyze:
   - `1,3,5` — specific books
   - `1-10` — range
   - `all` — everything
   - `new` — only unanalyzed
   - `q` — quit

### Auto Mode
```bash
python standalone_analyzer.py --auto
```

### Custom Folder
```bash
python standalone_analyzer.py --folder "C:\path\to\books"
```

### Windows Batch File
Double-click: `analyze_books.bat`

## Concepts Extracted

### Trading
- **entries**: signals, triggers, patterns
- **exits**: stop loss, take profit, trailing
- **risk**: position sizing, drawdown, management
- **backtesting**: walk-forward, optimization
- **metrics**: Sharpe, Sortino, expectancy, SQN, R-multiples
- **psychology**: discipline, bias, emotion

### ML
- **supervised**: classification, regression
- **features**: engineering, selection, importance
- **models**: XGBoost, random forest, neural networks
- **validation**: cross-validation, purging, k-fold
- **metrics**: accuracy, precision, recall, SHAP

## Rating System (1-10)

| Points | Criteria |
|--------|----------|
| 0-4 | Trading + ML concept coverage |
| 0-2 | Code & formula presence |
| 0-2 | Key actionable sentences |
| 0-2 | Breadth (multiple topics) |

## Output Files

Location: `07-TEMPLATES\book-analysis\`

| File | Content |
|------|---------|
| `{book}_analysis.json` | Full data (chapters, concepts, examples) |
| `{book}_summary.md` | Human-readable markdown |
| `MASTER_SUMMARY.md` | Table of all books by rating |
| `analysis_log.json` | Prevents re-analysis |

## Example Results

| Book | Rating | Concepts |
|------|--------|----------|
| De Prado — Advances in Financial ML | 10/10 | 74 trading + 69 ML |
| Jansen — ML for Algo Trading | 10/10 | 103 trading + 115 ML |
| Van Tharp — Trade Your Way | 10/10 | 109 trading + 15 ML |
| Sweeney — Maximum Adverse Excursion | 9/10 | (PDF - needs pymupdf4llm) |

## Dependencies

```bash
pip install ebooklib beautifulsoup4
pip install pymupdf4llm  # Optional, for PDFs
```

## File Support
- `.epub` — always works
- `.pdf` — needs pymupdf4llm

## Key Features
- **100% local** — no API calls
- **Logs analyzed books** — won't duplicate work
- **Chapter-by-chapter** — not just keyword counts
- **Context extraction** — shows examples of concepts
- **Key sentences** — finds actionable insights
- **Customizable** — edit concept dictionaries

## Customization

Edit `TRADING_CONCEPTS` and `ML_CONCEPTS` in `standalone_analyzer.py`:

```python
TRADING_CONCEPTS = {
    'crypto': ['bitcoin', 'ethereum', 'defi'],
    'hft': ['latency', 'order book'],
}
```

## Documentation
- `README.md` — full technical documentation
- `USAGE.md` — quick start guide
- `analyze_books.bat` — Windows launcher

## Public Git Repo
**Status**: ✅ **LIVE**
**Repo**: https://github.com/S23Web3/BooksAnalyzer

**Contents**:
- `standalone_analyzer.py` (main script)
- `README.md` (documentation)
- `USAGE.md` (quick guide)
- `requirements.txt` (dependencies)
- `.gitignore`
- `LICENSE` (MIT)
- `analyze_books.bat` (Windows launcher)

## When to Use This Skill

Trigger this skill when user:
- Wants to analyze a book
- Needs book recommendations
- Asks "is this book worth reading?"
- Wants to compare multiple books
- Needs concept extraction from books
- Has a folder of books to process

## Example Prompts
- "Analyze the books in my Downloads folder"
- "Rate this trading book"
- "Which books should I read first?"
- "Extract all position sizing concepts from Van Tharp"
- "Compare De Prado vs Jansen"

---

**Last Updated**: 2026-02-09
