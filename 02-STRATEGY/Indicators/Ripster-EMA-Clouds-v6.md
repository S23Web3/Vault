# Ripster EMA Clouds v6

## Status: ✅ Ready to Test

---

## How to Use
1. Copy the code below
2. TradingView → Pine Editor → Paste → Add to Chart

---

## Pine Script Code

```pinescript
// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © ripster47 - Converted to Pine Script v6

//@version=6
indicator("Ripster EMA Clouds v6", "Ripster EMA Clouds", overlay=true, max_lines_count=500)

// Inputs
matype = input.string(defval="EMA", title="MA Type", options=["EMA", "SMA"])

ma_len1 = input.int(defval=8, title="Short EMA1 Length")
ma_len2 = input.int(defval=9, title="Long EMA1 Length")
ma_len3 = input.int(defval=5, title="Short EMA2 Length")
ma_len4 = input.int(defval=12, title="Long EMA2 Length")
ma_len5 = input.int(defval=34, title="Short EMA3 Length")
ma_len6 = input.int(defval=50, title="Long EMA3 Length")
ma_len7 = input.int(defval=72, title="Short EMA4 Length")
ma_len8 = input.int(defval=89, title="Long EMA4 Length")
ma_len9 = input.int(defval=180, title="Short EMA5 Length")
ma_len10 = input.int(defval=200, title="Long EMA5 Length")

src = input.source(defval=hl2, title="Source")
emacloudleading = input.int(defval=0, minval=0, title="Leading Period For EMA Cloud")

showlong = input.bool(defval=false, title="Show Long Alerts")
showshort = input.bool(defval=false, title="Show Short Alerts")
showLine = input.bool(defval=false, title="Display EMA Line")
ema1 = input.bool(defval=true, title="Show EMA Cloud-1")
ema2 = input.bool(defval=true, title="Show EMA Cloud-2")
ema3 = input.bool(defval=true, title="Show EMA Cloud-3")
ema4 = input.bool(defval=false, title="Show EMA Cloud-4")
ema5 = input.bool(defval=false, title="Show EMA Cloud-5")

// MA Function
f_ma(source, length) =>
    matype == "EMA" ? ta.ema(source, length) : ta.sma(source, length)

// Calculate MAs
mashort1 = f_ma(src, ma_len1)
malong1 = f_ma(src, ma_len2)
mashort2 = f_ma(src, ma_len3)
malong2 = f_ma(src, ma_len4)
mashort3 = f_ma(src, ma_len5)
malong3 = f_ma(src, ma_len6)
mashort4 = f_ma(src, ma_len7)
malong4 = f_ma(src, ma_len8)
mashort5 = f_ma(src, ma_len9)
malong5 = f_ma(src, ma_len10)

// Cloud Colors - bullish/bearish
bull1 = color.new(#036103, 45)
bear1 = color.new(#880e4f, 45)
bull2 = color.new(#4caf50, 65)
bear2 = color.new(#f44336, 65)
bull3 = color.new(#2196f3, 70)
bear3 = color.new(#ffb74d, 70)
bull4 = color.new(#009688, 65)
bear4 = color.new(#f06292, 65)
bull5 = color.new(#05bed5, 65)
bear5 = color.new(#e65100, 65)

cloudcolor1 = mashort1 >= malong1 ? bull1 : bear1
cloudcolor2 = mashort2 >= malong2 ? bull2 : bear2
cloudcolor3 = mashort3 >= malong3 ? bull3 : bear3
cloudcolor4 = mashort4 >= malong4 ? bull4 : bear4
cloudcolor5 = mashort5 >= malong5 ? bull5 : bear5

// Line Colors
mashortcolor1 = mashort1 >= mashort1[1] ? color.olive : color.maroon
mashortcolor2 = mashort2 >= mashort2[1] ? color.olive : color.maroon
mashortcolor3 = mashort3 >= mashort3[1] ? color.olive : color.maroon
mashortcolor4 = mashort4 >= mashort4[1] ? color.olive : color.maroon
mashortcolor5 = mashort5 >= mashort5[1] ? color.rgb(179, 179, 43) : color.maroon

malongcolor1 = malong1 >= malong1[1] ? color.green : color.red
malongcolor2 = malong2 >= malong2[1] ? color.green : color.red
malongcolor3 = malong3 >= malong3[1] ? color.green : color.red
malongcolor4 = malong4 >= malong4[1] ? color.green : color.red
malongcolor5 = malong5 >= malong5[1] ? color.green : color.red

// Plots - Short MAs
mashortline1 = plot(ema1 ? mashort1 : na, title="Short EMA1", color=showLine ? mashortcolor1 : color.new(color.white, 100), linewidth=1, offset=emacloudleading)
mashortline2 = plot(ema2 ? mashort2 : na, title="Short EMA2", color=showLine ? mashortcolor2 : color.new(color.white, 100), linewidth=1, offset=emacloudleading)
mashortline3 = plot(ema3 ? mashort3 : na, title="Short EMA3", color=showLine ? mashortcolor3 : color.new(color.white, 100), linewidth=1, offset=emacloudleading)
mashortline4 = plot(ema4 ? mashort4 : na, title="Short EMA4", color=showLine ? mashortcolor4 : color.new(color.white, 100), linewidth=1, offset=emacloudleading)
mashortline5 = plot(ema5 ? mashort5 : na, title="Short EMA5", color=showLine ? mashortcolor5 : color.new(color.white, 100), linewidth=1, offset=emacloudleading)

// Plots - Long MAs
malongline1 = plot(ema1 ? malong1 : na, title="Long EMA1", color=showLine ? malongcolor1 : color.new(color.white, 100), linewidth=3, offset=emacloudleading)
malongline2 = plot(ema2 ? malong2 : na, title="Long EMA2", color=showLine ? malongcolor2 : color.new(color.white, 100), linewidth=3, offset=emacloudleading)
malongline3 = plot(ema3 ? malong3 : na, title="Long EMA3", color=showLine ? malongcolor3 : color.new(color.white, 100), linewidth=3, offset=emacloudleading)
malongline4 = plot(ema4 ? malong4 : na, title="Long EMA4", color=showLine ? malongcolor4 : color.new(color.white, 100), linewidth=3, offset=emacloudleading)
malongline5 = plot(ema5 ? malong5 : na, title="Long EMA5", color=showLine ? malongcolor5 : color.new(color.white, 100), linewidth=3, offset=emacloudleading)

// Fill Clouds
fill(mashortline1, malongline1, color=cloudcolor1, title="Cloud 1")
fill(mashortline2, malongline2, color=cloudcolor2, title="Cloud 2")
fill(mashortline3, malongline3, color=cloudcolor3, title="Cloud 3")
fill(mashortline4, malongline4, color=cloudcolor4, title="Cloud 4")
fill(mashortline5, malongline5, color=cloudcolor5, title="Cloud 5")

// Alert Conditions
longCondition = ta.crossover(mashort1, malong1) and mashort3 > malong3
shortCondition = ta.crossunder(mashort1, malong1) and mashort3 < malong3

alertcondition(longCondition, title="Long Signal", message="Ripster EMA Cloud - Long Signal")
alertcondition(shortCondition, title="Short Signal", message="Ripster EMA Cloud - Short Signal")

// Signal Shapes
plotshape(showlong and longCondition, title="Long Signal", style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small)
plotshape(showshort and shortCondition, title="Short Signal", style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small)
```

---

## Changes from v4 to v6

| v4 | v6 |
|----|-----|
| `study()` | `indicator()` |
| `input()` | `input.int()`, `input.bool()`, `input.string()`, `input.source()` |
| `ema()` | `ta.ema()` |
| `sma()` | `ta.sma()` |
| `crossover()` | `ta.crossover()` |
| `crossunder()` | `ta.crossunder()` |

---

## Tags
#indicator #ema #clouds #ripster #v6
