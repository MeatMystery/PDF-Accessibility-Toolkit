# FigureFix Figure Placement Block Remediation Tool

**Created by:** Chase Varvayanis  
**Date:** March 11, 2026  
**Initial code generated with ChatGPT (AI assistance)**  
**For use at:** Chico State TEIN – Content Remediation  

---

## PURPOSE

This tool automates remediation of tagged PDF files by ensuring that
all `/Figure` structure elements contain the required layout attribute:

`/Placement /Block`

Proper figure placement tagging supports improved accessibility
compliance and structural consistency in remediated documents.

---

## OVERVIEW

This script:

- Scans all PDF files in the same folder
- Detects tagged PDFs with a `/StructTreeRoot`
- Identifies structure elements mapped to `/Figure`
  (including RoleMap-resolved custom tags)
- Adds or corrects the layout attribute:
  `/A << /O /Layout /Placement /Block >>`
- Saves processed files into an `output` subfolder
- Leaves original PDFs unchanged

---

## REQUIREMENTS

- Python 3.12
- pip
- pikepdf (automatically installed if missing)

Tested on Windows.

---

## USAGE

1. Place `process_folder.py` and `RUN_WINDOWS.bat` in the same folder
   as your PDFs.
2. Double-click `RUN_WINDOWS.bat`.
3. Processed files will appear in the `output` folder.

---

## IMPORTANT NOTES

- Only affects tagged PDFs.
- Untagged PDFs are skipped.
- Does not alter visible page content.
- Designed specifically for accessibility remediation workflows.
- Always test on copies before using in production environments.

---

## DISCLAIMER

This script modifies low-level PDF structure elements.
Use with caution and verify results in Adobe Acrobat or your
accessibility validation tool before final distribution.

---

Chico State TEIN – Content Remediation Workflow Tool  
© 2026 Chase Varvayanis
