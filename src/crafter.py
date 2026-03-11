"""Stage C — Curvature/Craft: Generate Strike using AI provider."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from src.config import Config
from src.models import Strike, Target, Statement, Evidence, VALID_VERDICTS
from src.utils import compute_content_hash, load_system_prompt

logger = logging.getLogger("prinzclaw")


class Crafter:
    """Generates Strikes by calling the configured AI provider."""

    def __init__(self, config: Config, prompt_path: str | None = None):
        self.config = config
        self._system_prompt = load_system_prompt(prompt_path or "prompts/system_prompt.md")
        self._provider = config.ai_provider
        self._model = config.ai_model
        self._api_key = config.get_ai_api_key()

    async def craft(self, target: Target, statement: Statement,
                    evidence: list[Evidence], style: str = "") -> Strike:
        """Generate a Strike from analyzed data.

        Calls the AI provider to generate verdict, strike text, and
        structures the output in prinzclaw v1.0 format.
        """
        style = style or self.config.style
        user_prompt = self._build_user_prompt(target, statement, evidence, style)

        logger.info("Crafting strike against %s via %s/%s",
                     target.name, self._provider, self._model)

        ai_response = await self._call_ai(user_prompt)
        strike = self._parse_ai_response(ai_response, target, statement, evidence)

        # Compute content hash
        strike.content_hash = compute_content_hash(strike)

        logger.info("Strike crafted: %s [%s] — %s",
                     strike.report_id, strike.verdict, target.name)
        return strike

    def _build_user_prompt(self, target: Target, statement: Statement,
                           evidence: list[Evidence], style: str) -> str:
        """Build the user prompt for the AI provider."""
        evidence_text = ""
        if evidence:
            evidence_lines = []
            for i, e in enumerate(evidence, 1):
                evidence_lines.append(
                    f"{i}. {e.claim} (Source: {e.source}, {e.source_url}, {e.date})"
                )
            evidence_text = "\n".join(evidence_lines)
        else:
            evidence_text = "No contradicting evidence found in public records."

        return f"""ANALYZE THIS STATEMENT:

Target: {target.name} ({target.role}, {target.type})
Statement: "{statement.text}"
Source: {statement.source_url}
Date: {statement.date}

EVIDENCE FOUND:
{evidence_text}

Strike style: {style}

Generate a prinzclaw Strike. Respond ONLY with the JSON object. No markdown, no backticks, no preamble."""

    async def _call_ai(self, user_prompt: str) -> str:
        """Call the configured AI provider."""
        if self._provider == "gemini":
            return await self._call_gemini(user_prompt)
        elif self._provider == "anthropic":
            return await self._call_anthropic(user_prompt)
        elif self._provider == "openai":
            return await self._call_openai(user_prompt)
        else:
            raise ValueError(f"Unknown AI provider: {self._provider}")

    async def _call_gemini(self, user_prompt: str) -> str:
        """Call Google Gemini API."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Install google-generativeai: pip install google-generativeai")

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(
            model_name=self._model,
            system_instruction=self._system_prompt,
        )
        response = model.generate_content(user_prompt)
        return response.text

    async def _call_anthropic(self, user_prompt: str) -> str:
        """Call Anthropic Claude API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")

        client = anthropic.Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model=self._model,
            max_tokens=2048,
            system=self._system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    async def _call_openai(self, user_prompt: str) -> str:
        """Call OpenAI API."""
        try:
            import openai
        except ImportError:
            raise ImportError("Install openai: pip install openai")

        client = openai.OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
        )
        return response.choices[0].message.content

    def _parse_ai_response(self, response: str, target: Target,
                           statement: Statement,
                           provided_evidence: list[Evidence]) -> Strike:
        """Parse AI response into a Strike object."""
        # Strip markdown code fences if present
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("AI response was not valid JSON, building Strike from provided data")
            return self._build_fallback_strike(target, statement, provided_evidence, text)

        # Extract verdict
        verdict = data.get("verdict", "INSUFFICIENT_EVIDENCE")
        # Normalize verdict format (AI might use spaces/hyphens)
        verdict = verdict.upper().replace(" ", "_").replace("-", "_")
        if verdict not in VALID_VERDICTS:
            verdict = "INSUFFICIENT_EVIDENCE"

        # Extract evidence from AI response, falling back to provided evidence
        ai_evidence = data.get("evidence", [])
        evidence_objects = []
        if ai_evidence:
            for e in ai_evidence:
                if isinstance(e, dict):
                    evidence_objects.append(Evidence(
                        claim=e.get("claim") or e.get("text", ""),
                        source=e.get("source", ""),
                        source_url=e.get("source_url", ""),
                        date=e.get("date", ""),
                    ))
        if not evidence_objects:
            evidence_objects = provided_evidence

        # Extract strike text
        strike_text = data.get("strike", "")
        if not strike_text:
            strike_text = f"Statement by {target.name} requires further verification."

        return Strike(
            target=target,
            statement=statement,
            verdict=verdict,
            evidence=evidence_objects,
            strike=strike_text,
            report_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            agent_id="prinzclaw-agent",
            reviewed=False,
        )

    def _build_fallback_strike(self, target: Target, statement: Statement,
                                evidence: list[Evidence], raw_text: str) -> Strike:
        """Build a Strike when AI response can't be parsed as JSON."""
        return Strike(
            target=target,
            statement=statement,
            verdict="INSUFFICIENT_EVIDENCE",
            evidence=evidence,
            strike=raw_text[:500] if raw_text else "Analysis could not be completed.",
            report_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            agent_id="prinzclaw-agent",
            reviewed=False,
        )
