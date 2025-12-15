# File Tools (iOS & macOS)

Small Python utilities for file management on iOS and macOS (a-Shell-friendly).

## Tools

### Fix double .pdf suffix (recursive)
Renames files ending with `.pdf.pdf` (case-insensitive) to a single `.pdf`.

**Dry-run (report only):**
```sh
python3 -u fix_double_pdf_suffix.py
