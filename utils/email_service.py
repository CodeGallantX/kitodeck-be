from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_welcome_email(user):
    """
    Send a beautifully styled HTML welcome email to new users
    """
    subject = f'Welcome to {settings.PLATFORM_NAME}!'
    
    context = {
        'username': user.username,
        'email': user.email,
        'support_email': settings.SUPPORT_EMAIL,
        'platform_name': settings.PLATFORM_NAME,
        'login_url': f"{settings.FRONTEND_URL}/auth/login",
        'getting_started_url': f"{settings.FRONTEND_URL}/guides/getting-started"
    }
    
    try:
        # Render HTML content
        html_content = render_to_string('emails/welcome.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=f"{settings.PLATFORM_NAME} <{settings.DEFAULT_FROM_EMAIL}>",
            to=[user.email],
            reply_to=[settings.SUPPORT_EMAIL]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False

def send_safety_alert_email(user, report):
    """
    Send an alert email when high-risk content is detected
    """
    subject = f'[Alert] {report.get_risk_level_display()} Risk Detected'
    
    context = {
        'username': user.username,
        'risk_level': report.get_risk_level_display(),
        'risk_score': report.risk_score,
        'report_id': report.id,
        'report_date': report.created_at.strftime('%Y-%m-%d %H:%M'),
        'details': report.details,
        'support_email': settings.SUPPORT_EMAIL,
        'platform_name': settings.PLATFORM_NAME,
        'report_url': f"{settings.FRONTEND_URL}/reports/{report.id}"
    }
    
    try:
        html_content = render_to_string('emails/safety_alert.html', context)
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=f"{settings.PLATFORM_NAME} Safety Alerts <{settings.DEFAULT_FROM_EMAIL}>",
            to=[user.email],
            reply_to=[settings.SUPPORT_EMAIL]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Safety alert email sent to {user.email} for report {report.id}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send safety alert email to {user.email}: {str(e)}")
        return False