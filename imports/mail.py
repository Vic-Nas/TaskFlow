
from random import randint
import smtplib
from email.message import EmailMessage
from sys import argv

        
def sendVerifiMail(mail, size):
    code = ""
    for _ in range(size): code += str(randint(0, 9))
    
    senderMail = "taskflow.vicnas@gmail.com"
    senderPassword = "esic proi dgxi piws"
    smtpServer = "smtp.gmail.com"
    smtpPort = 587

    msg = EmailMessage()
    msg['Subject'] = "Your TaskFlow Verification Code"
    msg['From'] = senderMail
    msg['To'] = mail
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
            print(f"Verification email sent to {mail}")
    except Exception as e:
        print(f"Failed to send email to {mail}: {e}")
    return code