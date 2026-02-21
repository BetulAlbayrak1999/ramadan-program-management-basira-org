import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings


def _send_email(to: str, subject: str, html_body: str):
    """Send email via SMTP."""
    if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_USERNAME
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
            if settings.MAIL_USE_TLS:
                server.starttls()
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_new_registration_email(user_data: dict):
    """Send email notification to super admin about new registration."""
    admin_email = settings.SUPER_ADMIN_EMAIL
    if not admin_email:
        return

    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif;">
        <h2>طلب تسجيل جديد</h2>
        <p><strong>الاسم:</strong> {user_data.get('full_name')}</p>
        <p><strong>البريد الإلكتروني:</strong> {user_data.get('email')}</p>
        <p><strong>الهاتف:</strong> {user_data.get('phone')}</p>
        <p><strong>الجنس:</strong> {user_data.get('gender')}</p>
        <p><strong>العمر:</strong> {user_data.get('age')}</p>
        <p><strong>الدولة:</strong> {user_data.get('country')}</p>
        <p><strong>مصدر المعرفة:</strong> {user_data.get('referral_source', '-')}</p>
        <hr>
        <p>يرجى مراجعة الطلب من لوحة التحكم.</p>
    </div>
    """
    _send_email(admin_email, "طلب تسجيل جديد في البرنامج الرمضاني", html)


def send_password_reset_email(user_email: str, reset_token: str):
    """Send password reset email."""
    html = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif;">
        <h2>إعادة تعيين كلمة المرور</h2>
        <p>لقد طلبت إعادة تعيين كلمة المرور. استخدم الرمز التالي:</p>
        <h3 style="background: #f0f0f0; padding: 10px; text-align: center;">{reset_token}</h3>
        <p>إذا لم تطلب ذلك، يرجى تجاهل هذا البريد.</p>
    </div>
    """
    _send_email(user_email, "إعادة تعيين كلمة المرور", html)
