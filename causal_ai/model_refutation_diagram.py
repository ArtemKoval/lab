#!/usr/bin/env python3
"""
CAIO Diagram: The Refutability Maturity Layers
Topic: caio-refutation-mandate
Type: Concentric Rings
Output: caio-refutation-mandate-diagram-3.png
"""

import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TAUPE = HexColor('#8A7B6B')
WHITE = HexColor('#FFFFFF')

# --- Fonts ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG_PATH = '/home/claude/caio-refutation-mandate/caio-refutation-mandate-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram_3_temp.pdf'

CX, CY = 600, 540

# Concentric rings: outermost first (weakest discipline)
# Innermost = highest maturity
RINGS = [
    {"label": "CORRELATION-ONLY",
     "desc": "Pattern matching with no causal claims. Most production AI lives here.",
     "color": TAUPE,           # outermost — weakest
     "outer_r": 420,
     "text_color": NAVY},
    {"label": "VALIDATION-ONLY",
     "desc": "Model fits historical data. The default and most common discipline.",
     "color": AMETHYST,
     "outer_r": 340,
     "text_color": IVORY},
    {"label": "REFUTATION-TESTED",
     "desc": "Explicit conditions for failure are defined and monitored.",
     "color": SAPPHIRE,
     "outer_r": 250,
     "text_color": IVORY},
    {"label": "CAUSALLY IDENTIFIED",
     "desc": "Assumptions encoded, tested, falsifiable, and continuously monitored.",
     "color": NAVY,            # innermost — strongest
     "outer_r": 150,
     "text_color": IVORY},
]


def draw_diagram(c):
    # White background
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 36)
    c.drawCentredString(W / 2, H - 80, "The Refutability Maturity Layers")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 18)
    c.drawCentredString(
        W / 2, H - 115, "Four levels of discipline — moving inward represents increasing rigor")

    # Draw rings from outermost to innermost
    for ring in RINGS:
        c.setFillColor(ring["color"])
        c.setStrokeColor(IVORY)
        c.setLineWidth(2.5)
        c.circle(CX, CY, ring["outer_r"], stroke=1, fill=1)

    # Draw labels at the TOP of each ring band (above center)
    for i, ring in enumerate(RINGS):
        # Position label inside the ring's annular band
        if i == 0:
            inner_r = RINGS[1]["outer_r"]
        elif i < len(RINGS) - 1:
            inner_r = RINGS[i + 1]["outer_r"]
        else:
            inner_r = 0

        outer_r = ring["outer_r"]
        # Label positioned in upper portion of band
        if i == len(RINGS) - 1:
            # Innermost — center label
            label_y = CY + 12
            desc_y = CY - 20
        else:
            band_mid_r = (outer_r + inner_r) / 2
            label_y = CY + band_mid_r
            desc_y = label_y - 22

        # Label
        c.setFillColor(ring["text_color"])
        c.setFont('Poppins-Bold', 18)
        c.drawCentredString(CX, label_y, ring["label"])

    # Right-side annotation panel — explain each layer
    panel_x = 1080
    panel_top = 880
    line_h = 32
    cur_y = panel_top

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawString(panel_x, cur_y, "From belief to knowledge")
    cur_y -= 36
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 13)
    c.drawString(
        panel_x, cur_y, "Each layer increases the discipline applied to AI deployments.")
    cur_y -= 36

    def wrap_text(text, max_chars):
        """Word-aware wrap. Returns list of lines."""
        words = text.split()
        lines = []
        current = ""
        for w in words:
            if len(current) + len(w) + 1 <= max_chars:
                current = (current + " " + w).strip()
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines

    for i, ring in enumerate(RINGS):
        marker_r = 14
        c.setFillColor(ring["color"])
        c.setStrokeColor(IVORY)
        c.setLineWidth(1.5)
        c.circle(panel_x + 14, cur_y - 4, marker_r, stroke=1, fill=1)

        # Layer name
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 15)
        c.drawString(panel_x + 40, cur_y, ring["label"])

        # Description with proper word wrap
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 12)
        lines = wrap_text(ring["desc"], 56)
        for li, line in enumerate(lines):
            c.drawString(panel_x + 40, cur_y - 18 - li * 16, line)

        cur_y -= 30 + len(lines) * 16 + 14

    # Outer arrow legend — increasing rigor
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 12)
    # Place rigor arrow indicator
    c.drawCentredString(
        CX, 80, "Outer ring — most common practice    |    Inner core — rare and rigorous")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    out_root = OUTPUT_PNG_PATH.replace('.png', '')
    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, out_root
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG_PATH}")


if __name__ == '__main__':
    main()
