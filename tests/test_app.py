from io import BytesIO
from pathlib import Path

import pytest
from app import app, MAX_UPLOAD_BYTES

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'report_file' in response.data


@pytest.mark.parametrize(
    "sample, expected",
    [("passing", b"PASS"), ("failing", b"FAIL")],
)
def test_sample_reports(client, sample, expected):
    response = client.get(f"/sample/{sample}")
    assert response.status_code == 200
    assert expected in response.data


def test_unknown_sample(client):
    assert client.get("/sample/unknown").status_code == 404


def test_missing_upload(client):
    response = client.post("/analyze")
    assert response.status_code == 200
    assert b"Please choose a timing report file" in response.data


def test_invalid_extension(client):
    response = client.post(
        "/analyze",
        data={"report_file": (BytesIO(b"example"), "report.csv")},
        content_type="multipart/form-data",
    )
    assert b"Only .rpt and .txt files are supported." in response.data


def test_unrelated_text(client):
    response = client.post(
        "/analyze",
        data={"report_file": (BytesIO(b"Hello world"), "report.txt")},
        content_type="multipart/form-data",
    )
    assert b"does not look like a Vivado timing report" in response.data


def test_oversized_upload(client):
    response = client.post(
        "/analyze",
        data={
            "report_file": (
                BytesIO(b"x" * (MAX_UPLOAD_BYTES + 1)),
                "report.rpt",
            )
        },
        content_type="multipart/form-data",
    )
    assert b"File is too large" in response.data


@pytest.mark.parametrize("extension", ["rpt", "txt"])
def test_valid_upload(client, extension):
    report = (ROOT / "samples" / "passing_timing.rpt").read_bytes()
    response = client.post(
        "/analyze",
        data={
            "report_file": (BytesIO(report), f"report.{extension}")
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b"PASS" in response.data
    assert b"0.842" in response.data