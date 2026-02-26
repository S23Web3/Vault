"""
Build progress report PDF — single A4 portrait page.
Corporate update addressed to CEO and Finance Director.
Output: C:/Users/User/Documents/progress-report.pdf
"""

import py_compile
import os
import io
import tempfile
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

REPORT_DATE = "16 February 2026"

TO_LINES = [
    "Fathi Hajri, Chief Executive Officer",
    "Dilip Kamniani, Group Finance and Administration Manager",
]

FROM_LINE = "Malik & Nik"

SUBJECT = "Progress Update — Algorithmic Trading System & Infrastructure"

INTRO = (
    "Update on the proprietary trading system development and infrastructure. "
    "Please see the attached architecture diagram."
)

# Section 1 — System Development
SECTION1_TITLE = "1.  System Development Progress"

SECTION1_BODY = (
    "The core system is substantially complete — data pipeline, signal processing, "
    "simulation engine, position management, and reporting dashboard are all "
    "operational and validated on historical market data. "
    "Built and tested on cryptocurrency markets; the architecture applies equally "
    "to foreign exchange and commodities with minimal changes. "
    "A market regime pipeline with statistical validation is also complete."
)

# Section 2 — ML Next Phase
SECTION2_TITLE = "2.  Machine Learning — Next Phase"

SECTION2_BODY = (
    "The next phase (right-hand side of attached diagram) adds a machine learning "
    "layer to optimise decision parameters in real time. "
    "Once validated, it deploys to a live inference engine at sub-50ms latency "
    "with daily automated retraining. Start date subject to hardware approval."
)

# Section 3 — Infrastructure
SECTION3_TITLE = "3.  Infrastructure & Hardware Procurement"

SECTION3_BODY = (
    "Four workstations (~2,000 USD each) are ready to order for live operations. "
    "ML training requires more compute — Apple M5 Pro Max qualifies at ~4,000 USD. "
    "Recommended alternative: custom AMD build at 6,270 AED (<2,000 USD) covering "
    "both workloads. Full specs with Ragesh. Pending approval."
)

# Section 4 — Local server
SECTION4_TITLE = "4.  Secure Local File Server"

SECTION4_BODY = (
    "Recommend deploying a self-hosted local server (e.g. Nextcloud) for private "
    "team file sharing — browser, desktop, and mobile access. "
    "No internet connection; role-based accounts; SSH for technical staff, "
    "GUI for all others. Data stays fully on-premises. "
    "One low-power machine, operational within one working day."
)

SIGN_OFF = "Kind regards,"

# Hardware table rows
HW_ROWS = [
    ("CPU",         "AMD Ryzen 9 7900X (12 cores, used)",      "1,300 AED"),
    ("Motherboard", "MSI B650 Tomahawk WiFi DDR5",              "  700 AED"),
    ("RAM",         "2x16 GB DDR5 6000 MHz (32 GB)",           "  480 AED"),
    ("GPU",         "Gigabyte RTX 5060 Ti 16 GB",              "2,200 AED"),
    ("SSD",         "2 TB WD Black SN770 Gen4",                "  500 AED"),
    ("Cooler",      "DeepCool AK620",                          "  220 AED"),
    ("PSU",         "Corsair RM750e 750W Gold",                 "  420 AED"),
    ("Case",        "Lian Li Lancool 216",                      "  380 AED"),
    ("Extras",      "Paste, fans, cables",                      "   70 AED"),
    ("TOTAL",       "",                                         "6,270 AED"),
]

# ---------------------------------------------------------------------------
# Logo fetch helper
# ---------------------------------------------------------------------------

def fetch_logo(url, max_w_pt, max_h_pt):
    """Fetch logo from URL, return PIL Image scaled to fit within max dims."""
    import requests
    from PIL import Image

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGBA")

    # Scale to fit
    iw, ih = img.size
    scale = min(max_w_pt / iw, max_h_pt / ih, 1.0)
    new_w = int(iw * scale)
    new_h = int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    return img


def pil_to_reportlab(pil_img):
    """Convert PIL Image to a reportlab-compatible ImageReader."""
    from reportlab.lib.utils import ImageReader
    buf = io.BytesIO()
    # Convert RGBA to RGB for PDF compatibility
    bg = pil_img
    if pil_img.mode == "RGBA":
        bg = pil_img
    bg.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


# ---------------------------------------------------------------------------
# Word-wrap helper
# ---------------------------------------------------------------------------

def wrap_text(c, text, font_name, font_size, max_width):
    """Wrap text to lines that fit within max_width. Returns list of strings."""
    paragraphs = text.split("\n\n")
    all_lines = []
    for para in paragraphs:
        words = para.replace("\n", " ").split()
        line = ""
        for w in words:
            candidate = (line + " " + w).strip()
            if c.stringWidth(candidate, font_name, font_size) <= max_width:
                line = candidate
            else:
                if line:
                    all_lines.append(line)
                line = w
        if line:
            all_lines.append(line)
        all_lines.append("")   # blank line between paragraphs
    # Remove trailing blank
    while all_lines and all_lines[-1] == "":
        all_lines.pop()
    return all_lines


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def build_report(out_pdf):
    """Build the single-page A4 portrait progress report PDF."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Building progress report PDF...")

    page_w, page_h = A4   # 595.27 x 841.89 pts (portrait)
    margin = 45
    c = rl_canvas.Canvas(str(out_pdf), pagesize=A4)
    c.setTitle("Progress Update — Algorithmic Trading System")

    # -- Logos --
    SHORTCUT_URL = (
        "https://i0.wp.com/www.shortcut23.com/wp-content/uploads/"
        "2023/06/shortcut-2560-%C3%97-1440-px.png?fit=820%2C200&ssl=1"
    )
    GOLDIAMA_LOCAL = r"C:\Users\User\Pictures\Goldiama-Logo.jpg"

    logo_h_pt = 36   # max logo height in points
    logo_w_pt = 140  # max logo width in points
    logo_y = page_h - margin - logo_h_pt

    try:
        sc_img = fetch_logo(SHORTCUT_URL, logo_w_pt, logo_h_pt)
        sc_rl = pil_to_reportlab(sc_img)
        sc_w, sc_h = sc_img.size
        c.drawImage(sc_rl, margin, logo_y, width=sc_w, height=sc_h, mask="auto")
        print("  [OK] Shortcut23 logo loaded")
    except Exception as e:
        print(f"  [WARN] Shortcut23 logo failed: {e}")

    try:
        from PIL import Image as _PIL
        gd_img = _PIL.open(GOLDIAMA_LOCAL).convert("RGBA")
        iw, ih = gd_img.size
        scale = min(logo_w_pt / iw, logo_h_pt / ih, 1.0)
        gd_img = gd_img.resize((int(iw * scale), int(ih * scale)), _PIL.LANCZOS)
        gd_rl = pil_to_reportlab(gd_img)
        gd_w, gd_h = gd_img.size
        gd_x = page_w - margin - gd_w
        c.drawImage(gd_rl, gd_x, logo_y, width=gd_w, height=gd_h, mask="auto")
        print("  [OK] Goldiama logo loaded from local file")
    except Exception as e:
        print(f"  [WARN] Goldiama logo failed: {e}")

    # -- Header divider --
    header_divider_y = logo_y - 8
    c.setStrokeColorRGB(0.2, 0.2, 0.2)
    c.setLineWidth(1.0)
    c.line(margin, header_divider_y, page_w - margin, header_divider_y)

    # -- Title --
    y = header_divider_y - 18
    c.setFont("Courier-Bold", 16)
    c.setFillColorRGB(0.05, 0.05, 0.05)
    c.drawString(margin, y, "PROGRESS UPDATE")

    # -- Date --
    c.setFont("Courier", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawRightString(page_w - margin, y + 2, REPORT_DATE)

    y -= 16

    # -- To / From --
    c.setFont("Courier-Bold", 9)
    c.setFillColorRGB(0.15, 0.15, 0.15)
    label_w = 42
    c.drawString(margin, y, "To:")
    c.setFont("Courier", 9)
    c.setFillColorRGB(0.0, 0.0, 0.0)
    c.drawString(margin + label_w, y, TO_LINES[0])
    y -= 12
    c.drawString(margin + label_w, y, TO_LINES[1])
    y -= 12

    c.setFont("Courier-Bold", 9)
    c.setFillColorRGB(0.15, 0.15, 0.15)
    c.drawString(margin, y, "From:")
    c.setFont("Courier", 9)
    c.setFillColorRGB(0.0, 0.0, 0.0)
    c.drawString(margin + label_w, y, FROM_LINE)
    y -= 12

    c.setFont("Courier-Bold", 9)
    c.setFillColorRGB(0.15, 0.15, 0.15)
    c.drawString(margin, y, "Re:")
    c.setFont("Courier", 9)
    c.setFillColorRGB(0.0, 0.0, 0.0)
    max_w = page_w - 2 * margin - label_w
    subj_lines = wrap_text(c, SUBJECT, "Courier", 9, max_w)
    c.drawString(margin + label_w, y, subj_lines[0] if subj_lines else SUBJECT)
    y -= 10

    # Sub-divider
    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.setLineWidth(0.4)
    c.line(margin, y, page_w - margin, y)
    y -= 22

    # -- Intro paragraph --
    body_w = page_w - 2 * margin
    FONT_BODY = "Courier"
    FONT_SIZE = 8.5
    TITLE_SIZE = 9.5
    line_h = 11

    c.setFont(FONT_BODY, FONT_SIZE)
    c.setFillColorRGB(0.0, 0.0, 0.0)
    intro_lines = wrap_text(c, INTRO, FONT_BODY, FONT_SIZE, body_w)
    for ln in intro_lines:
        c.drawString(margin, y, ln)
        y -= line_h
    y -= 22

    # -- Section helper --
    def draw_section(title, body, hw_table=False):
        """Draw a titled section with body text, optional hardware table."""
        nonlocal y
        c.setFont("Courier-Bold", TITLE_SIZE)
        c.setFillColorRGB(0.05, 0.05, 0.05)
        c.drawString(margin, y, title)
        y -= 11

        c.setFont(FONT_BODY, FONT_SIZE)
        c.setFillColorRGB(0.0, 0.0, 0.0)
        body_lines = wrap_text(c, body, FONT_BODY, FONT_SIZE, body_w)
        for ln in body_lines:
            c.drawString(margin, y, ln)
            y -= line_h

        if hw_table:
            y -= 3
            col1 = margin
            col2 = margin + 90
            col3 = page_w - margin - 70
            tbl_line_h = 10
            c.setFont("Courier-Bold", 7.5)
            c.setFillColorRGB(0.15, 0.15, 0.15)
            c.rect(col1 - 2, y - 2, body_w + 4, tbl_line_h + 2, fill=1, stroke=0)
            c.setFillColorRGB(1, 1, 1)
            c.drawString(col1 + 2, y, "Component")
            c.drawString(col2 + 2, y, "Specification")
            c.drawRightString(col3 + 68, y, "Price")
            y -= tbl_line_h

            for row_idx, (comp, spec, price) in enumerate(HW_ROWS):
                is_total = comp == "TOTAL"
                fill_r = 0.94 if row_idx % 2 == 0 else 1.0
                if is_total:
                    fill_r = 0.88
                c.setFillColorRGB(fill_r, fill_r, fill_r)
                c.rect(col1 - 2, y - 2, body_w + 4, tbl_line_h, fill=1, stroke=0)
                c.setFillColorRGB(0.0, 0.0, 0.0)
                if is_total:
                    c.setFont("Courier-Bold", 7.5)
                else:
                    c.setFont(FONT_BODY, 7.5)
                c.drawString(col1 + 2, y, comp)
                c.drawString(col2 + 2, y, spec)
                c.drawRightString(col3 + 68, y, price)
                y -= tbl_line_h

        y -= 22

    draw_section(SECTION1_TITLE, SECTION1_BODY)
    draw_section(SECTION2_TITLE, SECTION2_BODY)
    draw_section(SECTION3_TITLE, SECTION3_BODY, hw_table=True)
    draw_section(SECTION4_TITLE, SECTION4_BODY)

    # -- Sign-off — pinned above footer with guard --
    footer_reserve = 52   # space reserved for sign-off + footer
    if y > footer_reserve:
        y -= 6
    c.setFont("Courier", 9)
    c.setFillColorRGB(0.0, 0.0, 0.0)
    c.drawString(margin, y, SIGN_OFF)
    y -= 14
    c.setFont("Courier-Bold", 9)
    c.drawString(margin, y, FROM_LINE)
    y -= 12
    c.setFont("Courier", 9)
    c.drawString(margin, y, "GDTrade")

    # -- Footer — always at bottom --
    c.setStrokeColorRGB(0.75, 0.75, 0.75)
    c.setLineWidth(0.4)
    c.line(margin, 30, page_w - margin, 30)
    c.setFont("Courier", 7)
    c.setFillColorRGB(0.55, 0.55, 0.55)
    c.drawString(margin, 20, "CONFIDENTIAL — For internal distribution only.")
    c.drawRightString(page_w - margin, 20,
                      f"Generated {datetime.now().strftime('%Y-%m-%d')}")

    c.save()
    ts2 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts2}] DONE. Open: {out_pdf}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Main entry point — build the progress report PDF."""
    out_pdf = Path("C:/Users/User/Documents/Obsidian Vault/progress-report.pdf")
    build_report(out_pdf)


if __name__ == "__main__":
    main()
