import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Bulk outreach target list (ESG/RFP Consultancies with verified general contact emails)
esg_targets = [
    {"company": "CSRWorks International", "email": "info@csrworks.com", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "Aeterni.eco", "email": "hello@aeterni.eco", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "ISOsafe", "email": "info@isosafe.com.au", "subject": "Automating compliance check cycles for ISOsafe"},
    {"company": "ESG Partners", "email": "info@esgpartners.ca", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "ThisRock Inc.", "email": "hello@thisrockesg.com", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "ESG Pro", "email": "info@esgpro.co.uk", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "Anthesis Global", "email": "info@anthesisgroup.com", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "Nexio Projects", "email": "contact@nexioprojects.com", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "Sourcing Champions", "email": "info@sourcingchampions.com", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "Planet First (UAE)", "email": "info@theplanetfirst.org", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "Gulf Test", "email": "info@gulftest.org", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "Clenergize", "email": "info@clenergize.com", "subject": "Cutting EcoVadis questionnaire prep time for your clients"},
    {"company": "DETA", "email": "info@deta.global", "subject": "Cutting EcoVadis questionnaire prep time for your clients"}
]

rfp_targets = [
    {"company": "Hudson Succeed", "email": "info@hudson-bidwriters.com", "subject": "AI-matching engine for RFP response drafting"},
    {"company": "GDI Consulting", "email": "info@gdicwins.com", "subject": "AI-matching engine for RFP response drafting"},
    {"company": "The RFP Firm", "email": "info@therfpfirm.com", "subject": "AI-matching engine for RFP response drafting"},
    {"company": "The RFP Success Company", "email": "info@therfpsuccesscompany.com", "subject": "AI-matching engine for RFP response drafting"},
    {"company": "The RFP House", "email": "info@therfphouse.com", "subject": "AI-matching engine for RFP response drafting"}
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

def send_email(server, sender_email, target, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = target["email"]
    msg['Subject'] = target["subject"]
    msg.attach(MIMEText(body, 'plain'))

    try:
        server.sendmail(sender_email, [target["email"]], msg.as_string())
        print(f"[SUCCESS] Sent email to {target['company']} ({target['email']})")
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
        print("[CRITICAL ERROR] Credentials not configured in .env!")
        exit(1)

    print(f"Starting bulk outreach campaign from {sender_email}...")
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
    except Exception as e:
        print(f"[CRITICAL ERROR] SMTP Login failed: {e}")
        exit(1)

    success_count = 0
    total_count = len(esg_targets) + len(rfp_targets)

    print(f"\n--- Processing {len(esg_targets)} ESG Targets ---")
    for target in esg_targets:
        if send_email(server, sender_email, target, esg_template_body):
            success_count += 1

    print(f"\n--- Processing {len(rfp_targets)} RFP Targets ---")
    for target in rfp_targets:
        if send_email(server, sender_email, target, rfp_template_body):
            success_count += 1

    server.close()
    print(f"\nBulk campaign complete. Successfully sent {success_count} / {total_count} emails.")
