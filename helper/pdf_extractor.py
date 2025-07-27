import fitz
from multiprocessing import Process, Queue

def is_page_complex(page):
    blocks = page.get_text("dict")["blocks"]
    num_text_blocks = 0
    num_spans = 0
    num_image_blocks = 0
    for block in blocks:
        if block['type'] == 1:
            num_image_blocks += 1
        elif block['type'] == 0:
            num_text_blocks += 1
            spans_count = sum(len(line["spans"]) for line in block.get("lines", []))
            num_spans += spans_count
    if num_image_blocks >= 1:
        return True
    if num_text_blocks > 20 and num_spans > 200:
        return True
    return False

def extract_lines_page_worker(pdf_path, page_num, q):
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        if is_page_complex(page):
            q.put(None)
            doc.close()
            return
        lines = []
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                span = line["spans"][0]
                x1 = min(s['bbox'][0] for s in line['spans'])
                y1 = min(s['bbox'][1] for s in line['spans'])
                x2 = max(s['bbox'][2] for s in line['spans'])
                y2 = max(s['bbox'][3] for s in line['spans'])
                text = ''.join(s["text"] for s in line["spans"]).strip()
                font_size = span["size"]
                is_bold = (span["flags"] & 2**2) != 0
                lines.append({
                    "page": page_num + 1,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "font_size": font_size,
                    "is_bold": is_bold,
                    "text": text
                })
        q.put(lines)
        doc.close()
    except Exception:
        q.put(None)

def extract_lines_from_pdf(pdf_path, timeout):
    import time
    import os
    from multiprocessing import Process, Queue

    import fitz  # Ensure imported here or handle differently in training/testing

    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()
    all_lines = []
    print(f"Extracting lines from {os.path.basename(pdf_path)} ...")

    skipped_complex = 0
    skipped_timeout = 0

    for page_num in range(num_pages):
        print(f"  Processing page {page_num + 1} ...", end=' ')
        q = Queue()
        p = Process(target=extract_lines_page_worker, args=(pdf_path, page_num, q))
        p.start()
        p.join(timeout)
        if p.is_alive():
            p.terminate()
            p.join()
            print(f"skipped (timeout >{int(timeout * 1000)} ms).")
            skipped_timeout += 1
            continue
        try:
            lines = q.get_nowait()
        except Exception:
            print("skipped (no output from worker).")
            skipped_timeout += 1
            continue
        if lines is None:
            print("skipped (complexity or error).")
            skipped_complex += 1
            continue
        print(f"extracted {len(lines)} lines.")
        all_lines.extend(lines)

    print(f"Total lines extracted: {len(all_lines)}")
    print(f"Pages skipped due to complexity: {skipped_complex}")
    print(f"Pages skipped due to timeout: {skipped_timeout}")

    return all_lines
