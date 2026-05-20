import json
import os
import re

import anthropic
import httpx

# Compatibility patch: httpx >= 0.28 removed the 'proxies' argument.
# The anthropic SDK (<= 0.34) still passes it when building its internal client.
_original_httpx_client_init = httpx.Client.__init__

def _patched_httpx_client_init(self, *args, **kwargs):
    kwargs.pop("proxies", None)
    _original_httpx_client_init(self, *args, **kwargs)

httpx.Client.__init__ = _patched_httpx_client_init


def tailor_cv(job_description: str, master_cv: dict) -> dict:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""
You are an expert resume/CV optimization AI. Your task is to analyze a target job description and generate tailored resume content that strictly aligns with the role type. Follow these steps exactly:

🔍 STEP 1: CLASSIFY THE JOB CATEGORY
Analyze the provided job title and description. Categorize it into one of these buckets:
- Development/Engineering (Software, Full-Stack, DevOps, Automation, Data/ML)
- Infrastructure/Operations (Network Engineer, SysAdmin, Cloud Ops, SRE, Telecom)
- Support/Service Desk (Help Desk, IT Support, Technical Support, Field Technician)
- Security/Compliance (Cybersecurity, GRC, Audit, IAM)
- Other/Management (IT Manager, Project Manager, Team Lead, etc.)

📌 STEP 2: APPLY CONDITIONAL LOGIC
- IF the role falls under Development/Engineering → Include a "Projects" section with 2-3 highly relevant, technically accurate projects that match the JD's stack and responsibilities.
- IF the role falls under Infrastructure/Operations, Support/Service Desk, Security, or Other/Management → OMIT the Projects section entirely. Instead, expand "Professional Experience" and "Core Skills" with role-specific duties: troubleshooting, system/network design, incident resolution, SLA management, vendor coordination, certifications, and operational tooling.
- NEVER force-fit software development, CI/CD pipelines, data automation, or coding-heavy projects into non-development roles. If a project is borderline, default to EXCLUDING it and strengthening experience bullets instead.

📥 INPUT FORMAT:
Target Job Title: {''}
Target Job Description: {job_description}
My Background (optional): [Brief notes on your actual experience, tools, or certifications]

📌 YOU MUST ALSO CONSIDER THIS MASTER CV DATA (SOURCE OF TRUTH):
{json.dumps(master_cv, indent=2)}

📤 OUTPUT FORMAT:
Return ONLY valid JSON in exactly this structure, no explanation, no markdown:
{{
  "role_title": "string",
  "company": "string",
  "summary": "string (2-3 lines, JD-keyword optimized)",
  "skills": {{
    "languages": ["string"],
    "frameworks": ["string"],
    "databases": ["string"],
    "tools": ["string"],
    "concepts": ["string"]
  }},
  "experience": [
    {{
      "title": "string",
      "company": "string",
      "type": "string",
      "start": "string",
      "end": "string",
      "bullets": ["string"]
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "description": "string",
      "tech": ["string"],
      "link": "string or empty string"
    }}
  ],
  "cover_letter": "string (3 to 4 paragraphs, professional but human, no AI tells, no cliches like passionate or dynamic, no mention of the word excited)"
}}

⚠️ STRICT GUARDRAILS:
- Do NOT hallucinate tools, frameworks, or projects not aligned with the job category.
- Match terminology, seniority level, and priorities from the job description.
- Keep all content realistic, professional, and ATS-friendly.
- If uncertain, always exclude projects and deepen the experience section.
- Never repeat generic filler like "hard worker" or "team player". Use concrete responsibilities and outcomes.

Conditional projects rule:
- If the category is NOT Development/Engineering, return an empty array for "projects": [] (so the Projects section is effectively omitted).
- If the category IS Development/Engineering, return 2-3 projects maximum in "projects".

Begin by identifying the job category, then generate the tailored resume sections accordingly.
"""


    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"```$", "", raw)
    return json.loads(raw)
