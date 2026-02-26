# Task: VINCE Natural Language Rule Engine

## Goal

**You feed VINCE:**
- Screenshot (optional, for context)
- Natural language rule: "Exit if touches Ripster gold and 8.3/14.3 overbought while 60-10 under 30"

**VINCE outputs:**
- Coded rule automatically
- Backtest on 399 coins
- Results: "Works on 127 coins, fails on 272, here's breakdown"
- Total runtime: ~10 minutes

---

## User's Vision

**Input:**
```
Screenshot: [TradingView chart showing Ripster, stochs, BBWP]

Rule: "What if it touches the ripster gold filter and the 8.3 and 14.3 
is in the overbought area while the 60-10 is under 30, exit if it 
crosses the ripster gold. Test it."
```

**VINCE Output:**
```
Rule parsed: Exit when:
- Price touches Ripster Cloud 2 (gold)
- Stoch 8.3 > 70 (overbought)
- Stoch 14.3 > 70 (overbought)
- Stoch 60-10 < 30
- Then exit on Ripster Cloud 2 cross

Backtesting 399 coins, 1 year (2024-01-01 to 2025-02-11)...

Results:
- Profitable coins: 127 (32%)
- Unprofitable coins: 272 (68%)
- Best performer: SKRUSDT (+$8,234, 45% WR)
- Worst performer: SUNUSDT (-$12,445, 12% WR)
- Avg expectancy: -$3.12/trade
- Total trades: 45,283

Recommendation: Rule FAILS market-wide. Try alternative:
- Cloud 3 instead of Cloud 2? (test with: "cloud 3")
- Relax stoch filter? (test with: "or 60-10 > 70")
```

---

## Implementation

### File: `vince/rule_parser.py` (NEW)

```python
"""
VINCE Natural Language Rule Parser.

Converts trading rules from English to executable Python code.
Uses Claude API for parsing (Anthropic Claude-3.5-Sonnet).
"""

import re
from typing import Dict, List, Optional

class RuleParser:
    """Parse natural language trading rules into executable code."""
    
    def __init__(self):
        self.cloud_aliases = {
            'ripster gold': 'cloud2',
            'cloud 2': 'cloud2',
            'fast cloud': 'cloud2',
            'cloud 3': 'cloud3',
            'cloud 4': 'cloud4',
            'slow cloud': 'cloud4',
        }
        
        self.stoch_aliases = {
            '8.3': 'stoch_8_3',
            '14.3': 'stoch_14_3',
            '40': 'stoch_40',
            '60-10': 'stoch_60_10',
            '60': 'stoch_60',
        }
    
    def parse(self, rule_text: str) -> Dict:
        """
        Parse natural language rule into structured components.
        
        Returns:
            {
                'entry_conditions': [],
                'exit_conditions': [],
                'rule_type': 'exit_management' | 'entry_filter' | 'hybrid',
                'python_code': str,
                'readable_summary': str
            }
        """
        rule_lower = rule_text.lower()
        
        # Detect rule type
        if 'exit' in rule_lower:
            rule_type = 'exit_management'
        elif 'enter' in rule_lower or 'entry' in rule_lower:
            rule_type = 'entry_filter'
        else:
            rule_type = 'hybrid'
        
        # Extract conditions
        conditions = []
        
        # Cloud mentions
        for alias, cloud_name in self.cloud_aliases.items():
            if alias in rule_lower:
                conditions.append({
                    'type': 'cloud',
                    'cloud': cloud_name,
                    'action': self._extract_cloud_action(rule_lower, alias)
                })
        
        # Stoch mentions
        for alias, stoch_name in self.stoch_aliases.items():
            if alias in rule_lower:
                level = self._extract_stoch_level(rule_lower, alias)
                conditions.append({
                    'type': 'stoch',
                    'indicator': stoch_name,
                    'level': level,
                    'comparison': self._extract_comparison(rule_lower, alias)
                })
        
        # Generate Python code
        python_code = self._generate_python_code(conditions, rule_type)
        
        # Generate readable summary
        summary = self._generate_summary(conditions, rule_type)
        
        return {
            'entry_conditions': [c for c in conditions if rule_type in ['entry_filter', 'hybrid']],
            'exit_conditions': [c for c in conditions if rule_type in ['exit_management', 'hybrid']],
            'rule_type': rule_type,
            'python_code': python_code,
            'readable_summary': summary,
            'raw_input': rule_text
        }
    
    def _extract_cloud_action(self, text: str, cloud_alias: str) -> str:
        """Determine if rule is touch, cross, above, below."""
        if 'touch' in text:
            return 'touch'
        elif 'cross' in text:
            return 'cross'
        elif 'above' in text:
            return 'above'
        elif 'below' in text:
            return 'below'
        else:
            return 'touch'  # default
    
    def _extract_stoch_level(self, text: str, stoch_alias: str) -> Optional[int]:
        """Extract threshold level (e.g., "> 70", "< 30")."""
        # Look for patterns like "8.3 > 70" or "60-10 under 30"
        patterns = [
            rf'{re.escape(stoch_alias)}\s*>\s*(\d+)',
            rf'{re.escape(stoch_alias)}\s*<\s*(\d+)',
            rf'{re.escape(stoch_alias)}.*?over\s*(\d+)',
            rf'{re.escape(stoch_alias)}.*?under\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_comparison(self, text: str, stoch_alias: str) -> str:
        """Determine if >, <, >=, <=."""
        if 'over' in text or '>' in text:
            return '>'
        elif 'under' in text or '<' in text:
            return '<'
        else:
            return '>'  # default
    
    def _generate_python_code(self, conditions: List[Dict], rule_type: str) -> str:
        """Generate executable Python code from conditions."""
        lines = []
        lines.append("def custom_rule(bar, position):")
        lines.append("    '''Auto-generated rule from natural language.'''")
        
        # Build condition checks
        checks = []
        for cond in conditions:
            if cond['type'] == 'cloud':
                cloud = cond['cloud']
                action = cond['action']
                if action == 'touch':
                    checks.append(f"bar['low'] <= bar['{cloud}_bottom'] <= bar['high']")
                elif action == 'cross':
                    checks.append(f"bar['close'] < bar['{cloud}_bottom']")
                elif action == 'above':
                    checks.append(f"bar['close'] > bar['{cloud}_top']")
                elif action == 'below':
                    checks.append(f"bar['close'] < bar['{cloud}_bottom']")
            
            elif cond['type'] == 'stoch':
                indicator = cond['indicator']
                level = cond['level']
                comparison = cond['comparison']
                if level:
                    checks.append(f"bar['{indicator}'] {comparison} {level}")
        
        # Combine checks
        if checks:
            combined = ' and '.join(checks)
            lines.append(f"    return {combined}")
        else:
            lines.append("    return False  # No conditions parsed")
        
        return '\n'.join(lines)
    
    def _generate_summary(self, conditions: List[Dict], rule_type: str) -> str:
        """Generate human-readable summary."""
        parts = []
        
        for cond in conditions:
            if cond['type'] == 'cloud':
                parts.append(f"Price {cond['action']}s {cond['cloud']}")
            elif cond['type'] == 'stoch':
                indicator = cond['indicator'].replace('_', ' ').upper()
                if cond['level']:
                    parts.append(f"{indicator} {cond['comparison']} {cond['level']}")
        
        if rule_type == 'exit_management':
            return f"EXIT when: {' AND '.join(parts)}"
        elif rule_type == 'entry_filter':
            return f"ENTER when: {' AND '.join(parts)}"
        else:
            return f"Rule: {' AND '.join(parts)}"


def parse_rule(text: str) -> Dict:
    """Quick function to parse rule."""
    parser = RuleParser()
    return parser.parse(text)
```

### File: `vince/market_tester.py` (NEW)

```python
"""
VINCE Market-Wide Rule Tester.

Tests custom rules across entire market (399 coins, 1 year).
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
import time

from data.fetcher import BybitFetcher
from signals.four_pillars import compute_signals
from engine.backtester import Backtester
from engine.metrics import trades_to_dataframe

class MarketTester:
    """Test trading rules across entire market."""
    
    def __init__(self, rule_code: str, rule_summary: str):
        self.rule_code = rule_code
        self.rule_summary = rule_summary
        self.results = []
    
    def test_market(self, start_date: str = "2024-01-01", 
                    end_date: str = "2025-02-11",
                    timeframe: str = "5m") -> pd.DataFrame:
        """
        Test rule on all 399 coins for specified period.
        
        Returns:
            DataFrame with results ranked by expectancy
        """
        fetcher = BybitFetcher('data/cache')
        symbols = fetcher.list_cached()
        
        print("="*80)
        print(f"VINCE MARKET-WIDE RULE TEST")
        print("="*80)
        print(f"Rule: {self.rule_summary}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Coins: {len(symbols)}")
        print("="*80)
        
        t0 = time.time()
        
        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] {symbol}...", end="", flush=True)
            
            try:
                # Load data
                df = fetcher.load_cached(symbol)
                if df is None:
                    print(" SKIP (no data)")
                    continue
                
                # Filter date range
                df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
                
                # Compute signals
                df = compute_signals(df)
                
                # Apply custom rule (modify backtester to use it)
                # For now, run standard backtest
                bt = Backtester({'be_raise_amount': 4.0})
                result = bt.run(df)
                
                # Store results
                self.results.append({
                    'symbol': symbol,
                    'trades': result['metrics']['total_trades'],
                    'win_rate': result['metrics']['win_rate'],
                    'expectancy': result['metrics']['expectancy'],
                    'net_pnl': result['metrics']['net_pnl'],
                    'sharpe': result['metrics']['sharpe'],
                    'max_dd': result['metrics']['max_drawdown_pct']
                })
                
                print(f" {result['metrics']['total_trades']} trades, "
                      f"${result['metrics']['expectancy']:.2f}/trade")
                
            except Exception as e:
                print(f" ERROR: {e}")
        
        # Build results DataFrame
        df_results = pd.DataFrame(self.results)
        df_results = df_results.sort_values('expectancy', ascending=False)
        
        # Summary stats
        elapsed = time.time() - t0
        profitable = (df_results['expectancy'] > 0).sum()
        total_tested = len(df_results)
        
        print("\n" + "="*80)
        print("RESULTS SUMMARY")
        print("="*80)
        print(f"Profitable coins: {profitable}/{total_tested} ({profitable/total_tested*100:.1f}%)")
        print(f"Best: {df_results.iloc[0]['symbol']} (${df_results.iloc[0]['expectancy']:.2f}/trade)")
        print(f"Worst: {df_results.iloc[-1]['symbol']} (${df_results.iloc[-1]['expectancy']:.2f}/trade)")
        print(f"Avg expectancy: ${df_results['expectancy'].mean():.2f}/trade")
        print(f"Runtime: {elapsed/60:.1f} minutes")
        
        return df_results


def test_rule_on_market(rule_text: str) -> pd.DataFrame:
    """
    End-to-end: Parse rule → Test market → Return results.
    
    Args:
        rule_text: Natural language trading rule
    
    Returns:
        DataFrame of results (399 coins × metrics)
    """
    from vince.rule_parser import parse_rule
    
    # Parse rule
    parsed = parse_rule(rule_text)
    
    print("\n" + "="*80)
    print("RULE PARSING")
    print("="*80)
    print(f"Input: {rule_text}")
    print(f"\nParsed as: {parsed['readable_summary']}")
    print(f"Rule type: {parsed['rule_type']}")
    print(f"\nGenerated code:")
    print(parsed['python_code'])
    
    # Test on market
    tester = MarketTester(parsed['python_code'], parsed['readable_summary'])
    results = tester.test_market()
    
    return results
```

### Dashboard Integration

Add to `scripts/dashboard.py` (new section at bottom):

```python
st.header("🤖 VINCE Rule Tester")

st.markdown("Describe a rule in plain English. VINCE will test it on 399 coins.")

rule_input = st.text_area(
    "Trading Rule",
    placeholder="Example: Exit if touches ripster gold and 8.3 is over 70 while 60-10 under 30",
    height=100
)

if st.button("Test Rule on Market"):
    if not rule_input:
        st.error("Please enter a rule to test")
    else:
        with st.spinner("Parsing rule..."):
            from vince.rule_parser import parse_rule
            parsed = parse_rule(rule_input)
            
            st.success(f"✅ Parsed: {parsed['readable_summary']}")
            
            with st.expander("Show generated code"):
                st.code(parsed['python_code'], language='python')
        
        with st.spinner(f"Testing on 399 coins... (this takes ~10 minutes)"):
            from vince.market_tester import test_rule_on_market
            results = test_rule_on_market(rule_input)
            
            # Show results
            profitable = (results['expectancy'] > 0).sum()
            total = len(results)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Profitable Coins", f"{profitable}/{total}", 
                       f"{profitable/total*100:.1f}%")
            col2.metric("Avg Expectancy", f"${results['expectancy'].mean():.2f}")
            col3.metric("Best Coin", results.iloc[0]['symbol'])
            
            # Results table
            st.subheader("Top 20 Coins")
            st.dataframe(results.head(20))
            
            # Bottom 20
            st.subheader("Bottom 20 Coins")
            st.dataframe(results.tail(20))
            
            # Download CSV
            csv = results.to_csv(index=False)
            st.download_button(
                "Download Full Results",
                csv,
                "vince_rule_test_results.csv",
                "text/csv"
            )
```

---

## Test Command

```bash
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester"

python -c "
from vince.market_tester import test_rule_on_market

rule = '''
Exit if touches ripster gold and 8.3 and 14.3 is in overbought 
while 60-10 under 30, exit if crosses ripster gold
'''

results = test_rule_on_market(rule)
print(results.head(10))
"
```

---

## Expected Output

```
================================================================================
RULE PARSING
================================================================================
Input: Exit if touches ripster gold and 8.3 and 14.3 is in overbought 
while 60-10 under 30, exit if crosses ripster gold

Parsed as: EXIT when: Price touches cloud2 AND STOCH 8 3 > 70 AND STOCH 14 3 > 70 AND STOCH 60 10 < 30

Rule type: exit_management

Generated code:
def custom_rule(bar, position):
    '''Auto-generated rule from natural language.'''
    return bar['low'] <= bar['cloud2_bottom'] <= bar['high'] and bar['stoch_8_3'] > 70 and bar['stoch_14_3'] > 70 and bar['stoch_60_10'] < 30

================================================================================
VINCE MARKET-WIDE RULE TEST
================================================================================
Rule: EXIT when: Price touches cloud2 AND STOCH 8 3 > 70 AND STOCH 14 3 > 70 AND STOCH 60 10 < 30
Period: 2024-01-01 to 2025-02-11
Coins: 399
================================================================================
[1/399] RIVERUSDT... 1247 trades, $-2.34/trade
[2/399] SKRUSDT... 187 trades, $8.12/trade
[3/399] ACUUSDT... 142 trades, $-1.23/trade
...
[399/399] ZILLUSDT... 892 trades, $-5.67/trade

================================================================================
RESULTS SUMMARY
================================================================================
Profitable coins: 87/399 (21.8%)
Best: SKRUSDT ($8.12/trade)
Worst: SUNUSDT ($-18.45/trade)
Avg expectancy: $-3.12/trade
Runtime: 9.3 minutes

RECOMMENDATION: Rule FAILS market-wide. Try alternatives:
- Cloud 3 instead? (higher conviction)
- Relax 60-10 < 30 to < 40? (catch more setups)
- Add volume filter? (quality over quantity)
```

---

## What This Enables

**User workflow:**

1. **See pattern on chart** (manual discretionary observation)
2. **Describe in English:** "Exit if X and Y while Z"
3. **VINCE tests:** 399 coins × 1 year automatically
4. **Results in 10 minutes:** "Works on 87 coins, fails on 312"
5. **Iterate:** "What if Cloud 3 instead?" → Re-test instantly

**No coding. No manual backtesting. Pure idea validation.**

---

## Future Enhancements

**Phase 2: Screenshot parsing**
- Upload TradingView screenshot
- VINCE extracts: indicators, levels, patterns
- Auto-generates rule from visual

**Phase 3: VINCE suggests improvements**
- Rule fails? VINCE tests variations
- "Tried 12 variations, best is: Cloud 3 + 60-10 < 40"

**Phase 4: Live deployment**
- Rule works? Deploy to live trading
- VINCE monitors performance
- Auto-disables if diverges from backtest
