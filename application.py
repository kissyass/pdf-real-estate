from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from urllib.parse import urljoin
from io import BytesIO
from PIL import Image as PILImage
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.colors import blue, black
from reportlab.lib.pagesizes import letter
from reportlab.platypus import PageBreak

application = Flask(__name__)
application.config["UPLOAD_FOLDER"] = "static/uploads"
pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))


def resize_and_save_logo(logo_file):
    """Resize and save the uploaded logo."""
    try:
        logo = PILImage.open(logo_file)
        logo.thumbnail((100, 100))  # Resize to fit in the footer
        logo_path = f"{application.config['UPLOAD_FOLDER']}/logo.png"
        logo.save(logo_path, format="PNG")
        return logo_path
    except Exception as e:
        print(f"Error processing logo: {e}")
        return None


def generate_footer_template(contact_info=None, logo_path=None):
    """Generate a footer template with three columns: logo, general info, and links."""
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)

    # Footer content positions
    footer_y = 0.5 * inch
    left_column_x = 0.5 * inch
    middle_column_x = 1.8 * inch
    right_column_x = 4.5 * inch

    # Adjust vertical alignment offsets
    base_y_offset = footer_y + 0.8 * inch  # Shift all columns down for alignment with logo
    middle_y_offset = base_y_offset
    right_y_offset = base_y_offset

    # Add logo to the footer if provided
    if logo_path:
        try:
            c.drawImage(logo_path, left_column_x, footer_y, width=0.8 * inch, height=0.8 * inch)
        except Exception as e:
            print(f"Error adding logo: {e}")

    # Draw divider line (lowered by 0.2 inch from the previous position)
    c.setLineWidth(1)
    c.line(0.5 * inch, footer_y + 1.1 * inch, 7.5 * inch, footer_y + 1.1 * inch)


    # Set font for the footer
    c.setFont("DejaVu", 8)

    # Middle column: General information
    for field in ["company_name", "agent_name", "address", "phone", "email"]:
        value = contact_info.get(field)
        if value:
            if field == "address":
                c.drawString(middle_column_x, middle_y_offset, "Address:")
                middle_y_offset -= 0.15 * inch  # Move to next line
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

    # Right column: Links
    for field, label in [
        ("map_link", "Google Maps"),
        ("whatsapp_link", "WhatsApp"),
        ("website_link", "Website"),
        ("telegram_link", "Telegram"),
        ("instagram_link", "Instagram"),
    ]:
        value = contact_info.get(field)
        if value:
            # Links with clickable and shortened display
            c.setFillColor(blue)
            c.drawString(right_column_x, right_y_offset, f"{label}")
            link_width = c.stringWidth(label, "DejaVu", 8)
            c.line(
                right_column_x,
                right_y_offset - 1,
                right_column_x + link_width,
                right_y_offset - 1,
            )  # Underline
            c.linkURL(value, (right_column_x, right_y_offset - 5, right_column_x + link_width, right_y_offset + 5))
            c.setFillColor(black)
            right_y_offset -= 0.15 * inch

    c.showPage()
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

def format_overview_section(overview_div, unicode_style, unicode_heading_style):
    """Format the overview section with proper styles."""
    elements = []

    # Extract and format the heading
    heading = overview_div.find("h4", class_="panel-title")
    if heading:
        elements.append(Paragraph(f"<b>{heading.get_text(strip=True)}</b>", unicode_heading_style))
        elements.append(Spacer(1, 6))  # Add space below the heading

    # Extract details with improved formatting
    details = overview_div.find_all("ul", class_="overview_element")
    for detail in details:
        items = detail.find_all("li")
        for item in items:
            text = item.get_text(strip=True)
            if text:  # Ignore empty lines
                elements.append(Paragraph(f"• {text}", unicode_style))  # Bullet points for details
                elements.append(Spacer(1, 4))  # Add space between points

    return elements

def format_panel_section(panel_div, unicode_style, unicode_heading_style):
    """Format a panel section with heading and details."""
    elements = []

    # Extract and format the panel heading
    heading = panel_div.find("h4", class_="panel-title")
    if heading:
        elements.append(Paragraph(f"<b>{heading.get_text(strip=True)}</b>", unicode_heading_style))
        elements.append(Spacer(1, 6))  # Add space below the heading

    # Extract and format the details
    body = panel_div.find("div", class_="panel-body")
    if body:
        details = body.find_all("div", class_="listing_detail")
        for detail in details:
            strong_text = detail.find("strong")
            other_text = (
                detail.get_text(separator=" ", strip=True)
                .replace(strong_text.get_text(strip=True), "").strip()
                if strong_text
                else detail.get_text(strip=True)
            )

            # Combine and format the text
            formatted_text = f"<b>{strong_text.get_text(strip=True)}</b> {other_text}" if strong_text else other_text
            elements.append(Paragraph(formatted_text.strip(":"), unicode_style))
            elements.append(Spacer(1, 4))  # Add space between details

    return elements

def extract_text_content(url):
    """Extract and format text content from specific `div`s on the webpage."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        text_sections = []

        # Define styles for better formatting
        styles = getSampleStyleSheet()
        unicode_body_style = ParagraphStyle(
            "UnicodeBody",
            parent=styles["BodyText"],
            fontName="DejaVu",
            fontSize=11,
            leading=14,
        )
        unicode_heading_style = ParagraphStyle(
            "UnicodeHeading",
            parent=styles["Heading2"],
            fontName="DejaVu",
            fontSize=14,
            leading=16,
            spaceAfter=8,
        )

        # Format sections with updated styles
        overview_div = soup.find("div", class_="single-overview-section panel-group property-panel")
        if overview_div:
            text_sections.extend(format_overview_section(overview_div, unicode_body_style, unicode_heading_style))

        description_div = soup.find("div", class_="wpestate_property_description property-panel")
        if description_div:
            text_sections.extend(format_overview_section(description_div, unicode_body_style, unicode_heading_style))

        panel_divs = soup.find_all("div", class_="panel panel-default")
        for panel in panel_divs[:-1]:  # Skip the last one
            heading = panel.find("h4", class_="panel-title")
            if heading and "Harita" not in heading.get_text(strip=True):
                text_sections.extend(format_panel_section(panel, unicode_body_style, unicode_heading_style))

        return text_sections
    except Exception as e:
        print(f"Error extracting text: {e}")
        return []

def extract_specific_images(url):
    """Extract specific image URLs from the webpage."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        li_elements = soup.find_all("li", {"data-target": "#carousel-listing"})
        image_urls = []
        for li in li_elements:
            img = li.find("img")
            if img and "src" in img.attrs:
                img_src = img["src"]
                if "-" in img_src:
                    base_url, suffix = img_src.rsplit("-", 1)
                    extension = suffix.split(".")[-1]
                    full_url = f"{base_url}.{extension}"
                    image_urls.append(urljoin(url, full_url))
        return image_urls
    except Exception as e:
        print(f"Error extracting images: {e}")
        return []


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


@application.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form.get("url")
        logo_file = request.files.get("logo")
        contact_info = {
            "company_name": request.form.get("company_name"),
            "agent_name": request.form.get("agent_name"),
            "address": request.form.get("address"),
            "map_link": request.form.get("map_link"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "whatsapp_link": request.form.get("whatsapp_link"),
            "website_link": request.form.get("website_link"),
            "telegram_link": request.form.get("telegram_link"),
            "instagram_link": request.form.get("instagram_link"),
        }

        # Extract data
        text_sections = extract_text_content(url)
        images = extract_specific_images(url)

        # Generate content PDF
        content_pdf = generate_content_pdf(text_sections, images)

        # Generate footer template
        footer_pdf = generate_footer_template(contact_info, logo_path=resize_and_save_logo(logo_file))

        # Overlay footer on content
        final_pdf = overlay_footer_on_content(footer_pdf, content_pdf)
        return send_file(final_pdf, as_attachment=True, download_name="final_document.pdf", mimetype="application/pdf")

    return render_template("index.html")

if __name__ == "__main__":
    application.run(debug=True)
