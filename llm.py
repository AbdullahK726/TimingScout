# llm.py
#
# Optional feature: ask an LLM to explain the already-extracted timing
# facts in plain English. The LLM never receives the raw report text and
# never decides PASS or FAIL - it only explains numbers Python already
# computed.

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = (
    "You are explaining timing-analysis facts already extracted by "
    "deterministic Python code. Do not invent or change values. Do not "
    "claim that you ran synthesis or timing analysis. Clearly state "
    "uncertainty when data is missing. Explain the result in plain "
    "English and suggest areas to investigate."
)


def explain_timing_with_llm(report, verdict):
    if os.environ.get("LLM_ENABLED", "false").lower() != "true":
        return "AI explanation is disabled. Set LLM_ENABLED=true in .env to turn it on."

    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    if api_key == "":
        return "AI explanation unavailable: no LLM_API_KEY was set."

    facts = build_facts_summary(report, verdict)

    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": facts},
        ],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            json=request_body,
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as error:
        return f"AI explanation unavailable: {error}"


def build_facts_summary(report, verdict):
    # Only these structured facts are sent to the LLM. The raw timing
    # report text is never included.
    lines = [
        f"status: {verdict.status}",
        f"wns_ns: {report.wns_ns}",
        f"tns_ns: {report.tns_ns}",
        f"failing_endpoints: {report.failing_endpoints}",
        f"total_endpoints: {report.total_endpoints}",
        f"startpoint: {report.startpoint}",
        f"endpoint: {report.endpoint}",
        f"path_type: {report.path_type}",
        f"data_arrival_time_ns: {report.data_arrival_time_ns}",
        f"data_required_time_ns: {report.data_required_time_ns}",
        f"slack_ns: {report.slack_ns}",
        f"missing_fields: {report.missing_fields}",
        "deterministic_recommendations:",
    ]
    for rec in verdict.recommendations:
        lines.append(f"- {rec}")
    return "\n".join(lines)
