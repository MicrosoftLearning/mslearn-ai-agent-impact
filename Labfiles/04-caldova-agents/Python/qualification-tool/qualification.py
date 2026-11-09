"""Training fault: the sourcing filter ignores qualification expiry.

Do not deploy this starter implementation outside an isolated lab.
"""

from datetime import date


def qualification_issue(cmo: dict, required_through: date) -> str | None:
    if cmo.get("qualification_status") != "Approved":
        return "Qualification status is not Approved"
    # Check qualification expiry
    return None
