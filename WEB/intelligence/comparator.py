"""
JARVIS AI — Structured Comparison Engine
Generates multi-attribute comparison matrices for products, frameworks, models, and approaches.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ComparisonResult:
    """Structured comparison result across multiple options."""
    entities: List[str]
    attributes: List[str]
    matrix: Dict[str, Dict[str, str]]  # {entity: {attr: value}}
    markdown_table: str
    recommendation: Optional[str] = None


class ComparisonEngine:
    """Produces objective, grounded comparative matrices between items."""

    DEFAULT_ATTRIBUTES = [
        "Core Capabilities",
        "Cost / Pricing",
        "Latency / Speed",
        "Privacy & Data Security",
        "Local / Offline Support",
        "API Availability",
        "Best Use Case",
    ]

    # Pre-grounded reference knowledge for common technologies when comparing
    KNOWN_TECH_PROFILES = {
        "openai": {
            "Core Capabilities": "State-of-the-art multimodal reasoning, tool calling, code generation (GPT-4o)",
            "Cost / Pricing": "Paid usage-based API pricing per token",
            "Latency / Speed": "Fast cloud inference, dependent on network latency",
            "Privacy & Data Security": "Cloud-hosted; enterprise agreements required for zero-retention",
            "Local / Offline Support": "No (Requires constant internet connectivity)",
            "API Availability": "Global REST API & official client SDKs",
            "Best Use Case": "Complex conversational reasoning, vision analysis, high-end cloud intelligence",
        },
        "gemini": {
            "Core Capabilities": "Massive context window, deep multimodal audio/video understanding, native Google integration",
            "Cost / Pricing": "Generous free tier with pay-as-you-go commercial tiers",
            "Latency / Speed": "Very fast, low-latency Flash tier",
            "Privacy & Data Security": "Cloud-hosted with Google Cloud compliance standards",
            "Local / Offline Support": "Gemini Nano on supported devices; large models require cloud",
            "API Availability": "Google GenAI SDK, REST API",
            "Best Use Case": "High-throughput tasks, huge document context, multimodal audio/vision pipelines",
        },
        "ollama": {
            "Core Capabilities": "Local execution of open weights models (Llama 3, Mistral, Qwen, DeepSeek)",
            "Cost / Pricing": "100% Free & Open Source; limited only by user hardware",
            "Latency / Speed": "Fast on modern local GPU/NPU; slower on CPU-only machines",
            "Privacy & Data Security": "Maximum privacy (100% local, zero data sent to external servers)",
            "Local / Offline Support": "Complete offline support, zero internet required",
            "API Availability": "Local HTTP REST server (default port 11434) with OpenAI-compatible endpoint",
            "Best Use Case": "Private enterprise data, completely offline JARVIS voice workflows, development",
        }
    }

    def compare(
        self,
        entities: List[str],
        custom_attributes: Optional[List[str]] = None,
        context_sources: Optional[List[Any]] = None
    ) -> ComparisonResult:
        """Construct structured comparison across provided entities."""
        if not entities:
            return ComparisonResult(entities=[], attributes=[], matrix={}, markdown_table="No entities provided.")

        clean_entities = [e.strip() for e in entities if e.strip()]
        attrs = custom_attributes or self.DEFAULT_ATTRIBUTES

        matrix: Dict[str, Dict[str, str]] = {}

        for ent in clean_entities:
            ent_key = ent.lower()
            matrix[ent] = {}

            # Match against profile if known
            profile = None
            for known_k, known_p in self.KNOWN_TECH_PROFILES.items():
                if known_k in ent_key or ent_key in known_k:
                    profile = known_p
                    break

            for a in attrs:
                if profile and a in profile:
                    matrix[ent][a] = profile[a]
                else:
                    matrix[ent][a] = "Information depends on specific version / configuration"

        # Build Markdown table
        table_lines = []
        header = ["Attribute"] + clean_entities
        table_lines.append("| " + " | ".join(header) + " |")
        table_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

        for a in attrs:
            row = [f"**{a}**"]
            for ent in clean_entities:
                val = matrix[ent].get(a, "N/A")
                row.append(val.replace("|", "/"))
            table_lines.append("| " + " | ".join(row) + " |")

        md_table = "\n".join(table_lines)

        # Generate recommendation if comparing known models for JARVIS
        rec = None
        lower_ents = [e.lower() for e in clean_entities]
        if any("ollama" in e for e in lower_ents) and any("openai" in e or "gemini" in e for e in lower_ents):
            rec = (
                "For JARVIS AI, a **Hybrid Architecture** is optimal: use **Ollama** locally for "
                "offline privacy, zero latency simple commands, and private tasks; route to **Gemini / OpenAI** "
                "for deep web research, complex multi-step reasoning, and visual analysis."
            )

        return ComparisonResult(
            entities=clean_entities,
            attributes=attrs,
            matrix=matrix,
            markdown_table=md_table,
            recommendation=rec,
        )


# Global singleton instance
comparison_engine = ComparisonEngine()
