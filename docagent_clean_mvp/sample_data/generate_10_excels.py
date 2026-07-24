import os
from openpyxl import Workbook

# Define categories and templates for 10 domains
domains = [
    {
        "name": "ISO27001_Information_Security.xlsx",
        "category": "Information Security",
        "behaviors": ["Access Control", "Security Training", "CISO Appointed", "Asset Management", "Incident Response"],
        "departments": ["IT Security", "HR", "Legal", "Operations"],
        "keywords": ["access", "ciso", "training", "firewall", "encryption", "password", "audit", "patch"],
        "clause_template": "The organization shall implement and maintain controls for {behavior} to safeguard information assets.",
        "status_template": "Fully implemented. Checked annually by IT Security. CISO reviews progress monthly."
    },
    {
        "name": "GDPR_Data_Privacy.xlsx",
        "category": "Data Privacy",
        "behaviors": ["GDPR Compliance", "Data Retention", "Consent Management", "Subject Access Request", "Data Encryption"],
        "departments": ["Legal & Compliance", "IT", "Customer Support"],
        "keywords": ["gdpr", "retention", "consent", "privacy", "personal data", "encryption", "breach", "cookies"],
        "clause_template": "Personal data processing must comply with GDPR guidelines, emphasizing {behavior} for customer trust.",
        "status_template": "Active. Customer data is encrypted at rest and in transit. Logs retained for audit."
    },
    {
        "name": "ISO22301_Business_Continuity.xlsx",
        "category": "Business Continuity",
        "behaviors": ["Disaster Recovery Plan", "RTO & RPO Standards", "System Backup", "Alternative Site", "Crisis Management"],
        "departments": ["IT Operations", "EHS", "Facilities"],
        "keywords": ["drp", "rto", "rpo", "backup", "disaster", "redundancy", "drill", "generator"],
        "clause_template": "Critical operations shall establish metrics like {behavior} to ensure recovery during disruptions.",
        "status_template": "Verified. Daily backups stored offsite with 4-hour RTO and 1-hour RPO target."
    },
    {
        "name": "ISO14001_Environmental_Management.xlsx",
        "category": "Environmental Management",
        "behaviors": ["Waste Management", "Energy Conservation", "Chemical Storage", "Carbon Footprint", "Water Recycle"],
        "departments": ["Facilities", "EHS", "Procurement"],
        "keywords": ["waste", "energy", "chemical", "emission", "recycling", "water", "sustainability", "co2"],
        "clause_template": "Operations must minimize ecological footprint through proactive {behavior} and monitoring.",
        "status_template": "Compliant. EcoVadis gold certified. All hazard waste processed via certified third party."
    },
    {
        "name": "ISO45001_Occupational_Health_Safety.xlsx",
        "category": "Health & Safety",
        "behaviors": ["Hazard Prevention", "Emergency Exits", "Fire Drills", "PPE Supply", "Incident Reporting"],
        "departments": ["EHS", "HR", "Facilities"],
        "keywords": ["hazard", "exit", "fire", "ppe", "safety", "injury", "medical", "first aid"],
        "clause_template": "The workplace must provide a safe environment by enforcing {behavior} protocols.",
        "status_template": "Active. PPE distributed quarterly. Safety audits conducted monthly with zero major incident report."
    },
    {
        "name": "RBA_Labor_Standard.xlsx",
        "category": "Labor Standards",
        "behaviors": ["Minimum Working Age", "Working Hours Limit", "Non-Discrimination", "Fair Wages", "Freedom of Association"],
        "departments": ["HR", "Legal", "General Affairs"],
        "keywords": ["age", "hours", "discrimination", "wage", "association", "overtime", "labor", "minor"],
        "clause_template": "The supplier shall respect labor rights by establishing controls on {behavior}.",
        "status_template": "Audited. Maximum 60 hours per week enforced. Zero tolerance for underage or forced labor."
    },
    {
        "name": "FCPA_Anti_Bribery_Compliance.xlsx",
        "category": "Anti-Bribery",
        "behaviors": ["Gifts & Entertainment", "Whistleblowing Channel", "Anti-Corruption Training", "Third Party Due Diligence", "Financial Audit"],
        "departments": ["Audit", "Legal", "Procurement"],
        "keywords": ["gift", "corruption", "bribery", "whistleblower", "audit", "compliance", "ethics", "hiring"],
        "clause_template": "All business activities must reject corrupt practices through strict {behavior} rules.",
        "status_template": "Implemented. Whistleblower hotline active 24/7. Annual compliance training completion at 100%."
    },
    {
        "name": "ISO9001_Quality_Management.xlsx",
        "category": "Quality Management",
        "behaviors": ["Customer Satisfaction", "Quality Audit", "Product Testing", "Supplier Evaluation", "Corrective Action"],
        "departments": ["Quality Assurance", "R&D", "Customer Service"],
        "keywords": ["quality", "testing", "audit", "defect", "calibration", "satisfaction", "inspection", "sop"],
        "clause_template": "Acme ensures product excellence by implementing standard processes for {behavior}.",
        "status_template": "ISO 9001:2015 certified. Audit log updated monthly. Defect rate controlled under 0.05%."
    },
    {
        "name": "Supplier_Code_of_Conduct.xlsx",
        "category": "Supply Chain ESG",
        "behaviors": ["Traceability", "Conflict Minerals", "Eco-Vadis Assessment", "Subcontractor Audit", "Material Safety Data"],
        "departments": ["Procurement", "EHS", "Logistics"],
        "keywords": ["traceability", "minerals", "supplier", "assessment", "audit", "safety sheet", "logistics", "material"],
        "clause_template": "Suppliers are required to provide full disclosure regarding {behavior}.",
        "status_template": "Registered. 95% of suppliers signed compliance declaration. Conflict mineral report filed annually."
    },
    {
        "name": "Intellectual_Property_Policy.xlsx",
        "category": "Intellectual Property",
        "behaviors": ["IP Protection", "NDA Signing", "Trade Secret Security", "Patent Management", "Open Source Compliance"],
        "departments": ["R&D", "Legal", "IT"],
        "keywords": ["ip", "nda", "patent", "copyright", "trade secret", "open source", "license", "trademark"],
        "clause_template": "To preserve competitive edge, Acme implements rigorous management of {behavior}.",
        "status_template": "Active. NDAs required for all visitors and suppliers. IP ownership clauses embedded in all R&D contracts."
    }
]

def generate_excels():
    output_dir = "C:\\aiagent-master\\docagent_clean_mvp\\sample_data\\raw_excels"
    os.makedirs(output_dir, exist_ok=True)
    
    for domain in domains:
        wb = Workbook()
        ws = wb.active
        ws.title = "Database"
        
        # Headers matching the engine:
        ws.append([
            "Category", 
            "Behavioral Principle", 
            "Keywords", 
            "Clause Content", 
            "Department", 
            "Current Status", 
            "Reference Source"
        ])
        
        filename = domain["name"]
        category = domain["category"]
        
        # Generate 100 rows per file
        for idx in range(1, 101):
            behavior = domain["behaviors"][(idx - 1) % len(domain["behaviors"])]
            dept = domain["departments"][(idx - 1) % len(domain["departments"])]
            
            # Select 3 random keywords from domain
            kws = [domain["keywords"][(idx + offset) % len(domain["keywords"])] for offset in range(3)]
            keywords_str = "\n".join(list(set(kws)))
            
            clause = domain["clause_template"].format(behavior=behavior) + f" [Control ID: {category[:3].upper()}-{idx:03d}]"
            status = domain["status_template"] + f" Verified on row {idx} audit."
            source = f"{filename[:-5].replace('_', ' ')} Policy manual Section {idx // 10 + 1}.{idx % 10 + 1}"
            
            ws.append([
                category,
                behavior,
                keywords_str,
                clause,
                dept,
                status,
                source
            ])
            
        filepath = os.path.join(output_dir, filename)
        wb.save(filepath)
        print(f"Generated {filename} with {ws.max_row - 1} rows.")

if __name__ == "__main__":
    generate_excels()
