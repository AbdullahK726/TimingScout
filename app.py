# app.py
#
# Flask web app for Timing Scout. Handles file upload, runs the parser
# and analyzer, optionally calls the LLM, and renders the results page.
#
# Flow: upload -> read/decode -> looks_like_vivado_report -> parse ->
# analyze -> (optional) explain with LLM -> render results.html

import os
from flask import Flask, render_template, request, abort

from parser import looks_like_vivado_report, parse_vivado_report
from analyzer import analyze_timing
from llm import explain_timing_with_llm

app = Flask(__name__)

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = (".rpt", ".txt")
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    uploaded_file = request.files.get("report_file")

    if uploaded_file is None or uploaded_file.filename == "":
        return render_template("index.html", error="Please choose a timing report file to upload.")

    filename = uploaded_file.filename.lower()
    if not filename.endswith(ALLOWED_EXTENSIONS):
        return render_template("index.html", error="Only .rpt and .txt files are supported.")

    # Read one extra byte so we can tell the difference between "exactly
    # the limit" and "over the limit" without loading a huge file fully.
    file_bytes = uploaded_file.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        return render_template("index.html", error="File is too large. Please upload a report under 2 MB.")

    report_text = file_bytes.decode("utf-8", errors="ignore")
    use_ai = request.form.get("use_ai") == "on"
    return run_analysis(report_text, use_ai)


@app.route("/sample/<name>")
def sample(name):
    if name not in ("passing", "failing"):
        abort(404)

    sample_filename = "passing_timing.rpt" if name == "passing" else "failing_timing.rpt"
    sample_path = os.path.join(SAMPLES_DIR, sample_filename)

    with open(sample_path, "r", encoding="utf-8") as sample_file:
        report_text = sample_file.read()

    use_ai = request.args.get("ai") == "1"
    return run_analysis(report_text, use_ai)


def run_analysis(report_text, use_ai):
    if not looks_like_vivado_report(report_text):
        return render_template("index.html", error="This file does not look like a Vivado timing report.")

    report = parse_vivado_report(report_text)
    verdict = analyze_timing(report)

    ai_explanation = None
    if use_ai:
        ai_explanation = explain_timing_with_llm(report, verdict)

    return render_template("results.html", report=report, verdict=verdict, ai_explanation=ai_explanation)


if __name__ == "__main__":
    app.run(debug=True)
