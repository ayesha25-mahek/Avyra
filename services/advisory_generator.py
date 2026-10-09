from services.llm_pool import LLMPool


class AdvisoryGenerator:

    def __init__(self):
        self.llm = LLMPool()

    def generate(self, content_model, output_request):

        raw_source = content_model.get("raw_text") or content_model.get("summary") or ""
        entities = content_model.get("entities") or []
        stats = content_model.get("statistics") or []

        prompt = f"""
You are an expert advisory document writer for Avyara Enterprise Workbench.

Create a structured advisory document using ONLY the information in the source material below.

SOURCE EVIDENCE CONTENT:
{raw_source[:8000]}

STRUCTURED EXTRACTED ENTITIES & STATS:
- Entities / Equipment: {entities}
- Numerical Parameters: {stats}

DOCUMENT STRUCTURE:
1. ADVISORY TITLE
2. DATE / CLASSIFICATION (if available)
3. EXECUTIVE OVERVIEW (2-3 sentences)
4. BACKGROUND & CONTEXT
5. KEY FINDINGS / THREAT INDICATORS (bullet list)
6. RISK ASSESSMENT
7. RECOMMENDATIONS (numbered, actionable)
8. CONCLUSION
9. REFERENCES / SOURCES (if mentioned in content)

REQUIREMENTS:
- Use ONLY facts from the content model.
- Never invent threats, statistics, or recommendations not supported by the source.
- Tone: {output_request.tone}
- Language: {output_request.language}
- Target audience: {output_request.target_audience}
- Do not mention AI.

Return ONLY the advisory document text.
"""
        result = self.llm.generate(prompt)
        if not result:
            raise ValueError("Advisory generator returned empty output.")
        return result.strip()
