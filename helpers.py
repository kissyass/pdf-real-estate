from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Spacer, Image, PageBreak, Paragraph
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import blue, black
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image as PILImage
from reportlab.lib.units import inch
import requests
from extractors import translate_text
from reportlab.lib.styles import getSampleStyleSheet

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


def generate_footer_template(contact_info=None, target_language='tr', logo_path=None):
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
                addr = translate_text("Address:", target_language, "en")
                c.drawString(middle_column_x, middle_y_offset, addr)
                # c.drawString(middle_column_x, middle_y_offset, "Address:")
                middle_y_offset -= 0.15 * inch
                for line in value.splitlines():
                    c.drawString(middle_column_x + 0.1 * inch, middle_y_offset, line.strip())
                    middle_y_offset -= 0.15 * inch
            else:
                translated_txt = translate_text(field.replace('_', ' ').capitalize(),  target_language, "en")
                c.drawString(
                    middle_column_x,
                    middle_y_offset,
                    f"{translated_txt}: {value}",
                    # f"{field.replace('_', ' ').capitalize()}: {value}",
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
    

def get_footer_height(contact_info, logo_height=0.8 * inch, line_spacing=0.15 * inch):
    """
    Calculate the height of the footer dynamically based on its content.
    Args:
        contact_info (dict): Dictionary containing footer content.
        logo_height (float): Height of the logo in inches.
        line_spacing (float): Space between lines in inches.
    Returns:
        float: Total height of the footer in inches.
    """
    # Base height for the logo
    footer_height = logo_height

    # Count lines in the footer (middle and right columns)
    middle_column_lines = 0
    right_column_lines = 0

    # Count lines in the middle column
    for field in ["company_name", "agent_name", "address", "phone", "email"]:
        value = contact_info.get(field)
        if value:
            if field == "address":
                middle_column_lines += len(value.splitlines()) + 1  # Address has multiple lines
            else:
                middle_column_lines += 1

    # Count lines in the right column
    for field in ["map_link", "whatsapp_link", "website_link", "telegram_link", "instagram_link"]:
        if contact_info.get(field):
            right_column_lines += 1

    # Take the maximum lines between middle and right columns
    max_lines = max(middle_column_lines, right_column_lines)
    footer_height += max_lines * line_spacing

    # Add some padding
    footer_height += 0.2 * inch

    return footer_height

# def generate_content_pdf_with_footer_check(text_sections, images, footer_height):
#     """
#     Generate a content PDF with page breaks based on footer height.
#     Args:
#         text_sections (list): Text sections to be added.
#         images (list): Image URLs to be added.
#         footer_height (float): Height of the footer in inches.
#     Returns:
#         BytesIO: PDF buffer.
#     """
#     pdf_buffer = BytesIO()
#     pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
#     elements = []

#     # Calculate available space on the page
#     max_page_height = 11 * inch - footer_height

#     # # Add text sections with dynamic page breaks
#     # current_height = 0
#     # for section in text_sections:
#     #     for line in section.splitlines():
#     #         line_height = 0.15 * inch  # Estimate line height
#     #         if current_height + line_height > max_page_height:
#     #             elements.append(PageBreak())
#     #             current_height = 0  # Reset for the new page
#     #         elements.append(Paragraph(line, getSampleStyleSheet()["BodyText"]))
#     #         elements.append(Spacer(1, line_height))
#     #         current_height += line_height

#     # Add text sections with dynamic page breaks
#     current_height = 0
#     styles = getSampleStyleSheet()
#     for section in text_sections:
#         paragraph = Paragraph(section, styles["BodyText"])
#         paragraph_height = 0.3 * inch  # Estimate paragraph height
        
#         if current_height + paragraph_height > max_page_height:
#             elements.append(PageBreak())
#             current_height = 0  # Reset for the new page
            
#         elements.append(paragraph)
#         elements.append(Spacer(1, 12))  # Add some space between paragraphs
#         current_height += paragraph_height + 12

#     # Add images with dynamic page breaks
#     for img_url in images:
#         img_data = download_and_validate_image(img_url)
#         if img_data:
#             img_height = 250  # Adjust height as needed
#             if current_height + img_height > max_page_height:
#                 elements.append(PageBreak())
#                 current_height = 0
#             elements.append(Image(img_data, width=400, height=img_height))
#             elements.append(Spacer(1, 12))
#             current_height += img_height

#     pdf.build(elements)
#     pdf_buffer.seek(0)
#     return pdf_buffer

# def generate_content_pdf_with_footer_check(text_sections, images, footer_height):
#     """
#     Generate a content PDF with page breaks based on footer height.
#     Args:
#         text_sections (list): Text sections to be added.
#         images (list): Image URLs to be added.
#         footer_height (float): Height of the footer in inches.
#     Returns:
#         BytesIO: PDF buffer.
#     """
#     pdf_buffer = BytesIO()
#     pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
#     elements = []
    
#     # Calculate available space on the page
#     max_page_height = 10 * inch - footer_height
#     current_height = 0

#     # Add text sections with dynamic page breaks
#     for section in text_sections:
#         # Since section is already a flowable (Paragraph or Spacer), add it directly
#         if isinstance(section, (Paragraph, Spacer)):
#             section_height = 0.2 * inch  # Estimate height for Paragraph
#             if current_height + section_height > max_page_height:
#                 elements.append(PageBreak())
#                 current_height = 0
            
#             elements.append(section)
#             current_height += section_height

#     # Add images with dynamic page breaks
#     for img_url in images:
#         img_data = download_and_validate_image(img_url)
#         if img_data:
#             img_height = 250  # Adjust height as needed
#             if current_height + img_height > max_page_height:
#                 elements.append(PageBreak())
#                 current_height = 0
#             elements.append(Image(img_data, width=400, height=img_height))
#             elements.append(Spacer(1, 12))
#             current_height += img_height

#     pdf.build(elements)
#     pdf_buffer.seek(0)
#     return pdf_buffer

def generate_content_pdf_with_footer_check(text_sections, images, footer_height):
    """
    Generate a content PDF with page breaks based on footer height.
    Args:
        text_sections (list): Text sections to be added.
        images (list): Image URLs to be added.
        footer_height (float): Height of the footer in inches.
    Returns:
        BytesIO: PDF buffer.
    """
    pdf_buffer = BytesIO()
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []
    
    # Calculate available space on the page
    max_page_height = 10.5 * inch - footer_height
    current_height = 0

    # Add text sections with dynamic page breaks
    for section in text_sections:
        # Since section is already a flowable (Paragraph or Spacer), add it directly
        if isinstance(section, (Paragraph, Spacer)):
            section_height = 0.2 * inch  # Estimate height for Paragraph
            if current_height + section_height > max_page_height:
                elements.append(PageBreak())
                current_height = 0
            
            elements.append(section)
            current_height += section_height

    # Add a page break before starting images
    elements.append(PageBreak())
    current_height = 0

    # Add images with dynamic page breaks
    for img_url in images:
        img_data = download_and_validate_image(img_url)
        if img_data:
            img_height = 250  # Adjust height as needed
            if current_height + img_height > max_page_height:
                elements.append(PageBreak())
                current_height = 0
            elements.append(Image(img_data, width=400, height=img_height))
            elements.append(Spacer(1, 12))
            current_height += img_height

    pdf.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer