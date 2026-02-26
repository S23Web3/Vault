"""
Creates a deep psychology summary from Van Tharp extraction.
Focuses on mental models, biases, discipline, and actionable practices.
"""

from pathlib import Path
import re

def create_summary(extraction_file, output_file):
    """Parse extraction and create focused psychology summary."""

    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print(f"Reading: {extraction_file}")
    with open(extraction_file, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # Split by chapter markers
    chapters = full_text.split('=' * 80)

    summary_sections = []

    # Ch 1: The Holy Grail
    ch1_text = [c for c in chapters if 'Chapter 1' in c or 'Holy Grail' in c]
    if ch1_text:
        summary_sections.append("## 1. THE HOLY GRAIL CONCEPT\n\n" + extract_key_points(ch1_text[0], [
            'holy grail', 'yourself', 'trader', 'market wizard', 'genius',
            'psychology', 'discipline', 'system is you'
        ]))

    # Ch 2: Judgmental Biases
    ch2_text = [c for c in chapters if 'Chapter 2' in c or 'Judgmental Biases' in c]
    if ch2_text:
        summary_sections.append("## 2. COGNITIVE BIASES THAT DESTROY TRADERS\n\n" + extract_key_points(ch2_text[0], [
            'bias', 'representativeness', 'availability', 'anchoring', 'conservatism',
            'lotto bias', 'need to understand', 'gambler', 'illusion'
        ]))

    # Ch 3: Setting Objectives
    ch3_text = [c for c in chapters if 'Chapter 3' in c or 'Setting Your Objectives' in c]
    if ch3_text:
        summary_sections.append("## 3. SETTING OBJECTIVES (PSYCHOLOGY OF GOALS)\n\n" + extract_key_points(ch3_text[0], [
            'objective', 'mission', 'goal', 'annual return', 'drawdown', 'monte carlo',
            'worst case', 'time frame', 'lifestyle'
        ]))

    # Ch 4: System Development (psychological steps)
    ch4_text = [c for c in chapters if 'Chapter 4' in c or 'Steps to Developing' in c]
    if ch4_text:
        summary_sections.append("## 4. DEVELOPING YOUR SYSTEM (PSYCHOLOGICAL DISCIPLINE)\n\n" + extract_key_points(ch4_text[0], [
            'inventory', 'belief', 'open mind', 'concept', 'mission', 'worst-case',
            'mental', 'plan', 'discipline', 'objectively'
        ]))

    # Ch 10: Stops/Exits (psychological discipline)
    ch10_text = [c for c in chapters if 'Chapter 10' in c or 'How to Take Profits and Losses' in c]
    if ch10_text:
        summary_sections.append("## 5. EXITS & DISCIPLINE (KNOW WHEN TO FOLD 'EM)\n\n" + extract_key_points(ch10_text[0], [
            'stop', 'loss', 'protect', 'capital', 'exit', 'discipline', 'cut losses',
            'emotional', 'fear', 'let winners run'
        ]))

    # Ch 14: Position Sizing (psychology of risk)
    ch14_text = [c for c in chapters if 'Chapter 14' in c or 'Position Sizing' in c]
    if ch14_text:
        summary_sections.append("## 6. POSITION SIZING (PSYCHOLOGY OF RISK)\n\n" + extract_key_points(ch14_text[0], [
            'position size', 'risk', 'kelly', 'percent risk', 'volatility',
            'ruin', 'bankruptcy', 'conservative', 'aggressive', 'comfort'
        ]))

    # Ch 15: Conclusion
    ch15_text = [c for c in chapters if 'Chapter 15' in c or 'Conclusion' in c]
    if ch15_text:
        summary_sections.append("## 7. FINAL WISDOM & ACTION STEPS\n\n" + extract_key_points(ch15_text[0], [
            'action', 'implement', 'discipline', 'practice', 'journey', 'continuous',
            'improve', 'work on yourself', 'commitment'
        ]))

    # Write summary
    output = Path(output_file)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("VAN THARP — PSYCHOLOGY DEEP SUMMARY\n")
        f.write("Trade Your Way to Financial Freedom\n")
        f.write("Personal Mental Models & Actionable Practices\n")
        f.write("=" * 80 + "\n\n")

        f.write("**Purpose**: This is YOUR psychology reference. Not technical strategy.\n")
        f.write("Focus on: Mental models, cognitive biases, discipline, self-sabotage patterns.\n\n")
        f.write("---\n\n")

        for section in summary_sections:
            f.write(section)
            f.write("\n\n---\n\n")

        f.write("## KEY QUOTES TO REMEMBER\n\n")
        f.write(extract_quotes(full_text))

        f.write("\n\n## DAILY PRACTICES\n\n")
        f.write("1. **Morning**: Review objectives. Check if today's plan aligns with mission.\n")
        f.write("2. **Pre-trade**: Identify which biases might affect you today. Name them.\n")
        f.write("3. **During trade**: Position sizing FIRST, entry LAST. Risk % before anything.\n")
        f.write("4. **Post-trade**: Log R-multiple. Was exit discipline maintained?\n")
        f.write("5. **Weekly**: Calculate SQN. Are you improving? Review worst-case scenario.\n")
        f.write("6. **Monthly**: Belief inventory. What changed? What needs work?\n\n")

        f.write("=" * 80 + "\n")
        f.write("END OF PSYCHOLOGY SUMMARY\n")
        f.write("=" * 80 + "\n")

    print(f"✓ Summary created: {output}")
    print(f"  Size: {output.stat().st_size / 1024:.1f} KB")

def extract_key_points(text, keywords):
    """Extract paragraphs containing key psychology terms."""
    paragraphs = text.split('\n\n')
    relevant = []

    for para in paragraphs:
        para_clean = para.strip()
        if len(para_clean) < 50:  # Skip headers/tiny bits
            continue

        # Check if paragraph contains any keyword
        para_lower = para_clean.lower()
        if any(kw in para_lower for kw in keywords):
            # Clean up excessive whitespace
            para_clean = re.sub(r'\s+', ' ', para_clean)
            relevant.append(para_clean)

    # Return first 15 most relevant paragraphs
    return '\n\n'.join(relevant[:15])

def extract_quotes(text):
    """Find powerful quotes (lines with quotation marks or bold emphasis)."""
    # Look for quoted text
    quote_pattern = r'"([^"]{30,200})"'
    quotes = re.findall(quote_pattern, text)

    if quotes:
        return '\n'.join([f'> "{q}"' for q in quotes[:10]])
    else:
        return "(No formatted quotes found — see full chapters for wisdom)"

if __name__ == "__main__":
    extraction = Path(r"C:\Users\User\Documents\Obsidian Vault\07-TEMPLATES\van-tharp-psychology-extraction.txt")
    summary = Path(r"C:\Users\User\Documents\Obsidian Vault\07-TEMPLATES\van-tharp-psychology-SUMMARY.md")

    if not extraction.exists():
        print(f"ERROR: Extraction file not found at {extraction}")
        exit(1)

    create_summary(extraction, summary)
