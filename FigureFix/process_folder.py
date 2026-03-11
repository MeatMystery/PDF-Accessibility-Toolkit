#!/usr/bin/env python3

"""
Batch-set /Placement /Block on all /Figure structure elements in tagged PDFs.

- Processes all PDFs in this folder
- Writes outputs to ./output
- Auto-installs pikepdf if missing
"""

import os
import sys
import glob
import traceback
import subprocess
from typing import Iterable
from collections import Counter

# -----------------------------
# Ensure dependencies installed
# -----------------------------
def ensure_deps():
    try:
        import pikepdf  # noqa
    except ImportError:
        print("Installing pikepdf...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pikepdf"])
        import pikepdf  # noqa

ensure_deps()

# -----------------------------
# Imports after dependency check
# -----------------------------
import pikepdf
from pikepdf import Name, Dictionary, Array, Object

# -----------------------------
# PDF Name constants
# -----------------------------
FIGURE = Name("/Figure")
STRUCT_ELEM = Name("/StructElem")
LAYOUT = Name("/Layout")
PLACEMENT = Name("/Placement")
BLOCK = Name("/Block")
A = Name("/A")
S = Name("/S")
K = Name("/K")
TYPE = Name("/Type")
O = Name("/O")
ROLEMAP = Name("/RoleMap")

# -----------------------------
# Helpers
# -----------------------------
def iter_kids(k_val: Object) -> Iterable[Object]:
    if k_val is None:
        return
    if isinstance(k_val, Array):
        for item in k_val:
            yield item
    else:
        yield k_val

def is_struct_elem(obj: Object) -> bool:
    if not isinstance(obj, Dictionary):
        return False
    if obj.get(TYPE) == STRUCT_ELEM:
        return True
    return (S in obj) or (K in obj)

def resolve_role(s_name: Name, rolemap: Dictionary) -> Name:
    if not isinstance(rolemap, Dictionary):
        return s_name

    current = s_name
    for _ in range(6):  # follow chained mappings
        mapped = rolemap.get(current)
        if mapped is None:
            break
        if isinstance(mapped, Name):
            current = mapped
        else:
            break
    return current

def ensure_layout_placement_block(struct_elem: Dictionary) -> bool:
    changed = False

    def ensure_in_attr_dict(attr_dict: Dictionary):
        nonlocal changed
        if attr_dict.get(O) != LAYOUT:
            return False
        if attr_dict.get(PLACEMENT) != BLOCK:
            attr_dict[PLACEMENT] = BLOCK
            changed = True
        return True

    a_val = struct_elem.get(A)

    if a_val is None:
        struct_elem[A] = Dictionary({O: LAYOUT, PLACEMENT: BLOCK})
        return True

    if isinstance(a_val, Dictionary):
        if not ensure_in_attr_dict(a_val):
            struct_elem[A] = Array([a_val, Dictionary({O: LAYOUT, PLACEMENT: BLOCK})])
            changed = True
        return changed

    if isinstance(a_val, Array):
        found_layout = False
        for item in a_val:
            if isinstance(item, Dictionary) and item.get(O) == LAYOUT:
                found_layout = True
                ensure_in_attr_dict(item)
        if not found_layout:
            a_val.append(Dictionary({O: LAYOUT, PLACEMENT: BLOCK}))
            changed = True
        return changed

    struct_elem[A] = Dictionary({O: LAYOUT, PLACEMENT: BLOCK})
    return True

def walk_structure(obj: Object, handler):
    if not isinstance(obj, Dictionary):
        return

    if is_struct_elem(obj):
        handler(obj)

    k_val = obj.get(K)
    if k_val is None:
        return

    for kid in iter_kids(k_val):
        if isinstance(kid, Dictionary):
            walk_structure(kid, handler)

# -----------------------------
# Process a single PDF
# -----------------------------
def process_pdf(in_path: str, out_path: str):
    with pikepdf.open(in_path) as pdf:
        struct_root = pdf.Root.get(Name("/StructTreeRoot"))
        if not isinstance(struct_root, Dictionary):
            return (0, 0)

        rolemap = struct_root.get(ROLEMAP)
        if not isinstance(rolemap, Dictionary):
            rolemap = Dictionary()

        figure_count = 0
        changed_count = 0
        tag_counter = Counter()

        def handle(se: Dictionary):
            nonlocal figure_count, changed_count

            s_val = se.get(S)
            if isinstance(s_val, Name):
                tag_counter[str(s_val)] += 1
                resolved = resolve_role(s_val, rolemap)

                if resolved == FIGURE:
                    figure_count += 1
                    if ensure_layout_placement_block(se):
                        changed_count += 1

        walk_structure(struct_root, handle)

        if figure_count == 0:
            common = ", ".join([f"{k}:{v}" for k, v in tag_counter.most_common(10)])
            print(f"  (No figures found.) Top tags: {common if common else 'None'}")

        pdf.save(out_path)
        return (figure_count, changed_count)

# -----------------------------
# Main folder processor
# -----------------------------
def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(folder, "output")
    os.makedirs(out_dir, exist_ok=True)

    pdfs = sorted(glob.glob(os.path.join(folder, "*.pdf")))

    if not pdfs:
        print("No PDFs found.")
        return 0

    print(f"Processing {len(pdfs)} PDFs in: {folder}")
    print(f"Output folder: {out_dir}\n")

    ok = 0
    failed = 0

    for in_path in pdfs:
        base = os.path.basename(in_path)
        out_path = os.path.join(out_dir, base)

        try:
            figures, changed = process_pdf(in_path, out_path)
            print(f"[OK] {base} — Figures: {figures}, Updated: {changed}")
            ok += 1
        except Exception:
            print(f"[FAIL] {base}")
            traceback.print_exc()
            failed += 1

    print("\nDone.")
    print(f"OK: {ok} | Failed: {failed}")
    print(f"See outputs in: {out_dir}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())