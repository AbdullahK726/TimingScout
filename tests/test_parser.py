# tests/test_parser.py
#
# Run with `python -m pytest` from the project root so that parser.py
# and analyzer.py (which live in the root, not in tests/) can be
# imported directly.

import parser
import analyzer

with open("samples/passing_timing.rpt", "r", encoding="utf-8") as f:
    PASSING_TEXT = f.read()

with open("samples/failing_timing.rpt", "r", encoding="utf-8") as f:
    FAILING_TEXT = f.read()


def test_recognizes_vivado_report():
    assert parser.looks_like_vivado_report(PASSING_TEXT) is True


def test_rejects_unrelated_text():
    random_text = "This is just some unrelated text file about lunch plans."
    assert parser.looks_like_vivado_report(random_text) is False


def test_parses_positive_wns():
    report = parser.parse_vivado_report(PASSING_TEXT)
    assert report.wns_ns == 0.842


def test_parses_negative_wns():
    report = parser.parse_vivado_report(FAILING_TEXT)
    assert report.wns_ns == -0.456


def test_parses_tns():
    report = parser.parse_vivado_report(FAILING_TEXT)
    assert report.tns_ns == -2.345


def test_parses_failing_endpoints():
    report = parser.parse_vivado_report(FAILING_TEXT)
    assert report.failing_endpoints == 3


def test_parses_startpoint():
    report = parser.parse_vivado_report(FAILING_TEXT)
    assert report.startpoint == "alu_result_reg_reg[7]/C"


def test_parses_endpoint():
    report = parser.parse_vivado_report(FAILING_TEXT)
    assert report.endpoint == "compare_stage_reg_reg[7]/D"


def test_parses_arrival_time():
    report = parser.parse_vivado_report(PASSING_TEXT)
    assert report.data_arrival_time_ns == 3.947


def test_parses_required_time():
    report = parser.parse_vivado_report(PASSING_TEXT)
    assert report.data_required_time_ns == 4.789


def test_parses_slack():
    report = parser.parse_vivado_report(PASSING_TEXT)
    assert report.slack_ns == 0.842


def test_calculates_slack_when_slack_line_missing():
    text_without_slack_line = PASSING_TEXT.replace("  Path Slack (ns):         0.842\n", "")
    report = parser.parse_vivado_report(text_without_slack_line)
    assert report.slack_ns == 4.789 - 3.947
    assert "slack_ns" not in report.missing_fields


def test_pass_using_wns():
    report = parser.parse_vivado_report(PASSING_TEXT)
    verdict = analyzer.analyze_timing(report)
    assert verdict.status == "PASS"


def test_fail_using_wns():
    report = parser.parse_vivado_report(FAILING_TEXT)
    verdict = analyzer.analyze_timing(report)
    assert verdict.status == "FAIL"


def test_pass_using_path_slack_when_wns_missing():
    text_without_wns_line = PASSING_TEXT.replace("    WNS(ns): 0.842\n", "")
    report = parser.parse_vivado_report(text_without_wns_line)
    assert report.wns_ns is None
    verdict = analyzer.analyze_timing(report)
    assert verdict.status == "PASS"


def test_fail_using_path_slack_when_wns_missing():
    text_without_wns_line = FAILING_TEXT.replace("    WNS(ns): -0.456\n", "")
    report = parser.parse_vivado_report(text_without_wns_line)
    assert report.wns_ns is None
    verdict = analyzer.analyze_timing(report)
    assert verdict.status == "FAIL"


def test_incomplete_when_no_timing_result_exists():
    text_without_any_numbers = "Timing Summary\nWNS(ns)\nDesign Timing Summary\nNo numeric results here."
    report = parser.parse_vivado_report(text_without_any_numbers)
    assert report.wns_ns is None
    assert report.slack_ns is None
    verdict = analyzer.analyze_timing(report)
    assert verdict.status == "INCOMPLETE"
