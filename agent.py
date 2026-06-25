"""AI Agent Buddy — Groq-powered brain with local JSON memory."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from groq import Groq

# llama3-70b-8192 was deprecated Aug 2025; use current 70B fast model
DEFAULT_MODEL = "llama-3.3-70b-versatile"
MEMORY_PATH = Path(__file__).parent / "memory.json"
FACT_PATTERN = re.compile(r"\[FACT:\s*(.+?)\]", re.IGNORECASE)

SYSTEM_PROMPT_BASE = """You are AI Agent Buddy, a warm, helpful personal assistant.
You remember personal details about the user and use them naturally in conversation.
Be concise, friendly, and conversational.

When the user shares NEW personal information (name, preferences, pets, family, job, hobbies, etc.),
append each new fact on its own line using this exact format at the very end of your reply:
[FACT: brief factual statement about the user]

Only include [FACT: ...] tags for genuinely new personal details not already in your memory.
Do not repeat facts you already know. Do not use [FACT: ...] for general knowledge."""


class AIBuddy:
    """Cloud-local hybrid agent: Groq LLM + local JSON memory."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        memory_path: Path = MEMORY_PATH,
        max_history: int = 20,
    ) -> None:
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError(
                "GROQ_API_KEY is not set. Export it before running the app."
            )
        self.client = Groq(api_key=key)
        self.model = model
        self.memory_path = memory_path
        self.max_history = max_history
        self.chat_history: list[dict[str, str]] = []

    def load_facts(self) -> list[str]:
        """Load persisted personal facts from memory.json."""
        if not self.memory_path.exists():
            self._write_memory({"facts": []})
            return []
        try:
            data = json.loads(self.memory_path.read_text(encoding="utf-8"))
            facts = data.get("facts", [])
            return [str(f).strip() for f in facts if str(f).strip()]
        except (json.JSONDecodeError, OSError):
            return []

    def save_fact(self, fact: str) -> bool:
        """Append a personal fact to memory.json if not already stored."""
        fact = fact.strip()
        fact_clean = fact.rstrip(".?!").strip()
        if not fact_clean:
            return False

        facts = self.load_facts()
        normalized = fact_clean.lower()
        if any(existing.strip().rstrip(".?!").strip().lower() == normalized for existing in facts):
            return False

        facts.append(fact)
        self._write_memory({"facts": facts})
        return True

    def delete_fact(self, fact: str) -> bool:
        """Remove a personal fact from memory.json."""
        fact = fact.strip()
        if not fact:
            return False

        facts = self.load_facts()
        normalized = fact.lower().rstrip(".?!").strip()
        updated_facts = [
            f for f in facts 
            if f.strip().rstrip(".?!").strip().lower() != normalized
        ]

        if len(updated_facts) < len(facts):
            self._write_memory({"facts": updated_facts})
            return True
        return False

    def _write_memory(self, data: dict[str, Any]) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def build_system_prompt(self) -> str:
        """Inject stored facts into the system prompt."""
        facts = self.load_facts()
        if not facts:
            return SYSTEM_PROMPT_BASE + "\n\nKnown facts about the user: (none yet)"
        bullet_list = "\n".join(f"- {fact}" for fact in facts)
        return (
            SYSTEM_PROMPT_BASE
            + f"\n\nKnown facts about the user:\n{bullet_list}"
        )

    def _extract_and_save_facts(self, text: str) -> tuple[str, list[str]]:
        """Parse [FACT: ...] tags, persist new facts, return clean reply."""
        saved: list[str] = []
        for match in FACT_PATTERN.finditer(text):
            fact = match.group(1).strip()
            if self.save_fact(fact):
                saved.append(fact)
        clean = FACT_PATTERN.sub("", text).strip()
        return clean, saved

    def chat(self, user_message: str) -> dict[str, Any]:
        """
        Process user input: update rolling history, call Groq, auto-save new facts.
        Returns dict with reply, saved_facts, and model used.
        """
        user_message = user_message.strip()
        if not user_message:
            return {"reply": "", "saved_facts": [], "model": self.model}

        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.build_system_prompt()},
            *self.chat_history,
            {"role": "user", "content": user_message},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            raw_reply = response.choices[0].message.content or ""
            error_occurred = False
        except Exception as exc:
            raw_reply = f"⚠️ Error: I've encountered an issue communicating with my brain. Details: {str(exc)}"
            error_occurred = True

        if error_occurred:
            reply = raw_reply
            saved_facts = []
        else:
            reply, saved_facts = self._extract_and_save_facts(raw_reply)
            self.chat_history.append({"role": "user", "content": user_message})
            self.chat_history.append({"role": "assistant", "content": reply})
            if len(self.chat_history) > self.max_history * 2:
                self.chat_history = self.chat_history[-self.max_history * 2 :]

        return {
            "reply": reply,
            "saved_facts": saved_facts,
            "model": self.model,
            "error": error_occurred,
        }

    def clear_history(self) -> None:
        """Reset short-term conversational memory."""
        self.chat_history.clear()
