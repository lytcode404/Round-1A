import os
from pypdf import PdfReader, PdfWriter

folder_path = 'train-test'
batch_size = 10

def safe_pdf_read(path):
    """
    Try reading a PDF file. If it's corrupted, delete it and return None.
    """
    try:
        reader = PdfReader(path)
        # Force load pages to catch EOF or other read errors early
        _ = reader.pages
        return reader
    except Exception as e:
        print(f"Error reading {path}: {e}. Deleting corrupted file.")
        try:
            os.remove(path)
            print(f"Deleted corrupted file: {path}")
        except Exception as del_err:
            print(f"Failed to delete corrupted file {path}: {del_err}")
        return None

def merge_pdfs(batch_files, output_path):
    writer = PdfWriter()
    merged_files = []
    for pdf_file in batch_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        reader = safe_pdf_read(pdf_path)
        if reader is None:
            # Corrupted file deleted in safe_pdf_read; skip it
            continue
        try:
            for page in reader.pages:
                writer.add_page(page)
            merged_files.append(pdf_file)
        except Exception as e:
            print(f"Error adding pages from {pdf_file}: {e}. Skipping this file.")
    if not merged_files:
        print(f"No valid PDFs to merge for {output_path}. Skipping merge.")
        return []

    # Write merged file
    try:
        with open(output_path, 'wb') as out_f:
            writer.write(out_f)
        print(f"Merged {len(merged_files)} PDFs into {output_path}")
    except Exception as e:
        print(f"Error writing merged PDF {output_path}: {e}")
        # Consider deleting the output file if partial or corrupted
        if os.path.exists(output_path):
            os.remove(output_path)
        return []

    return merged_files

# Main processing
pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
pdf_files.sort()

batch_num = 1
idx = 0

while idx < len(pdf_files):
    current_batch = pdf_files[idx: idx + batch_size]
    output_pdf_name = f"{batch_num}.pdf"
    output_pdf_path = os.path.join(folder_path, output_pdf_name)

    merged_files = merge_pdfs(current_batch, output_pdf_path)
    if merged_files:
        # Delete for merged files only
        for f in merged_files:
            try:
                os.remove(os.path.join(folder_path, f))
                print(f"Deleted original file {f} after merging.")
            except Exception as e:
                print(f"Failed to delete original file {f}: {e}")

        # Increment batch num and idx by number of files merged
        batch_num += 1
        idx += len(current_batch)
    else:
        # No files merged - likely all were corrupted in this batch, skip them anyway
        print(f"No files merged in batch starting at index {idx}, skipping these files.")
        # Delete all these files as corrupted (they would have been deleted already), but defensively:
        for f in current_batch:
            path = os.path.join(folder_path, f)
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"Deleted leftover file {f} in skipped batch.")
                except Exception as e:
                    print(f"Failed to delete leftover file {f}: {e}")
        # Move index forward
        idx += len(current_batch)

print("All done.")
