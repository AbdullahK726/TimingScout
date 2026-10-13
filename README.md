# Timing Scout

**AI-Assisted FPGA Timing Report Analyzer**

Timing Scout is a small undergraduate portfolio project. It is a local Flask
web app that reads a Vivado `report_timing_summary` timing report, pulls out
the important numbers with Python, decides PASS/FAIL/INCOMPLETE using simple
rules, and optionally asks an LLM to explain the result in plain English.

This is a learning and portfolio project, not a production tool. It is not a
replacement for Vivado and does not do any timing analysis itself - it only
reads and explains a report that Vivado already generated.

## 1. What Timing Scout does

1. You upload a `.rpt` or `.txt` file containing Vivado `report_timing_summary`
   output (or you click one of the two sample buttons).
2. `parser.py` extracts the key timing numbers with regular expressions.
3. `analyzer.py` applies fixed rules to decide PASS, FAIL, or INCOMPLETE.
4. The results page shows the numbers, the verdict, and a few rule-based
   recommendations.
5. If you check "Also generate an optional AI explanation," `llm.py` sends
   the *extracted numbers only* (never the raw report) to an LLM, which
   explains them in plain English.

## 2. Why I built it

I'm an electrical engineering student learning digital design and FPGA
flows. Reading a Vivado timing report and understanding *why* a design
failed timing is a skill that takes a while to build. I wanted a small tool
that practices two things at once: parsing real EDA tool output with Python,
and being careful about where an LLM is (and is not) trustworthy in an
engineering workflow.

## 3. What static timing analysis means

Static timing analysis (STA) checks every register-to-register path in a
design against the clock period, without simulating any actual data. For
every path, the tool computes how long a signal takes to arrive
(the **data arrival time**) and how long it is allowed to take
(the **data required time**, based on the clock period and constraints).
If arrival time is greater than required time, that path is too slow.

## 4. What WNS means

**WNS = Worst Negative Slack.** It is the single worst (most negative)
slack value among every path Vivado analyzed. Slack is calculated as:

```
slack = data required time - data arrival time
```

If WNS is negative, at least one path anywhere in the design did not meet
its timing constraint. If WNS is zero or positive, every path met timing.

## 5. What TNS means

**TNS = Total Negative Slack.** It is the sum of the negative slack across
every failing endpoint. A large negative TNS with many failing endpoints
usually means a systemic issue (for example, a clock constraint that is too
aggressive), while a small negative TNS on one endpoint usually means a
single slow path.

## 6. How PASS and FAIL are determined

This is decided entirely in `analyzer.py`, using fixed rules - never by the
LLM:

1. If WNS was found: `WNS < 0` -> FAIL, `WNS >= 0` -> PASS.
2. If WNS was not found but a critical path slack was: `slack < 0` -> FAIL,
   `slack >= 0` -> PASS.
3. If neither WNS nor slack could be found: status is INCOMPLETE.

## 7. Why the LLM does not receive the raw report

The most important design rule in this project is:

> **Python determines the facts. The LLM only explains the facts.**

The LLM never sees the uploaded report text, and it never decides PASS or
FAIL. `llm.py` only sends the structured values that `parser.py` and
`analyzer.py` already extracted and decided (WNS, TNS, failing endpoints,
startpoint, endpoint, slack, the deterministic recommendations, etc). This
keeps the LLM from ever inventing or contradicting a timing result, and
keeps the pass/fail logic auditable and testable without needing an API
call.

## 8. Project structure

```
timing-scout/
├── app.py            Flask routes: upload, sample reports, results page
├── parser.py          Extracts timing values from report text
├── analyzer.py         Deterministic PASS/FAIL/INCOMPLETE rules
├── llm.py              Optional LLM explanation (structured facts only)
├── requirements.txt
├── README.md
├── .env.example
├── templates/          index.html and results.html
├── static/style.css
├── samples/            synthetic passing/failing example reports
├── tests/test_parser.py
└── demo_hw/             optional SystemVerilog + Vivado Tcl demo
```

## 9. Installation

```
python -m venv venv
venv\Scripts\activate        (on Windows)
pip install -r requirements.txt
copy .env.example .env       (optional, only needed for the AI feature)
```

## 10. How to run the Flask app

```
python app.py
```

Then open `http://127.0.0.1:5000` in a browser.

## 11. How to run the tests

Run this from the project root, so `parser.py` and `analyzer.py` can be
imported directly:

```
python -m pytest
```

## 12. How to analyze the sample reports

From the home page, click **Analyze Passing Sample** or **Analyze Failing
Sample**. Both files live in `samples/` and are clearly marked as synthetic
example reports written for this project, not real Vivado output.

## 13. How the optional Vivado demo works

`demo_hw/` contains a tiny SystemVerilog datapath (`top.sv`), a clock
constraint file (`top.xdc`), and a Tcl script (`run_vivado.tcl`) that runs
synthesis and implementation and writes a real `report_timing_summary`
report. This is meant to be run manually in Vivado - the Flask app never
launches Vivado itself. The output file can then be uploaded to Timing
Scout to see it analyze a real report instead of a synthetic one.

## 14. Limitations

- The parser is written for a specific, simplified `report_timing_summary`
  text layout. A report from a different Vivado version or with different
  report options may not parse cleanly, in which case fields simply show as
  missing rather than being guessed.
- Only the single worst ("Max Delay Paths") path is parsed in detail, not
  every path in the design.
- The AI explanation is optional and, like any LLM output, should be
  treated as a plain-English summary to double check, not a guaranteed
  correct diagnosis.
- This project does not run Vivado or perform any timing analysis itself.

## 15. Possible future improvements

- Parse multiple critical paths instead of just the worst one.
- Support hold-time (WHS/THS) results in addition to setup (WNS/TNS).
- Add a small CLI mode so reports can be analyzed without the web UI.
- Support more Vivado report layouts/versions.
