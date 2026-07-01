import os
import uuid
from collections import Counter
import sys

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
)

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# -----------------------------
# Existing project imports
# -----------------------------

from extractors.unified_extractor import UnifiedExtractor
from aligners.logical_aligner import LogicalAligner

from comparators.replace import ReplaceComparator
from comparators.analyzers.formatting import FormattingComparator
from comparators.comparison_engine import ComparisonEngine

from renderer.pdf_renderer import PDFRenderer


# -----------------------------
# Flask
# -----------------------------

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(
    PROJECT_ROOT,
    "dashboard",
    "uploads",
)

OUTPUT_FOLDER = os.path.join(
    PROJECT_ROOT,
    "output",
)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ---------------------------------------------------
# Home
# ---------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------
# Compare
# ---------------------------------------------------

@app.route("/compare", methods=["POST"])
def compare():

    if "expected" not in request.files:
        return jsonify(
            {
                "success": False,
                "message": "Expected PDF missing.",
            }
        )

    if "actual" not in request.files:
        return jsonify(
            {
                "success": False,
                "message": "Actual PDF missing.",
            }
        )

    expected = request.files["expected"]
    actual = request.files["actual"]

    expected_path = os.path.join(
        UPLOAD_FOLDER,
        "expected.pdf",
    )

    actual_path = os.path.join(
        UPLOAD_FOLDER,
        "actual.pdf",
    )

    expected.save(expected_path)
    actual.save(actual_path)

    # -------------------------------------------
    # Pipeline
    # -------------------------------------------

    extractor = UnifiedExtractor()

    left_document = extractor.extract(expected_path)

    right_document = extractor.extract(actual_path)

    aligner = LogicalAligner()

    aligned_pairs = aligner.align(
        left_document,
        right_document,
    )

    engine = ComparisonEngine(

        comparators=[

            ReplaceComparator(),

            FormattingComparator(),

        ]

    )

    differences = engine.compare(
        aligned_pairs
    )

    renderer = PDFRenderer()

    output_pdf = os.path.join(
        OUTPUT_FOLDER,
        f"annotated_{uuid.uuid4().hex}.pdf",
    )
    app.config["LAST_OUTPUT"] = output_pdf

    renderer.render(

        input_pdf=actual_path,

        output_pdf=output_pdf,

        differences=differences,

    )

    # -------------------------------------------
    # Summary
    # -------------------------------------------

    counter = Counter()

    logs = []

    for diff in differences:

        counter[diff.category.value] += 1

        logs.append(

            {

                "category": diff.category.value,

                "expected": diff.expected_text,

                "actual": diff.actual_text,

                "description": diff.description,

            }

        )

    return jsonify(

        {

            "success": True,

            "aligned_pairs": len(aligned_pairs),

            "total": len(differences),

            "summary": counter,

            "logs": logs,

        }

    )


# ---------------------------------------------------
# Download
# ---------------------------------------------------

@app.route("/download")
def download():

    return send_file(

        os.path.join(

            app.config["LAST_OUTPUT"],
        ),

        as_attachment=True,

    )


# ---------------------------------------------------

if __name__ == "__main__":

    app.run(

        debug=True,

        port=5000,

    )