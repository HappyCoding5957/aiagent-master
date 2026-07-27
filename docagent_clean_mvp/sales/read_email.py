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

def read_target_email():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env = load_env(env_path)
    
    sender_email = env.get("SENDER_EMAIL")
    app_password = env.get("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        print("[ERROR] Credentials not found in .env!")
        return

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(sender_email, app_password)
        mail.select("inbox")

        # Search for Collective Health reply
        status, messages = mail.search(None, 'FROM "collectivehealth.com"')
        if status != "OK" or not messages[0]:
            print("No emails found from collectivehealth.com")
            return

        mail_ids = messages[0].split()
        latest_id = mail_ids[-1]  # Get the latest one
        
        _, msg_data = mail.fetch(latest_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")
                
                from_, encoding = decode_header(msg["From"])[0]
                if isinstance(from_, bytes):
                    from_ = from_.decode(encoding or "utf-8", errors="ignore")
                
                print(f"From: {from_}")
                print(f"Subject: {subject}")
                print(f"Date: {msg.get('Date')}")
                print("\n--- BODY ---")
                
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            body = part.get_payload(decode=True).decode(errors="ignore")
                        except Exception:
                            continue
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            print(body)
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                    print(body)
        
        mail.close()
        mail.logout()
    except Exception as e:
        print(f"[ERROR] Failed to read email: {e}")

if __name__ == "__main__":
    read_target_email()
