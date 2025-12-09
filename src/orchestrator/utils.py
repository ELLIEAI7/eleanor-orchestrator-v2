from typing import Optional

try:
    import pynvml
except ImportError:
    pynvml = None

UNCERTAINTY_TERMS = {
    "uncertain", "not sure", "unknown", "unclear", "ambiguous",
    "may", "might", "could", "possibly", "perhaps"
}

LOW_CONFIDENCE_MARKERS = {
    "not confident", "low confidence", "guess", "speculative", "estimate"
}

def confidence_from_logprobs(logprobs) -> float:
    """
    Convert a list of logprobs (natural log) to a rough confidence score.
    Uses mean logprob exponentiated, clipped to [0,1].
    """
    import math
    if not logprobs:
        return 0.0
    try:
        mean_lp = sum(logprobs) / len(logprobs)
        prob = math.exp(mean_lp)
        return max(0.0, min(0.99, prob))
    except Exception:
        return 0.0


def normalize_text(t: str) -> str:
    return t.strip()


def gpu_utilization() -> Optional[int]:
    """
    Return GPU utilization percent if NVML is available; otherwise None.
    """
    if not pynvml:
        return None
    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        return int(util.gpu)
        except Exception:
            return None
    finally:
        try:
            pynvml.nvmlShutdown()
        except Exception:
            pass


def heuristic_confidence_from_text(text: str, base: float = 0.1) -> float:
    """
    Rough heuristic for confidence when logprobs are unavailable:
    - Penalize uncertainty terms.
    - Reward longer, coherent text modestly.
    - Penalize explicit low-confidence markers.
    """
    lowered = text.lower()
    penalty = sum(1 for term in UNCERTAINTY_TERMS if term in lowered) * 0.05
    penalty += sum(1 for term in LOW_CONFIDENCE_MARKERS if term in lowered) * 0.07
    length_bonus = min(len(text) / 500.0 * 0.1, 0.15)
    conf = max(0.0, min(0.9, base + length_bonus - penalty))
    return conf


# UNESCO/UDHR-aligned helper sets for rapid heuristic checks
PROTECTED_CLASSES = {
    "race", "ethnicity", "gender", "sex", "sexual orientation", "religion", "faith",
    "disability", "age", "nationality", "origin", "immigration", "pregnancy", "veteran"
}

SENSITIVE_TOPICS = {
    "health", "biometric", "genetic", "financial", "political", "union", "religious"
}

# Body size limits (could also be enforced at proxy)
MAX_INPUT_CHARS = int(os.getenv("ELEANOR_MAX_INPUT", "8000"))
