import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from googletrans import Translator
import re

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
        # print('1')
        translated = translator.translate(text, src=src_language, dest=target_language)
        # translated = translator.translate(text, dest=target_language)
        return translated.text
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

# def translate_text(text, target_language='tr', src_language='tr'):
#     """
#     Translate text while preserving HTML-like elements.
    
#     Args:
#         text (str): The text to be translated.
#         target_language (str): The language to translate into (default is 'tr').
#         src_language (str): The source language (default is 'tr').
    
#     Returns:
#         str: Translated text with original HTML-like elements restored.
#     """
#     # Store original tags and replace with numbered placeholders
#     tag_pattern = r'<[^>]+>'
#     tags = re.findall(tag_pattern, text)
    
#     # Replace each tag with a unique placeholder
#     modified_text = text
#     for i, tag in enumerate(tags):
#         placeholder = f'[TAG{i}]'
#         modified_text = modified_text.replace(tag, placeholder)
    
#     # Translate the modified text
#     translator = Translator()
#     try:
#         translated = translator.translate(modified_text, src=src_language, dest=target_language)
#         translated_text = translated.text
        
#         # Restore the original tags
#         for i, tag in enumerate(tags):
#             placeholder = f'[TAG{i}]'
#             translated_text = translated_text.replace(placeholder, tag)
        
#         return translated_text
    
#     except Exception as e:
#         print(f"Translation error: {e}")
#         return text  # Return original text if translation fails


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

def format_description_section(description_div, unicode_style, unicode_heading_style, target_language='tr'):
    """Format the description section with proper styles."""
    elements = []

    # Process all content in order
    for element in description_div.children:
        if element.name == 'h4':
            # Handle headings
            text = element.get_text(strip=True)
            if text:
                translated_text = translate_text(text, target_language)
                elements.append(Paragraph(f"<b>{translated_text}</b>", unicode_heading_style))
                elements.append(Spacer(1, 6))

        elif element.name == 'p':
            # Handle paragraphs
            text = element.get_text(strip=True)
            if text:
                translated_text = translate_text(text, target_language)
                elements.append(Paragraph(translated_text, unicode_style))
                elements.append(Spacer(1, 4))

        elif element.name == 'ul':
            # Handle bullet point lists
            for li in element.find_all('li'):
                text = li.get_text(strip=True)
                if text:
                    translated_text = translate_text(text, target_language)
                    elements.append(Paragraph(f"• {translated_text}", unicode_style))
                    elements.append(Spacer(1, 4))

        elif element.name == 'hr':
            # Add extra space for horizontal rules
            elements.append(Spacer(1, 10))

    return elements

# def format_description_section(description_div, unicode_style, unicode_heading_style, target_language='tr'):
#     """
#     Format the description section with proper styles, handling nested content and all text sections.
    
#     Args:
#         description_div: BeautifulSoup object containing the description section
#         unicode_style: ReportLab style for regular text
#         unicode_heading_style: ReportLab style for headings
#         target_language: Target language for translation (default: 'tr')
        
#     Returns:
#         List of ReportLab elements (Paragraphs and Spacers)
#     """
#     elements = []
    
#     def process_element(element, level=0):
#         """Recursively process elements and their children."""
#         if not element:
#             return
        
#         # Handle different element types
#         if isinstance(element, str):
#             text = element.strip()
#             if text:
#                 translated_text = translate_text(text, target_language)
#                 elements.append(Paragraph(translated_text, unicode_style))
#                 elements.append(Spacer(1, 4))
#             return
        

#         # Process based on tag type
#         tag_name = element.name if hasattr(element, 'name') else None
#         print(tag_name)
        
#         if tag_name == 'h3' or tag_name == 'h4':
#             text = element.get_text(strip=True)
#             if text:
#                 translated_text = translate_text(text, target_language)
#                 elements.append(Paragraph(f"<b>{translated_text}</b>", unicode_heading_style))
#                 elements.append(Spacer(1, 6))
                
#         elif tag_name == 'p':
#             # Handle paragraphs, including those with nested elements
#             all_text = []
#             for content in element.contents:
#                 if content.name == 'strong' or content.name == 'b':
#                     text = content.get_text(strip=True)
#                     if text:
#                         all_text.append(f"<b>{text}</b>")
#                 elif content.name == 'a':
#                     text = content.get_text(strip=True)
#                     if text:
#                         all_text.append(text)
#                 else:
#                     text = str(content).strip()
#                     if text:
#                         all_text.append(text)
            
#             combined_text = ' '.join(all_text).strip()
#             if combined_text:
#                 # print(combined_text)
#                 translated_text = translate_text(combined_text, target_language)
#                 print(translated_text)
#                 elements.append(Paragraph(translated_text, unicode_style))
#                 elements.append(Spacer(1, 4))
                
#         elif tag_name == 'ul':
#             for li in element.find_all('li', recursive=False):
#                 bullet_text = []
#                 for content in li.contents:
#                     if content.name == 'strong' or content.name == 'b':
#                         text = content.get_text(strip=True)
#                         if text:
#                             bullet_text.append(f"<b>{text}</b>")
#                     else:
#                         text = str(content).strip()
#                         if text:
#                             bullet_text.append(text)
                
#                 combined_text = ' '.join(bullet_text).strip()
#                 if combined_text:
#                     translated_text = translate_text(combined_text, target_language)
#                     elements.append(Paragraph(f"• {translated_text}", unicode_style))
#                     elements.append(Spacer(1, 4))
                    
#         elif tag_name == 'hr':
#             elements.append(Spacer(1, 10))
            
#         elif tag_name == 'div':
#             # Process all children of div elements
#             for child in element.children:
#                 process_element(child, level + 1)
                
#         # Process any remaining children for other element types
#         if hasattr(element, 'children'):
#             for child in element.children:
#                 if child.name not in ['img', 'script', 'style']:  # Skip certain elements
#                     process_element(child, level + 1)
    
#     # Start processing from the root element
#     process_element(description_div)

#     print(elements)
    
#     return elements

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

        # description_div = soup.find("div", class_="wpestate_property_description property-panel")
        # if description_div:
        #     text_sections.extend(format_overview_section(description_div, unicode_body_style, unicode_heading_style, target_language))

        description_div = soup.find("div", class_="wpestate_property_description property-panel")
        if description_div:
            text_sections.extend(format_description_section(description_div, unicode_body_style, unicode_heading_style, target_language))

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
