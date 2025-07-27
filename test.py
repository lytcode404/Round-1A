import numpy as np
import joblib
import json
import os
import time

from helper.pdf_extractor import extract_lines_from_pdf

def predict_outline(pdf_path, model_path, timeout=0.5):
    clf = joblib.load(model_path)
    print(f"Loaded model from {model_path}")

    lines = extract_lines_from_pdf(pdf_path, timeout=timeout)
    if not lines:
        print(f"No lines extracted from {pdf_path}.")
        return {}

    features = np.array([[l['font_size'], int(l['is_bold']), len(l['text'])] for l in lines])
    preds = clf.predict(features)
    print(f"Predicted labels for {len(preds)} lines.")

    title = ""
    max_title_font = -1
    for line, pred in zip(lines, preds):
        if pred.lower() == "title" and line['font_size'] > max_title_font:
            title = line['text']
            max_title_font = line['font_size']

    outline = []
    for line, pred in zip(lines, preds):
        level = pred.upper()
        if level in {"H1", "H2", "H3"}:
            if line['text'] != title:
                outline.append({
                    "level": level,
                    "text": line['text'],
                    "page": line['page']
                })

    json_output = {
        "title": title,
        "outline": outline
    }

    return json_output

def main():
    pdf_path = "train-test/1.pdf"  # Change to your PDF to test
    model_path = "heading_classifier.pkl"
    output_dir = "test-results"
    os.makedirs(output_dir, exist_ok=True)
    output_json_path = os.path.join(output_dir, os.path.splitext(os.path.basename(pdf_path))[0] + "_outline.json")

    print("Starting outline prediction...")
    start_time = time.time()
    outline_json = predict_outline(pdf_path, model_path, timeout=0.5)
    end_time = time.time()
    print(f"Completed in {end_time - start_time:.2f} seconds.")

    if outline_json:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(outline_json, f, indent=4, ensure_ascii=False)
        print(f"Outline JSON saved to: {output_json_path}")
        print(json.dumps(outline_json, indent=4, ensure_ascii=False))
    else:
        print("No outline generated.")

if __name__ == "__main__":
    main()
