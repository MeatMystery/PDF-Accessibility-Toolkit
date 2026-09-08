#!/usr/bin/env python3
"""Infer and add /Scope attributes to tagged-PDF table header (/TH) elements.

Inference rules (conservative by design):
1. If every direct table cell in a /TR is a /TH, each /TH is inferred as /Column.
2. If the first cell is the only /TH and all remaining cells are /TD, that first /TH
   is inferred as /Row.
3. Mixed/complex rows are reported as ambiguous and left unchanged.

The script edits the structure element attribute dictionary Acrobat shows under
Attributes -> Attribute Objects, using a Table owner dictionary such as:
    /A << /O /Table /Scope /Column >>
or:
    /A << /O /Table /Scope /Row >>

Existing unrelated attribute dictionaries are preserved. Existing conflicting /Scope
values are reported and left unchanged unless --overwrite-existing is supplied.

By default the script writes repaired PDFs to an "output" folder and never overwrites
an input PDF.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DictionaryObject, NameObject
except ImportError:
    print(
        "This script requires pypdf. Install it with:\n"
        "    py -m pip install pypdf\n"
        "or:\n"
        "    python -m pip install pypdf",
        file=sys.stderr,
    )
    raise SystemExit(2)


TABLE = "/Table"
TR = "/TR"
TH = "/TH"
TD = "/TD"


@dataclass
class Stats:
    tables: int = 0
    rows: int = 0
    column_headers_inferred: int = 0
    row_headers_inferred: int = 0
    scopes_added: int = 0
    scopes_already_correct: int = 0
    conflicts: int = 0
    conflicts_overwritten: int = 0
    ambiguous_rows: int = 0
    malformed_rows: int = 0


def deref(obj):
    """Return the underlying PDF object when obj is an indirect reference."""
    if obj is None:
        return None
    try:
        return obj.get_object()
    except AttributeError:
        return obj


def as_name(value) -> Optional[str]:
    """Normalize a PDF name object to a string like '/TH'."""
    value = deref(value)
    if value is None:
        return None
    text = str(value)
    return text if text.startswith("/") else f"/{text}"


def get_dict_value(d: DictionaryObject, key: str):
    return d.get(NameObject(key))


def resolve_role(role, role_map: Optional[DictionaryObject]) -> Optional[str]:
    """Resolve custom structure types through /RoleMap, if present."""
    current = as_name(role)
    if current is None or not isinstance(role_map, DictionaryObject):
        return current

    seen: set[str] = set()
    for _ in range(20):
        if current in seen:
            break
        seen.add(current)
        mapped = role_map.get(NameObject(current))
        if mapped is None:
            break
        current = as_name(mapped)
        if current is None:
            break
    return current


def iter_kids(parent: DictionaryObject) -> Iterator[object]:
    """Yield raw objects from a structure object's /K entry."""
    kids = get_dict_value(parent, "/K")
    if kids is None:
        return

    kids = deref(kids)
    if isinstance(kids, ArrayObject):
        for kid in kids:
            yield kid
    else:
        yield kids


def iter_struct_children(parent: DictionaryObject) -> Iterator[DictionaryObject]:
    """Yield direct child structure elements (objects having an /S entry)."""
    for kid in iter_kids(parent):
        obj = deref(kid)
        if isinstance(obj, DictionaryObject) and get_dict_value(obj, "/S") is not None:
            yield obj


def walk_struct_elements(root: DictionaryObject) -> Iterator[DictionaryObject]:
    """Depth-first traversal of structure elements below /StructTreeRoot."""
    stack = list(reversed(list(iter_struct_children(root))))
    while stack:
        elem = stack.pop()
        yield elem
        children = list(iter_struct_children(elem))
        stack.extend(reversed(children))


def iter_rows_in_table(
    table: DictionaryObject, role_map: Optional[DictionaryObject]
) -> Iterator[DictionaryObject]:
    """Yield rows belonging to this table, but not rows inside nested tables."""
    stack = list(reversed(list(iter_struct_children(table))))
    while stack:
        elem = stack.pop()
        role = resolve_role(get_dict_value(elem, "/S"), role_map)
        if role == TR:
            yield elem
            continue
        if role == TABLE:
            # Nested table: it will be handled independently.
            continue
        children = list(iter_struct_children(elem))
        stack.extend(reversed(children))


def row_cells(
    row: DictionaryObject, role_map: Optional[DictionaryObject]
) -> tuple[list[DictionaryObject], list[str]]:
    """Return direct TH/TD cells plus any unexpected direct structure roles."""
    cells: list[DictionaryObject] = []
    unexpected: list[str] = []

    for child in iter_struct_children(row):
        role = resolve_role(get_dict_value(child, "/S"), role_map)
        if role in (TH, TD):
            cells.append(child)
        else:
            unexpected.append(role or "<unknown>")

    return cells, unexpected


def scope_from_table_attr(attr: DictionaryObject) -> Optional[str]:
    return as_name(get_dict_value(attr, "/Scope"))


def make_table_attr(scope: str) -> DictionaryObject:
    return DictionaryObject(
        {
            NameObject("/O"): NameObject("/Table"),
            NameObject("/Scope"): NameObject(scope),
        }
    )


def find_table_attribute_dicts(a_obj) -> list[DictionaryObject]:
    """Find all /O /Table dictionaries inside a structure element's /A entry."""
    if a_obj is None:
        return []

    a_obj = deref(a_obj)
    if isinstance(a_obj, DictionaryObject):
        if as_name(get_dict_value(a_obj, "/O")) == TABLE:
            return [a_obj]
        return []

    if isinstance(a_obj, ArrayObject):
        found: list[DictionaryObject] = []
        for item in a_obj:
            d = deref(item)
            if isinstance(d, DictionaryObject) and as_name(get_dict_value(d, "/O")) == TABLE:
                found.append(d)
        return found

    return []


def ensure_scope(
    th: DictionaryObject,
    scope: str,
    *,
    overwrite_existing: bool,
    stats: Stats,
) -> str:
    """Add/update the /O /Table attribute dictionary on a TH structure element."""
    a_key = NameObject("/A")
    a_obj = th.get(a_key)
    table_attrs = find_table_attribute_dicts(a_obj)

    if table_attrs:
        # Multiple table-owner attribute dictionaries are unusual. Keep them consistent.
        existing_values = [scope_from_table_attr(d) for d in table_attrs]
        nonempty = [s for s in existing_values if s is not None]

        if nonempty and all(s == scope for s in nonempty) and len(nonempty) == len(table_attrs):
            stats.scopes_already_correct += 1
            return "already-correct"

        if any(s is not None and s != scope for s in existing_values):
            stats.conflicts += 1
            if not overwrite_existing:
                return f"conflict-existing={','.join(s or '<missing>' for s in existing_values)}"
            stats.conflicts_overwritten += 1

        changed = False
        for attr in table_attrs:
            old = scope_from_table_attr(attr)
            if old != scope:
                attr[NameObject("/Scope")] = NameObject(scope)
                changed = True
        if changed:
            stats.scopes_added += 1
            return "updated"
        stats.scopes_already_correct += 1
        return "already-correct"

    # No /O /Table attribute dictionary exists. Preserve other owners.
    new_attr = make_table_attr(scope)
    if a_obj is None:
        th[a_key] = new_attr
    else:
        raw_a = deref(a_obj)
        if isinstance(raw_a, DictionaryObject):
            # Preserve the existing dictionary and add a Table-owner dictionary.
            th[a_key] = ArrayObject([a_obj, new_attr])
        elif isinstance(raw_a, ArrayObject):
            raw_a.append(new_attr)
        else:
            # Unexpected /A type. Do not destroy it.
            return "unsupported-A-type"

    stats.scopes_added += 1
    return "added"


def process_table(
    table: DictionaryObject,
    table_number: int,
    role_map: Optional[DictionaryObject],
    *,
    overwrite_existing: bool,
    stats: Stats,
    messages: list[str],
) -> None:
    rows = list(iter_rows_in_table(table, role_map))
    for row_number, row in enumerate(rows, start=1):
        stats.rows += 1
        cells, unexpected = row_cells(row, role_map)
        if unexpected:
            stats.malformed_rows += 1
            messages.append(
                f"Table {table_number}, row {row_number}: skipped; unexpected direct child tags: "
                + ", ".join(unexpected)
            )
            continue

        if not cells:
            stats.malformed_rows += 1
            messages.append(f"Table {table_number}, row {row_number}: skipped; no TH/TD cells found")
            continue

        roles = [resolve_role(get_dict_value(cell, "/S"), role_map) for cell in cells]
        th_indexes = [i for i, role in enumerate(roles) if role == TH]

        # Rule 1: every cell is TH -> column headers.
        if th_indexes and len(th_indexes) == len(cells):
            stats.column_headers_inferred += len(th_indexes)

            if not overwrite_existing:
                conflicts = []
                for idx in th_indexes:
                    attrs = find_table_attribute_dicts(cells[idx].get(NameObject("/A")))
                    scopes = [scope_from_table_attr(d) for d in attrs]
                    if any(scope is not None and scope != "/Column" for scope in scopes):
                        conflicts.append((idx + 1, scopes))
                if conflicts:
                    stats.conflicts += len(conflicts)
                    details = "; ".join(
                        f"cell {cell_no} has {','.join(s or '<missing>' for s in scopes)}"
                        for cell_no, scopes in conflicts
                    )
                    messages.append(
                        f"Table {table_number}, row {row_number}: inferred /Column but existing "
                        f"scope conflict ({details}); entire row left unchanged"
                    )
                    continue

            for idx in th_indexes:
                result = ensure_scope(
                    cells[idx],
                    "/Column",
                    overwrite_existing=overwrite_existing,
                    stats=stats,
                )
                if result == "unsupported-A-type":
                    messages.append(
                        f"Table {table_number}, row {row_number}, cell {idx + 1}: "
                        "unsupported /A value; left unchanged"
                    )
            continue

        # Rule 2: first cell is the only TH, remainder are TD -> row header.
        if (
            th_indexes == [0]
            and len(cells) >= 2
            and all(role == TD for role in roles[1:])
        ):
            stats.row_headers_inferred += 1

            if not overwrite_existing:
                attrs = find_table_attribute_dicts(cells[0].get(NameObject("/A")))
                scopes = [scope_from_table_attr(d) for d in attrs]
                if any(scope is not None and scope != "/Row" for scope in scopes):
                    stats.conflicts += 1
                    messages.append(
                        f"Table {table_number}, row {row_number}, cell 1: inferred /Row but "
                        f"existing scope is {','.join(s or '<missing>' for s in scopes)}; left unchanged"
                    )
                    continue

            result = ensure_scope(
                cells[0],
                "/Row",
                overwrite_existing=overwrite_existing,
                stats=stats,
            )
            if result == "unsupported-A-type":
                messages.append(
                    f"Table {table_number}, row {row_number}, cell 1: unsupported /A value; left unchanged"
                )
            continue

        # Anything more complex is intentionally not guessed.
        if th_indexes:
            stats.ambiguous_rows += 1
            role_text = " ".join(role or "?" for role in roles)
            messages.append(
                f"Table {table_number}, row {row_number}: ambiguous [{role_text}]; left unchanged"
            )


def repair_pdf(
    src: Path,
    dst: Optional[Path],
    *,
    overwrite_existing: bool,
    dry_run: bool,
) -> tuple[Stats, list[str]]:
    reader = PdfReader(str(src), strict=False)
    if reader.is_encrypted:
        # Empty-password PDFs are common; anything else should be handled explicitly.
        try:
            result = reader.decrypt("")
        except Exception as exc:  # pragma: no cover - library-specific error details
            raise RuntimeError("encrypted PDF could not be opened with an empty password") from exc
        if result == 0:
            raise RuntimeError("encrypted PDF requires a password")

    # Clone the complete document first, then edit the cloned object graph.
    writer = PdfWriter(clone_from=reader)
    root = writer.root_object
    struct_root_ref = root.get(NameObject("/StructTreeRoot"))
    if struct_root_ref is None:
        raise RuntimeError("PDF has no /StructTreeRoot (it does not appear to be tagged)")

    struct_root = deref(struct_root_ref)
    if not isinstance(struct_root, DictionaryObject):
        raise RuntimeError("/StructTreeRoot is not a dictionary")

    role_map_obj = deref(struct_root.get(NameObject("/RoleMap")))
    role_map = role_map_obj if isinstance(role_map_obj, DictionaryObject) else None

    stats = Stats()
    messages: list[str] = []

    tables = [
        elem
        for elem in walk_struct_elements(struct_root)
        if resolve_role(get_dict_value(elem, "/S"), role_map) == TABLE
    ]
    stats.tables = len(tables)

    for table_number, table in enumerate(tables, start=1):
        process_table(
            table,
            table_number,
            role_map,
            overwrite_existing=overwrite_existing,
            stats=stats,
            messages=messages,
        )

    if not dry_run:
        if dst is None:
            raise ValueError("destination path is required unless --dry-run is used")
        dst.parent.mkdir(parents=True, exist_ok=True)
        writer.write(str(dst))

    return stats, messages


def collect_pdfs(path: Path, output_dir_name: str) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"not a PDF: {path}")
        return [path]

    if not path.is_dir():
        raise ValueError(f"path does not exist: {path}")

    output_dir = path / output_dir_name
    return sorted(
        p
        for p in path.glob("*.pdf")
        if p.is_file() and output_dir not in p.parents
    )


def print_stats(src: Path, stats: Stats, messages: list[str], dry_run: bool) -> None:
    mode = "DRY RUN" if dry_run else "DONE"
    print(f"\n[{mode}] {src.name}")
    print(f"  Tables found:                {stats.tables}")
    print(f"  Rows inspected:              {stats.rows}")
    print(f"  Column headers inferred:     {stats.column_headers_inferred}")
    print(f"  Row headers inferred:        {stats.row_headers_inferred}")
    print(f"  Scope attributes added/set:  {stats.scopes_added}")
    print(f"  Already correct:             {stats.scopes_already_correct}")
    print(f"  Existing-scope conflicts:    {stats.conflicts}")
    print(f"  Conflicts overwritten:       {stats.conflicts_overwritten}")
    print(f"  Ambiguous rows skipped:      {stats.ambiguous_rows}")
    print(f"  Malformed rows skipped:      {stats.malformed_rows}")
    for msg in messages:
        print(f"    - {msg}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Infer /Row or /Column scope for TH tags in tagged PDF tables."
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="PDF or folder to process. Default: the folder containing this script.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help='Output folder name for folder processing (default: "output").',
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Replace existing conflicting /Scope values with the inferred value.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect and report what would be inferred without writing PDFs.",
    )
    args = parser.parse_args()

    base = Path(args.path).expanduser().resolve() if args.path else Path(__file__).resolve().parent

    try:
        pdfs = collect_pdfs(base, args.output_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not pdfs:
        print(f"No PDFs found at: {base}")
        return 0

    failures = 0
    for src in pdfs:
        if base.is_file():
            out_dir = src.parent / args.output_dir
        else:
            out_dir = base / args.output_dir
        dst = out_dir / src.name

        try:
            stats, messages = repair_pdf(
                src,
                None if args.dry_run else dst,
                overwrite_existing=args.overwrite_existing,
                dry_run=args.dry_run,
            )
            print_stats(src, stats, messages, args.dry_run)
            if not args.dry_run:
                print(f"  Output: {dst}")
        except Exception as exc:
            failures += 1
            print(f"\n[ERROR] {src.name}: {exc}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
