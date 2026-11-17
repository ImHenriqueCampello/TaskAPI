import smtplib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import notify_email  # noqa: E402

ARGS = SimpleNamespace(
    status="SUCCESS", job="taskapi", build="7",
    url="http://jenkins/job/taskapi/7/", commit="abc123", branch="main",
)


def test_message_uses_env_recipient():
    msg = notify_email.build_message(ARGS, {"NOTIFY_EMAIL": "a@x.com, b@x.com", "SMTP_USER": "me@x.com"})
    assert msg["To"] == "a@x.com, b@x.com"
    assert msg["From"] == "me@x.com"
    assert "taskapi #7 - SUCCESS" in msg["Subject"]
    assert "abc123" in msg.get_body(preferencelist=("plain",)).get_content()


def test_missing_recipient_raises():
    with pytest.raises(ValueError):
        notify_email.build_message(ARGS, {})


def test_send_uses_smtp_with_login(monkeypatch):
    calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            calls.append(("connect", host, port))
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): calls.append(("tls",))
        def login(self, u, p): calls.append(("login", u))
        def send_message(self, m): calls.append(("send", m["To"]))

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    env = {"NOTIFY_EMAIL": "a@x.com", "SMTP_HOST": "h", "SMTP_PORT": "2525",
           "SMTP_USER": "u", "SMTP_PASSWORD": "p"}
    notify_email.send(notify_email.build_message(ARGS, env), env)
    assert calls == [("connect", "h", 2525), ("tls",), ("login", "u"), ("send", "a@x.com")]


def test_main_returns_error_without_recipient(monkeypatch, capsys):
    monkeypatch.delenv("NOTIFY_EMAIL", raising=False)
    code = notify_email.main(["--status", "FAILURE", "--job", "j", "--build", "1"])
    assert code == 1
    assert "NOTIFY_EMAIL" in capsys.readouterr().err


def test_main_success(monkeypatch):
    monkeypatch.setenv("NOTIFY_EMAIL", "a@x.com")
    monkeypatch.setattr(notify_email, "send", lambda msg, env=None: None)
    assert notify_email.main(["--status", "SUCCESS", "--job", "j", "--build", "1"]) == 0


@pytest.mark.parametrize("status", ["SUCCESS", "FAILURE", "UNSTABLE", "ABORTED"])
def test_html_matches_text_and_escapes_values(status):
    args = SimpleNamespace(**vars(ARGS))
    args.status = status
    args.job = '<script>alert("job")</script>'
    msg = notify_email.build_message(args, {"NOTIFY_EMAIL": "a@x.com"})
    assert msg.is_multipart()
    assert args.job in msg.get_body(preferencelist=("plain",)).get_content()
    body = msg.get_body(preferencelist=("html",)).get_content()
    assert "&lt;script&gt;" in body
    assert args.job not in body
    assert "Ver execução" in body


@pytest.mark.parametrize("url", ["null", "", "javascript:alert(1)", "None", "http://[invalid"])
def test_invalid_url_omits_links(url):
    args = SimpleNamespace(**vars(ARGS))
    args.url = url
    msg = notify_email.build_message(args, {"NOTIFY_EMAIL": "a@x.com"})
    assert 'href=' not in msg.get_body(preferencelist=("html",)).get_content()
    assert "nullartifact" not in msg.get_body(preferencelist=("plain",)).get_content()


def test_reports_and_publication(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuites><testsuite tests="5" failures="1" errors="1" skipped="1"/></testsuites>')
    coverage = tmp_path / "coverage.xml"
    coverage.write_text('<coverage line-rate="0.95"/>')
    args = SimpleNamespace(**vars(ARGS), junit_path=str(junit), coverage_path=str(coverage),
                           duration_seconds=125, publication_status="published", docker_repo="owner/api")
    msg = notify_email.build_message(args, {"NOTIFY_EMAIL": "a@x.com"})
    for part in msg.iter_parts():
        body = part.get_content()
        for expected in ["5 total", "2 aprovados", "95.0%", "2 min 5 s", "owner/api", "latest, 7-abc123"]:
            assert expected in body


@pytest.mark.parametrize("contents", ["invalid", '<coverage line-rate="bad"/>'])
def test_invalid_reports_do_not_prevent_notification(tmp_path, contents):
    report = tmp_path / "report.xml"
    report.write_text(contents)
    args = SimpleNamespace(**vars(ARGS), junit_path=str(report), coverage_path=str(report))
    msg = notify_email.build_message(args, {"NOTIFY_EMAIL": "a@x.com"})
    assert "Indisponível" in msg.get_body(preferencelist=("plain",)).get_content()
