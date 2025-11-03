"""AI assistant integration for summarizing audit findings and suggesting fixes."""

import os
import json
from typing import Dict, Tuple, Any, List


def _build_prompt(
    all_results: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]],
    sol_files: List[str]
) -> List[Dict[str, str]]:
    """
    Build a system/user prompt for the AI summarization based on tool outputs.
    """
    system_prompt = (
        "You are a senior smart contract security auditor. "
        "Summarize the combined Slither and Solhint findings, prioritize by risk, "
        "and propose concrete, code-level remediation steps. "
        "Group results by: Critical/High, Medium, Low/Informational, and Style/Best Practices. "
        "Prefer concise, actionable guidance. Where helpful, include short Solidity snippets."
    )

    # Flatten findings into a compact textual description
    def fmt_issue(src: str, issue: Dict[str, Any]) -> str:
        return f"- [{issue.get('severity','Info')}] {issue.get('issue','')} @ {src} ({issue.get('location','')})"

    lines: List[str] = []
    for file_path, (slither_results, solhint_results) in all_results.items():
        src = os.path.basename(file_path)
        # Slither issues
        if isinstance(slither_results, dict):
            if "error" in slither_results:
                lines.append(f"Slither Error in {src}: {slither_results['error']}")
            else:
                for cat in ("vulnerabilities", "inefficiencies", "best_practices"):
                    for issue in slither_results.get(cat, []):
                        lines.append(fmt_issue(src, issue))
        # Solhint issues
        if isinstance(solhint_results, dict):
            if "error" in solhint_results:
                lines.append(f"Solhint Error in {src}: {solhint_results['error']}")
            else:
                for issue in solhint_results.get("best_practices", []):
                    lines.append(fmt_issue(src, issue))

    user_prompt = (
        "Project files: " + ", ".join(os.path.basename(p) for p in sol_files) + "\n\n" +
        "Findings (Slither + Solhint):\n" + "\n".join(lines)
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def generate_ai_summary(
    all_results: Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]],
    sol_files: List[str],
    model: str = "gpt-4o-mini",
    api_key: str = None,
) -> str:
    """
    Send Slither/Solhint results to OpenAI and return a concise markdown summary.
    Requires environment variable OPENAI_API_KEY or explicit api_key.
    """
    try:
        from openai import OpenAI
    except Exception as e:
        return (
            "AI summary unavailable: OpenAI SDK not installed. "
            "Install with: pip install openai."
        )

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        return (
            "AI summary unavailable: OPENAI_API_KEY is not set. "
            "Set it in the environment or pass --api-key."
        )

    client = OpenAI(api_key=key)
    messages = _build_prompt(all_results, sol_files)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=900,
        )
        content = completion.choices[0].message.content or ""
        return content.strip()
    except Exception as e:
        return f"AI summary failed: {str(e)}"


