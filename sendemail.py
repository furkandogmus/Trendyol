import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(sender_email, receiver_email, app_password, subject, body):
    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))  # Change subtype to "html"

    # Connect to Gmail's SMTP server
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        # Login to your Gmail account
        server.login(sender_email, app_password)
        text = message.as_string()
        # Send email
        server.sendmail(sender_email, receiver_email, text)
