# YouTube Upload Package — DocAgent Demo

## Logo files (in this folder)

- `docagent_logo_icon.png` — 800×800, transparent background. Use as the **channel avatar** (YouTube Studio → Customization → Branding → Picture) and as a video watermark.
- `docagent_logo_icon_flat.png` — same icon, solid dark background. Use if the upload target doesn't accept transparency.
- `docagent_wordmark_transparent.png` — 1600×420 horizontal logo (icon + "DocAgent" + tagline), transparent background. Best for the opening/closing title card overlay in the video itself, or as a watermark bug in the corner.
- `docagent_wordmark_flat.png` — same wordmark, solid dark background. Use as a static title card if you want a clean 2–3 second brand intro before the 90-second demo starts.

Both are generated programmatically (PIL/Python), not traced from any stock icon set, so there's no licensing question using them commercially.

---

## Title options (pick one, ranked by recommendation)

1. **DocAgent: AI Compliance Agent Answers 10 Security Frameworks in 90 Seconds** *(74 characters — recommended)*
2. AI-Powered Questionnaire Automation: CAIQ, SIG, NIST, VSA & ISO 27001 in One Engine *(84 characters)*
3. How I Built a Self-Hosted AI Agent for Enterprise Security Questionnaires *(75 characters)*
4. From 8 Hours to 90 Seconds: AI Agent for Compliance Questionnaire Response *(76 characters)*

**Why #1**: leads with the product name (builds brand recall for repeat viewers), states a concrete number (10 frameworks), and a concrete time (90 seconds) — both are strong click triggers and match what's actually on screen, so it won't read as clickbait.

---

## Description (copy-paste ready)

```
DocAgent is a private, self-hosted AI agent that reads enterprise compliance questionnaires — CAIQ, SIG, NIST, VSA, ISO 27001, and more — cross-references them against your policy documents, and drafts audit-ready answers with source citations and confidence scoring.

In this 90-second demo, DocAgent processes 10 questions across five major security and compliance frameworks, searching 1,000 rows of structured control data in real time. Every answer comes with a citation back to the exact row and document it was drawn from — no black box, no hallucinated compliance claims.

What you're seeing:
– Multi-framework document search (CAIQ, SIG, NIST, VSA, ISO 27001)
– Confidence-scored answers: auto-approved, flagged for human review, or marked as insufficient evidence
– Full audit trail for every match — built for teams that need to show their work, not just get an answer
– Self-hosted / private deployment — your compliance documents never leave your infrastructure

Who this is for: security teams, GRC managers, and boutique compliance/ESG consultancies who are tired of manually copy-pasting answers into vendor security questionnaires every time a customer's procurement team sends one over.

This is a self-hosted alternative positioned well below the cost of enterprise RFP/GRC platforms — built for teams that want the automation without the six-figure annual contract or the requirement to upload sensitive documents to a third-party cloud.

Interested in a custom build or a private deployment for your team? Reach out — link in the channel description.

#AIAgent #ComplianceAutomation #CAIQ #ISO27001 #NIST #SecurityQuestionnaire #GRC #EnterpriseAI #DocumentIntelligence #RAG
```

---

## Tags field (comma-separated, paste into YouTube Studio "Tags")

```
AI agent, compliance automation, security questionnaire, CAIQ, SIG questionnaire, NIST CSF, VSA vendor security alliance, ISO 27001, GRC software, vendor risk management, RFP automation, document intelligence, RAG retrieval augmented generation, enterprise AI, self-hosted AI, private AI deployment, AI compliance tool, vendor questionnaire automation, ESG questionnaire, AI for security teams
```

---

## Thumbnail text (large card text, 3–5 words max)

- `10 Frameworks. 90 Seconds.`
- `AI Reads Your Compliance Docs`
- `8hrs → 90sec`

Pair the thumbnail text with a screenshot of the blue-highlighted matched row from `demo_ui.html` — that single frame communicates "the AI found the exact answer" better than any text alone.

---

## Where to place the logo in the video itself

- 0:00–0:03: `docagent_wordmark_flat.png` full-screen as a title card before the demo starts.
- Throughout: small `docagent_logo_icon.png` as a corner watermark (CapCut/Premiere → add image → set opacity ~70%, corner position, resize to roughly 6% of frame width).
- End card (last 2–3 seconds): `docagent_wordmark_flat.png` again with your contact info or a "Message me for a custom build" text overlay.
