"""Generate the FM2 window SVGs for Shaper Origin:
  1. fenster01_au_outside.svg    — the outer plate (430x340, 24 holes)
  2. fenster01_innen_inside.svg  — the inner plate (360x260, 8 holes, owner-measured)
  3. fenster01_combined.svg      — both plates side by side on one sheet (reference layout)
  4. fenster01_stacked_test.svg  — ONE plate carrying BOTH hole patterns concentrically
     (outside 24 + inside 8), so you can CNC a single test plate and bolt-check both
     frames against it. Both frames mount centred on the same window opening, so the two
     patterns share a centre; each set is centred on the plate centre by its own bbox.
Hole data is read from the fm2-base spec JSONs (measured). Run from anywhere.
usage: python3 examples/make_window_svgs.py [out_dir]
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shaper_svg import shapes, writer

FM2 = "/Users/willian/src/fm2-base/spec/windows"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(FM2, "shaper")
os.makedirs(OUT, exist_ok=True)

outside = json.load(open(os.path.join(FM2, "outside_bolt_pattern.json")))
inside = json.load(open(os.path.join(FM2, "inside_bolt_pattern.json")))

O_W, O_H = outside["outline_extent_mm"]                 # 430 x 340
O_HOLES = [(h[0], h[1]) for h in outside["holes"]["centers_rel_to_outline_min_corner"]]
O_DIA = float(next(iter(outside["holes"].get("by_diameter", {"6.5":1})))) if "by_diameter" in outside["holes"] else outside["holes"]["diameter"]
I_W, I_H = inside["plate_outline_mm"]                   # 360 x 260
I_HOLES = [(h[0], h[1]) for h in inside["holes"]["centers_rel_to_outline_min_corner"]]
I_DIA = inside["holes"]["diameter"]                     # 6.5
R = 25.0

# 1. outside
els = shapes.plate((O_W, O_H), O_HOLES, O_H, (0, 0), R, O_DIA)
writer.write(os.path.join(OUT, "fenster01_au_outside.svg"), els, O_W, O_H)

# 2. inside
els = shapes.plate((I_W, I_H), I_HOLES, I_H, (0, 0), R, I_DIA)
writer.write(os.path.join(OUT, "fenster01_innen_inside.svg"), els, I_W, I_H)

# 3. combined: both on one sheet, 20 mm gap, bottoms aligned
GAP = 20.0
sheet_w = O_W + GAP + I_W
sheet_h = max(O_H, I_H)
els = shapes.plate((O_W, O_H), O_HOLES, sheet_h, (0, 0), R, O_DIA)
els += shapes.plate((I_W, I_H), I_HOLES, sheet_h, (O_W + GAP, 0), R, I_DIA)
writer.write(os.path.join(OUT, "fenster01_combined.svg"), els, sheet_w, sheet_h)

# 4. stacked test plate: both patterns concentric on the larger (430x340) outline.
#    Centre each hole set on the plate centre by its own bbox centre -> both frames,
#    which mount centred on the same opening, line up on one test plate.
def _centred(holes, cx, cy):
    xs = [h[0] for h in holes]; ys = [h[1] for h in holes]
    hx = (min(xs) + max(xs)) / 2.0; hy = (min(ys) + max(ys)) / 2.0
    return [(h[0] + (cx - hx), h[1] + (cy - hy)) for h in holes]

CX, CY = O_W / 2.0, O_H / 2.0
els = [shapes.rounded_rect(0, 0, O_W, O_H, R, O_H, "exterior")]
for hx, hy in _centred(O_HOLES, CX, CY):
    els.append(shapes.circle(hx, hy, O_DIA, O_H, "interior"))
for hx, hy in _centred(I_HOLES, CX, CY):
    els.append(shapes.circle(hx, hy, I_DIA, O_H, "interior"))
writer.write(os.path.join(OUT, "fenster01_stacked_test.svg"), els, O_W, O_H)

for f in ("fenster01_au_outside", "fenster01_innen_inside", "fenster01_combined",
          "fenster01_stacked_test"):
    print("wrote", os.path.join(OUT, f + ".svg"))
