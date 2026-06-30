from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import uuid
import fitz

from extractors.unified_extractor import UnifiedExtractor
from aligners.logical_aligner import LogicalAligner
from comparators.replace import ReplaceComparator
from comparators.insertion_deletion import InsertionDeletionComparator
from comparators.comparison_engine import ComparisonEngine
from renderer.pdf_renderer import PDFRenderer

app = Flask(__name__)

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "static", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "expected_pdf" not in request.files or "actual_pdf" not in request.files:
        return jsonify({"error": "Both Expected and Actual PDFs are required."}), 400

    expected_file = request.files["expected_pdf"]
    actual_file = request.files["actual_pdf"]

    if expected_file.filename == "" or actual_file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    run_id = str(uuid.uuid4())
    run_dir = os.path.join(CACHE_DIR, run_id)
    os.makedirs(run_dir, exist_ok=True)

    expected_path = os.path.join(run_dir, "expected.pdf")
    actual_path = os.path.join(run_dir, "actual.pdf")
    annotated_path = os.path.join(run_dir, "annotated_actual.pdf")

    expected_file.save(expected_path)
    actual_file.save(actual_path)

    try:
        # Step 1: Extract
        extractor = UnifiedExtractor()
        left_doc = extractor.extract(expected_path)
        right_doc = extractor.extract(actual_path)

        # Step 2: Align
        aligner = LogicalAligner()
        pairs = aligner.align(left_doc, right_doc)

        # Step 3: Compare
        engine = ComparisonEngine(
            comparators=[
                ReplaceComparator(),
                InsertionDeletionComparator()
            ]
        )
        differences = engine.compare(pairs)

        # Step 4: Render Annotated PDF (marked actual PDF)
        renderer = PDFRenderer()
        renderer.render(
            input_pdf=actual_path,
            output_pdf=annotated_path,
            differences=differences
        )

        # Step 5: Render Page Images for Left (Expected) PDF
        left_pages = []
        left_doc_fitz = fitz.open(expected_path)
        for idx, page in enumerate(left_doc_fitz):
            pix = page.get_pixmap(dpi=150)
            img_name = f"left_page_{idx + 1}.png"
            pix.save(os.path.join(run_dir, img_name))
            left_pages.append({
                "url": f"/static/cache/{run_id}/{img_name}",
                "width": float(page.rect.width),
                "height": float(page.rect.height)
            })
        left_doc_fitz.close()

        # Step 6: Render Page Images for Right (Actual) PDF
        right_pages = []
        right_doc_fitz = fitz.open(actual_path)
        for idx, page in enumerate(right_doc_fitz):
            pix = page.get_pixmap(dpi=150)
            img_name = f"right_page_{idx + 1}.png"
            pix.save(os.path.join(run_dir, img_name))
            right_pages.append({
                "url": f"/static/cache/{run_id}/{img_name}",
                "width": float(page.rect.width),
                "height": float(page.rect.height)
            })
        right_doc_fitz.close()

        # Step 7: Serialize Differences
        serialized_diffs = []
        for i, diff in enumerate(differences):
            left_target = None
            if diff.expected_word:
                left_target = {
                    "page": diff.expected_word.page,
                    "bbox": list(diff.expected_word.bbox)
                }
            elif diff.expected_line:
                left_target = {
                    "page": diff.expected_line.page,
                    "bbox": list(diff.expected_line.bbox)
                }

            right_target = None
            if diff.actual_word:
                right_target = {
                    "page": diff.actual_word.page,
                    "bbox": list(diff.actual_word.bbox)
                }
            elif diff.actual_line:
                right_target = {
                    "page": diff.actual_line.page,
                    "bbox": list(diff.actual_line.bbox)
                }

            serialized_diffs.append({
                "id": i + 1,
                "category": diff.category.value,
                "severity": diff.severity.value,
                "confidence": diff.confidence,
                "description": diff.description,
                "expected_text": diff.expected_text,
                "actual_text": diff.actual_text,
                "left_target": left_target,
                "right_target": right_target
            })

        return jsonify({
            "run_id": run_id,
            "left_pages": left_pages,
            "right_pages": right_pages,
            "differences": serialized_diffs,
            "download_url": f"/api/download/{run_id}"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/<run_id>")
def download(run_id):
    run_dir = os.path.join(CACHE_DIR, run_id)
    if not os.path.exists(run_dir):
        return "Not Found", 404
    return send_from_directory(
        directory=run_dir,
        path="annotated_actual.pdf",
        as_attachment=True,
        download_name="annotated_document.pdf"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
