#!/usr/bin/env python3
"""
CAIO Diagram: SLM vs LLM Capability Profile
Topic: slm-aws-business-case
Type: Radar overlay (two polygons on 8-axis radial grid)
Output: caio-slm-aws-business-case-diagram-3.png

Multi-dimensional comparison: a domain-tuned 7B SLM on AWS vs a 175B+
generalist LLM via API, scored across eight enterprise dimensions.
"""

import math
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

NAVY = HexColor('#1E2A4A')
SAPPHIRE = HexColor('#1A3A6B')
GRAPHITE = HexColor('#3A3A3A')
IVORY = HexColor('#F0EAD6')
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
TAUPE = HexColor('#8A7B6B')

pdfmetrics.registerFont(TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont('Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

W, H = 1600, 1200
OUTPUT_PNG = '/home/claude/work/caio-slm-aws-business-case-diagram-3.png'
OUTPUT_PDF = '/tmp/_diagram3_temp.pdf'


def draw_diagram(c):
    c.setFillColor(HexColor('#FFFFFF'))
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, H - 80, "Specialization beats scale on narrow tasks")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 18)
    c.drawCentredString(W / 2, H - 115,
                        "A domain-tuned 7B SLM on AWS vs a 175B+ generalist API across eight enterprise dimensions")

    # Radar chart center
    cx, cy = 540, 570
    max_r = 270

    # Dimensions (clockwise from 12 o'clock)
    dimensions = [
        "Cost per\ninference",
        "Latency",
        "Data\nsovereignty",
        "Compliance\nfit",
        "Domain\naccuracy",
        "Time to\ncustomize",
        "General\nreasoning",
        "Conversational\nbreadth",
    ]
    # Scores out of 10 (higher = better)
    slm_scores = [10, 9, 10, 9, 9, 9, 5, 4]
    llm_scores = [3, 5, 3, 4, 5, 4, 9, 10]

    n = len(dimensions)

    # Background gridlines — concentric polygons (TAUPE)
    c.setStrokeColor(TAUPE)
    c.setLineWidth(1)
    for level in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(n):
            ang = math.radians(90 - i * (360 / n))
            x = cx + max_r * level * math.cos(ang)
            y = cy + max_r * level * math.sin(ang)
            pts.append((x, y))
        p = c.beginPath()
        p.moveTo(pts[0][0], pts[0][1])
        for x, y in pts[1:]:
            p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # Axis spokes
    for i in range(n):
        ang = math.radians(90 - i * (360 / n))
        c.line(cx, cy, cx + max_r * math.cos(ang), cy + max_r * math.sin(ang))

    def poly_pts(scores):
        pts = []
        for i, s in enumerate(scores):
            ang = math.radians(90 - i * (360 / n))
            r = max_r * (s / 10)
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        return pts

    # LLM polygon first (smaller, drawn underneath SLM where they overlap)
    llm_pts = poly_pts(llm_scores)
    p = c.beginPath()
    p.moveTo(llm_pts[0][0], llm_pts[0][1])
    for x, y in llm_pts[1:]:
        p.lineTo(x, y)
    p.close()
    c.setFillColor(BURGUNDY)
    c.setFillAlpha(0.35)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(3)
    c.setStrokeAlpha(1.0)
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)

    # SLM polygon on top
    slm_pts = poly_pts(slm_scores)
    p = c.beginPath()
    p.moveTo(slm_pts[0][0], slm_pts[0][1])
    for x, y in slm_pts[1:]:
        p.lineTo(x, y)
    p.close()
    c.setFillColor(EMERALD)
    c.setFillAlpha(0.40)
    c.setStrokeColor(EMERALD)
    c.setLineWidth(3)
    c.setStrokeAlpha(1.0)
    c.drawPath(p, stroke=1, fill=1)
    c.setFillAlpha(1.0)

    # Axis labels — placed outside the polygon
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 17)
    for i, dim in enumerate(dimensions):
        ang = math.radians(90 - i * (360 / n))
        lx = cx + (max_r + 50) * math.cos(ang)
        ly = cy + (max_r + 50) * math.sin(ang)
        cos_v = math.cos(ang)
        lines = dim.split('\n')
        offset = 10 * (len(lines) - 1) if len(lines) > 1 else 0
        for j, line in enumerate(lines):
            ypos = ly + offset - j * 20
            if cos_v > 0.3:
                c.drawString(lx, ypos, line)
            elif cos_v < -0.3:
                c.drawRightString(lx, ypos, line)
            else:
                c.drawCentredString(lx, ypos, line)

    # Right column: legend and verdict
    rx = 1010
    ry = 850
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 28)
    c.drawString(rx, ry, "Capability profile")
    c.setStrokeColor(OCHRE)
    c.setLineWidth(2)
    c.line(rx, ry - 12, rx + 220, ry - 12)

    # SLM legend
    c.setFillColor(EMERALD)
    c.circle(rx + 18, ry - 65, 18, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawString(rx + 50, ry - 75, "Domain SLM on AWS")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 16)
    c.drawString(rx + 50, ry - 100, "Fine-tuned 7B on SageMaker, INT8")

    # LLM legend
    c.setFillColor(BURGUNDY)
    c.circle(rx + 18, ry - 160, 18, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawString(rx + 50, ry - 170, "Frontier LLM via API")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 16)
    c.drawString(rx + 50, ry - 195, "Generalist 175B+ accessed off-cloud")

    # Verdict
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 22)
    c.drawString(rx, ry - 280, "Six of eight dimensions")
    c.drawString(rx, ry - 308, "favor the SLM.")

    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 17)
    c.drawString(rx, ry - 360, "LLMs lead on general reasoning")
    c.drawString(rx, ry - 384, "and conversational breadth.")
    c.drawString(rx, ry - 415, "Architectural conclusion:")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 17)
    c.drawString(rx, ry - 440, "SLM-default with LLM fallback.")

    # Source
    c.setFillColor(TAUPE)
    c.setFont('Poppins-Light', 13)
    c.drawCentredString(W / 2, 100,
                        "Synthesis from production benchmarks • SWE-bench 2026 • enterprise SLM deployment studies")


def main():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    draw_diagram(c)
    c.save()
    import subprocess
    subprocess.run([
        'pdftoppm', '-png', '-r', '150',
        '-singlefile', OUTPUT_PDF, OUTPUT_PNG.replace('.png', '')
    ], check=True)
    print(f"Rendered: {OUTPUT_PNG}")


if __name__ == '__main__':
    main()
