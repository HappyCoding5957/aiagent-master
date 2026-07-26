import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email Configuration
# The script will read credentials from a local .env file.
# You need to create a .env file in C:\aiagent-master\docagent_clean_mvp\sales\.env with:
# SENDER_EMAIL=happycodinglabs@gmail.com
# GMAIL_APP_PASSWORD=your_gmail_app_password

# Target list for the vCISO campaign
targets = [
    {
        "company": "IRM Consulting & Advisory",
        "recipient_name": "Victoria Arkhurst",
        "email": "info@irmcon.com",
        "cc": [],
        "subject": "Cutting compliance questionnaire prep time for IRM clients",
        "body": """Hi Victoria,

I noticed IRM Consulting & Advisory helps clients prepare for SOC 2 / ISO 27001 assessments — I imagine a good chunk of that work is manually matching questionnaire items against each client's policy documents.

I built DocAgent, a self-hosted AI agent that does exactly that: it reads a client's policy library, cross-references it against a sustainability/security questionnaire, and drafts answers with source citations and confidence scoring — flagging anything it's not sure about for human review instead of guessing.

Here's a 90-second demo: https://youtu.be/AXWbFVKlzkM

Since your consultants are the ones who'd actually use this day to day, I'd love to get 10 minutes of feedback on whether this fits how you work — open to a quick call this week?

Best,
Frank Fu
Founder @ HappyCoding Labs"""
    },
    {
        "company": "vCISO.com",
        "recipient_name": "Chase Miller",
        "email": "chase@vciso.com",
        "cc": ["info@vciso.com"],
        "subject": "Automating CAIQ / SIG security questionnaires for vCISO.com",
        "body": """Hi Chase,

If your team at vCISO.com handles security questionnaire responses for clients — CAIQ, SIG, NIST, VSA, ISO 27001 — I built something that might directly help: DocAgent, a self-hosted AI agent that searches your evidence library, drafts an answer with a row-level citation for every question, and scores its own confidence so nothing gets auto-approved without evidence.

This demo shows it answering 10 questions across all five of those frameworks in 90 seconds: https://youtu.be/AXWbFVKlzkM

Since this maps closely to what vCISO teams field every week, I'd value your read on it — worth a quick call?

Best,
Frank Fu
Founder @ HappyCoding Labs"""
    },
    {
        "company": "Alpha Apex Group",
        "recipient_name": "Jake Jorgovan",
        "email": "hello@alphaapexgroup.com",
        "cc": [],
        "subject": "AI-matching assistant for Alpha Apex vCISO clients",
        "body": """Hi Jake,

I noticed Alpha Apex Group provides fractional CISO services. When onboarding new clients or audit cycles, matching security questionnaires against internal evidence folders is a massive manual drag.

I built DocAgent, a self-hosted AI agent that does exactly that: it reads your client's policy library, cross-references it against security questionnaires, and drafts answers with row-level source citations and confidence scoring.

Here's a 90-second demo: https://youtu.be/AXWbFVKlzkM

Would a draft-assist layer like this fit into your current vCISO client workflow? Open to a brief call to share more.

Best,
Frank Fu
Founder @ HappyCoding Labs"""
    },
    {
        "company": "FractionalCISO.com",
        "recipient_name": "Rob Black",
        "email": "info@fractionalciso.com",
        "cc": [],
        "subject": "Automating SIG / NIST questionnaire response cycles",
        "body": """Hi Rob,

If your team at FractionalCISO.com spends hours copy-pasting answers from client policy folders into compliance spreadsheets, I built something that might directly help: DocAgent. 

It is a self-hosted AI agent that reads client evidence libraries, drafts answers with exact row-level citations for every questionnaire item, and flags low-confidence answers for human approval instead of silently guessing.

This demo shows it answering 10 questions across five major frameworks in 90 seconds: https://youtu.be/AXWbFVKlzkM

I’d love to get 10 minutes of your feedback on whether this matches the bottlenecks you see with client questionnaires. Open to a quick call?

Best,
Frank Fu
Founder @ HappyCoding Labs"""
    }
]

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

def send_email(sender_email, app_password, target):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = target["email"]
    if target["cc"]:
        msg['Cc'] = ", ".join(target["cc"])
    msg['Subject'] = target["subject"]
    msg.attach(MIMEText(target["body"], 'plain'))

    recipients = [target["email"]] + target["cc"]

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.close()
        print(f"[SUCCESS] Sent email to {target['recipient_name']} ({target['email']}) at {target['company']}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email to {target['email']}: {e}")
        return False

if __name__ == "__main__":
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env = load_env(env_path)
    
    sender_email = env.get("SENDER_EMAIL")
    app_password = env.get("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        print("[CRITICAL ERROR] Please configure SENDER_EMAIL and GMAIL_APP_PASSWORD in C:\\aiagent-master\\docagent_clean_mvp\\sales\\.env first!")
        print("See README in sales folder for Gmail App Password setup instructions.")
        exit(1)

    print(f"Starting outreach campaign from {sender_email}...")
    success_count = 0
    for target in targets:
        if send_email(sender_email, app_password, target):
            success_count += 1
            
    print(f"\nCampaign complete. Successfully sent {success_count} / {len(targets)} emails.")
