from __future__ import annotations

import io
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Iterable

import pikepdf
from pikepdf import Name

from fontTools.ttLib import TTFont
from fontTools.agl import toUnicode


STANDARD_ENCODINGS = {
    "WinAnsiEncoding": {
        **{i: chr(i) for i in range(32, 127)},
        128: "EUR", 130: "quotesinglbase", 131: "florin", 132: "quotedblbase",
        133: "ellipsis", 134: "dagger", 135: "daggerdbl", 136: "circumflex",
        137: "perthousand", 138: "Scaron", 139: "guilsinglleft", 140: "OE",
        145: "quoteleft", 146: "quoteright", 147: "quotedblleft", 148: "quotedblright",
        149: "bullet", 150: "endash", 151: "emdash", 152: "tilde",
        153: "trademark", 154: "scaron", 155: "guilsinglright", 156: "oe",
        159: "Ydieresis",
        160: "space", 161: "exclamdown", 162: "cent", 163: "sterling",
        164: "currency", 165: "yen", 166: "brokenbar", 167: "section",
        168: "dieresis", 169: "copyright", 170: "ordfeminine", 171: "guillemotleft",
        172: "logicalnot", 173: "hyphen", 174: "registered", 175: "macron",
        176: "degree", 177: "plusminus", 178: "twosuperior", 179: "threesuperior",
        180: "acute", 181: "mu", 182: "paragraph", 183: "periodcentered",
        184: "cedilla", 185: "onesuperior", 186: "ordmasculine", 187: "guillemotright",
        188: "onequarter", 189: "onehalf", 190: "threequarters", 191: "questiondown",
        192: "Agrave", 193: "Aacute", 194: "Acircumflex", 195: "Atilde",
        196: "Adieresis", 197: "Aring", 198: "AE", 199: "Ccedilla",
        200: "Egrave", 201: "Eacute", 202: "Ecircumflex", 203: "Edieresis",
        204: "Igrave", 205: "Iacute", 206: "Icircumflex", 207: "Idieresis",
        208: "Eth", 209: "Ntilde", 210: "Ograve", 211: "Oacute",
        212: "Ocircumflex", 213: "Otilde", 214: "Odieresis", 215: "multiply",
        216: "Oslash", 217: "Ugrave", 218: "Uacute", 219: "Ucircumflex",
        220: "Udieresis", 221: "Yacute", 222: "Thorn", 223: "germandbls",
        224: "agrave", 225: "aacute", 226: "acircumflex", 227: "atilde",
        228: "adieresis", 229: "aring", 230: "ae", 231: "ccedilla",
        232: "egrave", 233: "eacute", 234: "ecircumflex", 235: "edieresis",
        236: "igrave", 237: "iacute", 238: "icircumflex", 239: "idieresis",
        240: "eth", 241: "ntilde", 242: "ograve", 243: "oacute",
        244: "ocircumflex", 245: "otilde", 246: "odieresis", 247: "divide",
        248: "oslash", 249: "ugrave", 250: "uacute", 251: "ucircumflex",
        252: "udieresis", 253: "yacute", 254: "thorn", 255: "ydieresis",
    },
    "MacRomanEncoding": {
        **{i: chr(i) for i in range(32, 127)},
        # Sparse and incomplete here by design; the script still works without it.
        # Add a full table if you need stronger MacRoman recovery.
    },
    "PDFDocEncoding": {
        **{i: chr(i) for i in range(32, 127)}
    },
}


@dataclass
class InferenceReport:
    page_num: int
    font_tag: str
    basefont: str = ""
    subtype: str = ""
    inferred: Dict[int, str] = field(default_factory=dict)
    skipped_reason: Optional[str] = None
    clues: list[str] = field(default_factory=list)


def pdf_name_to_str(obj) -> str:
    if obj is None:
        return ""
    s = str(obj)
    return s[1:] if s.startswith("/") else s


def hex_utf16be(text: str) -> str:
    return text.encode("utf-16-be").hex().upper()


def make_tounicode_cmap(mapping: Dict[int, str], cmap_name: str) -> bytes:
    lines = [
        "/CIDInit /ProcSet findresource begin",
        "12 dict begin",
        "begincmap",
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def",
        f"/CMapName /{cmap_name} def",
        "/CMapType 2 def",
        "1 begincodespacerange",
        "<00> <FF>",
        "endcodespacerange",
    ]

    items = sorted((k, v) for k, v in mapping.items() if isinstance(k, int) and 0 <= k <= 255 and v)
    for i in range(0, len(items), 100):
        chunk = items[i:i + 100]
        lines.append(f"{len(chunk)} beginbfchar")
        for code, uni in chunk:
            lines.append(f"<{code:02X}> <{hex_utf16be(uni)}>")
        lines.append("endbfchar")

    lines.extend([
        "endcmap",
        "CMapName currentdict /CMap defineresource pop",
        "end",
        "end",
        "",
    ])
    return "\n".join(lines).encode("ascii")


def parse_differences(encoding_obj) -> Dict[int, str]:
    """
    Parse a simple /Encoding dictionary with /BaseEncoding and /Differences.
    Returns byte -> glyphname.
    """
    result: Dict[int, str] = {}
    if not encoding_obj or not isinstance(encoding_obj, pikepdf.Dictionary):
        return result

    diffs = encoding_obj.get(Name.Differences)
    if not diffs:
        return result

    current_code = None
    for item in diffs:
        if isinstance(item, int):
            current_code = item
        else:
            if current_code is not None:
                result[current_code] = pdf_name_to_str(item)
                current_code += 1
    return result


def glyphname_to_unicode(name: str) -> Optional[str]:
    """
    Resolve glyph names through Adobe Glyph List rules.
    """
    if not name:
        return None

    # Strip subset-ish suffixes if present in unusual names.
    name = name.split(".")[0]

    try:
        uni = toUnicode(name)
        if uni:
            return uni
    except Exception:
        pass

    # uniXXXX / uXXXX fallback patterns
    m = re.fullmatch(r"uni([0-9A-Fa-f]{4})", name)
    if m:
        return chr(int(m.group(1), 16))

    m = re.fullmatch(r"u([0-9A-Fa-f]{4,6})", name)
    if m:
        return chr(int(m.group(1), 16))

    return None


def extract_fontfile_bytes(font_dict) -> Optional[bytes]:
    desc = font_dict.get(Name.FontDescriptor)
    if not desc:
        return None

    for key in (Name.FontFile2, Name.FontFile3, Name.FontFile):
        stream = desc.get(key)
        if stream:
            try:
                return bytes(stream.read_bytes())
            except Exception:
                return None
    return None


def load_ttfont(font_bytes: bytes) -> Optional[TTFont]:
    try:
        return TTFont(io.BytesIO(font_bytes))
    except Exception:
        return None


def invert_best_unicode_cmap(tt: TTFont) -> Dict[int, str]:
    """
    Build glyph-id -> Unicode char using the font's best Unicode cmap.
    """
    result: Dict[int, str] = {}
    try:
        best = tt.getBestCmap() or {}
    except Exception:
        return result

    glyph_order = tt.getGlyphOrder()
    gname_to_gid = {name: i for i, name in enumerate(glyph_order)}

    for codepoint, gname in best.items():
        gid = gname_to_gid.get(gname)
        if gid is not None:
            try:
                result[gid] = chr(codepoint)
            except ValueError:
                pass
    return result


def infer_simple_font_mapping(font_dict) -> Tuple[Dict[int, str], list[str]]:
    """
    Infer byte -> Unicode for simple 1-byte fonts using:
    - /Encoding base + /Differences
    - embedded TrueType/OpenType glyph order + cmap
    - glyph names via AGL
    """
    inferred: Dict[int, str] = {}
    clues: list[str] = []

    encoding_obj = font_dict.get(Name.Encoding)
    base_encoding_name = ""
    diff_names: Dict[int, str] = {}

    if isinstance(encoding_obj, pikepdf.Name):
        base_encoding_name = pdf_name_to_str(encoding_obj)
    elif isinstance(encoding_obj, pikepdf.Dictionary):
        base = encoding_obj.get(Name.BaseEncoding)
        if base:
            base_encoding_name = pdf_name_to_str(base)
        diff_names = parse_differences(encoding_obj)

    # 1) base encoding glyph names -> Unicode
    if base_encoding_name in STANDARD_ENCODINGS:
        for code, value in STANDARD_ENCODINGS[base_encoding_name].items():
            if len(value) == 1:
                inferred.setdefault(code, value)
            else:
                uni = glyphname_to_unicode(value)
                if uni:
                    inferred.setdefault(code, uni)
        clues.append(f"base encoding: {base_encoding_name}")

    # 2) Differences override
    for code, gname in diff_names.items():
        uni = glyphname_to_unicode(gname)
        if uni:
            inferred[code] = uni
    if diff_names:
        clues.append("used /Differences entries")

    # 3) Embedded font program hints
    font_bytes = extract_fontfile_bytes(font_dict)
    if font_bytes:
        tt = load_ttfont(font_bytes)
        if tt:
            clues.append("embedded TrueType/OpenType parsed")
            gid_to_uni = invert_best_unicode_cmap(tt)
            glyph_order = tt.getGlyphOrder()

            # Heuristic: in many simple fonts, code values often correspond to glyph ids
            # for a useful low range; use only where we do not already have better info.
            for code in range(256):
                if code in inferred:
                    continue
                if code < len(glyph_order):
                    uni = gid_to_uni.get(code)
                    if uni:
                        inferred[code] = uni

            # Heuristic: glyph names at same ordinal positions
            for code in range(min(256, len(glyph_order))):
                if code in inferred:
                    continue
                gname = glyph_order[code]
                uni = glyphname_to_unicode(gname)
                if uni:
                    inferred[code] = uni
        else:
            clues.append("embedded font present but not parseable as TT/OTF")

    return inferred, clues


def patch_pdf(input_pdf: str, output_pdf: str) -> list[InferenceReport]:
    reports: list[InferenceReport] = []

    with pikepdf.Pdf.open(input_pdf) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            resources = page.obj.get(Name.Resources)
            if not resources:
                continue
            fonts = resources.get(Name.Font)
            if not fonts:
                continue

            for tag, font in fonts.items():
                tag_str = str(tag)
                basefont = pdf_name_to_str(font.get(Name.BaseFont))
                subtype = pdf_name_to_str(font.get(Name.Subtype))

                report = InferenceReport(
                    page_num=page_num,
                    font_tag=tag_str,
                    basefont=basefont,
                    subtype=subtype,
                )

                if Name.ToUnicode in font:
                    report.skipped_reason = "already has /ToUnicode"
                    reports.append(report)
                    continue

                if subtype not in {"Type1", "TrueType", "MMType1"}:
                    report.skipped_reason = f"unsupported subtype for automatic 1-byte inference: {subtype}"
                    reports.append(report)
                    continue

                mapping, clues = infer_simple_font_mapping(font)
                report.clues.extend(clues)
                report.inferred = mapping

                if not mapping:
                    report.skipped_reason = "could not infer any byte->Unicode mappings"
                    reports.append(report)
                    continue

                cmap_name = f"AutoTU_P{page_num}_{tag_str.lstrip('/')}"
                cmap_stream = pdf.make_stream(make_tounicode_cmap(mapping, cmap_name))
                cmap_stream[Name.Type] = Name.CMap
                font[Name.ToUnicode] = cmap_stream

                reports.append(report)

        pdf.save(output_pdf)

    return reports


def print_report(reports: Iterable[InferenceReport]) -> None:
    total_patched = 0
    for r in reports:
        print(f"Page {r.page_num} {r.font_tag}")
        print(f"  BaseFont: {r.basefont or '(unknown)'}")
        print(f"  Subtype : {r.subtype or '(unknown)'}")
        if r.clues:
            print(f"  Clues   : {', '.join(r.clues)}")
        if r.skipped_reason:
            print(f"  Result  : skipped - {r.skipped_reason}")
        else:
            print(f"  Result  : patched with {len(r.inferred)} inferred mappings")
            sample = sorted(r.inferred.items())[:12]
            preview = ", ".join(f"{k:02X}->{repr(v)}" for k, v in sample)
            print(f"  Sample  : {preview}")
            total_patched += 1
        print()
    print(f"Patched {total_patched} font resource(s).")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python repair_tounicode.py input.pdf output.pdf")
        return 2

    input_pdf, output_pdf = argv[1], argv[2]
    reports = patch_pdf(input_pdf, output_pdf)
    print_report(reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))