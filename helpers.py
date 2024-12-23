from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import blue, black
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image as PILImage
from reportlab.lib.units import inch
import requests

# Register DejaVu font globally
pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

def resize_and_save_logo(logo_file, upload_folder):
    """Resize and save the uploaded logo."""
    try:
        logo = PILImage.open(logo_file)
        logo.thumbnail((100, 100))  # Resize to fit in the footer
        logo_path = f"{upload_folder}/logo.png"
        logo.save(logo_path, format="PNG")
        return logo_path
    except Exception as e:
        print(f"Error processing logo: {e}")
        return None


def generate_footer_template(contact_info=None, logo_path=None):
    """Generate a footer template with three columns: logo, general info, and links."""
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    footer_y = 0.5 * inch
    left_column_x = 0.5 * inch
    middle_column_x = 1.8 * inch
    right_column_x = 4.5 * inch

    base_y_offset = footer_y + 0.8 * inch
    middle_y_offset = base_y_offset
    right_y_offset = base_y_offset

    if logo_path:
        try:
            c.drawImage(logo_path, left_column_x, footer_y, width=0.8 * inch, height=0.8 * inch)
        except Exception as e:
            print(f"Error adding logo: {e}")

    c.setLineWidth(1)
    c.line(0.5 * inch, footer_y + 1.1 * inch, 7.5 * inch, footer_y + 1.1 * inch)

    c.setFont("DejaVu", 8)

    for field in ["company_name", "agent_name", "address", "phone", "email"]:
        value = contact_info.get(field)
        if value:
            if field == "address":
                c.drawString(middle_column_x, middle_y_offset, "Address:")
                middle_y_offset -= 0.15 * inch
                for line in value.splitlines():
                    c.drawString(middle_column_x + 0.1 * inch, middle_y_offset, line.strip())
                    middle_y_offset -= 0.15 * inch
            else:
                c.drawString(
                    middle_column_x,
                    middle_y_offset,
                    f"{field.replace('_', ' ').capitalize()}: {value}",
                )
                middle_y_offset -= 0.15 * inch

    for field, label in [
        ("map_link", "Google Maps"),
        ("whatsapp_link", "WhatsApp"),
        ("website_link", "Website"),
        ("telegram_link", "Telegram"),
        ("instagram_link", "Instagram"),
    ]:
        value = contact_info.get(field)
        if value:
            c.setFillColor(blue)
            c.drawString(right_column_x, right_y_offset, f"{label}")
            link_width = c.stringWidth(label, "DejaVu", 8)
            c.line(
                right_column_x,
                right_y_offset - 1,
                right_column_x + link_width,
                right_y_offset - 1,
            )
            c.linkURL(value, (right_column_x, right_y_offset - 5, right_column_x + link_width, right_y_offset + 5))
            c.setFillColor(black)
            right_y_offset -= 0.15 * inch

    c.showPage()
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer


def generate_content_pdf(text_sections, images):
    """Generate a PDF with text and images."""
    pdf_buffer = BytesIO()
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []

    # Add text sections
    elements.extend(text_sections)
    elements.append(Spacer(1, 12))
    elements.append(PageBreak())

    # Add images
    for img_url in images:
        img_data = download_and_validate_image(img_url)
        if img_data:
            elements.append(Image(img_data, width=400, height=250))
            elements.append(Spacer(1, 12))

    pdf.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer


def overlay_footer_on_content(footer_pdf, content_pdf):
    """Overlay the footer template on the content PDF."""
    writer = PdfWriter()
    footer_reader = PdfReader(footer_pdf)
    content_reader = PdfReader(content_pdf)

    footer_page = footer_reader.pages[0]  # Use the first page of the footer PDF

    for page in content_reader.pages:
        # Overlay the footer on each page of the content
        page.merge_page(footer_page)
        writer.add_page(page)

    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer


def download_and_validate_image(url):
    """Download an image and validate it."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = PILImage.open(BytesIO(response.content))
        img = img.convert("RGB")
        img.thumbnail((400, 300))
        output = BytesIO()
        img.save(output, format="JPEG")
        output.seek(0)
        return output
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None