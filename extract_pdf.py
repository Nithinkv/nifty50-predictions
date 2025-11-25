import pypdf
import os

pdf_path = "3.+Machine+Learning-Based+Automated+Trading+Strategies+for+the+Indian+Stock+Market.pdf"

try:
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    with open("paper_content.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Text extracted to paper_content.txt")
except Exception as e:
    print(f"Error reading PDF: {e}")
