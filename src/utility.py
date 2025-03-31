import json
import ast
import pdfkit
from xlsx2html import xlsx2html
import io, os
import fitz
import re


def load_json_file(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
        return data


def save_json_file(data, file_path):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
        print(f"JSON file saved at: {file_path}")


def clean_json_strings(json_str):
    clean_response = json_str.replace("```json\n", "").replace("```", "")
    response = ast.literal_eval(clean_response)
    return response


def normalize_string(s):
    return s.strip().lower()


def normalize_address(address):
    # Remove commas, spaces, and convert to lowercase
    normalized_address = re.sub(r"(\b[a-z]{2}\b),\1", r"\1", address)
    normalized_address = re.sub(r"[\s,]", "", address.lower())
    normalized_address = re.sub(r"[\s,.]", "", address.lower())
    return normalized_address


def remove_empty_pages(pdf_path, output_pdf_path):

    pdf_document = fitz.open(pdf_path)

    non_empty_pages = []
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text = page.get_text().strip()
        images = page.get_images()

        # Check if the page has any text or images
        if text or images:
            non_empty_pages.append(page_num)

    # Create a new PDF with only the non-empty pages
    new_pdf = fitz.open()
    for page_num in non_empty_pages:
        new_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)

    # Save the new PDF
    new_pdf.save(output_pdf_path)
    new_pdf.close()
    pdf_document.close()
    # print(f"Empty pages removed. New PDF saved at: {output_pdf_path}")


def excel_to_pdf(excel_path):
    # Convert Excel to HTML and store in a StringIO object
    html_stream = io.StringIO()
    xlsx2html(excel_path, html_stream)

    # Get the HTML content as a string
    html_content = html_stream.getvalue()

    # Save HTML content to a temporary file
    temp_html_file = "temp.html"
    with open(temp_html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Convert HTML to PDF using pdfkit
    temp_pdf_file = "temp.pdf"  # pdf file with empty pages
    pdfkit.from_file(temp_html_file, temp_pdf_file)

    pdf_path = excel_path.replace(".xlsx", ".pdf")
    remove_empty_pages(temp_pdf_file, pdf_path)
    # print(f"Excel file converted to PDF and saved at: {pdf_path}")

    # Delete the temporary HTML file
    os.remove(temp_html_file)
    os.remove(temp_pdf_file)
