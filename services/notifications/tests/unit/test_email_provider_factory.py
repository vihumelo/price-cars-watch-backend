from services.notifications.src.providers.email_provider_factory import build_email_provider
from services.notifications.src.providers.mailjet.mailjet_email_provider import MailjetEmailProvider


def test_factory_builds_mailjet_provider(monkeypatch):
    monkeypatch.setenv("EMAIL_PROVIDER", "mailjet")
    monkeypatch.setattr(
        "services.notifications.src.providers.email_provider_factory.get_mailjet_credentials",
        lambda: ("api-key", "secret-key"),
    )
    monkeypatch.setenv("MAILJET_CONFIRMATION_TEMPLATE_ID", "4")
    monkeypatch.setenv("MAILJET_NEW_LISTINGS_TEMPLATE_ID", "5")
    monkeypatch.setenv("MAILJET_SENDER_EMAIL", "noreply@example.com")
    monkeypatch.setenv("MAILJET_SENDER_NAME", "Prices Car Watch")
    monkeypatch.setenv("PUBLIC_FRONTEND_BASE_URL", "https://frontend.example.test")

    provider = build_email_provider()

    assert isinstance(provider, MailjetEmailProvider)
