# TableScopeFix

TableScopeFix is a small Windows tool for automatically adding table-header scope information to tagged PDFs.

PDF table headers are tagged as `TH` elements. For proper table accessibility, each header needs a `/Scope` identifier that defines whether it applies to a row or a column.

TableScopeFix determines this scope from the PDF's **tag structure** rather than from the visible appearance of the table. It analyzes the arrangement of `TR`, `TH`, and `TD` structure elements and adds the appropriate `/Scope /Row` or `/Scope /Column` identifier where the relationship can be determined.

This is especially useful for tables that are difficult to work with in Adobe Acrobat's Table Editor. The Table Editor can become graphically malformed or difficult to use when a table contains empty cells or other irregular structures. TableScopeFix does not depend on the Table Editor's visual representation. It works directly from the underlying tag structure, including **empty table-cell tags**.

This means that, before running TableScopeFix, users generally only need to:

1. Create a `Table` structure with the correct number of rows and columns.
2. Add empty `TH` or `TD` filler tags where necessary so that the tag structure accurately represents the table grid.
3. Mark the appropriate cells as `TH` headers.
4. Run TableScopeFix to assign the appropriate row or column scope.

The tool is intended for PDF accessibility remediation. It does **not** change the visible contents of the PDF, replace the original file, or modify table text.

## Before you start

You will need:

- A Windows computer
- Python 3.12 installed through **Company Portal**
- The complete TableScopeFix folder
- One or more tagged PDF files containing tables that need header scope information

Before using TableScopeFix for the first time, open **Company Portal**, search for **Python 3.12**, and install it.

The Python code and supporting files used by TableScopeFix are contained inside the hidden `.internal` folder. You normally do not need to open or modify this folder.

### Prepare the table structure first

TableScopeFix assigns scope based on the structure that already exists in the PDF. Before processing a table, make sure its tags represent the intended table layout.

You do **not** need to make the table look correct inside Acrobat's graphical Table Editor.

Instead:

1. Create or correct the `Table` tag.
2. Create the appropriate number of `TR` row tags.
3. Give each row the appropriate number of `TH` and `TD` cell tags.
4. Use empty cell tags as placeholders when a location in the table does not contain visible content.
5. Change the cells that function as headers from `TD` to `TH`.
6. Run TableScopeFix.

Empty tags are valid and important for this workflow. TableScopeFix uses their position in the structure when determining the shape of the table, even when those tags contain no visible content.

For example, a row may structurally look like:

```text
TR
├─ TH
├─ TD
├─ TD
└─ TD
```

even if one or more of those cells are empty.

As long as the underlying tag structure correctly represents the table's rows, columns, and header cells, TableScopeFix can use that structure without relying on Acrobat's graphical Table Editor.

## How to use it

1. Open the **TableScopeFix** folder.
2. Place the PDF file or files you want to process inside the **Input** folder.
3. Make sure each table has:
   - the correct number of rows;
   - the correct number of cell tags in each row;
   - empty filler tags where necessary; and
   - the appropriate header cells marked as `TH`.
4. Double-click:

   `Run TableScopeFix.exe`

5. A Command Prompt window will open while the PDFs are processed. Leave it open until processing is complete.
6. The **Output** folder will open automatically when processing finishes.
7. Open the corrected PDF from the **Output** folder.

The original PDF remains unchanged inside the **Input** folder.

If multiple PDFs are placed in the Input folder, TableScopeFix will process each one and place a corrected copy in the Output folder.

## How scope is determined

TableScopeFix examines the tagged structure of each table row and looks at the relationship between its `TH` and `TD` cells.

The inference is based on the **structure elements themselves**, not on whether a cell contains visible text or whether Acrobat's Table Editor displays the table correctly.

An empty `TH` or `TD` tag still counts as a cell when TableScopeFix evaluates the row.

For common table structures, the tool uses rules such as:

- If all cells in a table row are `TH` elements, they are treated as **column headers**.
- If the first cell is a `TH` and the remaining cells are `TD` elements, the first cell is treated as a **row header**.
- If the structure is ambiguous, the tool avoids making an uncertain change.

For example:

```text
TH | TH | TH
```

is interpreted as a column-header row.

Each header receives:

```text
/A <<
  /O /Table
  /Scope /Column
>>
```

A row such as:

```text
TH | TD | TD
```

is interpreted as having a row header.

The first cell receives:

```text
/A <<
  /O /Table
  /Scope /Row
>>
```

The same logic applies when one or more of the cells are empty. What matters is the arrangement of the `TH` and `TD` tags in the structure tree.

## Why empty filler tags matter

PDF table accessibility depends on the logical table structure, not only on visible content.

Some tables contain blank cells, intentionally empty locations, or layouts that cause Acrobat's Table Editor to display the table incorrectly. In these cases, trying to repair the table entirely through the graphical Table Editor can be difficult.

TableScopeFix allows the structure tree itself to serve as the source of truth.

For example, if the intended table contains four columns but a particular row only contains content in three of them, the structure should still contain four cell tags:

```text
TR
├─ TH
├─ TD
├─ TD
└─ TD   ← empty filler cell
```

The final `TD` does not need visible content. Its presence tells TableScopeFix that the row still contains four logical columns.

This allows a remediator to build the correct table grid directly in the tag tree, mark the appropriate cells as headers, and let TableScopeFix handle the scope identifiers afterward.

## After processing

Open the corrected PDF from the **Output** folder in Adobe Acrobat, PAC, or your normal PDF accessibility-checking workflow.

Review the affected tables to confirm that the inferred row and column relationships match the intended table structure.

TableScopeFix automates common table-header patterns, but complex tables may still require manual remediation.

It is also a good idea to review the rest of the accessibility report. TableScopeFix addresses table-header scope information only. It does not fix other accessibility issues such as:

- an incorrect number of table rows or columns;
- missing `TR`, `TH`, or `TD` structure elements;
- incorrect cells marked as headers;
- complex spanning-header relationships;
- incorrect reading order;
- missing alternative text;
- heading structure;
- form fields;
- document language; or
- unrelated PDF/UA or PAC findings.

## Troubleshooting

**Nothing happens when I double-click `Run TableScopeFix.exe`.**  
Make sure the entire TableScopeFix folder was extracted from the ZIP file before running it. Do not run the executable directly from inside the ZIP archive.

**The Command Prompt says Python cannot be found.**  
Open **Company Portal**, install **Python 3.12**, then close and reopen the TableScopeFix folder before trying again. If Python is already installed, contact your IT support team for help making Python available on your computer.

**No PDFs were processed.**  
Make sure the PDF files are inside the **Input** folder and have a `.pdf` file extension.

**I cannot find my corrected file.**  
Look inside the **Output** folder. The Output folder should also open automatically after processing finishes.

**A table header was not changed.**  
Check the underlying tag structure. Make sure the table has the correct number of `TR` rows and `TH`/`TD` cells, including empty filler cells where necessary. Also make sure the cells that function as headers are actually tagged as `TH`.

If the arrangement remains ambiguous, TableScopeFix may intentionally leave the scope unchanged rather than guess.

**The Table Editor looks broken even though the tags are correct.**  
This can happen with tables containing empty cells or unusual layouts. TableScopeFix does not rely on the graphical Table Editor. If the structure tree correctly represents the table grid, including the necessary empty `TH` and `TD` tags, the tool can still process it.

**PAC still shows table errors.**  
TableScopeFix only adds table-header scope information based on the existing tag structure. Other table structure problems may still need to be corrected manually.

## Technical note

PDF accessibility information is stored separately from the visible page content in the document's **tag structure**, also called the **structure tree**.

Accessible tables commonly contain structure elements such as:

```text
Table
└─ TR
   ├─ TH
   ├─ TD
   ├─ TD
   └─ TD
```

These structure elements define the logical table grid. A cell tag can participate in that structure even when it contains no visible page content.

TableScopeFix traverses this structure and identifies table-header (`TH`) elements. It uses the surrounding `TR`, `TH`, and `TD` arrangement to infer whether each header functions as a row or column header.

When the relationship can be determined, the tool adds a table attribute dictionary containing either:

```text
/O /Table
/Scope /Row
```

or:

```text
/O /Table
/Scope /Column
```

These attributes correspond to the Scope identifier shown in Adobe Acrobat's tag attribute interface.

Because the inference is based on the underlying tag structure, **empty `TH` and `TD` elements are included when determining the table layout**. This allows a remediator to construct the proper logical grid with empty filler cells even when Acrobat's Table Editor cannot display the table cleanly.

If a structure element already contains unrelated attributes, TableScopeFix preserves those attributes rather than replacing them.

The tool changes accessibility-tag metadata only. It does not rasterize, recreate, or visually modify PDF pages. In particular, TableScopeFix does not:

- change visible text;
- change fonts, images, or page layout;
- modify bookmarks;
- rewrite table contents;
- create the table grid automatically;
- decide which cells should be `TH` before processing;
- change reading order; or
- repair unrelated accessibility findings.

The user is responsible for creating the correct table structure and identifying the appropriate `TH` cells. TableScopeFix then uses that structure to add the required scope identifiers.

Corrected files are written as new PDFs in the **Output** folder so that the original source files remain available for comparison and recovery.

The program's Python code, launcher script, and supporting components are stored inside the hidden `.internal` folder. Normal users only need to interact with the **Input** folder, **Output** folder, and `Run TableScopeFix.exe`.

---

Developed for Chico State TEIN content remediation by Chase Varvayanis, with AI assistance. September 2026.
