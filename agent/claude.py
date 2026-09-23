import json
import os
import re
from typing import Any

from anthropic import Anthropic

from .prompts import SYSTEM_PROMPT, build_final_prompt, build_initial_prompt, build_recovery_prompt


class ClaudeClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set. Add it to the .env file.")

        workspace_id = os.getenv("ANTHROPIC_WORKSPACE_ID", "").strip()
        placeholder_values = {
            "your_workspace_id_here",
            "replace_with_your_workspace_id",
            "replace_with_your_actual_api_key",
        }
        default_headers = {}
        if workspace_id and workspace_id.lower() not in {value.lower() for value in placeholder_values}:
            default_headers["anthropic-workspace-id"] = workspace_id

        self.client = Anthropic(
            api_key=self.api_key,
            default_headers=default_headers if default_headers else None,
        )

    def _extract_text(self, response: Any) -> str:
        chunks: list[str] = []
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "text":
                chunks.append(getattr(block, "text", ""))
        text = "".join(chunks).strip()
        if not text:
            raise ValueError("Claude returned an empty response.")
        return text

    def _parse_json(self, text: str) -> Any:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = cleaned[start : end + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    type_match = re.search(r'"type"\s*:\s*"([^"]+)"', candidate)
                    question_match = re.search(r'"question"\s*:\s*"((?:[^"\\]|\\.)*)"', candidate, re.DOTALL)
                    if type_match and question_match:
                        return {
                            "type": type_match.group(1),
                            "question": bytes(question_match.group(1), "utf-8").decode("unicode_escape"),
                        }
            raise ValueError(f"Claude response was not valid JSON: {text[:500]}")

    def get_actions(self, user_request: str, context: str = "") -> dict[str, Any]:
        prompt = build_initial_prompt(user_request, context)
        response = self.client.messages.create(
            model="claude-opus-5-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_json(self._extract_text(response))

    def recover(self, user_request: str, error: str, tool_result: str) -> dict[str, Any]:
        prompt = build_recovery_prompt(user_request, error, tool_result)
        response = self.client.messages.create(
            model="claude-opus-5-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return self._parse_json(self._extract_text(response))

    def explain_results(self, user_request: str, result_summary: str) -> str:
        prompt = build_final_prompt(user_request, result_summary)
        response = self.client.messages.create(
            model="claude-opus-5-5",
            max_tokens=512,
            system="You are a helpful CFD assistant. Explain the result in clear natural language.",
            messages=[{"role": "user", "content": prompt}],
        )
        return self._extract_text(response)
