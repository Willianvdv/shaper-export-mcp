#!/usr/bin/env python3
"""shaper-export-mcp — an MCP server that exports geometry to Shaper Origin SVG,
using the exact colour/encoding that Shaper Origin recognises
add-in (see shaper_svg/palette.py for provenance).

Transport: newline-delimited JSON-RPC 2.0 over stdio (MCP stdio). No third-party
dependencies. Tools:
  shaper_palette        -> the Shaper colour table (reference)
  shaper_plate_svg      -> a rectangular plate (rounded corners) + through holes
  shaper_dxf_svg        -> a DXF (outline + circles) -> Shaper SVG
"""
import sys, os, json, math, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shaper_svg import palette, shapes, writer

PROTOCOL = "2024-11-05"
INFO = {"name": "shaper", "version": "0.1.0"}

TOOLS = [
    {"name": "shaper_palette", "description": "Return the Shaper Origin SVG colour encoding (cut type -> rgb).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "shaper_plate_svg",
     "description": "Write a Shaper-Origin SVG for a rectangular plate: a rounded-rectangle exterior cut (black) with interior through-holes (white). All mm.",
     "inputSchema": {"type": "object", "required": ["width_mm", "height_mm", "holes_mm", "out_path"],
                     "properties": {
                         "width_mm": {"type": "number"}, "height_mm": {"type": "number"},
                         "corner_radius_mm": {"type": "number", "default": 0},
                         "hole_diameter_mm": {"type": "number", "default": 6.5},
                         "holes_mm": {"type": "array", "description": "hole centres [[x,y],...] from the bottom-left corner",
                                      "items": {"type": "array", "items": {"type": "number"}}},
                         "out_path": {"type": "string"}}}},
    {"name": "shaper_dxf_svg",
     "description": "Convert a DXF (closed outline as LINE/ARC/LWPOLYLINE + CIRCLE holes) to a Shaper-Origin SVG. The outline becomes an exterior cut; circles become interior cuts.",
     "inputSchema": {"type": "object", "required": ["dxf_path", "out_path"],
                     "properties": {"dxf_path": {"type": "string"}, "out_path": {"type": "string"},
                                    "outline_cut": {"type": "string", "enum": ["exterior", "interior", "pocket", "guide", "online"], "default": "exterior"},
                                    "hole_cut": {"type": "string", "enum": ["interior", "pocket", "guide", "online"], "default": "interior"}}}},
]


def dxf_entities(path):
    lines = open(path, errors="replace").read().splitlines()
    i, in_ent, typ, cur = 0, False, None, None
    out = []
    while i + 1 < len(lines):
        code, val = lines[i].strip(), lines[i + 1].strip(); i += 2
        if code == "2" and val == "ENTITIES": in_ent = True; continue
        if code == "0" and val == "ENDSEC" and in_ent:
            if cur: out.append((typ, cur))
            break
        if not in_ent: continue
        if code == "0":
            if cur: out.append((typ, cur))
            typ, cur = val, {}
        elif cur is not None:
            cur.setdefault(code, []).append(val)
    return out


def dxf_to_elements(path, outline_cut, hole_cut):
    circles, segs = [], []
    for typ, d in dxf_entities(path):
        g = lambda k, j=0: float(d[k][j])
        if typ == "CIRCLE":
            circles.append((g("10"), g("20"), g("40") * 2))
        elif typ == "LINE":
            segs.append(((g("10"), g("20")), (g("11"), g("21"))))
        elif typ == "ARC":
            cx, cy, r, a0, a1 = g("10"), g("20"), g("40"), math.radians(g("50")), math.radians(g("51"))
            segs.append(((cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1))))
        elif typ == "LWPOLYLINE":
            xs, ys = [float(v) for v in d.get("10", [])], [float(v) for v in d.get("20", [])]
            pts = list(zip(xs, ys))
            closed = int(d.get("70", ["0"])[0]) & 1
            ring = pts + ([pts[0]] if closed else [])
            for a, b in zip(ring, ring[1:]): segs.append((a, b))
    allx = [p[0] for s in segs for p in s] + [c[0] for c in circles]
    ally = [p[1] for s in segs for p in s] + [c[1] for c in circles]
    for cx, cy, dia in circles: allx += [cx - dia / 2, cx + dia / 2]; ally += [cy - dia / 2, cy + dia / 2]
    minx, miny, maxx, maxy = min(allx), min(ally), max(allx), max(ally)
    W, H = maxx - minx, maxy - miny
    els = []
    # order the segments into a connected ring by matching endpoints
    def key(pt): return (round(pt[0], 3), round(pt[1], 3))
    remaining = list(segs)
    pts = []
    if remaining:
        a, b = remaining.pop(0); pts = [a, b]
        changed = True
        while remaining and changed:
            changed = False
            for idx, (p0, p1) in enumerate(remaining):
                if key(p1) == key(pts[-1]): pts.append(p0); remaining.pop(idx); changed = True; break
                if key(p0) == key(pts[-1]): pts.append(p1); remaining.pop(idx); changed = True; break
                if key(p1) == key(pts[0]):  pts.insert(0, p0); remaining.pop(idx); changed = True; break
                if key(p0) == key(pts[0]):  pts.insert(0, p1); remaining.pop(idx); changed = True; break
    def f(v): return f"{v * palette.MM_TO_CM:.4f}".rstrip("0").rstrip(".")
    if pts:
        d = "M " + f"{f(pts[0][0]-minx)} {f(H-(pts[0][1]-miny))}" + " " + \
            " ".join(f"L {f(x-minx)} {f(H-(y-miny))}" for x, y in pts[1:]) + " Z"
        els.append(f'  <path d="{d}" style="{palette.style(outline_cut)}" />')
    for cx, cy, dia in circles:
        els.append(shapes.circle(cx - minx, cy - miny, dia, H, hole_cut))
    return els, W, H


def call(name, args):
    if name == "shaper_palette":
        return json.dumps({"unit": palette.UNIT, "stroke_width": palette.STROKE_WIDTH,
                           "cut_fill_rgb": palette.CUT_FILL, "namespace": palette.NS_SHAPER,
                           "note": "cut type is encoded by fill colour; Shaper Origin spec"}, indent=1)
    if name == "shaper_plate_svg":
        els = shapes.plate((args["width_mm"], args["height_mm"]),
                           [(h[0], h[1]) for h in args["holes_mm"]], args["height_mm"], (0, 0),
                           args.get("corner_radius_mm", 0.0), args.get("hole_diameter_mm", 6.5))
        writer.write(args["out_path"], els, args["width_mm"], args["height_mm"])
        return f'Wrote {args["out_path"]} ({args["width_mm"]}x{args["height_mm"]} mm, {len(args["holes_mm"])} holes).'
    if name == "shaper_dxf_svg":
        els, W, H = dxf_to_elements(args["dxf_path"], args.get("outline_cut", "exterior"), args.get("hole_cut", "interior"))
        writer.write(args["out_path"], els, W, H)
        return f'Wrote {args["out_path"]} from {args["dxf_path"]} ({W:.1f}x{H:.1f} mm).'
    raise ValueError(f"unknown tool {name}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        mid = req.get("id"); method = req.get("method")
        if method == "initialize":
            res = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {}}, "serverInfo": INFO}
        elif method == "tools/list":
            res = {"tools": TOOLS}
        elif method == "tools/call":
            p = req.get("params", {})
            try:
                text = call(p["name"], p.get("arguments", {}))
                res = {"content": [{"type": "text", "text": text}]}
            except Exception as e:
                res = {"content": [{"type": "text", "text": f"Error: {e}\n{traceback.format_exc()}"}], "isError": True}
        elif method in ("notifications/initialized", "initialized"):
            continue
        else:
            if mid is not None:
                sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found"}}) + "\n"); sys.stdout.flush()
            continue
        if mid is not None:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}) + "\n"); sys.stdout.flush()


if __name__ == "__main__":
    main()
