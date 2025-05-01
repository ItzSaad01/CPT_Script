import os
import sys
import re
from pdf2image import convert_from_path
import pytesseract
from tkinter import Tk, filedialog
from tqdm import tqdm
from PIL import Image, ImageOps
from concurrent.futures import ThreadPoolExecutor, as_completed


BASE_DIR = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
# CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
# LOCAL_POPPLER_PATH = os.path.join(BASE_DIR, "poppler", "Library","bin")/
# LOCAL_TESSERACT_PATH = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")

# os.environ["PATH"] += os.pathsep + LOCAL_POPPLER_PATH
# pytesseract.pytesseract.tesseract_cmd = LOCAL_TESSERACT_PATH

TESSERACT_CONFIG = '--psm 6 --oem 1'
DPI = 300
MAX_THREADS = 4

cpt_pattern = r'\b\d{5}(?:-[A-Z0-9]{2})?\b'


def preprocess_image(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    bw = gray.point(lambda x: 0 if x < 160 else 255, '1')
    return bw

def process_page(args):
    page_index, image = args
    try:
        processed_img = preprocess_image(image)
        text = pytesseract.image_to_string(processed_img, lang='eng', config=TESSERACT_CONFIG)
        return page_index, text

    except Exception as e:
        print(f"[ERROR] OCR failed on page {page_index + 1}: {e}")
        return page_index, ""


def extract_text_from_pdf(pdf_path):

    print(f"\n[INFO] Processing '{os.path.basename(pdf_path)}'")
    try:
        # pages = convert_from_path(pdf_path, dpi=DPI, poppler_path=LOCAL_POPPLER_PATH)
        pages = convert_from_path(pdf_path, dpi=DPI, first_page=1, last_page=5)

    except Exception as e:
        print(f"[ERROR] Failed to convert PDF: {e}")
        return ""

    print(f"\n📄 Processing Image-PDF: {pdf_path} | Total Pages: {len(pages)}\n")

    results = [None] * len(pages)
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(process_page, (i, page)): i for i, page in enumerate(pages)}
        with tqdm(total=len(pages), desc="OCR", ncols=70) as pbar:
            for future in as_completed(futures):
                idx, text = future.result()
                results[idx] = (idx, text)
                pbar.update(1)
                
        # results = list(tqdm(executor.map(process_page, enumerate(pages)), total=len(pages), desc="OCR", ncols=70))

    results.sort()
    texts = [text for _, text in results]

    date_pattern = r'\d{2}[-/]\d{2}[-/]\d{4}'
    zip_words = ['drive', 'suite', 'street', 'ave', 'avenue', 'road', 'blvd', 'city', 'po box', 'zip', 'state', 'address']
    cpt_codes = []

    for page_text in texts:
        if len(page_text.strip()) < 200 or len(page_text.split()) < 150:
            continue

        for date in re.finditer(date_pattern, page_text):
            nearby_text = page_text[date.end():date.end() + 100]
            found_codes = re.findall(cpt_pattern, nearby_text)

            for code in found_codes:
                base_code = code.split('-')[0]
                
                if not base_code.isdigit() or not 10000 <= int(base_code) <= 99999:
                    continue

                context = page_text[max(date.end() - 40, 0):date.end() + 140].lower()
                if any(word in context for word in zip_words):
                    if code == base_code:
                        continue

                cpt_codes.append(code)

    return list(set(cpt_codes))


def save_codes_to_file(pdf_path, codes):

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_file = os.path.join(BASE_DIR, f"{base_name}_eob_codes.txt")

    print(f"[+] Saving extracted codes to {output_file}\n")
    with open(output_file, 'w') as f:
        for code in codes:
            f.write(code + '\n')

    print(f"[✓] SAVED {len(codes)} codes to '{output_file}'")

def process_pdf(pdf_path):
    codes = extract_text_from_pdf(pdf_path)
    if codes:
        save_codes_to_file(pdf_path, codes)
    else:
        print(f"[INFO] No CPT codes found in '{os.path.basename(pdf_path)}'.")


def main():

    print("[INFO] Select one or more PDF files to process")
    Tk().withdraw()
    
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])

    if not file_paths:
        print("[INFO] No files selected.")
        return

    for pdf_path in file_paths:
        process_pdf(pdf_path)

    print("\n[INFO] All PDFs processed successfully.")

if __name__ == "__main__":

    main()
    input("Press Enter to exit...")