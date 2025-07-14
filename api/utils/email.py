from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_welcome_email(user):
    subject = "Welcome to KitoDeck Ai!"
    from_email = "KitoDeck AI <noreply@kitodeck.ai>"
    to = [user.email]


    context = {
        "user name": user.username,
        "dashboard_url": "https://kitodetector-ai.vercel.app/dashboard",
        "current_year": 2025,
    }

    html_context = render_to_string("emails/welcome.html", context)

    msg = EmailMultiAlternatives(subject, html_context, from_email, to)
    msg.content_subtype = "html"
    msg.send()