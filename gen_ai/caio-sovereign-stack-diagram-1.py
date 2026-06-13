#!/usr/bin/env python3
"""
CAIO standalone diagram 1 — "Your AI Lives in the Overlap"
Three-circle Venn of control surfaces over a production AI system.
Output: 768x576 pt PDF, rasterized at 150 DPI to a 1600x1200 PNG.
"""
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
pdfmetrics.registerFont(TTFont("Poppins", f"{FONT_DIR}/Poppins-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Bold", f"{FONT_DIR}/Poppins-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Medium", f"{FONT_DIR}/Poppins-Medium.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Light", f"{FONT_DIR}/Poppins-Light.ttf"))
pdfmetrics.registerFont(TTFont("Poppins-Italic", f"{FONT_DIR}/Poppins-Italic.ttf"))

# CAIO palette (RGB 0-1)
NAVY     = colors.Color(30/255, 42/255, 74/255)
SAPPHIRE = colors.Color(34/255, 91/255, 158/255)
GRAPHITE = colors.Color(58/255, 63/255, 75/255)
IVORY    = colors.Color(240/255, 234/255, 214/255)
OCHRE    = colors.Color(200/255, 133/255, 58/255)
EMERALD  = colors.Color(30/255, 122/255, 90/255)
BURGUNDY = colors.Color(122/255, 34/255, 51/255)
TEAL     = colors.Color(31/255, 111/255, 122/255)
WHITE    = colors.white

PAGE_W, PAGE_H = 768, 576

def fit_font(c, text, font, max_w, start, min_size=6):
    s = start
    while s > min_size and pdfmetrics.stringWidth(text, font, s) > max_w:
        s -= 0.5
    return s

def centered(c, x, y, text, font, size, color):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(x, y, text)

def centered_fit(c, x, y, text, font, size, color, max_w):
    s = fit_font(c, text, font, max_w, size)
    centered(c, x, y, text, font, s, color)

def main():
    c = canvas.Canvas("caio-sovereign-stack-diagram-1.pdf", pagesize=(PAGE_W, PAGE_H))

    # white background
    c.setFillColor(WHITE)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # ---- Title ----
    centered(c, PAGE_W/2, 543, "Your AI Lives in the Overlap", "Poppins-Bold", 25, NAVY)
    centered(c, PAGE_W/2, 521,
             "A production AI system answers to three controllers at once \u2014 and you are none of them",
             "Poppins", 11.5, GRAPHITE)

    # ---- Circle geometry ----
    r = 125
    top = (384, 388)
    bl  = (312, 263)
    br  = (456, 263)

    fills = [
        (top, SAPPHIRE),
        (bl,  TEAL),
        (br,  BURGUNDY),
    ]

    # translucent fills (alpha)
    for (cx, cy), col in fills:
        c.setFillColor(colors.Color(col.red, col.green, col.blue, alpha=0.55))
        c.circle(cx, cy, r, fill=1, stroke=0)
    c.setFillColor(colors.Color(0, 0, 0, alpha=1.0))  # reset alpha

    # crisp outlines
    c.setLineWidth(2.4)
    for (cx, cy), col in fills:
        c.setStrokeColor(col)
        c.circle(cx, cy, r, fill=0, stroke=1)

    # ---- Exclusive-lobe labels (single bold keyword + descriptor + levers) ----
    # Top circle (Vendor / Models) — wide lobe
    centered_fit(c, 384, 470, "VENDOR", "Poppins-Bold", 19, NAVY, 200)
    centered_fit(c, 384, 451, "controls the models", "Poppins-Medium", 12, NAVY, 210)
    centered_fit(c, 384, 433, "deprecate \u00b7 reprice \u00b7 suspend", "Poppins", 9.5, GRAPHITE, 210)

    # Bottom-left (Provider / Compute)
    centered_fit(c, 270, 224, "PROVIDER", "Poppins-Bold", 16, NAVY, 130)
    centered_fit(c, 270, 207, "controls compute", "Poppins-Medium", 10, NAVY, 130)
    centered_fit(c, 270, 192, "capacity \u00b7 pricing", "Poppins", 9, GRAPHITE, 120)

    # Bottom-right (State / Regulation)
    centered_fit(c, 498, 224, "STATE", "Poppins-Bold", 16, IVORY, 130)
    centered_fit(c, 498, 207, "controls the rules", "Poppins-Medium", 10, IVORY, 130)
    centered_fit(c, 498, 192, "export \u00b7 sanctions", "Poppins", 9, IVORY, 120)

    # ---- Center triple-overlap label on an ivory pill ----
    pill_w, pill_h = 150, 56
    px, py = 384 - pill_w/2, 300 - pill_h/2
    c.setFillColor(IVORY)
    c.setStrokeColor(NAVY)
    c.setLineWidth(1.6)
    c.roundRect(px, py, pill_w, pill_h, 12, fill=1, stroke=1)
    centered(c, 384, 314, "YOUR AI", "Poppins-Bold", 14, NAVY)
    centered(c, 384, 300, "in production", "Poppins-Medium", 10.5, GRAPHITE)
    centered(c, 384, 286, "needs all three", "Poppins-Italic", 9, BURGUNDY)

    # ---- Bottom takeaway band ----
    band_y = 60
    c.setFillColor(NAVY)
    c.rect(96, band_y, PAGE_W - 192, 34, fill=1, stroke=0)
    centered(c, PAGE_W/2, band_y + 12,
             "Lose any one circle and the center goes dark \u2014 the rented layers are not yours to keep",
             "Poppins-Medium", 11.5, IVORY)

    # footer attribution
    centered(c, PAGE_W/2, 24, "Chief AI Officer Insights  \u00b7  Art Koval", "Poppins", 9, TAUPE_OR_GRAPHITE())

    c.showPage()
    c.save()

    # Rasterize the PDF to a 1600x1200 PNG at 150 DPI (768x576 pt page).
    import subprocess
    base = "caio-sovereign-stack-diagram-1"
    subprocess.run(["pdftoppm", "-png", "-r", "150", "-singlefile",
                    base + ".pdf", base], check=True)
    print("Rendered: " + base + ".png")

def TAUPE_OR_GRAPHITE():
    return colors.Color(138/255, 126/255, 109/255)

if __name__ == "__main__":
    main()
