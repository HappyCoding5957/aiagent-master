import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Corrected outreach target list for the bounced emails
targets = [
    {
        "company": "The RFP Success Company",
        "email": "contact@rfpsuccess.com",
        "subject": "AI-matching engine for RFP response drafting",
        "is_rfp": True
    },
    {
        "company": "Hudson Succeed",
        "email": "hi@hudson-bidwriters.com",
        "subject": "AI-matching engine for RFP response drafting",
        "is_rfp": True
    },
    {
        "company": "Gulf Test",
        "email": "admin@gulftest.org",
        "subject": "Automating compliance check cycles for Gulf Test",
        "is_rfp": False
    },
    {
        "company": "Nexio Projects",
        "email": "info@nexioprojects.com",
        "subject": "Cutting EcoVadis questionnaire prep time for your clients",
        "is_rfp": False
    },
    {
        "company": "ThisRock Inc. (Lindsay Hampson)",
        "email": "Lindsay@ThisRockESG.com",
        "subject": "Cutting EcoVadis questionnaire prep time for your clients",
        "is_rfp": False
    }
]

esg_template_body = """Hi there,

I noticed your team helps clients prepare for EcoVadis / CDP sustainability assessments — I imagine a good chunk of that work is manually matching questionnaire items against each client's policy documents.

I built DocAgent, a self-hosted AI agent that does exactly that: it reads a client's policy library, cross-references it against a sustainability/security questionnaire, and drafts answers with source citations and confidence scoring — flagging anything it's not sure about for human review instead of guessing.

Here's a 90-second demo: https://youtu.be/AXWbFVKlzkM

Since your consultants are the ones who'd actually use this day to day, I'd love to get 10 minutes of feedback on whether this fits how you work — open to a quick call this week?

Best,
Frank Fu
Founder @ HappyCoding Labs"""

rfp_template_body = """Hi there,

Your team deals with the same core bottleneck every RFP writer knows: matching new RFP questions against a growing library of past answers, fast enough to hit tight deadlines.

I built DocAgent — an AI agent that searches your content library, drafts an answer with a source citation for every question, and flags low-confidence matches for human review instead of silently guessing. It's self-hosted, so client RFP content never leaves your infrastructure.

90-second demo: https://youtu.be/AXWbFVKlzkM

Would a draft-assist layer like this fit into your current RFP workflow? Happy to show a live walkthrough if useful.

Best,
Frank Fu
Founder @ HappyCoding Labs"""

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

def send_email(server, sender_email, target):
    body = rfp_template_body if target["is_rfp"] else esg_template_body
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = target["email"]
    msg['Subject'] = target["subject"]
    msg.attach(MIMEText(body, 'plain'))

    try:
        server.sendmail(sender_email, [target["email"]], msg.as_string())
        print(f"[SUCCESS] Resent email to {target['company']} ({target['email']})")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to resend email to {target['email']}: {e}")
        return False

if __name__ == "__main__":
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env = load_env(env_path)
    
    sender_email = env.get("SENDER_EMAIL")
    app_password = env.get("GMAIL_APP_PASSWORD")

    if not sender_email or not app_password:
        print("[CRITICAL ERROR] Credentials not configured in .env!")
        exit(1)

    print(f"Starting corrections campaign from {sender_email}...")
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
    except Exception as e:
        print(f"[CRITICAL ERROR] SMTP Login failed: {e}")
        exit(1)

    success_count = 0
    for target in targets:
        if send_email(server, sender_email, target):
            success_count += 1

    server.close()
    print(f"\nCorrection campaign complete. Successfully resent {success_count} / {len(targets)} emails.")
