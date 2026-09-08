# PDF Accessibility Toolkit

A collection of small Windows utilities I wrote to help automate repetitive parts of PDF accessibility remediation.

These tools are designed for specific problems I regularly encountered while remediating tagged PDFs. They are not intended to replace Adobe Acrobat, PAC, or manual accessibility review. Instead, they handle a few targeted changes that can otherwise be repetitive, difficult, or awkward to perform manually.

The tools currently focus primarily on modifying PDF accessibility metadata and structure information without changing the visible contents of the document.

## Tools

### FigureFix1.2

Corrects a common PAC warning:

> Possibly inappropriate use of a `Figure` structure element

FigureFix examines figure tags in the PDF structure tree, including custom structure types mapped to `Figure`, and adds the appropriate layout metadata:

```text
/A << /O /Layout /Placement /Block >>
```

This identifies the figure as a block-level layout object and resolves the targeted PAC warning when it is caused by missing or incorrect figure placement information.

FigureFix does not alter the visible page, rewrite alternative text, or change reading order.

See the `FigureFix1.2` folder for complete instructions.

---

### TableScopeFix1.1

Automatically assigns `/Scope /Row` or `/Scope /Column` attributes to table header (`TH`) tags.

Rather than relying on Adobe Acrobat's graphical Table Editor, TableScopeFix works directly from the PDF's underlying tag structure. It examines the arrangement of `Table`, `TR`, `TH`, and `TD` elements to determine how headers are being used.

This is particularly useful for tables containing empty cells or unusual layouts where Acrobat's Table Editor may become graphically malformed or difficult to work with.

Empty `TH` and `TD` tags are intentionally included when determining the logical table grid. This means a remediator can:

1. Build the appropriate number of rows in the tag tree.
2. Add the correct number of cell tags to each row.
3. Use empty `TH` or `TD` filler tags where necessary.
4. Mark the appropriate cells as `TH`.
5. Run TableScopeFix to assign header scope.

For common structures:

```text
TH | TH | TH
```

is interpreted as a column-header row, while:

```text
TH | TD | TD
```

is interpreted as a row with a row header.

If the structure is ambiguous, the program avoids making an uncertain change.

See the `TableScopeFix1.1` folder for complete preparation and usage instructions.

---

### UnicodeEncodingFix0.1 (NON FUNCTIONAL)

An experimental utility related to repairing PDF Unicode/text-encoding problems.

This tool is currently **non-functional** and is included only for development/reference purposes.

Do not use it on production documents.

---

## General Folder Structure

The functional tools are generally organized so that users only need to interact with a few items:

```text
ToolName/
├── Run ToolName.exe
├── Input/
├── Output/
├── README.md
└── .internal/ or hidden program folder
```

Depending on the tool/version, the executable or internal folder name may differ slightly.

### Input

Place the PDFs you want to process here.

### Output

Processed copies are written here.

The original PDFs in `Input` are normally left unchanged.

### Hidden/Internal Files

The Python scripts, launcher files, and other program components are stored separately from the user-facing folders.

Normal users should not need to modify these files.

---

# Requirements

## Windows

These tools are currently intended for Windows.

## Python

The tools use Python for the actual PDF processing.

The current common requirement is:

- **Python 3.12**

### Chico State computers

On Chico State-managed computers, install Python through **Company Portal**.

1. Open **Company Portal**.
2. Search for **Python 3.12**.
3. Install it.
4. Run the desired accessibility tool afterward.

A helper script for automatically installing/configuring Python is **not currently included** in this repository because the campus environment requires software such as Python to be installed through Company Portal.

This also avoids having the toolkit attempt to bypass normal campus software-management procedures.

## Python Packages

Some tools require additional Python packages, particularly:

```text
pikepdf
```

Where supported, the launcher will attempt to install a missing Python package automatically.

An internet connection may therefore be required the first time a tool is run.

Python itself must still be installed first.

---

# Running the Tools

Each functional tool is intended to be run from its own folder.

In general:

1. Open the folder for the tool you want to use.
2. Read that tool's `README.md` for any required PDF preparation.
3. Place one or more PDFs in its `Input` folder.
4. Double-click the `.exe` launcher.
5. Leave the Command Prompt window open while processing occurs.
6. Open the `Output` folder and review the processed PDF.
7. Recheck the document in PAC, Adobe Acrobat, or your normal accessibility validation workflow.

Do not assume that successfully running one of these tools means the PDF is fully accessible.

Each utility addresses a specific issue only.

---

# Windows Security / Unsigned Executables

The executable launchers included with this project are **not digitally signed**.

Because of this, Windows may display a warning when you attempt to run one of them.

A common Windows Defender SmartScreen message is:

> Windows protected your PC

This does not necessarily mean Windows detected malware. Windows may show this warning simply because the executable does not have a recognized digital signature or established reputation.

If you downloaded the program from this repository and trust the copy you downloaded:

1. Double-click the executable.
2. If **Windows protected your PC** appears, click **More info**.
3. Verify that you intended to run the program.
4. Click **Run anyway**.

The exact wording may vary depending on the version of Windows and your organization's security settings.

## Downloaded ZIP files may also be blocked

Windows may mark files downloaded from the internet as coming from another computer.

If the toolkit was downloaded as a ZIP file, it can sometimes help to unblock the ZIP **before extracting it**:

1. Right-click the downloaded `.zip` file.
2. Select **Properties**.
3. If an **Unblock** checkbox appears near the bottom of the window, check it.
4. Click **Apply**.
5. Extract the ZIP normally.

Do this only for a copy of the toolkit that you obtained from a source you trust.

## Managed computers

Campus-managed computers may have additional security policies that prevent unsigned applications from running.

If Windows does not provide a **Run anyway** option, or organizational policy blocks the executable entirely, do not attempt to disable or circumvent campus security software.

Contact campus IT or run the underlying script through an approved Python installation if appropriate.

---

# Important Limitations

These programs perform targeted PDF accessibility remediation. They do not automatically make a PDF accessible.

Depending on the tool, they may modify things such as:

- structure-element attributes;
- table-header scope information; or
- other accessibility-related PDF metadata.

They generally do **not** automatically correct:

- reading order;
- missing alternative text;
- incorrect alternative text;
- heading hierarchy;
- incorrectly tagged content;
- missing table structure;
- complex table relationships;
- form-field accessibility;
- document language;
- color contrast;
- visible document content; or
- unrelated PAC/PDF-UA errors.

Always review the resulting PDF after processing.

For important documents, retain the original source PDF until the processed version has been inspected and validated.

---

# Why These Tools Exist

PDF accessibility information is stored largely in a document's **structure tree**, separately from what is visibly displayed on the page.

Some accessibility problems are therefore easier to repair by working directly with that underlying structure rather than through Acrobat's graphical interfaces.

For example, TableScopeFix can use empty table-cell tags as part of the logical grid even when Acrobat's Table Editor does not display that table cleanly. FigureFix can add structure metadata that PAC expects without changing the actual figure shown on the page.

The goal of this toolkit is to automate these kinds of narrowly defined structure-level repairs while leaving the remainder of the remediation process under the control of the remediator.

---

# Disclaimer

These utilities modify PDF files programmatically.

Although the functional tools are designed to write processed documents to separate `Output` folders rather than overwrite their source files, keep backups of important documents and review all output before using it in production.

The tools should be considered remediation aids, not substitutes for accessibility knowledge, manual verification, or conformance testing.

---

Developed for Chico State TEIN content remediation by Chase Varvayanis, with AI assistance. September 2026.
