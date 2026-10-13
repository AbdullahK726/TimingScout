# analyzer.py
#
# Applies simple, deterministic rules to decide whether a parsed timing
# report PASSES or FAILS, and offers rule-based suggestions for what to
# look at next. The LLM in llm.py is never involved in this decision -
# it only explains what analyzer.py already decided.

from dataclasses import dataclass


@dataclass
class Verdict:
    status: str
    summary: str
    recommendations: list


def analyze_timing(report):
    # WNS (Worst Negative Slack) is the worst slack among every timing
    # path Vivado analyzed. If WNS is negative, at least one path in the
    # whole design missed its timing constraint, so WNS is checked first.
    if report.wns_ns is not None:
        if report.wns_ns < 0:
            status = "FAIL"
            summary = f"WNS is {report.wns_ns} ns, which is negative, so the design FAILS timing."
        else:
            status = "PASS"
            summary = f"WNS is {report.wns_ns} ns, so the design PASSES timing."

    # If WNS could not be found, fall back to the slack of the single
    # critical path that was parsed from the report.
    elif report.slack_ns is not None:
        if report.slack_ns < 0:
            status = "FAIL"
        else:
            status = "PASS"
        summary = f"WNS was not found in the report. Using the critical path slack of {report.slack_ns} ns instead."

    # If neither value exists, a pass/fail call cannot be made at all.
    else:
        status = "INCOMPLETE"
        summary = "No WNS or slack value could be found, so PASS/FAIL could not be determined."

    recommendations = build_recommendations(report, status)
    return Verdict(status=status, summary=summary, recommendations=recommendations)


def build_recommendations(report, status):
    if status == "PASS":
        return ["Timing was met for this report. No timing fix is required based on these results."]

    if status == "INCOMPLETE":
        return ["Upload a report_timing_summary report that includes a WNS value or a critical path slack value."]

    # status == "FAIL"
    recommendations = []

    if report.startpoint and report.endpoint:
        recommendations.append(
            f"Inspect the critical path between startpoint '{report.startpoint}' and "
            f"endpoint '{report.endpoint}'. This should be investigated first."
        )
    else:
        recommendations.append("Inspect the critical path reported by Vivado for the failing endpoint.")

    # Look for a few keywords in the path names to give a more specific
    # hint. This is only a guess based on naming - not a real RTL analysis.
    path_text = f"{report.startpoint} {report.endpoint} {report.path_type}".lower()

    if "alu" in path_text or "compar" in path_text:
        recommendations.append("Possible area to inspect: ALU or comparison logic, which could be causing deep combinational delay.")

    if "mux" in path_text:
        recommendations.append("Possible area to inspect: long mux chains, which could be adding extra logic levels.")

    if "decode" in path_text:
        recommendations.append("Possible area to inspect: instruction decode logic, which may be contributing to the delay.")

    if "forward" in path_text:
        recommendations.append("Possible area to inspect: forwarding logic, which could be adding an extra combinational hop.")

    recommendations.append("This may indicate deep combinational logic between registers and should be investigated further.")
    recommendations.append("Verify that the target clock period and I/O constraints in the XDC file are correct.")
    recommendations.append("Check synthesis and implementation optimization settings, since more aggressive settings could reduce delay.")
    recommendations.append("Consider adding a pipeline register along this path if the architecture allows it.")

    return recommendations
