"""
Build system flow PDF — C-level presentation quality.
Page 1: Mermaid flowchart (top 55%) + component table (bottom 45%).
Pages 2+3: Vertical step rows drawn directly via reportlab (no Mermaid).
Output: C:/Users/User/Documents/strategy-system-flow.pdf
"""

import py_compile
import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Page 1 — Mermaid diagram (rendered via playwright)
# ---------------------------------------------------------------------------

PAGE1_TITLE = "System Architecture — Built Components"
PAGE1_MERMAID = """
flowchart LR
    A1[(Price Cache\\nN instruments\\n2026-01-20)] --> A3
    A2[(Metadata\\nMarket cap\\n2026-01-25)] --> A3
    A3[Period Loader\\nConcat + resample\\n2026-01-20]
    A3 --> B1 & B2 & B3 & B4
    B1[Momentum\\nOscillator\\n2026-01-28]
    B2[Trend Filter\\nEMA Clouds\\n2026-01-28]
    B3[Anchor\\nVol-weighted\\n2026-01-28]
    B4[Vol State L1\\nPercentile 0-100\\n7 states\\n2026-02-14]
    B4 --> B5[Vol Sequencer L2\\nTransitions\\n2026-02-14]
    B5 --> B6[Fwd Returns L3\\nReturn by state\\n2026-02-14]
    B1 & B2 & B3 & B4 --> SM
    SM[State Machine\\nA B C D grades\\n2026-01-30]
    SM --> BT[Backtester\\nMulti-slot\\n2026-02-05]
    BT --> PM[Position Mgr\\nSL to BE to Trail\\n2026-02-05]
    BT --> EM[Exit Mgr\\nSL TP Scale\\nbug pending]
    PM & EM --> CM[Commission\\nTaker + Rebate\\n2026-02-05]
    BT --> DASH[Dashboard\\nSingle Sweep\\nPortfolio PDF\\n2026-02-16]
    style A1 fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style A2 fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style A3 fill:#1a3a5a,color:#fff,stroke:#0d2a4a
    style B1 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B2 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B3 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B4 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B5 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style B6 fill:#2d4a27,color:#fff,stroke:#1a3a18
    style SM fill:#5a3a1a,color:#fff,stroke:#3a2010
    style BT fill:#5a3a1a,color:#fff,stroke:#3a2010
    style PM fill:#5a3a1a,color:#fff,stroke:#3a2010
    style EM fill:#8a2a0a,color:#fff,stroke:#6a1a00
    style CM fill:#5a3a1a,color:#fff,stroke:#3a2010
    style DASH fill:#1a5a5a,color:#fff,stroke:#0d4a4a
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #ffffff;
    font-family: Arial, sans-serif;
    padding: 32px 40px 24px 40px;
    width: 1754px;
  }}
  .mermaid {{
    display: flex;
    justify-content: center;
  }}
  .mermaid svg {{
    max-width: 100%;
    height: auto;
    min-height: 600px;
  }}
</style>
</head>
<body>
  <div class="mermaid">
{diagram}
  </div>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'default',
      flowchart: {{ useMaxWidth: false, htmlLabels: true, nodeSpacing: 60, rankSpacing: 80 }},
      themeVariables: {{
        fontSize: '18px',
        fontFamily: 'Arial'
      }}
    }});
  </script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Page 1 component table — plain English for C-level
# ---------------------------------------------------------------------------

# (label, hex_color, date, plain_english_description)
PAGE1_TABLE = [
    ("Price Cache",       "#1a3a5a", "2026-01-20", "Historical price data for all instruments stored locally for rapid access"),
    ("Metadata",          "#1a3a5a", "2026-01-25", "Market context data (market cap, instrument info) enriching each data point"),
    ("Period Loader",     "#1a3a5a", "2026-01-20", "Combines all data sources into a single unified, time-aligned data feed"),
    ("Momentum Osc",      "#2d4a27", "2026-01-28", "Measures buying and selling pressure to detect trend strength and reversals"),
    ("Trend Filter",      "#2d4a27", "2026-01-28", "Identifies the prevailing market direction using layered moving averages"),
    ("Anchor Signal",     "#2d4a27", "2026-01-28", "Volume-weighted reference level that anchors price context to key levels"),
    ("Vol State L1",      "#2d4a27", "2026-02-14", "Classifies current volatility into one of seven distinct market regimes"),
    ("Vol Sequencer L2",  "#2d4a27", "2026-02-14", "Tracks how volatility regimes transition from one state to the next"),
    ("Fwd Returns L3",    "#2d4a27", "2026-02-14", "Measures how price behaves after each volatility state to guide expectations"),
    ("State Machine",     "#5a3a1a", "2026-01-30", "Combines all signals into a single A-D grade indicating trade quality"),
    ("Backtester",        "#5a3a1a", "2026-02-05", "Simulates strategy execution across historical data to validate performance"),
    ("Position Mgr",      "#5a3a1a", "2026-02-05", "Manages open trades: moves stop-loss to break-even, then trails to protect gains"),
    ("Exit Manager",      "#8a2a0a", "2026-02-05", "Controls trade exits via stop-loss, take-profit, and scaling — fix in progress"),
    ("Commission",        "#5a3a1a", "2026-02-05", "Calculates realistic trading costs including exchange fees and rebate income"),
    ("Dashboard",         "#1a5a5a", "2026-02-16", "Interactive reporting tool: single runs, parameter sweeps, portfolio view, PDF export"),
]


# ---------------------------------------------------------------------------
# Pages 2 + 3 — vertical step rows (pure reportlab, no Mermaid)
# ---------------------------------------------------------------------------

# Each step: (label, date, hex_color, plain_english_description)
PAGE2_TITLE = "Analysis Pipeline — From Results to Machine Learning"
PAGE2_STEPS = [
    ("Backtester Output",    "2026-02-05", "#5a3a1a",
     "Raw trade-by-trade results from the simulation engine — the starting point for all analysis."),
    ("Results Analyzer L4",  "2026-02-15", "#3a2d5a",
     "Calculates win rate, Sharpe ratio, max drawdown, and other performance statistics across all tested setups."),
    ("Monte Carlo L4b",      "2026-02-15", "#3a2d5a",
     "Runs thousands of randomised simulations to classify each setup as Robust, Fragile, or not worth trading."),
    ("Feature Generator L5", "2026-02-20", "#c44a00",
     "Transforms simulation verdicts into structured data rows ready for machine learning input. (Bottleneck)"),
    ("Data Split",           "2026-02-20", "#6b5a00",
     "Divides data into three non-overlapping sets: 53% for training, 10% for validation, 20% permanently frozen for final test."),
    ("Feature Selection",    "2026-02-24", "#5a1a3a",
     "Automatically removes low-value inputs, keeping only the signals that genuinely predict future performance."),
    ("Feature Engineering",  "2026-02-24", "#5a1a3a",
     "Encodes market state and regime context into formats that machine learning models can interpret effectively."),
    ("Parameter Optimizer",  "2026-02-28", "#c44a00",
     "Tunes the prediction model using 5-fold cross-validation to maximise accuracy without overfitting. (Bottleneck)"),
]

PAGE3_TITLE = "Validation, Live Deployment & Continuous Learning"
PAGE3_STEPS = [
    ("Parameter Optimizer",  "2026-02-28", "#c44a00",
     "Finalised model parameters handed off from the training phase. (Bottleneck — shared critical path node)"),
    ("Trade Filter",         "2026-03-03", "#5a1a3a",
     "The model decides in real time whether to take or skip each signal, filtering out low-confidence setups."),
    ("Position Sizer",       "2026-03-03", "#5a1a3a",
     "Calculates optimal trade size for each signal using Kelly criterion to balance growth against risk of ruin."),
    ("Validation",           "2026-03-07", "#5a1a3a",
     "Checks model performance on the 10% held-out set — confirms it generalises beyond the training data."),
    ("Final Test",           "2026-03-10", "#7a0a0a",
     "One-time evaluation on the permanently frozen 20% dataset. This result is the definitive performance benchmark."),
    ("Inference Engine",     "2026-03-14", "#1a3a7a",
     "Runs the trained model live, generating trade decisions in under 50 milliseconds per signal."),
    ("Webhook / Alert",      "2026-03-14", "#1a3a7a",
     "Routes live trade decisions to connected systems or sends alerts to the trading operator in real time."),
    ("Exchange API",         "2026-03-17", "#1a3a7a",
     "Submits orders directly to the exchange, handling execution, confirmation, and error recovery automatically."),
    ("Daily Retrain",        "2026-03-17", "#1a5a27",
     "Monitors for model drift and retrains daily on fresh data to keep the system aligned with current market conditions."),
]


# ---------------------------------------------------------------------------
# Render helpers
# ---------------------------------------------------------------------------

def hex_to_rgb(h):
    """Convert hex colour string to 0-1 float RGB tuple."""
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def render_mermaid_to_png(diagram, out_path, page_w=1754, page_h=800):
    """Render a single Mermaid diagram to PNG via playwright headless Chromium."""
    from playwright.sync_api import sync_playwright

    html = HTML_TEMPLATE.format(diagram=diagram.strip())
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    tmp.write(html)
    tmp.close()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": page_w, "height": page_h})
            page.goto(f"file:///{tmp.name.replace(chr(92), '/')}")
            page.wait_for_function(
                "() => document.querySelectorAll('.mermaid svg').length > 0",
                timeout=20000
            )
            page.wait_for_timeout(1500)
            page.screenshot(path=str(out_path), full_page=True)
            browser.close()
    finally:
        os.unlink(tmp.name)

    print(f"  [OK] Rendered PNG: {out_path.name}")


# ---------------------------------------------------------------------------
# PDF builders
# ---------------------------------------------------------------------------

def build_page1(c, page_w, page_h, png_path):
    """Draw Page 1: diagram top (~45% height) then component table below filling rest of page."""
    from reportlab.lib.utils import ImageReader
    from PIL import Image

    margin = 20
    footer_h = 18
    header_h = 34   # matches build_step_page

    # --- Page title (matches pages 2+3 style) ---
    c.setFont("Courier-Bold", 14)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(margin, page_h - margin - 2, PAGE1_TITLE)

    # Divider under title
    title_divider_y = page_h - margin - header_h + 8
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    c.line(margin, title_divider_y, page_w - margin, title_divider_y)

    # Zone heights — diagram 42% of space below title, table fills remainder
    content_h = title_divider_y - footer_h - margin
    diag_zone_h = content_h * 0.42

    # --- Diagram: fill the diagram zone below the title ---
    img = Image.open(png_path)
    img_w, img_h = img.size
    avail_w = page_w - 2 * margin
    avail_h = diag_zone_h - 4
    scale = min(avail_w / img_w, avail_h / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale
    img_x = (page_w - draw_w) / 2
    img_y = title_divider_y - diag_zone_h + (diag_zone_h - draw_h) / 2
    c.drawImage(ImageReader(str(png_path)), img_x, img_y, width=draw_w, height=draw_h)

    # --- Divider + table header ---
    divider_y = title_divider_y - diag_zone_h
    c.setStrokeColorRGB(0.65, 0.65, 0.65)
    c.setLineWidth(0.5)
    c.line(margin, divider_y, page_w - margin, divider_y)

    header_y = divider_y - 3
    c.setFont("Courier-Bold", 12)
    c.setFillColorRGB(0.12, 0.12, 0.12)
    c.drawCentredString(page_w / 2, header_y, "Component Reference")

    # --- Table: two columns side by side ---
    rows = PAGE1_TABLE
    n_rows = len(rows)
    half = (n_rows + 1) // 2          # rows per column

    col_gap = 14
    col_w = (page_w - 2 * margin - col_gap) / 2
    table_top = header_y - 10
    row_h = (table_top - footer_h - margin) / half

    badge_w = int(col_w * 0.24)   # narrower badge → more room for description
    badge_gap = 8
    desc_col_w = col_w - badge_w - badge_gap

    for idx, (label, color, date, desc) in enumerate(rows):
        col_idx = idx // half
        row_idx = idx % half
        rx = margin + col_idx * (col_w + col_gap)
        row_top = table_top - row_idx * row_h

        r, g, b = hex_to_rgb(color)

        badge_h = row_h * 0.82
        badge_y = row_top - row_h / 2 - badge_h / 2

        # Colored badge
        c.setFillColorRGB(r, g, b)
        c.roundRect(rx, badge_y, badge_w, badge_h, 3, fill=1, stroke=0)

        # Label in badge — Courier-Bold 9, white, top portion
        c.setFillColorRGB(1.0, 1.0, 1.0)
        c.setFont("Courier-Bold", 9)
        words = label.split()
        llines = []
        ln = ""
        for w in words:
            t = (ln + " " + w).strip()
            if c.stringWidth(t, "Courier-Bold", 9) <= badge_w - 6:
                ln = t
            else:
                if ln:
                    llines.append(ln)
                ln = w
        if ln:
            llines.append(ln)

        date_zone_h = 11   # reserved at bottom for date
        lline_h = 11
        total_lh = len(llines) * lline_h
        # Centre label in upper portion (above date zone)
        label_zone_h = badge_h - date_zone_h - 2
        label_zone_mid = badge_y + date_zone_h + label_zone_h / 2
        lstart = label_zone_mid + total_lh / 2 - 2
        for li, ll in enumerate(llines):
            c.drawString(rx + 4, lstart - li * lline_h, ll)

        # Date — Courier 8, light, pinned to bottom of badge
        c.setFont("Courier", 8)
        c.setFillColorRGB(0.80, 0.80, 0.80)
        c.drawString(rx + 4, badge_y + 3, date)

        # Arrow connector: badge right edge → description
        arrow_y = badge_y + badge_h / 2
        arrow_x0 = rx + badge_w + 1
        arrow_x1 = rx + badge_w + badge_gap - 2
        c.setStrokeColorRGB(0.55, 0.55, 0.55)
        c.setLineWidth(0.8)
        c.line(arrow_x0, arrow_y, arrow_x1, arrow_y)
        # Arrowhead
        ah = 3
        c.line(arrow_x1, arrow_y, arrow_x1 - ah, arrow_y + ah)
        c.line(arrow_x1, arrow_y, arrow_x1 - ah, arrow_y - ah)

        # Description — Courier 11, pure black, left-aligned, vertically centred
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Courier", 11)
        desc_x = rx + badge_w + badge_gap

        words = desc.split()
        dlines = []
        ln = ""
        for w in words:
            t = (ln + " " + w).strip()
            if c.stringWidth(t, "Courier", 11) <= desc_col_w:
                ln = t
            else:
                if ln:
                    dlines.append(ln)
                ln = w
        if ln:
            dlines.append(ln)

        dline_h = 13
        max_d = int(badge_h / dline_h)
        dlines = dlines[:max_d]
        total_dh = len(dlines) * dline_h
        desc_cy = badge_y + badge_h / 2
        dstart = desc_cy + total_dh / 2 - 2
        for li, dl in enumerate(dlines):
            c.drawString(desc_x, dstart - li * dline_h, dl)

        # Row separator (within column, skip last row of each column)
        if row_idx < half - 1 or (col_idx == 0 and idx == half - 1):
            c.setStrokeColorRGB(0.88, 0.88, 0.88)
            c.setLineWidth(0.2)
            sep_y = row_top - row_h
            c.line(rx, sep_y + badge_h * 0.1, rx + col_w, sep_y + badge_h * 0.1)

    # --- Legend centred at bottom ---
    legend_y = margin + 2
    legend_items = [
        ("#1a3a5a", "Data Layer"),
        ("#2d4a27", "Signal Processing"),
        ("#5a3a1a", "Execution Engine"),
        ("#8a2a0a", "Bug Pending"),
        ("#1a5a5a", "Reporting"),
    ]
    c.setFont("Courier", 8)
    item_gap = 18
    box_w, box_h2 = 9, 7
    total_leg_w = sum(box_w + 4 + c.stringWidth(lbl, "Courier", 8) + item_gap
                      for _, lbl in legend_items) - item_gap
    lx = (page_w - total_leg_w) / 2
    for hx, lbl in legend_items:
        r, g, b = hex_to_rgb(hx)
        c.setFillColorRGB(r, g, b)
        c.rect(lx, legend_y + 1, box_w, box_h2, fill=1, stroke=0)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(lx + box_w + 4, legend_y + 1, lbl)
        lx += box_w + 4 + c.stringWidth(lbl, "Courier", 8) + item_gap

    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawRightString(page_w - margin, legend_y + 1,
                      "Algorithmic Trading System  |  2026-02-16  |  A4 Landscape")


def build_step_page(c, page_w, page_h, title, steps):
    """Draw a vertical-stack step page: colored block left, description left-aligned right. Courier 14pt."""
    margin = 24
    header_h = 34
    footer_h = 18

    # Page title
    c.setFont("Courier-Bold", 14)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(margin, page_h - margin - 2, title)

    # Divider
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    divider_y = page_h - margin - header_h + 8
    c.line(margin, divider_y, page_w - margin, divider_y)

    # Step rows
    avail_h = divider_y - margin - footer_h
    n = len(steps)
    row_h = avail_h / n
    label_col_w = 200
    gap = 16
    desc_col_w = page_w - 2 * margin - label_col_w - gap

    for i, (label, date, color, desc) in enumerate(steps):
        ry_top = divider_y - i * row_h
        ry_bottom = ry_top - row_h
        inner_pad = row_h * 0.07
        block_y = ry_bottom + inner_pad
        block_h = row_h - 2 * inner_pad

        r, g, b = hex_to_rgb(color)
        cy = block_y + block_h / 2

        # Colored label block — explicit opaque fill
        c.setFillColorRGB(r, g, b)
        c.roundRect(margin, block_y, label_col_w, block_h, 4, fill=1, stroke=0)

        # Step number circle — dark overlay using explicit grey, no alpha
        circle_r = 8
        cx_circle = margin + circle_r + 4
        cy_circle = block_y + block_h - circle_r - 3
        # Darken by blending color with black (no alpha needed)
        dr = max(0, r - 0.25)
        dg = max(0, g - 0.25)
        db = max(0, b - 0.25)
        c.setFillColorRGB(dr, dg, db)
        c.circle(cx_circle, cy_circle, circle_r, fill=1, stroke=0)
        # Step number in white
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Courier-Bold", 8)
        c.drawCentredString(cx_circle, cy_circle - 3, str(i + 1))

        # Layout: date pinned to bottom, label above it
        date_h = 11        # reserved height for date line
        date_y = block_y + 5
        label_x = margin + circle_r * 2 + 10
        label_w_avail = label_col_w - circle_r * 2 - 12

        # Label text (Courier-Bold 12, pure white) — centred in space ABOVE date
        c.setFillColorRGB(1.0, 1.0, 1.0)
        c.setFont("Courier-Bold", 12)

        words = label.split()
        llines = []
        ln = ""
        for w in words:
            t = (ln + " " + w).strip()
            if c.stringWidth(t, "Courier-Bold", 12) <= label_w_avail:
                ln = t
            else:
                if ln:
                    llines.append(ln)
                ln = w
        if ln:
            llines.append(ln)

        lline_h = 14
        total_lh = len(llines) * lline_h
        # Centre label in block area above the date zone
        label_zone_top = block_y + block_h
        label_zone_bot = date_y + date_h + 2
        label_zone_mid = (label_zone_top + label_zone_bot) / 2
        label_start_y = label_zone_mid + total_lh / 2 - 2
        for li, ll in enumerate(llines):
            c.drawString(label_x, label_start_y - li * lline_h, ll)

        # Date (Courier 10, pure white, pinned to bottom of block)
        c.setFont("Courier", 10)
        c.setFillColorRGB(1.0, 1.0, 1.0)
        c.drawString(label_x, date_y, date)

        # Description — Courier 10, pure BLACK, LEFT-aligned, vertically centred in row
        desc_x = margin + label_col_w + gap
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Courier", 10)

        words = desc.split()
        dlines = []
        ln = ""
        for w in words:
            t = (ln + " " + w).strip()
            if c.stringWidth(t, "Courier", 10) <= desc_col_w:
                ln = t
            else:
                if ln:
                    dlines.append(ln)
                ln = w
        if ln:
            dlines.append(ln)

        dline_h = 12
        max_d = int(block_h / dline_h)
        dlines = dlines[:max_d]
        total_dh = len(dlines) * dline_h
        desc_start_y = cy + total_dh / 2 + 1
        for li, dl in enumerate(dlines):
            c.drawString(desc_x, desc_start_y - li * dline_h, dl)

        # Row separator (skip last)
        if i < n - 1:
            c.setStrokeColorRGB(0.88, 0.88, 0.88)
            c.setLineWidth(0.25)
            c.line(margin, ry_bottom + inner_pad, page_w - margin, ry_bottom + inner_pad)

    # Footer
    c.setFont("Courier", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawRightString(page_w - margin, 8,
                      "Algorithmic Trading System  |  2026-02-16  |  A4 Landscape")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Render Page 1 Mermaid to PNG, then build 3-page A4 landscape PDF."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas as rl_canvas

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Building system flow PDF...")

    out_dir = Path(tempfile.gettempdir()) / "system_flow_pngs"
    out_dir.mkdir(exist_ok=True)
    out_pdf = Path("C:/Users/User/Documents/strategy-system-flow.pdf")

    # Render Page 1 Mermaid diagram
    p1_png = out_dir / "page1_diagram.png"
    print("  Rendering Page 1 Mermaid diagram...")
    render_mermaid_to_png(PAGE1_MERMAID, p1_png, page_w=1754, page_h=800)

    # Build PDF
    page_w, page_h = landscape(A4)  # 841.89 x 595.27 pts
    c = rl_canvas.Canvas(str(out_pdf), pagesize=landscape(A4))
    c.setTitle("Algorithmic Trading System — System Flow")
    c.setAuthor("System Flow Builder 2026-02-16")

    print("  Drawing Page 1...")
    build_page1(c, page_w, page_h, p1_png)
    c.showPage()

    print("  Drawing Page 2...")
    build_step_page(c, page_w, page_h, PAGE2_TITLE, PAGE2_STEPS)
    c.showPage()

    print("  Drawing Page 3...")
    build_step_page(c, page_w, page_h, PAGE3_TITLE, PAGE3_STEPS)

    c.save()

    # Cleanup
    p1_png.unlink(missing_ok=True)

    ts2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts2}] DONE. Open: {out_pdf}")


if __name__ == "__main__":
    main()
