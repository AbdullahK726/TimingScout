# parser.py
#
# Reads the plain text of a Vivado report_timing_summary report and pulls
# out the key timing numbers using simple regular expressions.
#
# This file only extracts facts. It never decides PASS or FAIL - that
# decision is made in analyzer.py.

import re
from dataclasses import dataclass, field


@dataclass
class TimingReport:
    wns_ns: float = None
    tns_ns: float = None
    failing_endpoints: int = None
    total_endpoints: int = None
    startpoint: str = None
    endpoint: str = None
    path_group: str = None
    path_type: str = None
    data_arrival_time_ns: float = None
    data_required_time_ns: float = None
    slack_ns: float = None
    critical_path_lines: list = field(default_factory=list)
    missing_fields: list = field(default_factory=list)


def looks_like_vivado_report(text):
    # A genuine Vivado report_timing_summary report always contains a
    # handful of distinctive phrases. Require at least two matches before
    # trusting that this file is really a Vivado timing report.
    markers = [
        "Timing Summary",
        "WNS(ns)",
        "report_timing_summary",
        "Vivado",
        "Design Timing Summary",
    ]
    hits = 0
    for marker in markers:
        if marker in text:
            hits += 1
    return hits >= 2


def find_number_after_label(text, label):
    # Search for the label, then return the first signed decimal number
    # that appears after it, for example "-0.456" or "3.947".
    label_pos = text.find(label)
    if label_pos == -1:
        return None

    remaining_text = text[label_pos + len(label):]
    match = re.search(r"-?\d+\.?\d*", remaining_text)
    if match is None:
        return None

    return float(match.group())


def find_text_after_label(text, label):
    # Search for the label, then return the rest of that same line, with
    # leading and trailing whitespace removed.
    label_pos = text.find(label)
    if label_pos == -1:
        return None

    line_start = label_pos + len(label)
    line_end = text.find("\n", line_start)
    if line_end == -1:
        line_end = len(text)

    value = text[line_start:line_end].strip()
    if value == "":
        return None

    return value


def parse_timing_summary(text):
    # Pulls the four "Design Timing Summary" numbers out of the report.
    summary = {}

    summary["wns_ns"] = find_number_after_label(text, "WNS(ns)")
    summary["tns_ns"] = find_number_after_label(text, "TNS(ns)")

    failing = find_number_after_label(text, "TNS Failing Endpoints")
    summary["failing_endpoints"] = int(failing) if failing is not None else None

    total = find_number_after_label(text, "TNS Total Endpoints")
    summary["total_endpoints"] = int(total) if total is not None else None

    return summary


def parse_critical_path(text):
    # Pulls the details of the single worst ("Max Delay Paths") path.
    path = {}

    path["startpoint"] = find_text_after_label(text, "Startpoint:")
    path["endpoint"] = find_text_after_label(text, "Endpoint:")
    path["path_group"] = find_text_after_label(text, "Path Group:")
    path["path_type"] = find_text_after_label(text, "Path Type:")
    path["data_arrival_time_ns"] = find_number_after_label(text, "Data Arrival Time (ns):")
    path["data_required_time_ns"] = find_number_after_label(text, "Data Required Time (ns):")
    path["slack_ns"] = find_number_after_label(text, "Path Slack (ns):")

    # Collect the raw lines of the "Max Delay Paths" block so the results
    # page can show the user the actual critical path text.
    lines = []
    start_pos = text.find("Slack (")
    if start_pos != -1:
        block = text[start_pos:]
        end_pos = block.find("\n\n\n")
        if end_pos != -1:
            block = block[:end_pos]
        for line in block.splitlines():
            stripped_line = line.strip()
            if stripped_line != "":
                lines.append(stripped_line)
    path["critical_path_lines"] = lines

    return path


def parse_vivado_report(text):
    summary = parse_timing_summary(text)
    path = parse_critical_path(text)

    report = TimingReport(
        wns_ns=summary["wns_ns"],
        tns_ns=summary["tns_ns"],
        failing_endpoints=summary["failing_endpoints"],
        total_endpoints=summary["total_endpoints"],
        startpoint=path["startpoint"],
        endpoint=path["endpoint"],
        path_group=path["path_group"],
        path_type=path["path_type"],
        data_arrival_time_ns=path["data_arrival_time_ns"],
        data_required_time_ns=path["data_required_time_ns"],
        slack_ns=path["slack_ns"],
        critical_path_lines=path["critical_path_lines"],
    )

    # Slack can be calculated as required time - arrival time, but only
    # when both values exist and an explicit slack value was not found.
    if report.slack_ns is None:
        if report.data_required_time_ns is not None and report.data_arrival_time_ns is not None:
            report.slack_ns = report.data_required_time_ns - report.data_arrival_time_ns

    # Track which fields could not be found. Missing values stay None -
    # they are never silently replaced with zero.
    field_names = [
        "wns_ns", "tns_ns", "failing_endpoints", "total_endpoints",
        "startpoint", "endpoint", "path_group", "path_type",
        "data_arrival_time_ns", "data_required_time_ns", "slack_ns",
    ]
    missing_fields = []
    for name in field_names:
        if getattr(report, name) is None:
            missing_fields.append(name)
    report.missing_fields = missing_fields

    return report
