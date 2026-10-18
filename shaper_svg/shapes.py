"""Geometry helpers — all inputs in MILLIMETRES. Each returns an SVG element
string already scaled to cm (Shaper unit) with the right cut style.
A plate is placed with its bottom-left corner at (ox, oy) in mm; SVG Y is
flipped so the drawing is right-side up."""
from . import palette

C = palette.MM_TO_CM


def _f(v):
    return f"{v * C:.4f}".rstrip("0").rstrip(".")


def circle(cx_mm, cy_mm, dia_mm, sheet_h_mm, cut="interior"):
    """A hole. In Shaper a through-hole is an INTERIOR cut (white)."""
    y = sheet_h_mm - cy_mm
    return (f'  <circle cx="{_f(cx_mm)}" cy="{_f(y)}" r="{_f(dia_mm/2)}" '
            f'style="{palette.style(cut)}" />')


def rounded_rect(x_mm, y_mm, w_mm, h_mm, r_mm, sheet_h_mm, cut="exterior"):
    """Outline of a plate with rounded corners, as an SVG path (cm, Y-flipped).
    cut='exterior' => cut around the outside (black)."""
    x0, x1 = x_mm, x_mm + w_mm
    # work in top-left origin after the flip: top edge is the larger model-y
    yt = sheet_h_mm - (y_mm + h_mm)   # top in SVG space
    yb = sheet_h_mm - y_mm            # bottom in SVG space
    r = r_mm

    def p(a, b):
        return f"{_f(a)} {_f(b)}"
    rc = _f(r)
    d = (f"M {p(x0 + r, yt)} "
         f"L {p(x1 - r, yt)} A {rc} {rc} 0 0 1 {p(x1, yt + r)} "
         f"L {p(x1, yb - r)} A {rc} {rc} 0 0 1 {p(x1 - r, yb)} "
         f"L {p(x0 + r, yb)} A {rc} {rc} 0 0 1 {p(x0, yb - r)} "
         f"L {p(x0, yt + r)} A {rc} {rc} 0 0 1 {p(x0 + r, yt)} Z")
    return f'  <path d="{d}" style="{palette.style(cut)}" />'


def plate(outline_wh_mm, holes_mm, sheet_h_mm, origin_mm=(0, 0), corner_r_mm=25.0,
          hole_dia_mm=6.5):
    """A rectangular plate (exterior outline + interior holes).
    holes_mm: list of (x, y) hole centres relative to the plate bottom-left corner."""
    ox, oy = origin_mm
    w, h = outline_wh_mm
    els = [rounded_rect(ox, oy, w, h, corner_r_mm, sheet_h_mm, "exterior")]
    for hx, hy in holes_mm:
        els.append(circle(ox + hx, oy + hy, hole_dia_mm, sheet_h_mm, "interior"))
    return els
