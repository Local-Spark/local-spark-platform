"""Shared, email-client-friendly HTML for Meu Braço Direito transactional mail."""

from html import escape
from urllib.parse import urlsplit

CONTENT = {
    "verify": (
        "Confirme seu e-mail",
        "Um passo para começar a cuidar da presença digital do seu negócio.",
        "Confirmar e-mail",
        "Este link vale por 24 horas. Se você não criou uma conta, ignore esta mensagem.",
    ),
    "reset": (
        "Redefina sua senha",
        "Recebemos um pedido para definir uma nova senha para sua conta.",
        "Redefinir senha",
        "Este link vale por 30 minutos. Se você não fez o pedido, ignore esta mensagem.",
    ),
    "staff_invite": (
        "Você foi convidado para a equipe",
        "Entre com o e-mail que recebeu este convite e confirme sua conta para ter acesso à administração.",
        "Aceitar convite",
        "Este convite vale por 48 horas. Se você não esperava recebê-lo, ignore esta mensagem.",
    ),
}
LEGACY_SUBJECTS = {
    "Confirme seu e-mail no Meu Braço Direito": "verify",
    "Defina sua senha no Meu Braço Direito": "reset",
    "Convite para operar o Meu Braço Direito": "staff_invite",
}


def render_html(payload: dict[str, str]) -> str | None:
    template = payload.get("template") or LEGACY_SUBJECTS.get(payload.get("subject", ""), "")
    content = CONTENT.get(template)
    link = payload.get("link") or next(
        (word for word in payload.get("body", "").split() if word.startswith(("http://", "https://"))), ""
    )
    if not content or urlsplit(link).scheme not in {"http", "https"} or not urlsplit(link).netloc:
        return None
    title, description, action, footer = (escape(part) for part in content)
    safe_link = escape(link, quote=True)
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Meu Braço Direito</title></head>
<body style="margin:0;background:#f6f5fb;color:#23253b;font-family:Arial,Helvetica,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f5fb;padding:36px 16px">
<tr><td align="center"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px">
<tr><td style="padding:0 0 22px;color:#5445e9;font-size:22px;font-weight:800;letter-spacing:-.5px">
meu braço <span style="color:#23253b">direito.</span></td></tr>
<tr><td style="background:#fff;border:1px solid #e8e5f1;border-radius:18px;padding:40px 36px">
<p style="margin:0 0 14px;color:#6558d8;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase">
Seu negócio, seu espaço</p>
<h1 style="margin:0 0 16px;color:#23253b;font-size:28px;line-height:1.2">{title}</h1>
<p style="margin:0 0 28px;color:#62677e;font-size:16px;line-height:1.6">{description}</p>
<table role="presentation" cellpadding="0" cellspacing="0"><tr><td style="background:#6254ec;border-radius:9px">
<a href="{safe_link}" style="display:inline-block;padding:15px 24px;color:#fff;font-size:15px;font-weight:700;
text-decoration:none">{action} &rarr;</a>
</td></tr></table>
<p style="margin:30px 0 8px;color:#62677e;font-size:13px;line-height:1.5">
Se o botão não funcionar, copie este endereço:</p>
<p style="margin:0;overflow-wrap:anywhere;word-break:break-all;font-size:12px;line-height:1.5">
<a href="{safe_link}" style="color:#5445e9">{safe_link}</a></p>
</td></tr>
<tr><td style="padding:22px 8px;color:#83879b;font-size:12px;line-height:1.6">
{footer}<br>Meu Braço Direito · Seu negócio merece aparecer.</td></tr>
</table></td></tr></table></body></html>"""
