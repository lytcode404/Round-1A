import fitz
import json
import re
import os
import time
from multiprocessing import Process, Queue

def is_bold(span):
    return (span["flags"] & 2**2) != 0

def looks_like_heading(line_text):
    return (
        bool(re.match(r"^(\d+(\.\d+)*|[IVXLC]+)\.?\s?[\w ]+$", line_text))
        or (line_text.isupper() and 3 <= len(line_text.split()) <= 12)
        or (len(line_text.split()) < 12 and not any(c.islower() for c in line_text))
    )

def is_page_complex(page):
    blocks = page.get_text("dict")["blocks"]
    num_text_blocks = 0
    num_spans = 0
    num_image_blocks = 0
    for block in blocks:
        if block['type'] == 1:
            num_image_blocks += 1
        if block['type'] == 0:
            num_text_blocks += 1
            spans_count = sum(len(line["spans"]) for line in block.get("lines", []))
            num_spans += spans_count
    if num_image_blocks >= 1:
        return True
    if num_text_blocks > 20 and num_spans > 200:
        return True
    return False

def parse_page_worker(pdf_path, page_num, h1_thresh, h2_thresh, h3_thresh, q):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    if is_page_complex(page):
        q.put({
            "title": None, "headings": [],
            "skipped": True, "reason": "Complex content detected (table/images)"
        })
        doc.close()
        return
    result = {"title": None, "headings": [], "skipped": False, "reason": ""}
    blocks = page.get_text("dict")["blocks"]
    title_found = False
    for block in blocks:
        if "lines" not in block: continue
        for line in block["lines"]:
            line_text = "".join([span["text"] for span in line["spans"]]).strip()
            if not line_text:
                continue
            sizes = [span["size"] for span in line["spans"]]
            max_size = max(sizes)
            any_bold = any(is_bold(span) for span in line["spans"])
            if not title_found and max_size >= h1_thresh:
                result["title"] = line_text
                title_found = True
            if max_size >= h1_thresh or (any_bold and looks_like_heading(line_text)):
                result["headings"].append({"level": "H1", "text": line_text, "page": page_num + 1})
            elif max_size >= h2_thresh or (looks_like_heading(line_text) and len(line_text.split()) <= 10):
                result["headings"].append({"level": "H2", "text": line_text, "page": page_num + 1})
            elif max_size >= h3_thresh or (any_bold and len(line_text.split()) <= 15):
                result["headings"].append({"level": "H3", "text": line_text, "page": page_num + 1})
    q.put(result)
    doc.close()

def extract_outline_from_pdf(pdf_path, timeout_per_page=2, limit=-1):
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    outline = {"title": "", "outline": []}
    # Always use minimum of pages and limit (unless limit == -1 meaning no limit)
    if limit != -1:
        num_pages = min(num_pages, limit)
    font_sizes = []
    pages_to_sample = min(5, num_pages)
    for page_num in range(pages_to_sample):
        try:
            blocks = doc[page_num].get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span["size"])
        except Exception:
            continue
    doc.close()
    if not font_sizes:
        print("No text extracted.")
        return outline
    unique_sizes = sorted(set(font_sizes), reverse=True)
    h1_thresh = unique_sizes[0]
    h2_thresh = unique_sizes[1] if len(unique_sizes) > 1 else h1_thresh - 2
    h3_thresh = unique_sizes[2] if len(unique_sizes) > 2 else h2_thresh - 2

    for page_num in range(num_pages):
        q = Queue()
        p = Process(target=parse_page_worker, args=(pdf_path, page_num, h1_thresh, h2_thresh, h3_thresh, q))
        p.start()
        p.join(timeout_per_page)
        if p.is_alive():
            p.terminate()
            p.join()
            print(f"Skipped page {page_num+1}/{num_pages} due to timeout >{int(timeout_per_page*1000)} ms.")
            continue
        try:
            result = q.get_nowait()
        except Exception:
            print(f"Skipped page {page_num+1}/{num_pages} due to no output from worker.")
            continue
        if result.get("skipped"):
            print(f"Skipped page {page_num+1}/{num_pages}: {result.get('reason')}")
            continue
        print(f"Parsed page {page_num+1}/{num_pages}")
        if not outline["title"] and result.get("title"):
            outline["title"] = result["title"]
        for hd in result.get("headings", []):
            if hd["text"] != outline["title"]:
                outline["outline"].append(hd)
    return outline

def process_all_pdfs(input_dir="input", output_dir="output", timeout=2, limit=-1):
    os.makedirs(output_dir, exist_ok=True)
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in input directory.")
        return
    for pdf_file in pdf_files:
        input_path = os.path.join(input_dir, pdf_file)
        output_path = os.path.join(output_dir, os.path.splitext(pdf_file)[0] + ".json")
        print(f"Processing '{pdf_file}'...")
        outline = extract_outline_from_pdf(input_path, timeout, limit=limit)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(outline, f, indent=4, ensure_ascii=False)
        print(f"Saved outline to '{output_path}'")

if __name__ == "__main__":
    # Change the limit here
    limit = 50  # set to -1 for no page limit, or 50 for up to 50 pages per PDF
    process_all_pdfs(timeout=2, limit=limit)
