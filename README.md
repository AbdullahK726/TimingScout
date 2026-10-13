# TimingScout

**AI-Assisted FPGA Timing Report Analyzer**


TimingScout is a Python and Flask application that extracts metrics from Vivado timing reports, applies deterministic rules to classify the available setup timing results, and displays recommendations. An optional AI integration explains the extracted results in plain language.

## Why I Built It

I built TimingScout to connect my interests in computer architecture, digital design, and software development. The project combines Python text processing, Flask web development, API integration, and automated testing in a tool for understanding FPGA timing reports.

## Features

- Upload `.rpt` and `.txt` timing reports with file-extension and size validation.
- Extract Worst Negative Slack (WNS), Total Negative Slack (TNS), failing endpoints, and critical-path details.
- Display PASS, FAIL, or INCOMPLETE based on the available WNS or path slack.
- Generate rule-based recommendations for investigating reported timing violations.
- Explore synthetic passing and failing sample reports.
- Optionally request an AI explanation through an OpenAI-compatible API.
- Test report parsing, analysis rules, web routes, and upload validation with pytest.

## How It Works

1. Flask receives an uploaded report or loads a sample.
2. The parser checks the report format and extracts timing metrics using regular expressions.
3. The analyzer applies fixed rules to produce a verdict and recommendations.
4. The results page displays the extracted metrics and analysis.
5. If enabled, the AI integration receives structured results and generates an explanation.

### Verdict Rules

| Available result | Verdict |
|---|---|
| WNS is negative | FAIL |
| WNS is zero or positive | PASS |
| WNS is missing, but path slack is available | Classify using that path's slack |
| Both WNS and path slack are missing | INCOMPLETE |

The verdict describes the setup timing information parsed by the app. It does not establish full timing closure, check hold timing, or verify timing constraints. When only path slack is available, the verdict applies to that path.

The AI does not determine the verdict. It receives structured extracted values and recommendations rather than the raw uploaded report. Its explanation should still be checked for accuracy.

## Technology Stack

- **Language:** Python
- **Web framework:** Flask
- **Frontend:** HTML, CSS, Jinja2 templates
- **API client:** HTTPX
- **Configuration:** python-dotenv
- **Testing:** pytest and Flask's test client

## Project Structure

| Path | Purpose |
|---|---|
| `app.py` | Web routes, report uploads, and result rendering |
| `parser.py` | Report recognition and timing-metric extraction |
| `analyzer.py` | Verdict rules and recommendations |
| `llm.py` | Optional AI explanations |
| `templates/` | Homepage and results templates |
| `static/` | Stylesheet |
| `samples/` | Synthetic passing and failing reports |
| `tests/test_parser.py` | Parser and analyzer tests |
| `tests/test_app.py` | Web-route and upload-validation tests |
| `demo_hw/` | Optional SystemVerilog datapath and Vivado demo script |

## Windows Setup

Run these commands in PowerShell from the project folder. Python must be installed and available through the `py` launcher.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Run the App

```powershell
.\.venv\Scripts\python.exe app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser. Try both sample reports or upload a supported timing report. Press **Ctrl + C** in the terminal to stop the app.

The included debug server is intended for local development.

### Run the Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The suite contains **27 test cases**:

- **17 parser/analyzer cases** covering metric extraction, verdicts, and missing fields.
- **10 web-app cases** covering the homepage, sample routes, valid uploads, missing files, unsupported extensions, unrelated text, and oversized uploads.

## Optional AI Configuration

The app's report parsing and rule-based analysis work without an API key.

To configure AI explanations:

```powershell
Copy-Item .env.example .env
```

Edit `.env` to set `LLM_ENABLED=true` and supply your endpoint's `LLM_API_KEY`, `LLM_MODEL`, and `LLM_BASE_URL`. Restart the app, then enable the AI explanation option.

Keep `.env` private. The repository's `.gitignore` excludes it and the virtual environment.

## Optional Vivado Demo

The `demo_hw/` directory contains a SystemVerilog datapath, clock constraints, and a Tcl script for generating a timing report with Vivado. Run the demo separately in Vivado, then upload its generated report to TimingScout.

The bundled sample reports are synthetic fixtures, not measured FPGA results.

## Limitations

- The parser supports a specific simplified report layout; other Vivado formats may produce missing fields.
- Only one critical path is parsed in detail.
- TimingScout interprets existing reports; it does not run static timing analysis or automatically modify RTL.
- Recommendations based on signal names are investigation suggestions, not confirmed diagnoses.
- AI explanations are optional and may contain errors.


