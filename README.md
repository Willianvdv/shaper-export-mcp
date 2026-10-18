# shaper-export-mcp

Export CAD geometry to **Shaper Origin** SVG — an MCP server that produces the
**exact same colour encoding** as Autodesk's official Fusion 360 *"Shaper Origin
Export"* add-in, so the files drop straight onto the tool.

## The encoding (why this repo exists)

Shaper Origin reads the **fill colour** of each shape to decide the cut type.
These are the precise values the Fusion add-in writes — reverse-engineered from
the installed bundle
`…/Autodesk/ApplicationPlugins/ShaperUtilities.bundle/Contents/commands/exportToOrigin/MyGeomMath.pyc`
(the colours are built at runtime, so they were recovered by unmarshalling the
module's string constants). See [`shaper_svg/palette.py`](shaper_svg/palette.py).

| cut type | meaning | fill (as written) | hex |
|---|---|---|---|
| exterior | cut around the **outside** of the shape | `rgb(0,0,0)` | `#000000` |
| interior | cut **through** the part (a hole) | `rgb(255,255,255)` | `#ffffff` |
| pocket | partial-depth pocket | `rgb(100,100,100)` | `#646464` |
| guide | guide line (not cut) | `rgb(37,107,246)` | `#256bf6` |
| online | on-line / cut-along | `rgb(237,230,0)` | `#ede600` |

Document conventions, also matched exactly: **units in cm** (Fusion is
centimetre-internal), `stroke-width:0.0010cm`, `stroke-linecap:round`,
`stroke-linejoin:round`, `fill-rule:nonzero`, namespace
`http://www.shapertools.com/namespaces/shaper`, `shaper:cutDepth`, and the
`<!-- Generator: … -->` comment.

## Tools

- **`shaper_palette`** — returns the colour table above (reference).
- **`shaper_plate_svg`** — a rectangular plate: rounded-rectangle **exterior** cut
  with **interior** through-holes. Inputs in mm (`width_mm`, `height_mm`,
  `corner_radius_mm`, `hole_diameter_mm`, `holes_mm` = `[[x,y],…]` from the
  bottom-left corner, `out_path`). Emits true arcs for the corners.
- **`shaper_dxf_svg`** — a DXF (closed `LINE`/`ARC`/`LWPOLYLINE` outline +
  `CIRCLE` holes) → Shaper SVG. The outline becomes an exterior cut, circles
  interior cuts. (Arc corners are currently written as chords; use
  `shaper_plate_svg` when you need true rounded corners.)

## Run / install as an MCP server

No third-party dependencies (stdlib only). Register at user scope:

```sh
claude mcp add -s user shaper -- python3 /Users/willian/src/shaper-export-mcp/mcp/server.py
```

## Library use

```python
from shaper_svg import shapes, writer
els = shapes.plate((430, 340), holes_mm, 340, corner_r_mm=25, hole_dia_mm=6.5)
writer.write("out.svg", els, 430, 340)
```

`examples/make_window_svgs.py` generates the FM2 plexiglass window files
(outside / inside / combined) from the measured patterns in `fm2-base`.

## Note

This reproduces the add-in's **output format**; it is not affiliated with
Autodesk or Shaper. "Shaper Origin" and "Fusion 360" are trademarks of their
owners.
