from services.llm_provider import LLMProvider


class ExecutiveSummaryGenerator:

    def __init__(self):

        self.llm = LLMProvider()

    def generate(
        self,
        content_model,
        output_request
    ):

        raw_source = content_model.get("raw_text") or content_model.get("summary") or ""
        key_facts = content_model.get("important_facts") or content_model.get("key_points") or []
        entities = content_model.get("entities") or []
        stats = content_model.get("statistics") or []

        prompt = f"""
You are an expert executive briefing writer for Avyara Enterprise Workbench.

Create a concise and accurate executive summary from the supplied source material.

SOURCE EVIDENCE CONTENT:
{raw_source[:8000]}

STRUCTURED EXTRACTED FACTS & ENTITIES:
- Key Facts: {key_facts}
- Identified Entities / Equipment: {entities}
- Recorded Parameters / Statistics: {stats}

REQUIREMENTS:
1. Base the summary STRICTLY on the facts and evidence provided above.
2. Never invent equipment names, measurements, defects, or statutory standards not present in the source.
3. Preserve all names, equipment IDs, numbers, and dates accurately.
4. Clearly explain the main topic.
5. Include the most important findings.
6. Include important recommendations when available.
7. Remove unnecessary details.
8. Make the result easy for a decision maker to read.
9. Use headings and bullet points where appropriate.
10. Write in the requested language.
11. Match the requested tone.
12. Do not mention AI.

LANGUAGE:
{output_request.language}

TONE:
{output_request.tone}

TARGET AUDIENCE:
{output_request.target_audience}

Return ONLY the executive summary.
"""

        print("\nGenerating executive summary...")

        result = self.llm.generate(prompt)

        if not result:

            raise ValueError(
                "Executive summary generator returned empty output."
            )

        return result.strip()