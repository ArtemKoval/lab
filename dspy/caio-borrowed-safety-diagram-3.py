"""CAIO 'Borrowed Safety' — Diagram 3: The Continuous Assurance Loop.
1600x1200, white ground, no footer. Five-node closed process wheel drawn
clockwise; the final node returns to the first, forming a loop."""
import math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FB = "/usr/share/fonts/truetype/google-fonts/"
for nm, fn in [("Poppins", "Poppins-Regular.ttf"), ("Poppins-Bold", "Poppins-Bold.ttf"),
               ("Poppins-Medium", "Poppins-Medium.ttf"), ("Poppins-Light", "Poppins-Light.ttf"),
               ("Poppins-Italic", "Poppins-Italic.ttf")]:
    pdfmetrics.registerFont(TTFont(nm, FB + fn))

NAVY = HexColor("#1E2A4A"); SAPPHIRE = HexColor("#1A3A6B"); GRAPHITE = HexColor("#3A3A3A")
IVORY = HexColor("#F0EAD6"); OCHRE = HexColor("#C49A2A"); EMERALD = HexColor("#1A5C3A")
BURGUNDY = HexColor("#6B1C2A"); AMETHYST = HexColor("#5A2D6A"); TAUPE = HexColor("#8A7B6B")

W, H = 1600, 1200
CX = W / 2


def align_for(cos_v):
    if cos_v > 0.3:
        return "L"
    if cos_v < -0.3:
        return "R"
    return "C"


def draw_label(c, x, y, text, font, size, color, cos_v, leading=None):
    leading = leading or size * 1.15
    c.setFont(font, size); c.setFillColor(color)
    a = align_for(cos_v)
    lines = text.split("\n")
    yy = y + (len(lines) - 1) * leading / 2.0
    for ln in lines:
        if a == "L":
            c.drawString(x, yy, ln)
        elif a == "R":
            c.drawRightString(x, yy, ln)
        else:
            c.drawCentredString(x, yy, ln)
        yy -= leading


def arrowhead(c, x, y, dirx, diry, size, color):
    ang = math.atan2(diry, dirx)
    l = ang + math.radians(143); r = ang - math.radians(143)
    p = c.beginPath()
    p.moveTo(x, y)
    p.lineTo(x + size * math.cos(l), y + size * math.sin(l))
    p.lineTo(x + size * math.cos(r), y + size * math.sin(r))
    p.close()
    c.setFillColor(color); c.drawPath(p, fill=1, stroke=0)


def process_wheel(c, cx, cy, orbit_r, node_r, hub_r, nodes, hub_text,
                  label_size=20, num_size=42, hub_size=20):
    """nodes: list of (angle_deg, fill_color, number_str, label_str). Drawn
    clockwise. Draw order: connector arcs, then nodes, then arrowheads, hub."""
    gap = math.degrees(math.atan2(node_r * 1.18, orbit_r))
    c.setStrokeColor(TAUPE); c.setLineWidth(8); c.setLineCap(1)
    seg_ends = []
    n = len(nodes)
    for i in range(n):
        a0 = nodes[i][0]; a1 = nodes[(i + 1) % n][0]
        s = a0 - gap
        e = a1 + gap
        ext = e - s
        while ext > 0:
            ext -= 360
        p = c.beginPath()
        p.arc(cx - orbit_r, cy - orbit_r, cx + orbit_r, cy + orbit_r, s, ext)
        c.drawPath(p, fill=0, stroke=1)
        seg_ends.append(e)
    c.setLineCap(0)
    for ang, col, num, lab in nodes:
        rad = math.radians(ang)
        nx = cx + orbit_r * math.cos(rad); ny = cy + orbit_r * math.sin(rad)
        c.setFillColor(col); c.circle(nx, ny, node_r, fill=1, stroke=0)
        c.setFillColor(IVORY); c.setFont("Poppins-Bold", num_size)
        c.drawCentredString(nx, ny - num_size * 0.35, num)
        lr = orbit_r + node_r + 32
        lx = cx + lr * math.cos(rad); ly = cy + lr * math.sin(rad)
        draw_label(c, lx, ly - label_size * 0.35, lab, "Poppins-Medium",
                   label_size, NAVY, math.cos(rad))
    for e in seg_ends:
        rad = math.radians(e)
        ax = cx + orbit_r * math.cos(rad); ay = cy + orbit_r * math.sin(rad)
        arrowhead(c, ax, ay, math.sin(rad), -math.cos(rad), 20, NAVY)
    c.setFillColor(NAVY); c.circle(cx, cy, hub_r, fill=1, stroke=0)
    c.setFillColor(IVORY); c.setFont("Poppins-Medium", hub_size)
    hl = hub_text.split("\n")
    yy = cy + (len(hl) - 1) * (hub_size * 1.12) / 2.0 - hub_size * 0.35
    for ln in hl:
        c.drawCentredString(cx, yy, ln); yy -= hub_size * 1.12


def build():
    c = canvas.Canvas("caio-borrowed-safety-diagram-3.pdf", pagesize=(W, H))
    c.setFillColor(white); c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(NAVY); c.setFont("Poppins-Bold", 32)
    c.drawCentredString(CX, 1140, "The Continuous Assurance Loop")
    c.setFillColor(GRAPHITE); c.setFont("Poppins-Light", 17)
    c.drawCentredString(CX, 1102,
                        "Safety is a state you maintain — not a property you buy once.")

    nodes = [
        (90, NAVY, "1", "Baseline"),
        (18, SAPPHIRE, "2", "Customize"),
        (-54, EMERALD, "3", "Re-evaluate"),
        (-126, BURGUNDY, "4", "Red-team"),
        (162, AMETHYST, "5", "Monitor &\nre-baseline"),
    ]
    process_wheel(c, CX, 540, 310, 92, 70, nodes, "Continuous\nAssurance")

    c.setFillColor(GRAPHITE); c.setFont("Poppins-Light", 20)
    c.drawCentredString(CX, 92,
                        "Every customization restarts the loop. The model changes; the discipline does not.")
    c.showPage(); c.save()
    print("diagram-3 built")


if __name__ == "__main__":
    build()
