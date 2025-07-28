```markdown
# 🧠 Intelligent PDF Outline Extractor — Adobe Challenge 2025 Round 1A

This project is a CPU-optimized, Docker-compatible Python tool that intelligently extracts document outlines (titles and headings like H1, H2, H3) from a collection of PDFs. It is designed to work offline, without OCR or internet access, and processes up to 50-page PDFs in under 10 seconds.

---

## 📌 Problem Statement

In Round 1A of the Adobe Challenge 2025, the goal is to build a system that:
- Analyzes PDFs,
- Detects the hierarchical structure of content (Title, H1, H2, H3),
- Outputs the structure in a predefined JSON format,
- Runs on CPU without OCR or external APIs,
- Works efficiently within memory (~200MB) and time (<10s) constraints.

---

## ⚙️ Features

- 🧠 **Heuristic-based heading detection** (based on font size, boldness, layout patterns)
- ⚡ **Multiprocessing** for fast per-page analysis with timeouts
- 🧱 **Level-wise heading classification** (`title`, `h1`, `h2`, `h3`)
- ⛔ **Skips noisy pages** with tables/images or malformed structures
- 💾 **Structured JSON output** for each PDF
- 🖥️ **Runs completely offline (no OCR/API/internet)**

---

## 📂 Project Structure

```

├── input/                  # Folder to store input PDF files
├── output/                 # Folder where JSON outputs are saved
├── main.py                 # Main script to process all PDFs
├── extract\_outline.py      # Logic to extract outline from a single PDF
├── requirements.txt        # Python dependencies
├── Dockerfile              # (Optional) Docker setup for deployment
└── README.md               # You're here!

````

---

## 📥 Input

Place your PDFs inside the `input/` folder.

---

## 📤 Output

Each output JSON will be saved in the `output/` folder, named after the input PDF.

Example output (`output/sample.json`):

```json
{
  "title": "South of France - Cities",
  "headings": [
    { "text": "Introduction", "level": "h1", "page_no": 1 },
    { "text": "Nice", "level": "h2", "page_no": 2 },
    { "text": "Food & Culture", "level": "h3", "page_no": 3 }
  ]
}
````

---

## 🚀 How to Run

### 📦 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Ensure you're using Python 3.8+ and compatible versions of `PyMuPDF` and `numpy==1.x` (for compatibility with `fitz`).

> ⚠️ If using `numpy>=2.x`, you may face crashes due to binary incompatibilities. Downgrade if needed.

### ▶️ 2. Run the Extractor

```bash
python main.py
```

All PDFs in `input/` will be processed, and corresponding JSONs will be saved to `output/`.

---

## 🧠 How It Works

1. **Font Analysis**: The first 5 pages are scanned to determine the most common font sizes and bold styles.
2. **Heading Heuristics**: Each line is checked for:

   * Large font size,
   * Bold font,
   * Regex match (e.g., numbered sections),
   * Layout cues (e.g., centered, short spans).
3. **Heading Classification**:

   * Largest font → `title`
   * Next → `h1`
   * Medium → `h2`
   * Smallest acceptable → `h3`
4. **Timeout Per Page**: Each page is parsed in a separate process with a timeout (default 2s) to prevent crashes.
5. **Output**: Structured JSON is written with detected headings and page numbers.

---

## 🐳 Optional: Docker Support

You can run the system in a container (CPU-only):

```bash
docker build -t pdf-outline .
docker run -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" pdf-outline
```

---

## 🛠 Troubleshooting

* **PyMuPDF crashes with NumPy 2.x**: Downgrade NumPy to `<2.0`
* **PDF too complex / skipped**: Page may contain images/tables or too many blocks
* **Heading detection inaccurate?** Tweak thresholds in `extract_outline.py`

---

## 🏁 Challenge Compliance

| Constraint        | Met? | Notes                                    |
| ----------------- | ---- | ---------------------------------------- |
| CPU-only          | ✅    | No GPU dependencies                      |
| ≤200MB model size | ✅    | No ML models used                        |
| ≤10 seconds       | ✅    | Uses multiprocessing with timeouts       |
| Structured output | ✅    | Outputs clean JSON with title + headings |
| No OCR            | ✅    | Text extraction uses `fitz` only         |

---

## ✍️ Author

Built :-
Dilshad: rdilshad3559@gmail.com 
Sania Gupta: saniagupta3107@gmail.com

For Adobe Challenge 2025 — Round 1A
---

## 📄 License

MIT License

```
