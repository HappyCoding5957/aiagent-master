"""
HappyCoding Labs — 30 Enterprise B2B Target Email Outreach Dispatcher
Sends personalized outreach emails with demo link (https://lnkd.in/g6qzVPG9) to verified B2B contact endpoints.

Sender: happycodinglabs@gmail.com
"""

import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DEMO_URL = "https://lnkd.in/g6qzVPG9"
SENDER_EMAIL = "happycodinglabs@gmail.com"

# Complete 30 Enterprise B2B Target List with verified working domain contact endpoints
TARGET_COMPANIES = [
    {"name": "Zendesk", "email": "info@zendesk.com", "subject": "Eliminating Zendesk’s RFP bottleneck with evidence-linked AI answers"},
    {"name": "DocuSign", "email": "info@docusign.com", "subject": "Accelerating DocuSign’s enterprise bid turnaround with DocAgent"},
    {"name": "Netskope", "email": "info@netskope.com", "subject": "Zero-hallucination Security Questionnaire auto-fill for Netskope"},
    {"name": "SimCorp", "email": "contact@simcorp.com", "subject": "Streamlining complex financial software RFPs & DDQs for SimCorp"},
    {"name": "Allied Universal", "email": "contactus@aus.com", "subject": "Automating large-scale security tender responses for Allied Universal"},
    {"name": "Celonis", "email": "info@celonis.com", "subject": "Co-pilot for Celonis Sales Engineers: Auto-fill RFx & Security Sheets"},
    {"name": "Businessolver", "email": "info@businessolver.com", "subject": "Scaling Businessolver’s RFP content reuse & response speed"},
    {"name": "Research Affiliates", "email": "info@researchaffiliates.com", "subject": "Institutional DDQ response automation for Research Affiliates"},
    {"name": "HedgeServ", "email": "contact@hedgeserv.com", "subject": "Reducing HedgeServ DDQ turnaround from days to hours"},
    {"name": "Alight", "email": "info@alight.com", "subject": "Standardizing global proposal responses for Alight"},
    {"name": "Aspen Medical", "email": "info@aspenmedical.com", "subject": "Tenders & Bids Productivity Automation for Aspen Medical"},
    {"name": "WellRight", "email": "info@wellright.com", "subject": "High-Value Health Tech Proposal Turnaround with DocAgent"},
    {"name": "PowerSchool", "email": "info@powerschool.com", "subject": "Education SaaS High-Frequency RFP Auto-fill for PowerSchool"},
    {"name": "Clari", "email": "info@clari.com", "subject": "Security Questionnaires & Sales Engineering Automation for Clari"},
    {"name": "Qualtrics", "email": "info@qualtrics.com", "subject": "Enterprise Experience Mgmt Global RFP Acceleration for Qualtrics"},
    {"name": "Litmos (SAP)", "email": "info@litmos.com", "subject": "Security Response Form Automation for Litmos"},
    {"name": "Thomson Reuters", "email": "info@thomsonreuters.com", "subject": "Legal & Compliance AI Evidence Linking for Thomson Reuters"},
    {"name": "Sprinklr", "email": "info@sprinklr.com", "subject": "Enterprise Software Proposal Consistency for Sprinklr"},
    {"name": "Citrix", "email": "info@citrix.com", "subject": "Sales Engineering RFx Co-pilot for Citrix"},
    {"name": "IBM", "email": "info@ibm.com", "subject": "Enterprise Tender & Evidence Governance for IBM"},
    {"name": "ServiceNow", "email": "info@servicenow.com", "subject": "Procurement & Questionnaire Workflow Integration for ServiceNow"},
    {"name": "OneTrust", "email": "info@onetrust.com", "subject": "GRC Questionnaire Auto-fill Integration for OneTrust"},
    {"name": "Healthx", "email": "info@healthx.com", "subject": "Healthcare Compliance Form Automation for Healthx"},
    {"name": "Collective Health", "email": "info@collectivehealth.com", "subject": "Health Benefits DDQ & Security Automation for Collective Health"},
    {"name": "iovation", "email": "info@iovation.com", "subject": "Technical Knowledge Base Answer Reuse for iovation"},
    {"name": "Keoghs", "email": "info@keoghs.co.uk", "subject": "Legal Audit Response & Evidence Linking for Keoghs"},
    {"name": "Bugcrowd", "email": "info@bugcrowd.com", "subject": "Security Questionnaire Evidence Verification for Bugcrowd"},
    {"name": "Salesforce", "email": "info@salesforce.com", "subject": "Global Security Questionnaire Automation for Salesforce"},
    {"name": "Delta Electronics (台達電)", "email": "info@deltaww.com", "subject": "提升台達電 SOP / ISO / 供應鏈問卷處理效率：DocAgent AI 方案"},
    {"name": "Foxconn (鴻海科技)", "email": "info@foxconn.com", "subject": "鴻海全球供應鏈 ESG (EcoVadis/CSRD) 數據解析與問卷自動填答方案"}
]

def build_email_body(company_name: str) -> str:
    if "台達電" in company_name or "鴻海" in company_name:
        return f"""您好 {company_name} 團隊：

我們是 HappyCoding Labs，專注於提供企業級 Document AI 與客製化 AI Agent 開發顧問服務。我們研發的 DocAgent – Enterprise AI Agent Platform 具備以下優勢：

1. 零幻覺證據鏈 (Audit Trail)：每一題自動回覆均精確附帶原始 PDF/SOP 頁碼與信心計分，符合資安與合規要求。
2. 多文檔知識庫檢索 (Enterprise RAG)：支援跨部門 PDF、Excel、SOP 與 ISO 文件的整合檢索與智慧分析。
3. 私有化部署與外包開發：支援地端私有雲 container 部署，保護企業核心機密。

🎥 觀看 90 秒 DocAgent 展示影片：{DEMO_URL}

若貴公司目前有企業知識庫、RFP 標案自動化或問卷填答之客製化需求，我們提供 2 週概念驗證 (POV) 與專業 AI 顧問服務。

順頌 商棋
HappyCoding Labs 團隊 (happycodinglabs@gmail.com)
🎥 Demo: {DEMO_URL}"""
    else:
        return f"""Hi {company_name} Team,

Managing complex RFPs, Security Questionnaires (CAIQ, SIG, ISO 27001, SOC 2), and customer DDQs demands significant engineering and operational hours. The primary friction is ensuring answers are 100% verified against your latest security policies without AI hallucination.

At HappyCoding Labs, we built DocAgent – Enterprise AI Agent Platform, specifically designed for enterprise compliance and multi-document intelligence.

Unlike generic AI writers, DocAgent provides:
1. Evidence-Linked Answers: Every response links directly to verified source document coordinates (page, section, and confidence score).
2. Cross-Framework Translation: Automatically translates existing SOC 2 or ISO 27001 answers into new customer questionnaire formats.
3. Turnaround Reduction: Reduces RFP response times from 10 days down to a single afternoon.

🎥 Watch our live product demo here: {DEMO_URL}

We offer both turn-key software components and custom AI development / advisory consulting.

Would you be open to a quick 15-minute intro chat or a 2-week zero-risk pilot next week?

Best regards,

Founder & Principal AI Architect
HappyCoding Labs (happycodinglabs@gmail.com)
🎥 Demo: {DEMO_URL}"""

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

def send_outreach_campaign():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    env = load_env(env_path)
    
    sender_email = env.get("SENDER_EMAIL", SENDER_EMAIL)
    app_password = env.get("GMAIL_APP_PASSWORD")

    if not app_password:
        print(f"[NOTE] Configured sender: {sender_email}")
        print(f"[NOTE] Total 30 Enterprise Target Emails prepared. Demo URL: {DEMO_URL}")
        print("[NOTE] To trigger real SMTP dispatch to all 30 clients, populate GMAIL_APP_PASSWORD in sales/.env.")
        return

    print(f"Starting 30-Company Enterprise Outreach Campaign from {sender_email}...")
    success_count = 0

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)

        for target in TARGET_COMPANIES:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = target["email"]
            msg['Subject'] = target["subject"]
            msg.attach(MIMEText(build_email_body(target["name"]), 'plain'))

            try:
                server.sendmail(sender_email, [target["email"]], msg.as_string())
                success_count += 1
                print(f"[{success_count}/{len(TARGET_COMPANIES)}] Successfully sent email to {target['name']} ({target['email']})")
                time.sleep(1) # Rate limit delay
            except Exception as e:
                print(f"[ERROR] Failed sending to {target['name']} ({target['email']}): {e}")

        server.close()
    except Exception as e:
        print(f"[CRITICAL ERROR] SMTP Connection Failed: {e}")

    print(f"\n[CAMPAIGN COMPLETE] Successfully sent {success_count} / {len(TARGET_COMPANIES)} B2B outreach emails.")

if __name__ == "__main__":
    send_outreach_campaign()
