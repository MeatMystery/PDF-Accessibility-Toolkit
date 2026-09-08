#!/usr/bin/env python3

"""
Figure Fix batch processor.

- Reads tagged PDFs from ../Input
- Writes corrected copies to ../Output
- Leaves originals unchanged
- Auto-installs pikepdf if missing
"""

import glob
import os
import subprocess
import sys
import traceback
from collections import Counter
from typing import Iterable


def ensure_deps():
    """Install pikepdf for the current user if it is not already available."""
    try:
        import pikepdf  # noqa: F401
        return
    except ImportError:
        pass

    print("Figure Fix needs the pikepdf Python package.")
    print("Installing it for your Windows account now...\n")

    install_attempts = [
        [sys.executable, "-m", "pip", "install", "--user", "pikepdf"],
        [sys.executable, "-m", "pip", "install", "pikepdf"],
    ]

    last_error = None
    for command in install_attempts:
        try:
            subprocess.check_call(command)
            return
        except Exception as exc:
            last_error = exc

    print("\nERROR: pikepdf could not be installed.")
    print("Make sure you are connected to the internet and Python 3.12 is installed.")
    print(f"Details: {last_error}")
    raise last_error


ensure_deps()

import pikepdf
from pikepdf import Array, Dictionary, Name, Object

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
    for _ in range(6):
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


def process_pdf(in_path: str, out_path: str):
    with pikepdf.open(in_path) as pdf:
        struct_root = pdf.Root.get(Name("/StructTreeRoot"))
        if not isinstance(struct_root, Dictionary):
            pdf.save(out_path)
            return (0, 0, False)

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
            common = ", ".join(
                [f"{k}:{v}" for k, v in tag_counter.most_common(10)]
            )
            print(f"       No figures found. Top tags: {common if common else 'None'}")

        pdf.save(out_path)
        return (figure_count, changed_count, True)


def main():
    internal_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(internal_dir)
    input_dir = os.path.join(app_dir, "Input")
    output_dir = os.path.join(app_dir, "Output")

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    pdfs = sorted(glob.glob(os.path.join(input_dir, "*.pdf")))

    print("=" * 60)
    print("FIGURE FIX")
    print("=" * 60)
    print(f"Input : {input_dir}")
    print(f"Output: {output_dir}\n")

    if not pdfs:
        print("No PDF files were found in the Input folder.")
        print("\nPlace one or more PDFs in Input, then run Figure Fix.exe again.")
        return 0

    print(f"Found {len(pdfs)} PDF file(s).\n")

    ok = 0
    failed = 0

    for index, in_path in enumerate(pdfs, start=1):
        base = os.path.basename(in_path)
        out_path = os.path.join(output_dir, base)

        print(f"[{index}/{len(pdfs)}] {base}")
        try:
            figures, changed, tagged = process_pdf(in_path, out_path)
            if tagged:
                print(f"       Complete - Figures found: {figures}, Updated: {changed}")
            else:
                print("       Complete - No tag structure was found; file copied unchanged.")
            ok += 1
        except Exception:
            print("       FAILED")
            traceback.print_exc()
            failed += 1
        print()

    print("=" * 60)
    print("Finished")
    print(f"Successful: {ok} | Failed: {failed}")
    print(f"Corrected files are in: {output_dir}")
    print("=" * 60)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
