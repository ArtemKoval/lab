#!/usr/bin/env python3
"""CAIO standalone diagram 1 - churns vs compounds bullseye. White bg, 1600x1200, no footer."""
import math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color, HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FB = "/usr/share/fonts/truetype/google-fonts"
pdfmetrics.registerFont(TTFont("Poppins",        f"{FB}/Poppins-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Bold",   f"{FB}/Poppins-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Medium", f"{FB}/Poppins-Medium.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Light",  f"{FB}/Poppins-Light.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Italic", f"{FB}/Poppins-Italic.ttf"))

NAVY    = HexColor("#1E2A4A")
SAPPH   = HexColor("#21508A")
GRAPH   = HexColor("#33384A")
EMERALD = HexColor("#1C7A57")
TAUPE   = HexColor("#7C6F5E")

W, H = 1600, 1200
CX = W / 2

def alpha(col, a):
    return Color(col.red, col.green, col.blue, alpha=a)

def fit_font(c, text, font, max_w, start, min_size=8):
    s = start
    while s > min_size and c.stringWidth(text, font, s) > max_w:
        s -= 0.5
    return s

c = canvas.Canvas("/tmp/_caio_diagram_temp.pdf", pagesize=(W, H))

# white background
c.setFillColor(white); c.rect(0, 0, W, H, stroke=0, fill=1)

# ---- header block (kicker byline + title + subtitle); this is a header, not a footer ----
c.setFillColor(SAPPH); c.setFont("Poppins-Medium", 18)
c.drawString(96, H - 86, "ART KOVAL  ·  CHIEF AI OFFICER INSIGHTS")
c.setFillColor(NAVY); c.setFont("Poppins-Bold", 46)
c.drawString(96, H - 144, "What Churns vs What Compounds")
c.setFillColor(GRAPH); c.setFont("Poppins-Light", 23)
c.drawString(96, H - 182, "Generative AI's inputs are rentable. The durable advantage is the layer you own.")

# ---- bullseye geometry ----
cy = 470
r_compute, r_models, r_data, r_core = 360, 270, 185, 110

# filled shells, largest first (rented = translucent graphite; core = emerald)
def shell(r, a):
    c.setFillColor(alpha(GRAPH, a)); c.circle(CX, cy, r, stroke=0, fill=1)
shell(r_compute, 0.10)
shell(r_models, 0.16)
shell(r_data, 0.24)
c.setFillColor(EMERALD); c.circle(CX, cy, r_core, stroke=0, fill=1)

# crisp separating rings
c.setStrokeColor(white); c.setLineWidth(3)
for r in (r_compute, r_models, r_data, r_core):
    c.circle(CX, cy, r, stroke=1, fill=0)

# ---- on-ring labels (short; navy; centered at band apex) ----
def band_label(text, r_mid, size):
    s = fit_font(c, text, "Poppins-Bold", 2 * math.sqrt(max(r_mid - 4, 1)) * 9, size)
    c.setFillColor(NAVY); c.setFont("Poppins-Bold", s)
    c.drawCentredString(CX, cy + r_mid - s * 0.36, text)
band_label("Compute", 315, 21)
band_label("Foundation models", 226, 19)
band_label("Public data", 147, 18)

# core label (ivory, stacked, three lines)
c.setFillColor(HexColor("#F0EAD6")); c.setFont("Poppins-Bold", 21)
for i, ln in enumerate(("Owned", "context &", "governance")):
    c.drawCentredString(CX, cy + 22 - i * 25, ln)

# ---- side captions: rent/churn (left) and own/compound (right) ----
# left: rented layer
lx = 150
c.setFillColor(alpha(GRAPH, 0.45)); c.circle(lx, cy + 16, 9, stroke=0, fill=1)
c.setFillColor(NAVY); c.setFont("Poppins-Bold", 22)
c.drawString(lx + 22, cy + 9, "RENTED")
c.setFillColor(GRAPH); c.setFont("Poppins-Light", 17)
c.drawString(lx + 1, cy - 26, "shared by design")
c.drawString(lx + 1, cy - 50, "interchangeable · churns")

# right: owned layer
rx = W - 150
c.setFillColor(EMERALD); c.circle(rx, cy + 16, 9, stroke=0, fill=1)
c.setFillColor(NAVY); c.setFont("Poppins-Bold", 22)
c.drawRightString(rx - 22, cy + 9, "OWNED")
c.setFillColor(GRAPH); c.setFont("Poppins-Light", 17)
c.drawRightString(rx - 1, cy - 26, "path-dependent")
c.drawRightString(rx - 1, cy - 50, "accrues · compounds")

# thin leader from owned caption toward the core (drawn line, no glyph)
c.setStrokeColor(alpha(EMERALD, 0.55)); c.setLineWidth(2); c.setDash(3, 4)
c.line(rx - 150, cy + 16, CX + r_core + 8, cy + 16)
c.setDash()

# ---- data attribution line (no footer bar) ----
c.setFillColor(TAUPE); c.setFont("Poppins-Italic", 15)
c.drawString(96, 60, "Architecture view. Layer economics per Stanford HAI AI Index 2025 and Menlo Ventures, 2025.")

c.showPage()
c.save()
import subprocess as _sp
_sp.run(["pdftoppm", "-png", "-r", "150", "-singlefile", "/tmp/_caio_diagram_temp.pdf", "caio-rented-foundations-diagram-1"], check=True)
print("rendered caio-rented-foundations-diagram-1.png")
