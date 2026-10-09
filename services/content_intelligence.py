import json
import os

from dotenv import load_dotenv
from services.llm_pool import LLMPool

load_dotenv()


class ContentIntelligence:

    def __init__(self, provider: str = "auto"):
        self.provider = provider
        self.llm = LLMPool(preferred_provider=provider)

    def analyze(self, extracted_text, source_files=None, file_metas=None):

        if not extracted_text or not extracted_text.strip():
            raise ValueError(
                "No content was provided for analysis."
            )

        source_files = source_files or []
        file_metas = file_metas or []

        prompt = f"""
You are the Content Intelligence Engine of BizzoraAI.

Your job is to understand source material and convert it
into a structured representation that can later be used
to generate different deliverables.

Supported deliverables include:

- Video
- Presentation
- Executive Summary
- LinkedIn Post
- X/Twitter Post
- Infographic
- Advisory
- Article
- Social Media Content

SOURCE CONTENT:

{extracted_text}

SOURCE FILES:

{json.dumps(source_files, ensure_ascii=False)}

Analyze the source carefully.

Do NOT invent facts.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "title": "",
    "content_type": "",
    "summary": "",
    "language": "",
    "main_topic": "",

    "key_points": [],

    "important_facts": [],

    "statistics": [],

    "entities": [],

    "events": [],

    "quotes": [],

    "recommendations": [],

    "target_audience": [],

    "important_visuals": [],

    "keywords": [],

    "source_files": []
}}

Rules:

1. Extract information only from the source.
2. Never fabricate facts.
3. Preserve names of people and organizations.
4. Preserve numbers accurately.
5. Preserve dates accurately.
6. Preserve locations accurately.
7. Identify important events.
8. Identify important statistics.
9. Identify useful visual information.
10. If information is unavailable, use an empty
    string or empty array.
11. Keep the result reusable by multiple
    output generators.
"""

        print("\nAnalyzing source content...")

        response = self.llm.generate(prompt)

        if not response:
            raise ValueError(
                "LLM returned an empty response."
            )

        text = response.strip()

        # Remove markdown code fences
        if text.startswith("```"):

            text = text.replace(
                "```json",
                ""
            )

            text = text.replace(
                "```",
                ""
            )

            text = text.strip()

        import re
        try:
            content_model = json.loads(text)
        except json.JSONDecodeError as e:
            # Attempt to extract JSON substring if wrapped in commentary
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                try:
                    content_model = json.loads(json_match.group(0))
                except Exception:
                    content_model = None
            else:
                content_model = None

            if content_model is None:
                first_lines = [l.strip() for l in extracted_text.splitlines() if l.strip()][:5]
                content_model = {
                    "title": first_lines[0][:80] if first_lines else "Ingested Industrial Document",
                    "summary": " ".join(first_lines)[:400] if first_lines else "Ingested technical content.",
                    "key_points": [l for l in first_lines[:3]],
                }

        # Basic validation
        required_fields = [
            "title",
            "content_type",
            "summary",
            "language",
            "main_topic",
            "key_points",
            "important_facts",
            "statistics",
            "entities",
            "events",
            "quotes",
            "recommendations",
            "target_audience",
            "important_visuals",
            "keywords",
            "source_files"
        ]

        for field in required_fields:
            if field not in content_model:
                content_model[field] = []
                if field in [
                    "title",
                    "content_type",
                    "summary",
                    "language",
                    "main_topic"
                ]:
                    content_model[field] = ""

        # Deterministically extract equipment tags, line numbers, and measurements from source
        eq_tags = list(dict.fromkeys(re.findall(r"\b[A-Z]{1,4}-[0-9]{2,4}[A-Z]?\b", extracted_text)))
        measurements = list(dict.fromkeys(re.findall(r"\b\d+(?:\.\d+)?\s*(?:bar|psi|C|°C|mm|m|kW|V|A|Hz|rpm|mm/s|kPa|MPa)\b", extracted_text, re.IGNORECASE)))

        existing_entities = [str(e) for e in content_model.get("entities", [])]
        for tag in eq_tags:
            if tag not in existing_entities:
                existing_entities.append(tag)
        content_model["entities"] = existing_entities

        existing_stats = [str(s) for s in content_model.get("statistics", [])]
        for m in measurements:
            if m not in existing_stats:
                existing_stats.append(m)
        content_model["statistics"] = existing_stats

        # Always preserve actual source files, raw extracted text, and file metadata
        content_model["raw_text"] = extracted_text
        content_model["source_files"] = source_files
        content_model["file_metas"] = file_metas

        return content_model
    def print_model(self, content_model):

        print("\n")
        print("=" * 60)
        print("          CONTENT INTELLIGENCE RESULT")
        print("=" * 60)

        print(
            f"\nTitle: {content_model.get('title', '')}"
        )

        print(
            f"Content Type: "
            f"{content_model.get('content_type', '')}"
        )

        print(
            f"Language: "
            f"{content_model.get('language', '')}"
        )

        print(
            f"Main Topic: "
            f"{content_model.get('main_topic', '')}"
        )

        print("\nSummary:")
        print(
            content_model.get(
                "summary",
                ""
            )
        )

        print("\nKey Points:")

        for point in content_model.get(
            "key_points",
            []
        ):
            print(f"  • {point}")

        print("\nImportant Facts:")

        for fact in content_model.get(
            "important_facts",
            []
        ):
            print(f"  • {fact}")

        print("\nStatistics:")

        for statistic in content_model.get(
            "statistics",
            []
        ):
            print(f"  • {statistic}")

        print("\nEntities:")

        for entity in content_model.get(
            "entities",
            []
        ):
            print(f"  • {entity}")

        print("\nEvents:")

        for event in content_model.get(
            "events",
            []
        ):
            print(f"  • {event}")

        print("\nRecommendations:")

        for recommendation in content_model.get(
            "recommendations",
            []
        ):
            print(f"  • {recommendation}")

        print("\nTarget Audience:")

        for audience in content_model.get(
            "target_audience",
            []
        ):
            print(f"  • {audience}")

        print("\nImportant Visuals:")

        for visual in content_model.get(
            "important_visuals",
            []
        ):
            print(f"  • {visual}")

        print("\nKeywords:")

        for keyword in content_model.get(
            "keywords",
            []
        ):
            print(f"  • {keyword}")

        print("\n" + "=" * 60)

    def save(self, content_model, filename):

        output_dir = "output/content"

        os.makedirs(
            output_dir,
            exist_ok=True
        )

        output_path = os.path.join(
            output_dir,
            filename
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                content_model,
                file,
                indent=4,
                ensure_ascii=False
            )

        print(
            f"\nContent model saved to: {output_path}"
        )

        return output_path