from flask import Flask, render_template, request, send_file, session, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from models import db
from auth import auth
from helpers import resize_and_save_logo, generate_footer_template, generate_content_pdf, overlay_footer_on_content, generate_content_pdf_with_footer_check, get_footer_height
from extractors import extract_text_content, extract_specific_images
from functools import wraps
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

application = Flask(__name__)
application.secret_key = 'ac2a886207a64fc58632b2f997afb0e9'
application.config["UPLOAD_FOLDER"] = "static/uploads"
pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

# Database configuration
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(application)

# Register the authentication blueprint
application.register_blueprint(auth)

# Create tables
with application.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@application.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        url = request.form.get("url")
        target_language = request.form.get("language")  # Get selected language
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
        text_sections = extract_text_content(url, target_language)

        images = extract_specific_images(url)

        # # Generate content PDF
        # content_pdf = generate_content_pdf(text_sections, images)

        # # Generate footer template
        # footer_pdf = generate_footer_template(contact_info, target_language, logo_path=resize_and_save_logo(logo_file, application.config["UPLOAD_FOLDER"]))

        # # Overlay footer on content
        # final_pdf = overlay_footer_on_content(footer_pdf, content_pdf)


        # Calculate footer height
        footer_height = get_footer_height(contact_info)

        # Generate content PDF with footer height consideration
        content_pdf = generate_content_pdf_with_footer_check(text_sections, images, footer_height)

        # Generate footer template
        footer_pdf = generate_footer_template(contact_info, target_language, logo_path=resize_and_save_logo(logo_file, application.config["UPLOAD_FOLDER"]))

        # Overlay footer on content
        final_pdf = overlay_footer_on_content(footer_pdf, content_pdf)

        return send_file(final_pdf, as_attachment=True, download_name="final_document.pdf", mimetype="application/pdf")

    return render_template("index.html")

if __name__ == "__main__":
    application.run(debug=True)
