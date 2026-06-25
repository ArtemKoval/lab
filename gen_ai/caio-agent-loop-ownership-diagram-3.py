#!/usr/bin/env python3
"""
CAIO Diagram: Rented Core, Owned Loop
Topic: agent-loop-ownership
Type: Concentric rings (onion) — model rented, loop and surfaces owned
Output: caio-agent-loop-ownership-diagram-3.png
"""

import math
import subprocess
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

# --- Palette (CAIO standard) ---
NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
MUSTARD = HexColor('#C4952A')
TAUPE = HexColor('#8A7B6B')
UMBER = HexColor('#6B4226')
WHITE = HexColor('#FFFFFF')

# --- Font Registration ---
pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas Setup ---
W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-agent-loop-ownership-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'

CX, CY = 800, 548
R_OUTER = 450
R_MID = 320
R_INNER = 165


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    c.setFillColor(WHITE)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title + subtitle
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 44)
    c.drawCentredString(CX, 1138, 'Rented Core, Owned Loop')
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 23)
    c.drawCentredString(CX, 1094, 'The model is a commodity you rent \u2014 everything wrapped around it is the asset you own')

    # Concentric disks: draw largest first, smaller on top
    c.setFillColor(SAPPHIRE)
    c.circle(CX, CY, R_OUTER, stroke=0, fill=1)
    c.setFillColor(EMERALD)
    c.circle(CX, CY, R_MID, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.circle(CX, CY, R_INNER, stroke=0, fill=1)

    # Thin separator rings (ivory) for crispness
    c.setStrokeColor(IVORY)
    c.setLineWidth(2.2)
    c.circle(CX, CY, R_MID, stroke=1, fill=0)
    c.circle(CX, CY, R_INNER, stroke=1, fill=0)

    # --- Outer ring (Sapphire) label in top arc ---
    c.setFillColor(IVORY)
    c.setFont('Poppins-Medium', 19)
    c.drawCentredString(CX, 935, 'TOOLS  \u00b7  OBSERVATION  \u00b7  EVALUATION  \u00b7  GOVERNANCE')
    c.setFont('Poppins-Bold', 21)
    c.drawCentredString(CX, 899, 'OWNED')

    # outer ring bottom arc descriptor
    c.setFillColor(IVORY)
    c.setFont('Poppins-Light', 18)
    c.drawCentredString(CX, 168, 'the integration, the logs, the scorecard, the controls')

    # --- Middle ring (Emerald) label in top arc ---
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 31)
    c.drawCentredString(CX, 798, 'THE LOOP')
    c.setFont('Poppins-Medium', 18)
    c.drawCentredString(CX, 766, 'reflection  \u00b7  retry  \u00b7  orchestration')
    c.setFont('Poppins-Bold', 19)
    c.drawCentredString(CX, 732, 'OWNED')

    # --- Inner disk (Navy) center label ---
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 35)
    c.drawCentredString(CX, 576, 'MODEL')
    c.setFont('Poppins-Light', 18)
    c.drawCentredString(CX, 546, 'reasoning + planning')
    c.setFillColor(MUSTARD)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(CX, 508, 'RENTED')

    # Bottom caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 25)
    c.drawCentredString(CX, 52, 'Rent the core. Own the loop.')

    c.showPage()
    c.save()

    subprocess.run(
        ['pdftoppm', '-png', '-r', '150', '-singlefile', OUTPUT_PDF, OUTPUT_PNG[:-4]],
        check=True,
    )
    print('Rendered:', OUTPUT_PNG)


if __name__ == '__main__':
    main()
