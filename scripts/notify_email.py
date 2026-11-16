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
    msg.set_content(
        "Resumo da execução do pipeline\n"
        "-------------------------------\n"
        f"Job:       {args.job}\n"
        f"Build:     #{args.build}\n"
        f"Status:    {args.status}\n"
        f"Branch:    {args.branch}\n"
        f"Commit:    {args.commit}\n"
        f"Detalhes:  {args.url}\n"
        f"Artefatos: {args.url}artifact/\n"
    )
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
