import asyncio
import time
from typing import Dict
import uuid
import hashlib

from .config import settings
from .adapters import CriticAdapter
from .critics import parse_critic_output
from .schemas import DeliberationEvent, ConflictEvent, FinalDecision, CriticBreakdown
from .streaming import emit
from .precedent import store_precedent
from .utils import heuristic_confidence_from_text, confidence_from_logprobs, PROTECTED_CLASSES, SENSITIVE_TOPICS
from .logging_setup import configure_logging

CRITICS = ["rights", "fairness", "risk", "truth", "pragmatics"]


def _conflict_checks(critic: str, parsed: Dict[str, str]) -> ConflictEvent | None:
    principle = (parsed.get("constitutional_principle", "none") or "none").lower()
    confidence = parsed.get("confidence", 0.0) or 0.0
    claim = parsed.get("claim", "").lower()

    thr = settings.THRESHOLDS
    tags_local: list[str] = []

    if critic == "rights" and principle != "none" and confidence > thr["rights"]:
        tags_local.append("udhr")
        return ConflictEvent(critic="rights", severity="high", message="Potential rights violation detected (UDHR).")
    if critic == "rights":
        if any(term in claim for term in PROTECTED_CLASSES):
            tags_local.append("protected_class")
            return ConflictEvent(critic="rights", severity="high", message="Protected class detected; check non-discrimination (UDHR/UNESCO).")
        if "consent" not in claim and "consent" not in parsed.get("evidence", "").lower():
            tags_local.append("consent")
            return ConflictEvent(critic="rights", severity="medium", message="Consent not evident; verify autonomy (UDHR Art. 1,12).")
    if critic == "risk" and (principle != "none" or "harm" in claim) and confidence > thr["risk"]:
        return ConflictEvent(critic="risk", severity="medium", message="Potential high-risk action detected.")
    if critic == "fairness" and principle != "none" and confidence > thr["fairness"]:
        return ConflictEvent(critic="fairness", severity="medium", message="Potential distributional harm detected.")
    if critic == "truth" and principle != "none" and confidence > thr["truth"]:
        return ConflictEvent(critic="truth", severity="low", message="Potential misinformation detected.")
    if critic == "pragmatics" and confidence < thr["pragmatics"]:
        return ConflictEvent(critic="pragmatics", severity="low", message="Feasibility uncertain; clarify constraints.")
    return None


async def run_critic_stream(ws, critic: str, adapter: CriticAdapter, user_input: str, results: dict):
    """
    Stream a single critic:
    - announce start
    - stream partial tokens (if available)
    - fallback to full completion on failure
    - emit conflicts
    - emit completion event
    """
    model = settings.MODELS[critic]
    system_prompt = settings.SYSTEM_PROMPTS[critic]

    # Signal start
    await emit(ws, DeliberationEvent(critic=critic, message=f"{critic} critic starting", confidence=0.05).dict())

    collected_text = ""
    try:
        async for chunk in adapter.stream(model, system_prompt, user_input):
            if not chunk:
                continue
            # support dict payloads that include logprobs
            if isinstance(chunk, dict):
                content = chunk.get("content", "")
                logprobs = chunk.get("logprobs")
            else:
                content = chunk
                logprobs = None

            if not content:
                continue

            collected_text += content
            token_conf = confidence_from_logprobs(logprobs) if logprobs else heuristic_confidence_from_text(collected_text, base=0.12)
            await emit(
                ws,
                DeliberationEvent(
                    critic=critic,
                    message=content,
                    confidence=token_conf,
                ).dict(),
            )
    except Exception as exc:
        # fallback to non-streaming
        await emit(
            ws,
            ConflictEvent(
                critic=critic,
                severity="low",
                message=f"{critic} critic stream failed, falling back to completion: {exc}",
            ).dict(),
        )
        resp = await adapter.complete(model, system_prompt, user_input)
        content = resp.get("message", {}).get("content", "") if isinstance(resp, dict) else ""
        collected_text += content

    parsed = parse_critic_output(collected_text)
    results[critic] = parsed

    conflict = _conflict_checks(critic, parsed)
    if conflict:
        await emit(ws, conflict.dict())

    # Final critic completion event
    await emit(ws, DeliberationEvent(
        critic=critic,
        message=f"{critic} critic complete",
        confidence=parsed.get("confidence", 0.0),
    ).dict())


logger = configure_logging()


async def orchestrate(ws, user_input: str, adapter: CriticAdapter):
    results: Dict[str, Dict] = {}
    conflicts: list[str] = []
    audit_id = f"AUD-{uuid.uuid4()}"
    audit_hash = hashlib.sha256(user_input.encode("utf-8")).hexdigest()

    async with asyncio.TaskGroup() as tg:
        for critic in CRITICS:
            tg.create_task(run_critic_stream(ws, critic, adapter, user_input, results))

    final = compute_final_decision(results, conflicts)
    final.auditId = audit_id
    final.auditHash = audit_hash
    # Persist precedent
    case_id = store_precedent({
        "input": user_input,
        "outcome": final.outcome,
        "confidence": final.confidence,
        "mitigations": final.mitigations,
        "critics": results,
        "precedentId": final.precedentId,
        "timestamp": int(time.time()),
        "flags": final.flags,
        "tags": _build_tags(results, final),
        "severity": final.severity,
        "auditId": audit_id,
        "auditHash": audit_hash,
    })
    final.precedentId = case_id

    logger.info({"event": "deliberation_complete", "auditId": audit_id, "precedentId": case_id, "outcome": final.outcome, "flags": final.flags})
    await emit(ws, final.dict())
    return final


def _build_tags(results: Dict[str, Dict], final: FinalDecision) -> list[str]:
    tags: list[str] = []
    for critic, vals in results.items():
        principle = (vals.get("constitutional_principle", "none") or "none").lower()
        if principle != "none":
            tags.append(f"{critic}:principle")
        if vals.get("mitigation"):
            tags.append(f"{critic}:mitigation")
    tags.append(f"outcome:{final.outcome}")
    return tags


def compute_final_decision(results: Dict[str, Dict], conflicts: list[str]) -> FinalDecision:
    # Simple aggregation; rights/risk/fairness take precedence
    outcome = "allowed_with_mitigations"
    mitigations: list[str] = []

    thr = settings.THRESHOLDS
    lib = settings.MITIGATION_LIBRARY

    rights = results.get("rights", {})
    risk = results.get("risk", {})
    fairness = results.get("fairness", {})
    truth = results.get("truth", {})
    prag = results.get("pragmatics", {})

    if rights.get("constitutional_principle", "none").lower() != "none" and rights.get("confidence", 0) > thr["rights"]:
        outcome = "blocked"
        mitigations.append(lib["rights"]["conflict"])
        conflicts.append("rights")
    elif risk.get("constitutional_principle", "none").lower() != "none" and risk.get("confidence", 0) > thr["risk"]:
        outcome = "blocked"
        mitigations.append(lib["risk"]["conflict"])
        conflicts.append("risk")
    elif fairness.get("constitutional_principle", "none").lower() != "none" and fairness.get("confidence", 0) > thr["fairness"]:
        outcome = "allowed_with_mitigations"
        mitigations.append(lib["fairness"]["conflict"])
        conflicts.append("fairness")
    elif truth.get("constitutional_principle", "none").lower() != "none" and truth.get("confidence", 0) > thr["truth"]:
        outcome = "allowed_with_mitigations"
        mitigations.append(lib["truth"]["conflict"])
        conflicts.append("truth")
    elif prag.get("confidence", 1) < thr["pragmatics"]:
        outcome = "needs_clarification"
        mitigations.append(lib["pragmatics"]["conflict"])
        conflicts.append("pragmatics")

    critic_breakdown = {
        name: CriticBreakdown(
            summary=vals.get("claim", ""),
            details=[vals.get("evidence", ""), vals.get("constitutional_principle", ""), vals.get("mitigation", "")],
            confidence=vals.get("confidence", 0.0),
        )
        for name, vals in results.items()
    }

    confidence = sum(v.get("confidence", 0) for v in results.values()) / max(len(results), 1)

    severity = "medium"
    if outcome == "blocked":
        severity = "high"
    elif outcome in ("needs_clarification", "allowed_with_mitigations"):
        severity = "medium"
    else:
        severity = "low"

    return FinalDecision(
        outcome=outcome,
        confidence=confidence,
        mitigations=mitigations,
        criticBreakdown=critic_breakdown,
        precedentId=f"EC-{int(time.time())}",
        flags=list(conflicts),
        severity=severity,
    )
