"""
Feature Store Architecture in the MLOps Pipeline
Composite circular diagram: outer pipeline ring + inner feature store hub
"""
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import math

# Register Poppins
FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
pdfmetrics.registerFont(TTFont("Poppins", f"{FONT_DIR}/Poppins-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Bold", f"{FONT_DIR}/Poppins-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Medium", f"{FONT_DIR}/Poppins-Medium.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Light", f"{FONT_DIR}/Poppins-Light.ttf"))

# Palette
NAVY    = HexColor("#1E2A4A")
IVORY   = HexColor("#F0EAD6")
OCHRE   = HexColor("#C49A2A")
BURGUNDY = HexColor("#7A1F2B")
SAPPHIRE = HexColor("#1B4B7A")
EMERALD  = HexColor("#1F5C3A")
AMETHYST = HexColor("#5A3A7A")
TAUPE    = HexColor("#7A6F5A")
WHITE    = HexColor("#FFFFFF")

# Canvas
W, H = 1600, 1200
CX, CY = 800, 620  # main composition center (offset down for title)

def polar(cx, cy, r, deg):
    """Math angle: 0=right, 90=up, 180=left, 270=down."""
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)

def arrow_head(c, x1, y1, x2, y2, size=14, color=NAVY):
    """Draw a small triangular arrowhead at (x2,y2) pointing from (x1,y1)."""
    a = math.atan2(y2 - y1, x2 - x1)
    p = c.beginPath()
    p.moveTo(x2, y2)
    p.lineTo(x2 - size * math.cos(a - math.radians(25)),
             y2 - size * math.sin(a - math.radians(25)))
    p.lineTo(x2 - size * math.cos(a + math.radians(25)),
             y2 - size * math.sin(a + math.radians(25)))
    p.close()
    c.setFillColor(color)
    c.setStrokeColor(color)
    c.drawPath(p, fill=1, stroke=0)

def edge_point(cx, cy, r, target_x, target_y):
    """Return point on circle edge facing target."""
    a = math.atan2(target_y - cy, target_x - cx)
    return cx + r * math.cos(a), cy + r * math.sin(a)

# Output
OUT_PDF = "/home/claude/caio-feature-store-architecture-diagram.pdf"
c = canvas.Canvas(OUT_PDF, pagesize=(W, H))

# White background
c.setFillColor(WHITE)
c.rect(0, 0, W, H, fill=1, stroke=0)

# ---- Title ----
c.setFillColor(NAVY)
c.setFont("Poppins-Bold", 28)
c.drawCentredString(W / 2, H - 30, "Feature Store Architecture in the MLOps Pipeline")
c.setFont("Poppins-Light", 14)
c.setFillColor(TAUPE)
c.drawCentredString(W / 2, H - 55, "Data collection and preparation expanded into its feature store internals")

# ============================================================
# OUTER PIPELINE RING (6 stages)
# ============================================================
R_PIPELINE = 430
PIPE_NODE_R = 65
pipeline_stages = [
    ("Data\nPreparation", 90),
    ("Data\nVersioning", 30),
    ("Model\nTraining", 330),
    ("Model\nEvaluation", 270),
    ("Model\nValidation", 210),
    ("Model\nDeployment", 150),
]

# Curved arrows between consecutive pipeline nodes (clockwise)
c.setStrokeColor(TAUPE)
c.setLineWidth(2.5)
for i in range(len(pipeline_stages)):
    _, a1 = pipeline_stages[i]
    _, a2 = pipeline_stages[(i + 1) % len(pipeline_stages)]
    # Compute arc between edges of nodes
    ang_offset = math.degrees(PIPE_NODE_R / R_PIPELINE) * 0.95
    start_a = a1 - ang_offset
    end_a = a2 + ang_offset
    # Normalize for clockwise sweep: clockwise means decreasing angle.
    # If end_a >= start_a we'd be going counter-clockwise the long way,
    # so subtract 360 from end_a to wrap correctly.
    if end_a >= start_a:
        end_a -= 360
    # Sample points along arc
    steps = 24
    pts = []
    for s in range(steps + 1):
        t = s / steps
        a = start_a + (end_a - start_a) * t
        pts.append(polar(CX, CY, R_PIPELINE, a))
    # Draw polyline
    p = c.beginPath()
    p.moveTo(*pts[0])
    for pt in pts[1:]:
        p.lineTo(*pt)
    c.drawPath(p, stroke=1, fill=0)
    # Arrowhead at end
    arrow_head(c, pts[-2][0], pts[-2][1], pts[-1][0], pts[-1][1], size=14, color=TAUPE)

# Draw pipeline nodes
for i, (label, ang) in enumerate(pipeline_stages):
    x, y = polar(CX, CY, R_PIPELINE, ang)
    # Filled amethyst circle
    c.setFillColor(AMETHYST)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2)
    c.circle(x, y, PIPE_NODE_R, stroke=1, fill=1)
    # Stage number in small circle
    c.setFillColor(IVORY)
    c.circle(x, y + PIPE_NODE_R - 22, 16, stroke=0, fill=1)
    c.setFillColor(AMETHYST)
    c.setFont("Poppins-Bold", 16)
    c.drawCentredString(x, y + PIPE_NODE_R - 27, str(i + 1))
    # Label (two lines)
    c.setFillColor(IVORY)
    c.setFont("Poppins-Bold", 13)
    lines = label.split("\n")
    for j, line in enumerate(lines):
        c.drawCentredString(x, y - 4 - j * 16, line)

# Pipeline ring caption
c.setFillColor(AMETHYST)
c.setFont("Poppins-Bold", 14)
c.drawString(60, 1050, "AUTOMATED MLOPS PIPELINE")
c.setFillColor(TAUPE)
c.setFont("Poppins", 11)
c.drawString(60, 1030, "Six stages flowing clockwise from data preparation to deployment")

# ============================================================
# ZOOM-IN INDICATOR
# Dashed line from stage 1 (Data Prep, top) down toward hub
# ============================================================
stage1_x, stage1_y = polar(CX, CY, R_PIPELINE, 90)
HUB_R = 175
c.setStrokeColor(TAUPE)
c.setDash(6, 6)
c.setLineWidth(2)
c.line(stage1_x, stage1_y - PIPE_NODE_R, CX, CY + HUB_R)
c.setDash()  # reset to solid

# Zoom label along the dashed line
c.setFillColor(TAUPE)
c.setFont("Poppins", 10)
c.saveState()
c.translate(CX + 12, (stage1_y - PIPE_NODE_R + CY + HUB_R) / 2)
c.drawString(0, 0, "expanded view")
c.restoreState()

# ============================================================
# I/O NODES (mid-orbit)
# ============================================================
R_IO = 330
IO_NODE_R = 50

io_nodes = [
    ("Batch\nSource",      160, BURGUNDY, "in"),
    ("Streaming\nSource",  200, BURGUNDY, "in"),
    ("Offline\nFeatures",   20, EMERALD,  "out"),
    ("Online\nFeatures",   340, EMERALD,  "out"),
]

# Data Transform node (between inputs and hub, on the left side)
TRANS_X, TRANS_Y = polar(CX, CY, 230, 180)
TRANS_R = 55

# Inputs to data transform
for label, ang, color, kind in io_nodes:
    if kind != "in":
        continue
    nx, ny = polar(CX, CY, R_IO, ang)
    sx, sy = edge_point(nx, ny, IO_NODE_R, TRANS_X, TRANS_Y)
    ex, ey = edge_point(TRANS_X, TRANS_Y, TRANS_R, nx, ny)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2.5)
    c.line(sx, sy, ex, ey)
    arrow_head(c, sx, sy, ex, ey, size=12, color=NAVY)

# Data transform to hub
sx, sy = edge_point(TRANS_X, TRANS_Y, TRANS_R, CX, CY)
ex, ey = edge_point(CX, CY, HUB_R, TRANS_X, TRANS_Y)
c.setStrokeColor(NAVY)
c.setLineWidth(2.5)
c.line(sx, sy, ex, ey)
arrow_head(c, sx, sy, ex, ey, size=12, color=NAVY)

# Hub to outputs
for label, ang, color, kind in io_nodes:
    if kind != "out":
        continue
    nx, ny = polar(CX, CY, R_IO, ang)
    sx, sy = edge_point(CX, CY, HUB_R, nx, ny)
    ex, ey = edge_point(nx, ny, IO_NODE_R, CX, CY)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2.5)
    c.line(sx, sy, ex, ey)
    arrow_head(c, sx, sy, ex, ey, size=12, color=NAVY)

# Data Transform node (ochre)
c.setFillColor(OCHRE)
c.setStrokeColor(NAVY)
c.setLineWidth(2)
c.circle(TRANS_X, TRANS_Y, TRANS_R, stroke=1, fill=1)
c.setFillColor(NAVY)
c.setFont("Poppins-Bold", 11)
c.drawCentredString(TRANS_X, TRANS_Y + 4, "Data")
c.drawCentredString(TRANS_X, TRANS_Y - 10, "Transform")

# I/O nodes
for label, ang, color, kind in io_nodes:
    nx, ny = polar(CX, CY, R_IO, ang)
    c.setFillColor(color)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2)
    c.circle(nx, ny, IO_NODE_R, stroke=1, fill=1)
    c.setFillColor(IVORY)
    c.setFont("Poppins-Bold", 11)
    lines = label.split("\n")
    for j, line in enumerate(lines):
        c.drawCentredString(nx, ny + 4 - j * 14, line)

# ============================================================
# CENTER HUB: FEATURE STORE
# ============================================================
c.setFillColor(NAVY)
c.setStrokeColor(NAVY)
c.setLineWidth(2)
c.circle(CX, CY, HUB_R, stroke=1, fill=1)

c.setFillColor(IVORY)
c.setFont("Poppins-Bold", 16)
c.drawCentredString(CX, CY + HUB_R - 28, "FEATURE STORE")

# Three component circles inside the hub
COMP_R = 42
comp_positions = [
    ("Feature\nServer",   CX,         CY + 40),
    ("Feature\nRegistry", CX - 58,    CY - 55),
    ("Feature\nStorage",  CX + 58,    CY - 55),
]
for label, x, y in comp_positions:
    c.setFillColor(SAPPHIRE)
    c.setStrokeColor(IVORY)
    c.setLineWidth(1.5)
    c.circle(x, y, COMP_R, stroke=1, fill=1)
    c.setFillColor(IVORY)
    c.setFont("Poppins-Bold", 9.5)
    lines = label.split("\n")
    for j, line in enumerate(lines):
        c.drawCentredString(x, y + 3 - j * 11, line)

# Side annotations
c.setFillColor(BURGUNDY)
c.setFont("Poppins-Bold", 14)
c.drawString(60, 720, "INPUTS")
c.setFillColor(TAUPE)
c.setFont("Poppins", 10)
c.drawString(60, 702, "Batch and streaming feeds")

c.setFillColor(EMERALD)
c.setFont("Poppins-Bold", 14)
c.drawRightString(W - 60, 720, "OUTPUTS")
c.setFillColor(TAUPE)
c.setFont("Poppins", 10)
c.drawRightString(W - 60, 702, "Offline training, online inference")

# Legend strip
legend_y = 90
legend_items = [
    (AMETHYST,  "Pipeline stage"),
    (BURGUNDY,  "Data input"),
    (OCHRE,     "Transformation"),
    (NAVY,      "Feature store"),
    (SAPPHIRE,  "Store component"),
    (EMERALD,   "Feature output"),
]
total_w = 1400
item_w = total_w / len(legend_items)
start_x = (W - total_w) / 2
for i, (col, lab) in enumerate(legend_items):
    cx = start_x + i * item_w + 20
    c.setFillColor(col)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1)
    c.circle(cx, legend_y, 11, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Poppins-Medium", 11)
    c.drawString(cx + 22, legend_y - 4, lab)

# Footer
c.setFillColor(TAUPE)
c.setFont("Poppins-Light", 9)
c.drawCentredString(W / 2, 38, "Art Koval \u2014 Chief AI Officer Insights")

c.save()
print(f"Saved {OUT_PDF}")
