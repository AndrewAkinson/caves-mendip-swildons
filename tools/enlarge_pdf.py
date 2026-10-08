"""Make a PDF's pages bigger, so a phone lets you zoom further into it.

Phone PDF viewers stop zooming at a fixed multiple of the page size, so
on the 82 cm plan they run out of zoom before the small labels and
symbols are readable. The drawing is all vector, so enlarging the page
loses nothing: everything on it, header and scale bar included, scales
together, and the scale bar still measures true.

    python3 tools/enlarge_pdf.py output/Swildons-plan.pdf 3

Rewrites the file in place with Ghostscript. Plain Python, no packages.
"""
import os
import shutil
import subprocess
import sys


def page_size(gs, pdf):
    """Width and height of the first page in points, read by Ghostscript."""
    out = subprocess.run(
        [gs, "-q", "-dNODISPLAY", "-dNOSAFER", "-c",
         f"({pdf}) (r) file runpdfbegin 1 pdfgetpage /MediaBox pget pop == quit"],
        check=True, capture_output=True, text=True).stdout
    x0, y0, x1, y1 = (float(v) for v in out.strip().strip("[]").split())
    return x1 - x0, y1 - y0


def enlarge(pdf, factor):
    gs = shutil.which("gs") or sys.exit("enlarge_pdf: Ghostscript (gs) not found")
    w, h = page_size(gs, pdf)
    tmp = pdf + ".tmp"
    subprocess.run(
        [gs, "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pdfwrite",
         "-dCompatibilityLevel=1.7",
         f"-dDEVICEWIDTHPOINTS={round(w * factor)}",
         f"-dDEVICEHEIGHTPOINTS={round(h * factor)}",
         "-dFIXEDMEDIA", "-dPDFFitPage",
         "-sOutputFile=" + tmp, pdf], check=True)
    os.replace(tmp, pdf)
    print(f"{pdf}: {w / 72 * 2.54:.0f} x {h / 72 * 2.54:.0f} cm -> "
          f"{w * factor / 72 * 2.54:.0f} x {h * factor / 72 * 2.54:.0f} cm")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    enlarge(sys.argv[1], float(sys.argv[2]))
