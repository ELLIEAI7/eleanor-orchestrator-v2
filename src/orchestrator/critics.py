import re
from typing import Dict


def parse_critic_output(text: str) -> Dict[str, str]:
    """Parse Eleanor critic structured output into a dict."""
    def extract(label: str, default: str = "") -> str:
        pattern = rf"- {label}:\s*(.*)"
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m else default

    claim = extract("Claim")
    evidence = extract("Evidence")
    principle = extract("Constitutional Principle") or extract("Principle") or "None"
    confidence_raw = extract("Confidence", "0.0")
    mitigation = extract("Mitigation")

    try:
        confidence = float(re.findall(r"[\d.]+", confidence_raw)[0])
    except Exception:
        confidence = 0.0

    return {
        "claim": claim,
        "evidence": evidence,
        "constitutional_principle": principle,
        "confidence": confidence,
        "mitigation": mitigation,
    }
