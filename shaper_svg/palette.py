"""Shaper Origin SVG encoding — the EXACT constants used by Autodesk's official
"Shaper Origin Export" Fusion add-in (ShaperUtilities).

Provenance: reverse-engineered from the installed add-in
  ~/Library/Application Support/Autodesk/ApplicationPlugins/ShaperUtilities.bundle
    /Contents/commands/exportToOrigin/MyGeomMath.pyc   (class MyBoard.getSVG)
by unmarshalling its string constants (the colours are built at runtime, not
stored as text). These are the values Shaper Origin recognises; keep them exact.

Cut type is encoded by the FILL colour (Shaper reads the colour, there is no
shaper:cutType attribute). Depth is optional via shaper:cutDepth.
"""

# fill colours per cut type, written verbatim as rgb() like the add-in does
EXTERIOR = "rgb(0,0,0)"        # #000000  cut around the OUTSIDE of the shape
INTERIOR = "rgb(255,255,255)"  # #ffffff  interior cut, goes THROUGH the part (a hole)
POCKET   = "rgb(100,100,100)"  # #646464  pocket (partial depth)
GUIDE    = "rgb(37,107,246)"   # #256bf6  guide line (not cut)
ONLINE   = "rgb(237,230,0)"    # #ede600  on-line / cut-along (centred on the line)

CUT_FILL = {"exterior": EXTERIOR, "interior": INTERIOR, "pocket": POCKET,
            "guide": GUIDE, "online": ONLINE}

# SVG document constants (as the add-in writes them)
NS_SVG   = "http://www.w3.org/2000/svg"
NS_XLINK = "http://www.w3.org/1999/xlink"
NS_SHAPER = "http://www.shapertools.com/namespaces/shaper"
GENERATOR = "Fusion 360, Shaper Origin Export Add-In"  # mirrors the add-in's comment

# Fusion works in centimetres, so the add-in emits cm everywhere.
UNIT = "cm"
MM_TO_CM = 0.1
STROKE_WIDTH = "0.0010cm"       # hairline, exactly as the add-in
STROKE_LINECAP = "round"
STROKE_LINEJOIN = "round"
FILL_RULE = "nonzero"

# dash styles the add-in supports (guide/hidden lines)
DASH = {"SOLID": None, "DASH": "10,5", "HIDDEN": "30,6,8,6"}


def style(cut_type, dash="SOLID", stroke=None):
    """Inline style string for a path/shape of the given Shaper cut type."""
    fill = CUT_FILL[cut_type]
    stroke = stroke or fill
    parts = [f"fill:{fill}", f"stroke:{stroke}", f"stroke-width:{STROKE_WIDTH}",
             f"stroke-linecap:{STROKE_LINECAP}", f"stroke-linejoin:{STROKE_LINEJOIN}",
             f"fill-rule:{FILL_RULE}"]
    if DASH.get(dash):
        parts.append(f"stroke-dasharray:{DASH[dash]}")
    return ";".join(parts)
