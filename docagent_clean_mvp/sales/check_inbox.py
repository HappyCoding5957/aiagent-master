import os
import imaplib
import email
from email.header import decode_header

def load_env(env_path):
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    env_vars[key.strip()] = val.strip()
    return env_vars

def check_gmail_inbox():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env = load_env(env_path)
    
    sender_email = env.get("SENDER_EMAIL")
    app_password = env.get("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        print("[ERROR] Credentials not found in .env!")
        return

    try:
        # Connect to Gmail IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(sender_email, app_password)
        mail.select("inbox")

        # Search for all emails
        status, messages = mail.search(None, "ALL")
        if status != "OK":
            print("[ERROR] Failed to search inbox.")
            return

        mail_ids = messages[0].split()
        total_mails = len(mail_ids)
        print(f"Total emails in inbox: {total_mails}")

        # Fetch the top 15 most recent emails
        recent_ids = mail_ids[-15:]
        recent_ids.reverse()  # Show most recent first

        print("\n--- Recent 15 Emails ---")
        for i, mail_id in enumerate(recent_ids):
            _, msg_data = mail.fetch(mail_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decode email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8", errors="ignore")
                    
                    # Decode sender
                    from_, encoding = decode_header(msg["From"])[0]
                    if isinstance(from_, bytes):
                        from_ = from_.decode(encoding or "utf-8", errors="ignore")
                    
                    date_ = msg.get("Date")
                    
                    print(f"[{i+1}] From: {from_}")
                    print(f"    Subject: {subject}")
                    print(f"    Date: {date_}")
                    print("-" * 50)
        
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"[ERROR] Failed to check inbox: {e}")

if __name__ == "__main__":
    check_gmail_inbox()
