# services/pdf_fill.py
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, json, textwrap

def fill_pdf_form(template_path, field_map_json, data_dict):
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.append_pages_from_reader(reader)
    fmap = json.loads(field_map_json) if field_map_json else {}

    for k, v in fmap.items():
        val = _get(data_dict, v)
        if val is None:
            val = ''
        writer.update_page_form_field_values(writer.pages[0], {k: str(val)})
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out


def stamp_pdf(template_path, coordinate_map_json, data_dict, font_name=None):
    reader = PdfReader(template_path)
    page = reader.pages[0]
    mb = page.mediabox
    w = float(mb.width)
    h = float(mb.height)
    cmap = json.loads(coordinate_map_json) if coordinate_map_json else {}
    overlay = io.BytesIO()
    c = canvas.Canvas(overlay, pagesize=(w, h))
    if font_name:
        try:
            pdfmetrics.registerFont(TTFont(font_name, f"{font_name}.ttf"))
            base_font = font_name
        except Exception:
            base_font = "Helvetica"
    else:
        base_font = "Helvetica"
    for key, cfg in cmap.items():
        x = float(cfg.get("x", 0))
        y = float(cfg.get("y", 0))
        size = float(cfg.get("size", 10))
        src = cfg.get("source", key)
        val = data_dict
        for p in str(src).split('.'):
            val = val.get(p) if isinstance(val, dict) else None
        text = "" if val is None else str(val)
        max_width = cfg.get("max_width")
        leading = float(cfg.get("leading", size + 2))
        multiline = bool(cfg.get("multiline", False))
        align = cfg.get("align", "left")
        c.setFont(base_font, size)
        if not multiline:
            if align == "center" and max_width:
                tw = pdfmetrics.stringWidth(text, base_font, size)
                x_adj = x + (float(max_width) - tw) / 2.0
                c.drawString(x_adj, y, text)
            else:
                c.drawString(x, y, text)
        else:
            lines = text.split("\n")
            wrapped = []
            if max_width:
                for ln in lines:
                    if not ln:
                        wrapped.append("")
                        continue
                    chunk = []
                    for part in ln.split():
                        chunk.append(part)
                        test = " ".join(chunk)
                        if pdfmetrics.stringWidth(test, base_font, size) > float(max_width):
                            chunk.pop()
                            wrapped.append(" ".join(chunk))
                            chunk = [part]
                    wrapped.append(" ".join(chunk))
            else:
                wrapped = lines
            yy = y
            for ln in wrapped:
                if align == "center" and max_width:
                    tw = pdfmetrics.stringWidth(ln, base_font, size)
                    x_adj = x + (float(max_width) - tw) / 2.0
                    c.drawString(x_adj, yy, ln)
                else:
                    c.drawString(x, yy, ln)
                yy -= leading
    c.showPage()
    c.save()
    overlay.seek(0)
    over_pdf = PdfReader(overlay)
    writer = PdfWriter()
    base_page = reader.pages[0]
    base_page.merge_page(over_pdf.pages[0])
    writer.add_page(base_page)
    for i in range(1, len(reader.pages)):
        writer.add_page(reader.pages[i])
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out


def _get(d, path):
    cur = d
    for p in str(path).split('.'):
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
    return cur
