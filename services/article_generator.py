from services.llm_pool import LLMPool


class ArticleGenerator:

    def __init__(self):
        self.llm = LLMPool()

    def generate(self, content_model, output_request):

        raw_source = content_model.get("raw_text") or content_model.get("summary") or ""
        entities = content_model.get("entities") or []
        stats = content_model.get("statistics") or []

        prompt = f"""
You are an expert article writer for Avyara Enterprise Workbench.

Write a full-length, high-quality technical article using ONLY the information
in the source content below.

SOURCE EVIDENCE CONTENT:
{raw_source[:8000]}

STRUCTURED EXTRACTED FACTS:
- Entities / Equipment: {entities}
- Numerical Parameters: {stats}

ARTICLE REQUIREMENTS:
1. Compelling headline (H1)
2. Engaging introduction (hook + thesis)
3. Well-structured body with H2/H3 subheadings
4. Use bullet points, numbered lists, and data where appropriate
5. Include relevant quotes or statistics from the content model
6. Strong conclusion with key takeaways
7. Length: appropriate to detail level ({output_request.target_audience} audience)
8. Tone: {output_request.tone}
9. Language: {output_request.language}
10. Do NOT fabricate facts, statistics or quotes
11. Do NOT mention AI

Return ONLY the article text in clean markdown format.
"""
        result = self.llm.generate(prompt)
        if not result:
            raise ValueError("Article generator returned empty output.")
        return result.strip()
