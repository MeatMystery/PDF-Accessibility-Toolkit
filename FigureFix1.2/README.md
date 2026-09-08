# FigureFix1.2

FigureFix1.2 is a small Windows tool for correcting a common PDF accessibility checker (PAC) issue:

> Possibly inappropriate use of a `Figure` structure element

The tool updates the relevant figure-tag layout properties in a tagged PDF. It does **not** change the visible contents of the PDF, rewrite alternative text, or replace the original file.

## Folder layout

Figure Fix is organized so users do not need to interact with the underlying script files:

```text
FigureFix1.2/
├── FigureFix1.2.exe      <- double-click this to run the tool
├── Input/              <- place PDFs to be processed here
│   └── .placeholder.txt <- keeps the folder in GitHub
├── Output/             <- corrected PDFs appear here
│   └── .placeholder.txt <- keeps the folder in GitHub
├── README.md
└── .figure_fix/        <- internal program files; normally hidden
```

The `.placeholder.txt` files in **Input** and **Output** are repository placeholders so GitHub keeps the empty folder structure. They are ignored by the processor and can be left in place.

The `.figure_fix` folder contains the Python code and batch launcher used by the executable. The launcher marks this folder as hidden when Figure Fix runs. You normally do not need to open or modify it.

## Before you start

You will need:

- A Windows computer
- Python 3.12 installed through **Company Portal**
- The complete Figure Fix folder
- One or more tagged PDF files that need this specific PAC fix

Before using Figure Fix for the first time, open **Company Portal**, search for **Python 3.12**, and install it.

Figure Fix also uses a Python package called `pikepdf`. If it is not already installed, Figure Fix will attempt to install it automatically the first time it runs. An internet connection may be required for that first run.

## How to use it

1. Open the **FigureFix1.2** folder.
2. Put one or more PDF files in the **Input** folder.
3. Double-click **Figure Fix.exe**.
4. A Command Prompt window will show the processing status. Leave it open until processing is complete.
5. Open the **Output** folder.
6. The processed PDFs will be there with the same filenames as the originals.

The original files in **Input** are left unchanged.

If an output file with the same name already exists, running Figure Fix again will replace that output copy with the newly processed version.

## After processing

Open the corrected PDF from **Output** in PAC and run the checker again. Figure Fix is designed to address the **“Possibly inappropriate use of a ‘Figure’ structure element”** warning shown in the PDF/UA accessibility report.

You should still review the rest of the PAC report. This tool fixes only the figure-structure issue; it does not fix other accessibility problems such as missing alternative text, incorrect reading order, headings, tables, or form fields.

## Troubleshooting

**Figure Fix says no PDFs were found.**  
Make sure the files are inside the **Input** folder and that they have a `.pdf` file extension.

**Windows says Python cannot be found.**  
Open **Company Portal**, install **Python 3.12**, then run **FigureFix1.2.exe** again. If Python is already installed but is still not detected, contact your IT support team.

**The first run fails while installing pikepdf.**  
Make sure you have an internet connection. If your network blocks Python package installation, contact IT support.

**I cannot find the internal program files.**  
That is intentional. The `.figure_fix` folder is marked as hidden by the launcher. In Windows File Explorer, enable **View > Show > Hidden items** if you need to access it for troubleshooting.

**I cannot find my corrected file.**  
Look in the **Output** folder. The source file should remain in **Input**.

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

Corrected files are written as new PDFs in **Output**, so the original source PDFs remain available in **Input** for comparison and recovery.

---

Developed for Chico State TEIN content remediation by Chase Varvayanis, with AI assistance. September 2026.
