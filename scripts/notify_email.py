#!/usr/bin/env python3
"""Envia por e-mail o resumo da execução do pipeline Jenkins.

Toda a configuração vem de variáveis de ambiente (nada fixo no código):
  NOTIFY_EMAIL   destinatário(s), separados por vírgula (obrigatória)
  SMTP_HOST      servidor SMTP (padrão: smtp.gmail.com)
  SMTP_PORT      porta SMTP (padrão: 587, STARTTLS)
  SMTP_USER      usuário de autenticação (opcional)
  SMTP_PASSWORD  senha/token de app (opcional)
  SMTP_FROM      remetente (padrão: SMTP_USER)

Uso: notify_email.py --status SUCCESS --job taskapi --build 12 \
        --url http://jenkins/job/taskapi/12/ --commit abc123 --branch main
"""
import argparse
import os
import smtplib
import sys
import html
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
from email.message import EmailMessage


def build_message(args, env=os.environ):
    recipients = [r.strip() for r in env.get("NOTIFY_EMAIL", "").split(",") if r.strip()]
    if not recipients:
        raise ValueError("Variável de ambiente NOTIFY_EMAIL não definida.")

    sender = env.get("SMTP_FROM") or env.get("SMTP_USER") or "jenkins@localhost"
    msg = EmailMessage()
    msg["Subject"] = f"[Jenkins] {args.job} #{args.build} - {args.status}"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    status_labels = {
        "SUCCESS": ("Sucesso", "#15803d"),
        "FAILURE": ("Falha", "#b91c1c"),
        "UNSTABLE": ("Instável", "#a16207"),
        "ABORTED": ("Cancelado", "#475569"),
    }
    label, color = status_labels.get(args.status, (args.status, "#475569"))
    duration = getattr(args, "duration_seconds", None)
    duration_text = f"{duration // 60} min {duration % 60} s" if duration is not None else "Indisponível"
    rows = [
        ("Job", args.job), ("Build", f"#{args.build}"), ("Status", label),
        ("Duração até a notificação", duration_text),
        ("Branch", args.branch.removeprefix("origin/")), ("Commit", args.commit),
    ]

    tests = "Indisponível"
    try:
        root = ET.parse(getattr(args, "junit_path", "reports/junit.xml")).getroot()
        suites = [node for node in root.iter("testsuite") if not node.findall("testsuite")]
        if suites:
            counts = {key: sum(int(node.get(key, "0")) for node in suites)
                      for key in ("tests", "failures", "errors", "skipped")}
            passed = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
            tests = (f"{counts['tests']} total · {passed} aprovados · "
                     f"{counts['failures']} falhos · {counts['errors']} erros · {counts['skipped']} ignorados")
    except (OSError, ET.ParseError, ValueError):
        pass

    coverage = "Indisponível"
    try:
        root = ET.parse(getattr(args, "coverage_path", "reports/coverage.xml")).getroot()
        coverage = f"{float(root.attrib['line-rate']) * 100:.1f}% (mínimo: 90%)"
    except (OSError, ET.ParseError, ValueError, KeyError):
        pass

    publication = getattr(args, "publication_status", "not-run")
    publication_label = {"published": "Concluída", "failed": "Falhou", "not-run": "Não executada"}[publication]
    rows.extend([("Testes", tests), ("Cobertura", coverage), ("Publicação Docker Hub", publication_label)])
    repository = getattr(args, "docker_repo", "")
    if repository:
        rows.append(("Repositório", repository))
    if publication == "published":
        rows.append(("Tags publicadas", f"latest, {args.build}-{args.commit}"))

    url = args.url.strip()
    links = []
    try:
        parsed = urlsplit(url)
        valid_url = parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except ValueError:
        valid_url = False

    if valid_url:
        url = url.rstrip("/") + "/"
        links = [("Ver execução", url), ("Ver console", url + "console"), ("Ver artefatos", url + "artifact/")]

    text = "Resumo da execução do pipeline\n\n"
    text += "\n".join(f"{name}: {value}" for name, value in rows)
    text += "\n\n" + "\n".join(f"{name}: {target}" for name, target in links)
    msg.set_content(text)

    table_rows = "".join(
        f'<tr><td style="padding:10px;border-bottom:1px solid #e2e8f0;color:#64748b">{html.escape(name)}</td>'
        f'<td style="padding:10px;border-bottom:1px solid #e2e8f0;word-break:break-word">{html.escape(str(value))}</td></tr>'
        for name, value in rows
    )
    buttons = " ".join(
        f'<a href="{html.escape(target, quote=True)}" style="display:inline-block;margin:4px;padding:12px;background:#1e293b;color:white;text-decoration:none;border-radius:6px">{name}</a>'
        for name, target in links
    )
    body = f"""<!doctype html><html lang="pt-BR"><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;background:#f1f5f9;font-family:Arial,sans-serif;color:#0f172a">
<table role="presentation" width="100%"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" style="max-width:600px;background:white;border-radius:12px"><tr><td style="padding:28px">
<p style="color:#64748b">TaskAPI · Jenkins</p>
<h1 style="font-size:24px">Execução #{html.escape(args.build)} concluída</h1>
<p style="color:{color};font-weight:bold">{html.escape(label)}</p>
<table width="100%" style="border-collapse:collapse;font-size:14px">{table_rows}</table>
<p style="margin-top:24px">{buttons}</p>
<p style="font-size:12px;color:#64748b">Notificação automática do pipeline TaskAPI.</p>
</td></tr></table></td></tr></table></body></html>"""
    msg.add_alternative(body, subtype="html")
    return msg


def send(msg, env=os.environ):
    host = env.get("SMTP_HOST", "smtp.gmail.com")
    port = int(env.get("SMTP_PORT", "587"))
    user = env.get("SMTP_USER")
    password = env.get("SMTP_PASSWORD")
    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--status", required=True)
    p.add_argument("--job", required=True)
    p.add_argument("--build", required=True)
    p.add_argument("--url", default="")
    p.add_argument("--commit", default="n/a")
    p.add_argument("--branch", default="n/a")
    p.add_argument("--duration-seconds", type=int)
    p.add_argument("--junit-path", default="reports/junit.xml")
    p.add_argument("--coverage-path", default="reports/coverage.xml")
    p.add_argument("--docker-repo", default="")
    p.add_argument("--publication-status", choices=["published", "failed", "not-run"], default="not-run")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        send(build_message(args))
    except Exception as exc:  # noqa: BLE001 - queremos reportar qualquer falha
        print(f"Falha ao enviar e-mail: {exc}", file=sys.stderr)
        return 1
    print("E-mail de notificação enviado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
