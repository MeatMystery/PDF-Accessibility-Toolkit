# Figure Fix

Figure Fix is a small Windows tool for correcting a common PDF accessibility checker (PAC) issue:

> Possibly inappropriate use of a `Figure` structure element

This issue can happen when a PDF's accessibility tags identify something as a figure but do not include the layout information PAC expects. Figure Fix updates the relevant figure-tag properties in a tagged PDF so that PAC can interpret them correctly.

It is intended for PDF accessibility remediation. It does **not** change the visible contents of the PDF, rewrite alternative text, or replace the original file.

## Before you start

You will need:

- A Windows computer
- Python 3.12 installed through **Company Portal**
- The complete Figure Fix folder, including `process_folder.py` and `RUN_WINDOWS.bat`
- One or more tagged PDF files that need this specific PAC fix

Before using Figure Fix for the first time, open **Company Portal**, search for **Python 3.12**, and install it. Figure Fix needs Python in order to run.

The first time you run the tool after Python is installed, it may install the small Python component it needs. An internet connection may be required for that first run.

## How to use it

1. Open the **Figure Fix** folder.
2. Place the PDF file you want to fix directly inside that folder, in the same location as `process_folder.py` and `RUN_WINDOWS.bat`.

   Do not place the PDF inside the `output` folder or another subfolder.

3. Double-click `RUN_WINDOWS.bat`.
4. A black Command Prompt window will open while the tool processes the PDF. Leave it open until it says it is finished.
5. Open the `output` folder inside the Figure Fix folder.
6. Your corrected PDF will be there. The original PDF stays unchanged in the main Figure Fix folder.

If you place more than one PDF in the Figure Fix folder, the tool will process each one and place a corrected copy in `output`.

## After processing

Open the corrected PDF from the `output` folder in PAC and run the checker again. The tool is designed to address the **“Possibly inappropriate use of a ‘Figure’ structure element”** warning shown in the PDF/UA accessibility report.

It is still a good idea to review the rest of the PAC report. This tool fixes only the figure-structure issue; it does not fix other accessibility problems such as missing alternative text, incorrect reading order, headings, tables, or form fields.

## Troubleshooting

**Nothing happens when I double-click `RUN_WINDOWS.bat`.**  
Right-click the file and select **Run as administrator** only if your computer blocks it. Otherwise, make sure Windows recognizes it as a Windows Batch File and that Python is installed.

**The Command Prompt says Python cannot be found.**  
Open **Company Portal**, install **Python 3.12**, then close and reopen the Figure Fix folder before trying again. If it is already installed, contact your IT support team for help making Python available on your computer.

**I cannot find my corrected file.**  
Look in the `output` folder inside Figure Fix. Make sure the source PDF was placed next to `process_folder.py`, not in a subfolder.

**PAC still shows other errors.**  
That is expected when the PDF has additional accessibility issues. Use PAC or Adobe Acrobat to address those separately.

## Technical note

PDFs store accessibility information separately from what is visible on the page. This information is called the **tag structure** or **structure tree**. A figure in that structure is normally identified with a `/Figure` tag. Some PDFs use custom tag names instead; Figure Fix also recognizes those when the PDF's **RoleMap** identifies the custom tag as a figure.

For every applicable figure tag, Figure Fix adds or updates the PDF's layout attributes to the following values:

```text
/A << /O /Layout /Placement /Block >>
```

In plain language, this tells a checker that the tagged item is a block-level object in the document's layout. PAC uses this information when evaluating whether a `Figure` structure element is being used appropriately. Adding the layout attribute resolves the specific warning targeted by this tool when the warning is caused by missing or incorrect figure-placement metadata.

The script processes PDFs with `pikepdf`. It changes the accessibility-tag metadata only; it does not rasterize, re-create, or visually edit pages. In particular, Figure Fix does not:

- change text, images, page layout, fonts, or bookmarks;
- create, remove, or rewrite alternative text;
- change the reading order;
- add headings, table tags, form labels, or language metadata; or
- repair unrelated PAC or PDF/UA findings.

Corrected files are written as new PDFs in `output`, so the original source PDF remains available for comparison and recovery.

---

Developed for Chico State TEIN content remediation by Chase Varvayanis, with AI assistance. March 2026.
