"""
Recalculate Excel formulas using LibreOffice headless mode.
Usage: python scripts/recalc.py <input.xlsx> [output.xlsx]
"""

import subprocess
import sys
import os
import shutil


def find_libreoffice():
    """Find LibreOffice executable."""
    candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        shutil.which("soffice"),
        shutil.which("libreoffice"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def recalc(input_path, output_path=None):
    """Recalculate formulas in an Excel file using LibreOffice."""
    lo = find_libreoffice()
    if not lo:
        print("ERROR: LibreOffice not found. Install from https://www.libreoffice.org/")
        sys.exit(1)

    input_path = os.path.abspath(input_path)
    if not os.path.exists(input_path):
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    output_dir = os.path.dirname(output_path or input_path)

    cmd = [
        lo,
        "--headless",
        "--calc",
        "--convert-to", "xlsx",
        "--outdir", output_dir,
        input_path,
    ]

    print(f"Recalculating: {input_path}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"ERROR: LibreOffice failed:\n{result.stderr}")
        sys.exit(1)

    # LibreOffice outputs to same filename in outdir
    base = os.path.splitext(os.path.basename(input_path))[0]
    generated = os.path.join(output_dir, f"{base}.xlsx")

    if output_path and output_path != generated:
        shutil.move(generated, output_path)
        print(f"Output: {output_path}")
    else:
        print(f"Output: {generated}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/recalc.py <input.xlsx> [output.xlsx]")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    recalc(inp, out)
