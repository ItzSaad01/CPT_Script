import os
import sys
import re
from pdf2image import convert_from_path
import pytesseract
from tkinter import Tk, filedialog
from tqdm import tqdm
import cv2
import numpy as np


#BASE_DIR = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
# LOCAL_POPPLER_PATH = os.path.join(CURRENT_DIR, "poppler", "Library","bin")
# LOCAL_TESSERACT_PATH = os.path.join(CURRENT_DIR, "tesseract", "tesseract.exe")

# os.environ["PATH"] += os.pathsep + LOCAL_POPPLER_PATH
# pytesseract.pytesseract.tesseract_cmd = LOCAL_TESSERACT_PATH

pattern = r'(?<!\d)(\b[1-9]\d{4}(?:-[A-Z0-9]{2})?\b)(?!\.\d{2})'

def preprocess_image(pil_img):
    open_cv_image = np.array(pil_img.convert('L'))
    blurred = cv2.GaussianBlur(open_cv_image, (5,5), 0)
    _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresholded

def extract_text_from_pdf(pdf_path):

    print(f"\n[INFO] Processing '{os.path.basename(pdf_path)}'")
    try:
        pages = convert_from_path(pdf_path, dpi=400)

    except Exception as e:
        print(f"[ERROR] Failed to convert PDF: {e}")
        return ""

    print(f"\n📄 Processing Image-PDF: {pdf_path}\nTotal Pages: {len(pages)}\n")

    date_pattern = r'\d{2}[-/]\d{2}[-/]\d{4}'
    # pattern = r'\b\d{5}(?:-[A-Z0-9]{2})?\b'
    cpt_codes = []

    for i, page in enumerate(tqdm(pages, desc="OCR Processing", ncols=70)):
        preprocessed = preprocess_image(page)
        page_text = pytesseract.image_to_string(preprocessed)

        MINIMUM_WORDS = 100
        if len(page_text.strip()) < 150 or len(page_text.split()) < MINIMUM_WORDS:
            continue

        dates = list(re.finditer(date_pattern, page_text))

        if not dates:
            continue

        for date in dates:
            nearby_text = page_text[date.end():date.end() + 100]
            found_codes = re.findall(pattern, nearby_text)

            for code in found_codes:

                base_code = code.split('-')[0]

                if not 10000 <= int(base_code) <= 99999:
                    continue
                
                full_context_start = max(date.end() - 40, 0)
                full_context_end = min(date.end() + 100 + 40, len(page_text))
                context_text = page_text[full_context_start:full_context_end].lower()
                zip_words = ['drive', 'suite','street', 'ave', 'avenue', 'road', 'blvd', 'city', 'po box', 'zip', 'state', 'address']

                if any(word in context_text for word in zip_words):
                    if code == base_code:
                        continue

                cpt_codes.append(code)

    return list(set(cpt_codes))

def save_codes_to_file(pdf_path, codes):

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(CURRENT_DIR, f"{base_name}_eob_codes.txt")

    print(f"[+] Saving extracted codes to {output_file}...\n")
    with open(output_file, 'w') as f:
        for code in codes:
            f.write(code + '\n')

    print(f"[INFO] Saved {len(codes)} codes to '{output_file}'")

def main():

    print("[INFO] Select one or more PDF files to process")
    Tk().withdraw()
    
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])

    if not file_paths:
        print("[INFO] No files selected.")
        return

    for pdf_path in file_paths:
        codes = extract_text_from_pdf(pdf_path)

        if codes:
            save_codes_to_file(pdf_path, codes)
        else:
            print("[INFO] No CPT codes found.")

if __name__ == "__main__":
    main()

    input("Press Enter to exit")