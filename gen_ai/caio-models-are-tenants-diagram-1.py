import math
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FB = "/usr/share/fonts/truetype/google-fonts/"
pdfmetrics.registerFont(TTFont("Poppins", FB + "Poppins-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Bold", FB + "Poppins-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Medium", FB + "Poppins-Medium.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Light", FB + "Poppins-Light.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Italic", FB + "Poppins-Italic.ttf"))

W, H = 1600, 1200
NAVY = HexColor("#1E2A4A")
GRAPHITE = HexColor("#3A3A3A")
WHITE = HexColor("#FFFFFF")
EMERALD = HexColor("#1A5C3A")
TEAL = HexColor("#1A7A7A")
SAPPHIRE = HexColor("#1A3A6B")
AMETHYST = HexColor("#5A2D6A")
BURGUNDY = HexColor("#6B1C2A")
TAUPE = HexColor("#8A7B6B")
DIVIDER = HexColor("#8A7B6B")

c = canvas.Canvas("caio-models-are-tenants-diagram-1.pdf", pagesize=(W, H))
c.setFillColor(WHITE)
c.rect(0, 0, W, H, fill=1, stroke=0)


def ctext(x, y, s, font, size, color):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(x, y, s)


def ltext(x, y, s, font, size, color):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawString(x, y, s)


# Title block
ctext(800, 1132, "The Sovereignty Spiral", "Poppins-Bold", 42, NAVY)
ctext(800, 1090, "Where inference runs. Control unwinds as your data moves outward.", "Poppins-Light", 22, GRAPHITE)
ctext(800, 1058, "inner: most control   \u00b7   outer: most convenience and scale", "Poppins-Medium", 16, GRAPHITE)

# Divider between spiral and legend
c.setStrokeColor(DIVIDER)
c.setLineWidth(2)
c.line(948, 230, 948, 905)

# Spiral guide curve
cx, cy = 540, 600
c.setStrokeColor(TAUPE)
c.setLineWidth(7)
pts = []
phi = -0.30
while phi <= 5.9:
    th = 2.0 - phi
    r = 60 + 62 * phi
    pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    phi += 0.04
path = c.beginPath()
path.moveTo(*pts[0])
for q in pts[1:]:
    path.lineTo(*q)
c.drawPath(path, stroke=1, fill=0)

# Core marker
c.setFillColor(NAVY)
c.circle(cx, cy, 16, fill=1, stroke=0)
ctext(cx, cy - 46, "your data", "Poppins-Italic", 15, GRAPHITE)

# Station disks along the spiral
colors = [EMERALD, TEAL, SAPPHIRE, AMETHYST, BURGUNDY]
nums = ["1", "2", "3", "4", "5"]
phis = [0.0, 1.4, 2.8, 4.2, 5.6]
for col, num, ph in zip(colors, nums, phis):
    th = 2.0 - ph
    r = 60 + 62 * ph
    x = cx + r * math.cos(th)
    y = cy + r * math.sin(th)
    c.setFillColor(col)
    c.circle(x, y, 52, fill=1, stroke=0)
    ctext(x, y - 12, num, "Poppins-Bold", 36, WHITE)

# Legend
lx = 998
rows = [
    (EMERALD, "1", "On-device", "Data never leaves the device"),
    (TEAL, "2", "On-premise", "Inside your own data center"),
    (SAPPHIRE, "3", "Private cloud", "Single tenant, your keys"),
    (AMETHYST, "4", "Dedicated managed", "Vendor-run, contractually isolated"),
    (BURGUNDY, "5", "Public endpoint", "Shared API, vendor's policy"),
]
ys = [885, 725, 565, 405, 245]
for (col, num, name, desc), y in zip(rows, ys):
    c.setFillColor(col)
    c.roundRect(lx, y - 23, 46, 46, 8, fill=1, stroke=0)
    ctext(lx + 23, y - 9, num, "Poppins-Bold", 24, WHITE)
    ltext(lx + 66, y + 5, name, "Poppins-Bold", 26, col)
    ltext(lx + 66, y - 26, desc, "Poppins", 18, GRAPHITE)


c.showPage()
c.save()
import subprocess
subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile",
                "caio-models-are-tenants-diagram-1.pdf",
                "caio-models-are-tenants-diagram-1"], check=True)
print("diagram 1 rendered: caio-models-are-tenants-diagram-1.png")
