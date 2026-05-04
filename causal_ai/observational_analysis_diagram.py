#!/usr/bin/env python3
"""
CAIO Carousel: Predictions Are Not Interventions — The Do-Operator
Topic: interventions-do-operator
Slides: 10 (Ivory background, Navy footer)
Output: caio-interventions-do-operator-carousel.pdf
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
OCHRE = HexColor('#C49A2A')
EMERALD = HexColor('#1A5C3A')
BURGUNDY = HexColor('#6B1C2A')
AMETHYST = HexColor('#5A2D6A')
TEAL = HexColor('#1A7A7A')
TAUPE = HexColor('#8A7B6B')
UMBER = HexColor('#6B4226')
MOSS = HexColor('#4A5A3A')
MUSTARD = HexColor('#C4952A')

# --- Fonts ---
pdfmetrics.registerFont(
    TTFont('Poppins', '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Bold', '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Medium', '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'))
pdfmetrics.registerFont(TTFont(
    'Poppins-Light', '/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf'))

# --- Canvas ---
W, H = 1080, 1080
TOTAL_SLIDES = 10
OUTPUT_PDF = '/home/claude/caio-interventions-do-operator-carousel.pdf'


# ============================================================
# Common chrome (background, footer, accent bar) on every slide
# ============================================================
def draw_chrome(c, slide_num, accent_color=NAVY):
    # Ivory background
    c.setFillColor(IVORY)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    # Top accent bar
    c.setFillColor(accent_color)
    c.rect(0, H - 8, W, 8, stroke=0, fill=1)

    # Footer bar (Navy, 60px high, plus 2px Ochre accent line)
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 60, stroke=0, fill=1)
    c.setFillColor(OCHRE)
    c.rect(0, 60, W, 2, stroke=0, fill=1)

    # Footer text
    c.setFillColor(IVORY)
    c.setFont('Poppins-Light', 13)
    c.drawString(36, 25, "Art Koval")
    c.drawRightString(W - 36, 25, f"{slide_num}/{TOTAL_SLIDES}")


# ============================================================
# Reusable element drawers
# ============================================================
def draw_donut(c, cx, cy, outer_r, inner_r, segments, total_override=None,
               center_label=None, center_label_color=NAVY,
               center_sub=None, center_sub_color=GRAPHITE):
    """Draw a donut on Ivory bg with segments=[(label, value, color)]."""
    total = total_override if total_override else sum(
        v for _, v, _ in segments)
    start_ang = 90
    for label, value, color in segments:
        extent = -(value / total) * 360
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.wedge(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                start_ang, extent, stroke=1, fill=1)
        start_ang += extent
    # Inner cutout — Ivory matches slide bg
    c.setFillColor(IVORY)
    c.circle(cx, cy, inner_r, stroke=0, fill=1)
    if center_label:
        c.setFillColor(center_label_color)
        c.setFont('Poppins-Bold', 56)
        c.drawCentredString(cx, cy + 4, center_label)
    if center_sub:
        c.setFillColor(center_sub_color)
        c.setFont('Poppins', 12)
        c.drawCentredString(cx, cy - 30, center_sub)


def draw_segment_external_labels(c, cx, cy, outer_r, segments, total_override=None,
                                 label_offset=44, font_size=12, sub_font_size=11):
    """Draw external labels with leader lines for donut segments."""
    total = total_override if total_override else sum(
        v for _, v, _ in segments)
    start_ang = 90
    for label, value, color in segments:
        extent = -(value / total) * 360
        mid_ang = start_ang + extent / 2
        rad = math.radians(mid_ang)
        ix = cx + (outer_r + 6) * math.cos(rad)
        iy = cy + (outer_r + 6) * math.sin(rad)
        ox = cx + (outer_r + label_offset) * math.cos(rad)
        oy = cy + (outer_r + label_offset) * math.sin(rad)
        c.setStrokeColor(color)
        c.setLineWidth(1.2)
        c.line(ix, iy, ox, oy)
        is_right = math.cos(rad) >= 0
        text_x = ox + (8 if is_right else -8)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', font_size)
        if is_right:
            c.drawString(text_x, oy + 2, label)
            c.setFillColor(GRAPHITE)
            c.setFont('Poppins', sub_font_size)
            c.drawString(text_x, oy - 12, f"{round((value/total)*100)}%")
        else:
            c.drawRightString(text_x, oy + 2, label)
            c.setFillColor(GRAPHITE)
            c.setFont('Poppins', sub_font_size)
            c.drawRightString(text_x, oy - 12, f"{round((value/total)*100)}%")
        start_ang += extent


def draw_stat_callout_ring(c, cx, cy, r, big_text, big_color, label_text, label_color=NAVY):
    """Navy-filled ring with large stat number + label below."""
    c.setFillColor(NAVY)
    c.setStrokeColor(OCHRE)
    c.setLineWidth(3)
    c.circle(cx, cy, r, stroke=1, fill=1)
    # Big number — Mustard or Ochre on Navy passes AA at large sizes
    c.setFillColor(big_color)
    c.setFont('Poppins-Bold', 38)
    c.drawCentredString(cx, cy - 4, big_text)
    # Label below ring on Ivory bg
    c.setFillColor(label_color)
    c.setFont('Poppins-Medium', 13)
    # Word-wrap for label if long
    words = label_text.split('|')
    if len(words) == 1:
        c.drawCentredString(cx, cy - r - 26, label_text)
    else:
        c.drawCentredString(cx, cy - r - 22, words[0].strip())
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 11)
        c.drawCentredString(cx, cy - r - 40, words[1].strip())


# ============================================================
# SLIDE 1 — Cover
# ============================================================
def slide_1_cover(c):
    draw_chrome(c, 1, accent_color=NAVY)

    # Top accent stripe (12px for cover slide)
    c.setFillColor(BURGUNDY)
    c.rect(0, H - 12, W, 12, stroke=0, fill=1)

    # Title
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 44)
    c.drawCentredString(W / 2, 920, "Predictions Are Not")
    c.drawCentredString(W / 2, 870, "Interventions")

    # Subtitle
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Medium', 20)
    c.drawCentredString(W / 2, 815, "The Do-Operator and the Hidden Cost")
    c.drawCentredString(W / 2, 788, "of Confusing Them")

    # Three stat callout rings
    ring_y = 470
    ring_r = 95
    rings_cx = [240, 540, 840]

    draw_stat_callout_ring(c, rings_cx[0], ring_y, ring_r,
                           "$81B",
                           MUSTARD,
                           "Causal AI market | Fortune Business Insights, 2025")

    draw_stat_callout_ring(c, rings_cx[1], ring_y, ring_r,
                           "25,000",
                           MUSTARD,
                           "A/B tests Booking.com runs | per year (~70 per day)")

    draw_stat_callout_ring(c, rings_cx[2], ring_y, ring_r,
                           "1/3",
                           MUSTARD,
                           "of MS experiments | yield positive results")

    # Bottom positioning text
    c.setFillColor(NAVY)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, 200, "Why every CAIO needs to read deployed models as either")
    c.drawCentredString(
        W / 2, 175, "decision engines or prediction engines — and govern each accordingly.")

    # Author tag
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Medium', 14)
    c.drawCentredString(W / 2, 110, "Art Koval / Chief AI Officer Insights")


# ============================================================
# SLIDE 2 — Hero donut: the sign flip
# ============================================================
def slide_2_sign_flip(c):
    draw_chrome(c, 2)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 980, "Same Data. Opposite Sign.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 16)
    c.drawCentredString(
        W / 2, 945, "What observational analysis cannot tell you about the action you are about to take")

    # Single hero donut showing the breakdown of the apparent +$39 signal
    cx, cy = W / 2, 540
    outer_r = 220
    inner_r = 130

    segments = [
        ("Hidden common cause", 60, SAPPHIRE),
        ("Genuine direct effect", 25, EMERALD),
        ("Other confounders", 15, AMETHYST),
    ]
    draw_donut(c, cx, cy, outer_r, inner_r, segments)
    # Stacked center: observational reading on top, true causal effect below
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawCentredString(cx, cy + 58, "observational reading")
    c.setFillColor(EMERALD)
    c.setFont('Poppins-Bold', 44)
    c.drawCentredString(cx, cy + 22, "+$39")
    # Divider rule between the two readings
    c.setStrokeColor(GRAPHITE)
    c.setLineWidth(0.8)
    c.line(cx - 50, cy - 2, cx + 50, cy - 2)
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawCentredString(cx, cy - 22, "true causal effect")
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 44)
    c.drawCentredString(cx, cy - 60, "−$38")

    draw_segment_external_labels(c, cx, cy, outer_r, segments,
                                 label_offset=58, font_size=12, sub_font_size=11)

    # Caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 235,
                        "The signal that drove the decision was 60% common-cause artifact.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(W / 2, 210,
                        "When the company intervened to push everyone into high engagement,")
    c.drawCentredString(W / 2, 192,
                        "the membership-driven spending pattern broke. The true effect emerged. Negative.")
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 130,
                        "Illustrative — figures from canonical observational vs. experimental comparison in causal inference literature")


# ============================================================
# SLIDE 3 — Concentric rings: Two kinds of ML systems
# ============================================================
def slide_3_two_kinds(c):
    draw_chrome(c, 3)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 980, "Two Kinds of ML Systems")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W / 2, 945, "Whether the model's outputs reshape its own inputs is a structural distinction, not a stylistic one")

    # Concentric rings — outer "predict the world", middle "act on the prediction", inner "decision engine"
    cx, cy = W / 2 - 30, 540
    rings = [
        (260, TAUPE,    "Pure prediction",
                        "outputs do not affect future inputs",
                        "weather, geology, astronomy"),
        (200, SAPPHIRE, "Predictive ML in production",
                        "outputs inform decisions but have no formal account of the intervention",
                        "where enterprise deployments tend to live"),
        (140, BURGUNDY, "Decision engines",
                        "outputs are interventions that reshape future training data",
                        "credit risk, fraud, recommendations, pricing"),
        (80,  NAVY,     "Causal AI",
                        "outputs reasoned about as do-operations",
                        "the only category that survives intact"),
    ]

    for (r, color, _, _, _) in rings:
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.circle(cx, cy, r, stroke=1, fill=1)

    # Center label
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 14)
    c.drawCentredString(cx, cy + 8, "Causal AI")
    c.setFont('Poppins', 10)
    c.drawCentredString(cx, cy - 8, "do-operations")

    # Side legend with descriptions matched to rings
    legend_x = cx + 290
    legend_y_top = 760
    legend_step = 110
    legend_colors = [TAUPE, SAPPHIRE, BURGUNDY, NAVY]
    legend_labels = [
        ("Pure prediction",    "outputs do not affect inputs"),
        ("Predictive ML",      "no formal intervention account"),
        ("Decision engines",   "outputs reshape future data"),
        ("Causal AI",          "do-operations are explicit"),
    ]
    for i, ((title, sub), color) in enumerate(zip(legend_labels, legend_colors)):
        ly = legend_y_top - i * legend_step
        # Color swatch circle
        c.setFillColor(color)
        c.setStrokeColor(NAVY)
        c.setLineWidth(1.5)
        c.circle(legend_x, ly, 14, stroke=1, fill=1)
        # Title + sub
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 14)
        c.drawString(legend_x + 28, ly + 4, title)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 11)
        c.drawString(legend_x + 28, ly - 12, sub)

    # Caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 200,
                        "Enterprise AI mostly lives in layer 2 or 3. Enterprise governance mostly treats it as layer 1.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(W / 2, 175,
                        "The mismatch is the source of an entire class of silent reliability failures in production.")


# ============================================================
# SLIDE 4 — Hub-and-spoke: What makes a decision a decision
# ============================================================
def slide_4_hub_spoke(c):
    draw_chrome(c, 4)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 980, "What Makes a Decision a Decision")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W / 2, 945, "An ideal intervention has three formal properties — and most enterprise ML quietly violates all three")

    cx, cy = W / 2, 530
    hub_r = 110
    orbit_r = 245
    sat_r = 78

    # Three satellites
    satellites = [
        ("Targeted",
         "Acts on a specific\nvariable in the DGP",
         SAPPHIRE),
        ("Set",
         "Forces the variable\nto a fixed value",
         BURGUNDY),
        ("Severed",
         "Breaks the variable's\ndependence on its causes",
         EMERALD),
    ]

    n = len(satellites)
    for i, (title, desc, color) in enumerate(satellites):
        # Three positions at top, lower-left, lower-right (120° apart starting from top)
        ang = math.radians(90 - i * 120)
        x = cx + orbit_r * math.cos(ang)
        y = cy + orbit_r * math.sin(ang)
        # Connector
        c.setStrokeColor(TAUPE)
        c.setLineWidth(2)
        # Connector goes from edge of hub to edge of satellite
        edge_hub_x = cx + hub_r * math.cos(ang)
        edge_hub_y = cy + hub_r * math.sin(ang)
        edge_sat_x = x - sat_r * math.cos(ang)
        edge_sat_y = y - sat_r * math.sin(ang)
        c.line(edge_hub_x, edge_hub_y, edge_sat_x, edge_sat_y)
        # Satellite
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2)
        c.circle(x, y, sat_r, stroke=1, fill=1)
        # Title
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 18)
        c.drawCentredString(x, y + 4, title)
        # Description: above for top satellite (away from hub), below for the rest
        c.setFillColor(NAVY)
        c.setFont('Poppins-Medium', 12)
        lines = desc.split('\n')
        if i == 0:  # top satellite: description above
            for j, ln in enumerate(lines):
                c.drawCentredString(x, y + sat_r + 22 +
                                    (len(lines) - 1 - j) * 16, ln)
        else:
            for j, ln in enumerate(lines):
                c.drawCentredString(x, y - sat_r - 22 - j * 16, ln)

    # Hub
    c.setFillColor(NAVY)
    c.setStrokeColor(OCHRE)
    c.setLineWidth(3)
    c.circle(cx, cy, hub_r, stroke=1, fill=1)
    c.setFillColor(IVORY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx, cy + 14, "Ideal")
    c.drawCentredString(cx, cy - 12, "Intervention")
    c.setFillColor(MUSTARD)
    c.setFont('Poppins', 12)
    c.drawCentredString(cx, cy - 38, "do(X = x)")

    # Caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 195,
                        "If your model can't say which variable it targets and what it sets it to,")
    c.drawCentredString(W / 2, 175,
                        "the model is producing a forecast — not a decision.")


# ============================================================
# SLIDE 5 — Dual donut comparison: P(Y|X) vs P(Y|do(X))
# ============================================================
def slide_5_dual_donut(c):
    draw_chrome(c, 5)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 980, "Two Different Questions")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W / 2, 945, "The do-operator is what separates the slice of the existing world from the world the intervention creates")

    cy = 540
    outer_r = 145
    inner_r = 85

    # Left: P(Y | X)
    cx_left = 300
    left_segs = [
        ("Common-cause",  55, SAPPHIRE),
        ("Direct path",   30, EMERALD),
        ("Other paths",   15, AMETHYST),
    ]
    draw_donut(c, cx_left, cy, outer_r, inner_r, left_segs)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 26)
    c.drawCentredString(cx_left, cy - 8, "P(Y|X)")
    # Captions
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx_left, 760, "Conditional probability")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(cx_left, 735, "What does Y look like in")
    c.drawCentredString(cx_left, 718, "the slice where X happened")
    # Below
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(cx_left, 360, "Mixes every path")
    c.drawCentredString(cx_left, 342, "between X and Y")
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx_left, 318, "Observational. Symmetric.")

    # Right: P(Y | do(X))
    cx_right = 780
    right_segs = [
        ("Direct causal effect", 100, BURGUNDY),
    ]
    draw_donut(c, cx_right, cy, outer_r, inner_r, right_segs)
    c.setFillColor(IVORY)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 22)
    c.drawCentredString(cx_right, cy - 8, "P(Y|do(X))")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 18)
    c.drawCentredString(cx_right, 760, "Interventional probability")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(cx_right, 735, "What does Y look like if")
    c.drawCentredString(cx_right, 718, "we force X to take a value")
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(cx_right, 360, "Severs every path")
    c.drawCentredString(cx_right, 342, "into X — keeps the causal one")
    c.setFillColor(EMERALD)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(cx_right, 318, "Decision-grade. Asymmetric.")

    # Center separator label
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Bold', 24)
    c.drawCentredString(W / 2, cy + 4, "≠")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 11)
    c.drawCentredString(W / 2, cy - 18, "different by")
    c.drawCentredString(W / 2, cy - 30, "construction")

    # Bottom insight
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 230,
                        "These are two different mathematical objects.")
    c.drawCentredString(W / 2, 208,
                        "In the presence of common causes, they differ in magnitude — and in sign.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(W / 2, 175,
                        "Enterprise dashboards routinely report P(Y|X) and let leadership read it as P(Y|do(X)).")
    c.drawCentredString(W / 2, 158,
                        "The do-notation is the formal device that makes the substitution visible.")


# ============================================================
# SLIDE 6 — Three stat callout rings: cost of randomization
# ============================================================
def slide_6_experiment_cost(c):
    draw_chrome(c, 6)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 980, "The Price of Knowing for Sure")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W / 2, 945, "Randomization is the gold standard precisely because it is robust to a wrong DAG. It is not free.")

    # Three callout rings — each tells one part of the experimentation cost story
    ring_y = 580
    ring_r = 110
    rings_cx = [220, 540, 860]

    # Ring 1: Booking.com 25,000 tests
    draw_stat_callout_ring(c, rings_cx[0], ring_y, ring_r,
                           "25,000",
                           MUSTARD,
                           "A/B tests at Booking.com per year")

    # Ring 2: 1 in 3 experiments yields neutral, 1 in 3 negative
    draw_stat_callout_ring(c, rings_cx[1], ring_y, ring_r,
                           "2 in 3",
                           MUSTARD,
                           "Microsoft experiments yield neutral or negative results")

    # Ring 3: Pivotal clinical trial cost
    draw_stat_callout_ring(c, rings_cx[2], ring_y, ring_r,
                           "$28M",
                           MUSTARD,
                           "Median cost of a pivotal clinical trial")

    # Below each ring: a one-line context
    contexts_y = 410
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 12)
    c.drawCentredString(rings_cx[0], contexts_y,
                        "About 70 controlled tests every day.")
    c.drawCentredString(rings_cx[0], contexts_y - 16,
                        "Only feasible at hyperscale.")
    c.drawCentredString(rings_cx[1], contexts_y,
                        "Two-thirds of experiments do not")
    c.drawCentredString(rings_cx[1], contexts_y - 16,
                        "move the metric — yet still cost.")
    c.drawCentredString(rings_cx[2], contexts_y,
                        "Some interventions cannot be run at all —")
    c.drawCentredString(rings_cx[2], contexts_y - 16,
                        "infeasible, unethical, impossible.")

    # Caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 285,
                        "Experimentation discipline is real. The bill is real. And not every enterprise can absorb it.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(W / 2, 255,
                        "Causal simulation is the third path: derive the experimental answer from observational data —")
    c.drawCentredString(W / 2, 237,
                        "provided the underlying DAG is correct. Randomization is robust to ignorance. Simulation is not.")
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 130,
                        "Sources: VWO 2025, Kohavi & Thomke (HBR) 2017, ISMP / Applied Clinical Trials 2026")


# ============================================================
# SLIDE 7 — Polar area: where interventions break down
# ============================================================
def slide_7_polar_area(c):
    draw_chrome(c, 7)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(
        W / 2, 980, "When Real Interventions Are Off the Table")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W / 2, 945, "Five categories where simulation through a causal model is the only path to a quantitative answer")

    # Polar area chart
    cx, cy = W / 2, 510
    base_r = 230

    # Five categories with relative magnitude weights (subjective, illustrative)
    categories = [
        ("Infeasible",   80, SAPPHIRE,
         "macroeconomic levers, market structure"),
        ("Unethical",    95, BURGUNDY,
         "exposure-to-harm trials, vulnerable groups"),
        ("Impossible",   60, AMETHYST,
         "physical or cosmological constants"),
        ("Costly",       90, EMERALD,
         "drug trials, market roll-outs, regulatory cycles"),
        ("Irreversible", 75, UMBER,
         "structural reorganizations, brand decisions"),
    ]
    n = len(categories)
    angle_per = 360 / n
    max_v = max(v for _, v, _, _ in categories)

    # Draw faint gridline circles at three levels
    c.setStrokeColor(TAUPE)
    c.setLineWidth(0.8)
    for level in [0.33, 0.66, 1.00]:
        c.circle(cx, cy, base_r * level, stroke=1, fill=0)

    # Draw segments
    for i, (label, value, color, sub) in enumerate(categories):
        start_ang = 90 - i * angle_per - angle_per
        # Area-proportional radius
        r = base_r * math.sqrt(value / max_v)
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(2.5)
        c.wedge(cx - r, cy - r, cx + r, cy + r,
                start_ang, angle_per, stroke=1, fill=1)

    # External labels at each segment midpoint
    # Per-segment offsets — bottom segment uses smaller offset to avoid body caption
    label_offsets = {0: 75, 1: 95, 2: 40, 3: 95, 4: 75}
    for i, (label, value, color, sub) in enumerate(categories):
        mid_ang_deg = 90 - i * angle_per - angle_per / 2
        mid_rad = math.radians(mid_ang_deg)
        label_r = base_r + label_offsets.get(i, 75)
        lx = cx + label_r * math.cos(mid_rad)
        ly = cy + label_r * math.sin(mid_rad)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 15)
        c.drawCentredString(lx, ly + 8, label)
        c.setFillColor(GRAPHITE)
        c.setFont('Poppins', 10)
        # Wrap sub-text into two lines if it has commas
        if ',' in sub:
            parts = sub.split(',', 1)
            c.drawCentredString(lx, ly - 6, parts[0].strip())
            c.drawCentredString(lx, ly - 18, parts[1].strip())
        else:
            c.drawCentredString(lx, ly - 8, sub)

    # Caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 195,
                        "When the experiment cannot be run, the only remaining ground for the answer")
    c.drawCentredString(W / 2, 175,
                        "is a causal model that has been refuted, repeatedly, against the interventions you can run.")


# ============================================================
# SLIDE 8 — Radar overlay: predictive ML vs causal AI capability
# ============================================================
def slide_8_radar_overlay(c):
    draw_chrome(c, 8)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 30)
    c.drawCentredString(W / 2, 985, "Predictive ML vs Causal AI")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 14)
    c.drawCentredString(
        W / 2, 955, "Capability profile across six strategic dimensions")

    cx, cy = W / 2 - 30, 530
    max_r = 220

    dimensions = [
        "Sample efficiency",
        "Transfer to new domains",
        "Robustness under shift",
        "Intervention reasoning",
        "Auditability",
        "Decision-grade output",
    ]
    n_axes = len(dimensions)

    # Gridline polygons
    c.setStrokeColor(TAUPE)
    c.setLineWidth(0.8)
    for level in [0.25, 0.50, 0.75, 1.00]:
        r = max_r * level
        p = c.beginPath()
        for i in range(n_axes):
            ang = math.radians(90 - i * (360 / n_axes))
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)
            if i == 0:
                p.moveTo(x, y)
            else:
                p.lineTo(x, y)
        p.close()
        c.drawPath(p, stroke=1, fill=0)

    # Radial axes
    for i in range(n_axes):
        ang = math.radians(90 - i * (360 / n_axes))
        x = cx + max_r * math.cos(ang)
        y = cy + max_r * math.sin(ang)
        c.line(cx, cy, x, y)

    # Polygons
    def _poly(scores, color, alpha):
        points = []
        for i, v in enumerate(scores):
            ang = math.radians(90 - i * (360 / n_axes))
            r = max_r * (v / 5.0)
            points.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            p.lineTo(x, y)
        p.close()
        c.setFillAlpha(alpha)
        c.setFillColor(color)
        c.setStrokeColor(color)
        c.setStrokeAlpha(1.0)
        c.setLineWidth(2.5)
        c.drawPath(p, stroke=1, fill=1)
        c.setFillAlpha(1.0)
        for x, y in points:
            c.setFillColor(color)
            c.setStrokeColor(IVORY)
            c.setLineWidth(1.5)
            c.circle(x, y, 5, stroke=1, fill=1)

    causal_scores = [4.5, 4.2, 4.4, 4.8, 4.3, 4.5]
    predictive_scores = [3.0, 1.8, 1.7, 1.0, 2.0, 2.2]
    _poly(causal_scores, BURGUNDY, 0.22)
    _poly(predictive_scores, SAPPHIRE, 0.50)

    # Axis labels
    label_r = max_r + 50
    label_positions = [
        (90, 'center', 12, 0),
        (30, 'left', 8, 0),
        (-30, 'left', 8, 0),
        (-90, 'center', -12, 0),
        (-150, 'right', -8, 0),
        (150, 'right', -8, 0),
    ]
    for i, (line) in enumerate(dimensions):
        ang_deg, anchor, dx, _ = label_positions[i]
        ang = math.radians(ang_deg)
        x = cx + label_r * math.cos(ang) + dx
        y = cy + label_r * math.sin(ang)
        c.setFillColor(NAVY)
        c.setFont('Poppins-Bold', 12)
        if anchor == 'center':
            c.drawCentredString(x - dx, y, line)
        elif anchor == 'left':
            c.drawString(x, y, line)
        else:
            c.drawRightString(x, y, line)

    # Legend
    legend_x = 800
    legend_y = 285
    c.setFillColor(BURGUNDY)
    c.setStrokeColor(BURGUNDY)
    c.setLineWidth(2)
    c.setFillAlpha(0.22)
    c.rect(legend_x, legend_y + 22, 26, 16, stroke=1, fill=1)
    c.setFillAlpha(1.0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawString(legend_x + 36, legend_y + 28, "Causal AI")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 10)
    c.drawString(legend_x + 36, legend_y + 14, "do-operator")

    c.setFillColor(SAPPHIRE)
    c.setStrokeColor(SAPPHIRE)
    c.setLineWidth(2)
    c.setFillAlpha(0.50)
    c.rect(legend_x, legend_y - 22, 26, 16, stroke=1, fill=1)
    c.setFillAlpha(1.0)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawString(legend_x + 36, legend_y - 16, "Predictive ML")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 10)
    c.drawString(legend_x + 36, legend_y - 30, "correlation-based")

    # Caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 195,
                        "These two are not competitors. They are layers in the same stack.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(W / 2, 170,
                        "Predictive ML answers what will happen. Causal AI answers what should we do.")
    c.drawCentredString(W / 2, 152,
                        "Enterprise decision systems need both, governed differently.")


# ============================================================
# SLIDE 9 — Segmented wheel: three commitments for the CAIO
# ============================================================
def slide_9_three_commitments(c):
    draw_chrome(c, 9)

    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(W / 2, 980, "Three Commitments for the CAIO")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 15)
    c.drawCentredString(
        W / 2, 945, "Operating AI as a decision discipline rather than a prediction discipline — without a new platform")

    cx, cy = W / 2, 530
    outer_r = 250
    inner_r = 95

    # Three equal sectors
    sectors = [
        ("Audit",
         "Decision engines vs.\nprediction engines",
         "Document which models drive interventions",
         SAPPHIRE),
        ("Represent",
         "Decisions as\ndo-operations",
         "Encode the intervention, not just the conditional",
         EMERALD),
        ("Refute",
         "Models against\nreal interventions",
         "Surprising predictions become priorities",
         BURGUNDY),
    ]
    n = len(sectors)
    angle_per = 360 / n
    start_ang = 90  # Top

    for i, (title, line1, line2, color) in enumerate(sectors):
        seg_start = start_ang - i * angle_per - angle_per
        c.setFillColor(color)
        c.setStrokeColor(IVORY)
        c.setLineWidth(3)
        c.wedge(cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                seg_start, angle_per, stroke=1, fill=1)
        # Text inside sector — at a radius between inner and outer
        mid_ang_deg = seg_start + angle_per / 2
        mid_rad = math.radians(mid_ang_deg)
        text_r = (outer_r + inner_r) / 2
        tx = cx + text_r * math.cos(mid_rad)
        ty = cy + text_r * math.sin(mid_rad)
        c.setFillColor(IVORY)
        c.setFont('Poppins-Bold', 22)
        c.drawCentredString(tx, ty + 14, title)
        c.setFont('Poppins', 11)
        for j, ln in enumerate(line1.split('\n')):
            c.drawCentredString(tx, ty - 8 - j * 14, ln)

    # Inner cutout — Ivory + central label
    c.setFillColor(IVORY)
    c.setStrokeColor(NAVY)
    c.setLineWidth(2)
    c.circle(cx, cy, inner_r, stroke=1, fill=1)
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 16)
    c.drawCentredString(cx, cy + 14, "Decision")
    c.drawCentredString(cx, cy - 6, "Discipline")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(cx, cy - 28, "no new platform")
    c.drawCentredString(cx, cy - 42, "required")

    # External taglines removed — internal segment labels carry the message; external ring would collide with wheel and body caption.

    # Bottom caption
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 195,
                        "These three commitments do not require a new vendor or a new structure.")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins', 13)
    c.drawCentredString(W / 2, 170,
                        "They require a CAIO who has internalized that prediction and decision are different operations —")
    c.drawCentredString(W / 2, 152,
                        "and is willing to govern the organization accordingly.")


# ============================================================
# SLIDE 10 — Closing + sources
# ============================================================
def slide_10_closing(c):
    draw_chrome(c, 10)

    # Top accent stripe wider for closing
    c.setFillColor(BURGUNDY)
    c.rect(0, H - 12, W, 12, stroke=0, fill=1)

    # Single ring with closing icon
    cx, cy = W / 2, 700
    c.setFillColor(NAVY)
    c.setStrokeColor(OCHRE)
    c.setLineWidth(4)
    c.circle(cx, cy, 110, stroke=1, fill=1)
    c.setFillColor(MUSTARD)
    c.setFont('Poppins-Bold', 32)
    c.drawCentredString(cx, cy + 12, "do(X)")
    c.setFillColor(IVORY)
    c.setFont('Poppins-Light', 12)
    c.drawCentredString(cx, cy - 18, "the formal device that")
    c.drawCentredString(cx, cy - 32, "separates predicting")
    c.drawCentredString(cx, cy - 46, "from intervening")

    # Headline
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 28)
    c.drawCentredString(W / 2, 540, "Read every model in your portfolio")
    c.drawCentredString(W / 2, 502, "as either a predictor or a decider.")
    c.setFillColor(BURGUNDY)
    c.setFont('Poppins-Medium', 18)
    c.drawCentredString(W / 2, 460, "Govern each accordingly.")

    # CTA
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 16)
    c.drawCentredString(W / 2, 400,
                        "Full article on Substack — link in comments.")

    # Sources block
    c.setFillColor(NAVY)
    c.setFont('Poppins-Bold', 13)
    c.drawCentredString(W / 2, 320, "Sources")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    sources = [
        "Fortune Business Insights, Causal AI Market Size, 2026",
        "VWO, How to Run 25,000 A/B Tests in 2026 (Booking.com), 2025",
        "Kohavi & Thomke, The Surprising Power of Online Experiments, HBR 2017",
        "Larsen et al., Statistical Challenges in Online Controlled Experiments, 2023",
        "ISMP / Applied Clinical Trials, Clinical Trial Cost Analysis, 2026",
        "Mordor Intelligence, Enterprise AI Market Report, January 2026",
    ]
    for i, src in enumerate(sources):
        c.drawCentredString(W / 2, 295 - i * 16, src)

    # Author tag
    c.setFillColor(NAVY)
    c.setFont('Poppins-Medium', 13)
    c.drawCentredString(W / 2, 165, "Art Koval")
    c.setFillColor(GRAPHITE)
    c.setFont('Poppins-Light', 11)
    c.drawCentredString(W / 2, 145, "Chief AI Officer Insights")


# ============================================================
# Build all slides
# ============================================================
def build():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=(W, H))
    builders = [
        slide_1_cover,
        slide_2_sign_flip,
        slide_3_two_kinds,
        slide_4_hub_spoke,
        slide_5_dual_donut,
        slide_6_experiment_cost,
        slide_7_polar_area,
        slide_8_radar_overlay,
        slide_9_three_commitments,
        slide_10_closing,
    ]
    for builder in builders:
        builder(c)
        c.showPage()
    c.save()
    print(f"Built: {OUTPUT_PDF}")


if __name__ == '__main__':
    build()
