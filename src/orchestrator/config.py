import os
from typing import Dict
from .adapters import OllamaAdapter, CriticAdapter


class Settings:
    def __init__(self):
        self.OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        # Critic model names
        self.MODELS = {
            "rights": os.getenv("RIGHTS_MODEL_NAME", "eleanor-rights"),
            "fairness": os.getenv("FAIRNESS_MODEL_NAME", "eleanor-fairness"),
            "risk": os.getenv("RISK_MODEL_NAME", "eleanor-risk"),
            "truth": os.getenv("TRUTH_MODEL_NAME", "eleanor-truth"),
            "pragmatics": os.getenv("PRAGMATICS_MODEL_NAME", "eleanor-pragmatics"),
        }
        # Domain-specific safety thresholds and mitigation templates
        self.THRESHOLDS = {
            "rights": float(os.getenv("RIGHTS_THRESHOLD", 0.50)),
            "risk": float(os.getenv("RISK_THRESHOLD", 0.60)),
            "fairness": float(os.getenv("FAIRNESS_THRESHOLD", 0.60)),
            "truth": float(os.getenv("TRUTH_THRESHOLD", 0.70)),
            "pragmatics": float(os.getenv("PRAG_THRESHOLD", 0.40)),
        }
        self.MITIGATION_LIBRARY = self._default_mitigations()
        self.SYSTEM_PROMPTS = self._default_prompts()
        self._apply_overlays()
        self._apply_profile()

    def _default_prompts(self) -> Dict[str, str]:
        return {
            "rights": (
                "You are the Eleanor Rights Critic. Evaluate dignity, autonomy, non-discrimination, and privacy "
                "grounded in the UDHR (esp. Arts. 1,2,3,7,12,18,19,23) and the UNESCO 2022 AI Recommendation. "
                "Respond ONLY in the format:\n\n"
                "Rights Critic Assessment:\n"
                "- Claim: ...\n"
                "- Evidence: ...\n"
                "- Constitutional Principle: ...\n"
                "- Confidence: <0.0–1.0>\n"
                "- Mitigation: ...\n"
            ),
            "fairness": (
                "You are the Eleanor Fairness Critic. Evaluate distributional fairness and subgroup impacts "
                "referencing UDHR Articles 2 and 7 and UNESCO 2022 guidance on non-discrimination and inclusiveness. "
                "Respond ONLY in the format:\n\n"
                "Fairness Critic Assessment:\n"
                "- Claim: ...\n"
                "- Evidence: ...\n"
                "- Constitutional Principle: ...\n"
                "- Confidence: <0.0–1.0>\n"
                "- Mitigation: ...\n"
            ),
            "risk": (
                "You are the Eleanor Risk Critic. Evaluate harm likelihood, severity, reversibility, and precaution "
                "aligned with UNESCO 2022 Safety & Security and Precautionary Principle guidance. "
                "Respond ONLY in the format:\n\n"
                "Risk Critic Assessment:\n"
                "- Claim: ...\n"
                "- Evidence: ...\n"
                "- Constitutional Principle: ...\n"
                "- Confidence: <0.0–1.0>\n"
                "- Mitigation: ...\n"
            ),
            "truth": (
                "You are the Eleanor Truth Critic. Evaluate factual accuracy, deception risk, omission, and completeness "
                "aligned with UDHR Art. 19 (freedom to seek/receive information) and UNESCO transparency/explainability. "
                "Respond ONLY in the format:\n\n"
                "Truth Critic Assessment:\n"
                "- Claim: ...\n"
                "- Evidence: ...\n"
                "- Constitutional Principle: ...\n"
                "- Confidence: <0.0–1.0>\n"
                "- Mitigation: ...\n"
            ),
            "pragmatics": (
                "You are the Eleanor Pragmatics Critic. Evaluate feasibility, cost, proportionality, and operational constraints "
                "with attention to sustainability and proportionality principles in the UNESCO 2022 recommendation. "
                "Respond ONLY in the format:\n\n"
                "Pragmatics Critic Assessment:\n"
                "- Claim: ...\n"
                "- Evidence: ...\n"
                "- Constitutional Principle: ...\n"
                "- Confidence: <0.0–1.0>\n"
                "- Mitigation: ...\n"
            ),
        }

    def _default_mitigations(self) -> Dict[str, Dict[str, str]]:
        return {
            "rights": {
                "conflict": "Resolve rights constraint (dignity, autonomy, non-discrimination per UDHR) before proceeding.",
                "default": "Document informed consent; ensure protected classes (race, gender, religion, age, disability, nationality) are not impacted.",
            },
            "risk": {
                "conflict": "Redesign for reversibility and reduce harm likelihood; add human-in-the-loop where possible (UNESCO precaution).",
                "default": "Add monitoring and safe rollback; test for edge cases and failure modes before deployment.",
            },
            "fairness": {
                "conflict": "Address distributional harm; add subgroup checks and fairness constraints (UDHR Arts. 2 & 7).",
                "default": "Audit for bias; ensure similarly situated groups receive equal treatment; document fairness tests.",
            },
            "truth": {
                "conflict": "Provide citations, verify claims, and correct inaccuracies (UDHR Art. 19, UNESCO transparency).",
                "default": "Include sources and ensure completeness; avoid omissions that mislead.",
            },
            "pragmatics": {
                "conflict": "Clarify feasibility, resources, sustainability, and operational constraints before proceeding.",
                "default": "Provide clear implementation steps, cost/latency constraints, and sustainability considerations.",
            },
        }

    def _apply_overlays(self):
        """
        Optional institutional overlays via JSON:
        export ELEANOR_OVERLAY_FILE=/path/to/overlay.json
        {
          "thresholds": { "rights": 0.55, "risk": 0.65 },
          "mitigations": { "rights": { "conflict": "...custom..." } }
        }
        """
        import json
        overlay_path = os.getenv("ELEANOR_OVERLAY_FILE")
        if not overlay_path or not os.path.exists(overlay_path):
            return
        try:
            with open(overlay_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "thresholds" in data and isinstance(data["thresholds"], dict):
                for k, v in data["thresholds"].items():
                    if k in self.THRESHOLDS:
                        try:
                            self.THRESHOLDS[k] = float(v)
                        except Exception:
                            pass
            if "mitigations" in data and isinstance(data["mitigations"], dict):
                for critic, entries in data["mitigations"].items():
                    if critic in self.MITIGATION_LIBRARY and isinstance(entries, dict):
                        self.MITIGATION_LIBRARY[critic].update(entries)
        except Exception:
            # Fail silently to preserve runtime availability.
            return

    def _apply_profile(self):
        """
        Optional compliance profile presets:
        - ELEANOR_PROFILE=euai : tighter thresholds for rights/fairness/risk/truth, higher pragmatics caution
        - ELEANOR_PROFILE=nist-high : tuned for high-risk classification (more sensitivity)
        """
        profile = os.getenv("ELEANOR_PROFILE", "").lower()
        if profile == "euai":
            self.THRESHOLDS.update({
                "rights": 0.40,
                "fairness": 0.50,
                "risk": 0.50,
                "truth": 0.60,
                "pragmatics": 0.50,
            })
        elif profile == "nist-high":
            self.THRESHOLDS.update({
                "rights": 0.45,
                "fairness": 0.55,
                "risk": 0.55,
                "truth": 0.65,
                "pragmatics": 0.45,
            })

    def build_adapter(self) -> CriticAdapter:
        # Currently only Ollama, but this adapter hook keeps portability.
        return OllamaAdapter(self.OLLAMA_HOST)


settings = Settings()
