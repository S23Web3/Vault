# PDF Orientation and Alignment Fix
**Date:** 2026-02-17
**Task:** Add landscape orientation for diagrams 2 and 6, center alignment for all
**File Updated:** `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-UML-DIAGRAMS-PDF.md`

---

## Changes Applied

### 1. Added CSS Styling

```css
/* Center alignment for all diagrams */
.diagram-container {
    display: flex;
    justify-content: center;
    align-items: center;
    text-align: center;
    margin: 2em 0;
}

/* Landscape orientation for specific pages */
@page {
    size: A4 portrait;
    margin: 1cm;
}

@page :nth(2) {
    size: A4 landscape;  /* Diagram 2: Data Flow Sequence */
}

@page :nth(6) {
    size: A4 landscape;  /* Diagram 6: VINCE Deployment */
}

/* Center text and diagrams */
.centered {
    text-align: center;
    margin-left: auto;
    margin-right: auto;
}

h2, h3 {
    text-align: center;
}
```

### 2. Wrapped All Content in Centered Divs

**Before:**
```markdown
## Diagram 1: System Overview
[diagram]
```

**After:**
```markdown
<div class="centered">

## Diagram 1: System Overview

<div class="diagram-container">
[diagram]
</div>

</div>
```

### 3. Landscape Page Markers

Added comments for clarity:
```html
<!-- LANDSCAPE PAGE -->
<div class="centered" style="width: 100%; height: 100%;">
```

---

## Page Layout

| Page | Content | Orientation | Alignment |
|------|---------|-------------|-----------|
| 1 | Diagram 1: System Overview | Portrait | Center |
| **2** | **Diagram 2: Data Flow Sequence** | **Landscape** | **Center** |
| 3 | Diagram 3: BBW State Transitions | Portrait | Center |
| 4 | Diagram 4: Layer 3 Output | Portrait | Center |
| 5 | Diagram 5: Data Contracts | Portrait | Center |
| **6** | **Diagram 6: VINCE Deployment** | **Landscape** | **Center** |
| 7 | Diagram 7: 400-Coin Sweep | Portrait | Center |
| 8 | Diagram 8: File Structure | Portrait | Center |
| 9-10 | Summary Tables | Portrait | Center |

---

## Export Methods

### Method 1: Obsidian Native (Recommended)

**If @page CSS Supported:**
1. Open `BBW-V2-UML-DIAGRAMS-PDF.md` in Obsidian
2. Ctrl+P → "Export to PDF"
3. Diagrams 2 and 6 should automatically be landscape
4. All content centered

**If @page CSS NOT Supported:**
- All pages will be portrait
- Content still centered
- Manually rotate pages 2 and 6 in PDF viewer

### Method 2: Print to PDF

1. Open in Obsidian
2. Ctrl+P (Print)
3. Print to PDF
4. **CSS @page rules may not work in browser print**
5. Manual rotation required

### Method 3: Pandoc (Best CSS Support)

```powershell
cd "C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2"

pandoc BBW-V2-UML-DIAGRAMS-PDF.md -o BBW-Diagrams.pdf `
  --pdf-engine=wkhtmltopdf `
  --css=custom.css
```

**Note:** wkhtmltopdf has better @page support than most tools

### Method 4: Manual Split (Fallback)

If CSS orientation doesn't work:

**Create 3 separate files:**

1. **Portrait pages (1,3,4,5,7,8,9,10):**
   - Export with portrait orientation

2. **Landscape page 2:**
   - Extract Diagram 2 only
   - Export with landscape orientation

3. **Landscape page 6:**
   - Extract Diagram 6 only
   - Export with landscape orientation

**Merge PDFs:**
```powershell
# Using PDFtk (install: choco install pdftk)
pdftk portrait.pdf landscape2.pdf landscape6.pdf cat output final.pdf
```

---

## CSS @page Browser Support

| Tool | @page Support | Orientation Control |
|------|--------------|---------------------|
| Chrome Print | ❌ Limited | Manual only |
| Firefox Print | ❌ Limited | Manual only |
| wkhtmltopdf | ✅ Good | Automatic |
| Prince XML | ✅ Excellent | Automatic |
| Obsidian Export | ⚠️ Varies | Test required |

**Recommendation:** Test in Obsidian first. If orientation doesn't work, use Pandoc + wkhtmltopdf.

---

## Center Alignment Implementation

### All Diagrams

```html
<div class="diagram-container">
```mermaid
[diagram code]
```
</div>
```

**Result:** Diagram centered horizontally and vertically on page

### All Headings

```css
h2, h3 {
    text-align: center;
}
```

**Result:** All headings centered

### All Tables

```markdown
| Column | Type |
|:------:|:----:|
```

**Result:** Table content centered using `:----:` alignment

---

## Testing Checklist

**Before Export:**
- [ ] Open `BBW-V2-UML-DIAGRAMS-PDF.md` in Obsidian
- [ ] Verify CSS block present at top
- [ ] Check all diagrams wrapped in `<div class="diagram-container">`

**After Export:**
- [ ] Check page 2 orientation (should be landscape)
- [ ] Check page 6 orientation (should be landscape)
- [ ] Verify all diagrams centered on page
- [ ] Verify all headings centered
- [ ] Verify tables centered

**If Orientation Fails:**
- [ ] Try Pandoc + wkhtmltopdf method
- [ ] Or manually rotate pages 2 and 6 in PDF viewer
- [ ] Or use manual split method

---

## Alternative: Manual Rotation Instructions

If CSS doesn't control orientation:

**Windows (Adobe Acrobat/Reader):**
1. Open exported PDF
2. Select page 2
3. Right-click → Rotate Page → 90° Clockwise
4. Select page 6
5. Right-click → Rotate Page → 90° Clockwise
6. Save

**Windows (Free - PDF-XChange Editor):**
1. Open exported PDF
2. Ctrl+Click pages 2 and 6
3. Right-click → Rotate Pages → 90° Clockwise
4. Save

**Online (pdf.online):**
1. Upload exported PDF
2. Select "Rotate PDF"
3. Rotate pages 2 and 6
4. Download

---

## Files Modified This Session

1. **BBW-V2-UML-DIAGRAMS-PDF.md**
   - Path: `C:\Users\User\Documents\Obsidian Vault\PROJECTS\four-pillars-backtester\docs\bbw-v2\BBW-V2-UML-DIAGRAMS-PDF.md`
   - Added CSS for orientation and centering
   - Wrapped all content in centered divs
   - Added landscape markers for pages 2 and 6

2. **2026-02-17-pdf-orientation-fix.md** (this file)
   - Path: `C:\Users\User\Documents\Obsidian Vault\06-CLAUDE-LOGS\2026-02-17-pdf-orientation-fix.md`
   - Documentation of changes
   - Export methods and testing instructions
   - Fallback options

---

## Diagram Size Optimization for Landscape

### Diagram 2: Data Flow Sequence

**Optimized for landscape:**
- 9 participants across horizontal axis
- Expanded labels (more readable on wide page)
- More detailed annotations

### Diagram 6: VINCE Deployment

**Optimized for landscape:**
- 3 subgraphs side-by-side (Local → Cloud → Live)
- Horizontal flow (left to right)
- Expanded component details

---

## Next Steps

### For User

1. **Test CSS Method:**
   - Export `BBW-V2-UML-DIAGRAMS-PDF.md` from Obsidian
   - Check if pages 2 and 6 are landscape
   - Verify centering on all pages

2. **If CSS Fails:**
   - Option A: Use Pandoc + wkhtmltopdf
   - Option B: Manually rotate pages 2 and 6
   - Option C: Use manual split/merge method

3. **Report Results:**
   - Which export method worked?
   - Did @page CSS control orientation?
   - Any remaining alignment issues?

### For Future Documents

**Best Practices:**
- Always include CSS block for orientation/alignment
- Mark landscape pages with HTML comments
- Test multiple export methods
- Have manual rotation as fallback

---

**END OF SESSION LOG**
