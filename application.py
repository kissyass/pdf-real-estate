from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from urllib.parse import urljoin
from io import BytesIO

application = Flask(__name__)

# Register a Unicode font (e.g., DejaVu Sans)
pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

def extract_specific_images(url):
    """Extract specific image URLs from the webpage."""
    response = requests.get(url)
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
                absolute_url = urljoin(url, full_url)
                image_urls.append(absolute_url)
    return image_urls

def format_overview_section(overview_div, unicode_style, unicode_heading_style):
    """Format the overview section with proper styles."""
    elements = []

    # Extract the heading
    heading = overview_div.find("h4", class_="panel-title")
    if heading:
        elements.append(Paragraph(heading.get_text(strip=True), unicode_heading_style))
        elements.append(Spacer(1, 4))  # Small space after heading

    # Extract details
    details = overview_div.find_all("ul", class_="overview_element")
    for detail in details:
        # Extract individual items in the list
        items = detail.find_all("li")
        row_content = []
        for item in items:
            text = item.get_text(strip=True)
            # Format as bold if it's the first item in the row (label)
            if "first_overview" in item.get("class", []):
                row_content.append(f"<b>{text}</b>")
            else:
                row_content.append(text)

        # Join row content with spaces
        row_text = " ".join(row_content)
        elements.append(Paragraph(row_text, unicode_style))
        elements.append(Spacer(1, 2))  # Space between rows

    return elements

def format_panel_section(panel_div, unicode_style, unicode_heading_style):
    """Format a panel section with heading and details."""
    elements = []

    # Extract and format the panel heading
    heading = panel_div.find("h4", class_="panel-title")
    if heading:
        elements.append(Paragraph(heading.get_text(strip=True), unicode_heading_style))
        elements.append(Spacer(1, 4))  # Small space after heading

    # Extract and format the panel body
    body = panel_div.find("div", class_="panel-body")
    if body:
        # Iterate over detail divs inside the panel body
        details = body.find_all("div", class_="listing_detail")
        for detail in details:
            strong_text = detail.find("strong")
            other_text = detail.get_text(separator=" ", strip=True).replace(strong_text.get_text(strip=True), "").strip() if strong_text else detail.get_text(strip=True)

            # Format strong (bold) label and value on the same line
            row_content = ""
            if strong_text:
                row_content += f"<b>{strong_text.get_text(strip=True)}</b> "
            row_content += other_text

            elements.append(Paragraph(row_content, unicode_style))
            elements.append(Spacer(1, 1))  # Small space between rows

        # Handle standalone links, e.g., "Google Harita ile Aç"
        links = body.find_all("a", class_="acc_google_maps")
        for link in links:
            # Style the link with underline and blue color
            link_text = f'<a href="{link["href"]}" color="blue" underline="true">{link.get_text(strip=True)}</a>'
            elements.append(Paragraph(link_text, unicode_style))
            elements.append(Spacer(1, 1))

    return elements

def extract_text_content(url):
    """Extract text content from specific `div`s in the webpage."""
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    text_sections = []

        # Define styles for text and headings
    styles = getSampleStyleSheet()
    unicode_body_style = ParagraphStyle(
        "UnicodeBody",
        parent=styles["BodyText"],
        fontName="DejaVu",
        fontSize=10,
        leading=12,
    )
    unicode_heading_style = ParagraphStyle(
        "UnicodeHeading",
        parent=styles["Heading2"],
        fontName="DejaVu",
        fontSize=14,
        leading=16,
        spaceAfter=6,
    )
    
    # 1. Extract from 'single-overview-section panel-group property-panel'
    overview_div = soup.find("div", class_="single-overview-section panel-group property-panel")
    if overview_div:
        text_sections.extend(format_overview_section(overview_div, unicode_body_style, unicode_heading_style))
    
    # 2. Extract from 'wpestate_property_description property-panel'
    description_div = soup.find("div", class_="wpestate_property_description property-panel")
    if description_div:
        text_sections.extend(format_overview_section(description_div, unicode_body_style, unicode_heading_style))
    
    # 3. Extract all 'panel panel-default' divs except the last one
    panel_divs = soup.find_all("div", class_="panel panel-default")
    if panel_divs:
        for panel in panel_divs[:-1]:  # Skip the last one
            # Check if this is the "Haritalar" section and skip it
            heading = panel.find("h4", class_="panel-title")
            if heading and "Harita" in heading.get_text(strip=True):
                continue  # Skip this panel

            # Format and add the other panels
            text_sections.extend(format_panel_section(panel, unicode_body_style, unicode_heading_style))

    return text_sections

def download_image(url):
    """Download an image and return it as a BytesIO object."""
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

def generate_pdf(text_sections, images):
    """Generate a PDF with the given text and images and return it as a BytesIO object."""
    pdf_buffer = BytesIO()
    pdf = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    elements = []
    
    # Add text sections
    elements.extend(text_sections)

    # Add a Turkish heading before images
    if images:
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle(
            "Heading",
            parent=styles["Heading2"],
            fontName="DejaVu",
            fontSize=14,
            leading=16,
            spaceAfter=12,
        )
        elements.append(Paragraph("Resimler", heading_style))
        elements.append(Spacer(1, 12))  # Add space below the heading
    
    # Add images
    for img_url in images:
        img_data = download_image(img_url)
        img = Image(img_data, width=400, height=300)  # Adjust size as needed
        elements.append(img)
        elements.append(Spacer(1, 20))  # Add space between images
    
    pdf.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

@application.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form.get("url")
        if url:
            try:
                text_sections = extract_text_content(url)
                if not text_sections:
                    return render_template("index.html", message="No text content found.")
                
                image_urls = extract_specific_images(url)
                if not image_urls:
                    return render_template("index.html", message="No images found with the specific criteria.")
                
                pdf_buffer = generate_pdf(text_sections, image_urls)
                return send_file(
                    pdf_buffer,
                    as_attachment=True,
                    download_name="property_details.pdf",
                    mimetype="application/pdf",
                )
            except Exception as e:
                return render_template("index.html", message=f"Error: {str(e)}")
    
    return render_template("index.html")

if __name__ == "__main__":
    application.run(debug=True)
