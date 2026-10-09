class OutputRequest:

    SUPPORTED_OUTPUTS = [
        "video",
        "linkedin",
        "twitter",
        "presentation",
        "advisory",
        "executive_summary",
        "infographic",
        "article",
        "inspection_analysis",
        # Industrial workflow outputs
        "defect_report",
        "technical_report",
        "drawing_analysis",
        "inspection_summary",
        "extracted_text",
        "document_summary",
        "equipment_tags",
        "data_summary",
        "abnormal_values",
        "analysis_workbook",
    ]

    def __init__(
        self,
        outputs,
        language="English",
        tone="Professional",
        target_audience="General"
    ):

        if not outputs:
            raise ValueError(
                "At least one output must be selected."
            )

        invalid_outputs = [
            output
            for output in outputs
            if output not in self.SUPPORTED_OUTPUTS
        ]

        if invalid_outputs:
            raise ValueError(
                f"Unsupported outputs: {invalid_outputs}"
            )

        self.outputs = outputs
        self.language = language
        self.tone = tone
        self.target_audience = target_audience

    def to_dict(self):

        return {
            "outputs": self.outputs,
            "language": self.language,
            "tone": self.tone,
            "target_audience": self.target_audience
        }

    def print_request(self):

        print("\n")
        print("=" * 60)
        print("              OUTPUT REQUEST")
        print("=" * 60)

        print("\nSelected outputs:")

        for output in self.outputs:
            print(f"  [SUCCESS] {output}")

        print(
            f"\nLanguage: {self.language}"
        )

        print(
            f"Tone: {self.tone}"
        )

        print(
            f"Target audience: {self.target_audience}"
        )

        print("=" * 60)