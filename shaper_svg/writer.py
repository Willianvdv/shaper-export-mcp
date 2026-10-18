"""Assemble a Shaper-Origin-ready SVG document from element strings.
Document shell matches Autodesk's Shaper add-in: cm units, the three namespaces,
the Generator comment, width/height in cm with a matching viewBox."""
from . import palette

C = palette.MM_TO_CM


def document(elements, width_mm, height_mm, generator_version="1.0 (shaper-export-mcp)"):
    w, h = width_mm * C, height_mm * C
    head = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<!-- Generator: {palette.GENERATOR}, Version {generator_version} -->\n'
        f'<svg xmlns="{palette.NS_SVG}" xmlns:xlink="{palette.NS_XLINK}" '
        f'xmlns:shaper="{palette.NS_SHAPER}" '
        f'shaper:fusionaddin="version:{generator_version}" '
        f'width="{w:.4f}{palette.UNIT}" height="{h:.4f}{palette.UNIT}" '
        f'viewBox="0 0 {w:.4f} {h:.4f}">\n'
    )
    return head + "\n".join(elements) + "\n</svg>\n"


def write(path, elements, width_mm, height_mm, **kw):
    svg = document(elements, width_mm, height_mm, **kw)
    with open(path, "w") as f:
        f.write(svg)
    return path
