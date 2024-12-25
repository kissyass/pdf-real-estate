import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from googletrans import Translator

def translate_text(text, target_language='tr', src_language='tr'):
    """
    Translate text to the target language.
    Args:
        text (str): The text to be translated.
        target_language (str): The language to translate into (default is 'en').
    Returns:
        str: Translated text.
    """
    translator = Translator()
    try:
        # Perform the translation
        translated = translator.translate(text, src=src_language, dest=target_language)
        # translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

def format_overview_section(overview_div, unicode_style, unicode_heading_style, target_language='tr'):
    """Format the overview section with proper styles."""
    elements = []

    # Extract and format the heading
    heading = overview_div.find("h4", class_="panel-title")
    if heading:
        translated_heading = translate_text(heading.get_text(strip=True), target_language)
        elements.append(Paragraph(f"<b>{translated_heading}</b>", unicode_heading_style))
        # elements.append(Paragraph(f"<b>{heading.get_text(strip=True)}</b>", unicode_heading_style))
        elements.append(Spacer(1, 6))  # Add space below the heading

    # Extract details with improved formatting
    details = overview_div.find_all("ul", class_="overview_element")
    for detail in details:
        items = detail.find_all("li")
        for item in items:
            text = item.get_text(strip=True)
            if text:  # Ignore empty lines
                translated_text = translate_text(text, target_language)
                elements.append(Paragraph(f"• {translated_text}", unicode_style))  # Bullet points for details
                # elements.append(Paragraph(f"• {text}", unicode_style))  # Bullet points for details
                elements.append(Spacer(1, 4))  # Add space between points

    return elements

def format_panel_section(panel_div, unicode_style, unicode_heading_style, target_language='tr'):
    """Format a panel section with heading and details."""
    elements = []

    # Extract and format the panel heading
    heading = panel_div.find("h4", class_="panel-title")
    if heading:
        translated_heading = translate_text(heading.get_text(strip=True), target_language)
        elements.append(Paragraph(f"<b>{translated_heading}</b>", unicode_heading_style))
        # elements.append(Paragraph(f"<b>{heading.get_text(strip=True)}</b>", unicode_heading_style))
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
            translated_txt = translate_text(formatted_text, target_language)
            elements.append(Paragraph(translated_txt.strip(":"), unicode_style))
            # elements.append(Paragraph(formatted_text.strip(":"), unicode_style))
            elements.append(Spacer(1, 4))  # Add space between details

    return elements

def extract_text_content(url, target_language='tr'):
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
            text_sections.extend(format_overview_section(overview_div, unicode_body_style, unicode_heading_style, target_language))

        description_div = soup.find("div", class_="wpestate_property_description property-panel")
        if description_div:
            text_sections.extend(format_overview_section(description_div, unicode_body_style, unicode_heading_style, target_language))

        panel_divs = soup.find_all("div", class_="panel panel-default")
        for panel in panel_divs[:-1]:  # Skip the last one
            heading = panel.find("h4", class_="panel-title")
            if heading and "Harita" not in heading.get_text(strip=True):
                text_sections.extend(format_panel_section(panel, unicode_body_style, unicode_heading_style, target_language))

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
