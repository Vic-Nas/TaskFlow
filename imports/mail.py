
from random import randint
import smtplib
from email.message import EmailMessage
from sys import argv

        
def sendVerifiMail(email, size):
    code = ""
    for _ in range(size): code += str(randint(0, 9))
    
    senderMail = "taskflow.vicnas@gmail.com"
    senderPassword = "esic proi dgxi piws"
    smtpServer = "smtp.gmail.com"
    smtpPort = 587

    msg = EmailMessage()
    msg['Subject'] = "Your TaskFlow Verification Code"
    msg['From'] = senderMail
    msg['To'] = email
    msg.set_content(
        f"""Hello,

Here is your verification code: {code}

If you did not request this code, please ignore this email.

Best regards,
TaskFlow Team"""
    )
    try:
        with smtplib.SMTP(smtpServer, smtpPort) as server:
            server.starttls()
            server.login(senderMail, senderPassword)
            server.send_message(msg)
            print(f"Verification email sent to {email}")
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
    return code


def sendFeedBackMail(email, text, *filePaths):
    senderMail = "taskflow.vicnas@gmail.com"
    senderPassword = "esic proi dgxi piws"
    smtpServer = "smtp.gmail.com"
    smtpPort = 587

    msg = EmailMessage()
    msg['Subject'] = f"Feedback from {email}"
    msg['From'] = senderMail
    msg['To'] = senderMail  # Feedback sent to TaskFlow's inbox
    msg.set_content(
        f"""Feedback received from: {email}

{text}

-- End of feedback --
"""
    )

    # Attach each file
    for path in filePaths:
        try:
            with open(path, 'rb') as f:
                file_data = f.read()
                file_name = path.split("/")[-1]  # or use os.path.basename
                msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
        except Exception as e:
            print(f"Failed to attach file '{path}': {e}")

    try:
        with smtplib.SMTP(smtpServer, smtpPort) as server:
            server.starttls()
            server.login(senderMail, senderPassword)
            server.send_message(msg)
            print(f"Feedback email from {email} sent successfully.")
    except Exception as e:
        print(f"Failed to send feedback email from {email}: {e}")
