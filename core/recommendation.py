"""Service recommendation engine."""

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "welfare_services.json")


def load_knowledge_base() -> dict:
    """Load the welfare services JSON knowledge base."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_services_for_categories(categories: list[str]) -> list[dict]:
    """Retrieve services matching the detected issue categories."""
    kb = load_knowledge_base()
    services = []
    seen_names = set()

    for category in categories:
        category_services = kb.get("services", {}).get(category, [])
        for service in category_services:
            if service["name"] not in seen_names:
                services.append({**service, "category": category})
                seen_names.add(service["name"])
    return services


def get_crisis_resources() -> list[dict]:
    """Retrieve crisis/emergency resources."""
    kb = load_knowledge_base()
    return kb.get("crisis_resources", [])


def get_external_resources(categories: list[str]) -> dict:
    """Retrieve relevant external resources (job boards, housing platforms)."""
    kb = load_knowledge_base()
    external = kb.get("external_resources", {})
    result = {}

    for category in categories:
        if category == "financial" and "finance" in external:
            result["job_platforms"] = external["finance"].get("job_platforms", [])
        if category == "housing" and "housing" in external:
            result["housing_platforms"] = external["housing"].get("platforms", [])
    return result


def format_services_context(services: list[dict]) -> str:
    """Format services into a readable context string for the LLM."""
    if not services:
        return "No specific services found for this concern."

    lines = []
    for s in services:
        lines.append(f"- **{s['name']}**: {s['description']}")
        if s.get("contact"):
            lines.append(f"  Contact: {s['contact']}")
        if s.get("phone"):
            lines.append(f"  Phone: {s['phone']}")
        if s.get("location"):
            lines.append(f"  Location: {s['location']}")
        if s.get("hours"):
            lines.append(f"  Hours: {s['hours']}")
        if s.get("booking"):
            lines.append(f"  Booking: {s['booking']}")
        lines.append("")
    return "\n".join(lines)


def format_crisis_context(resources: list[dict]) -> str:
    """Format crisis resources into a readable context string."""
    lines = ["**URGENT SUPPORT RESOURCES:**", ""]
    for r in resources:
        lines.append(f"- **{r['name']}**: {r['description']}")
        lines.append(f"  Phone/Contact: {r['phone']} ({r['available']})")
        lines.append("")
    return "\n".join(lines)


def format_external_context(resources: dict) -> str:
    """Format external resources into a readable context string."""
    if not resources:
        return ""
    lines = ["**Additional External Resources:**", ""]
    for key, items in resources.items():
        for item in items:
            lines.append(f"- **{item['name']}**: {item['description']}")
        lines.append("")
    return "\n".join(lines)
