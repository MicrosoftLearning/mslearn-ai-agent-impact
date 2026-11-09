"""Independent, fail-closed policy used by the compliance checkpoint."""

from datetime import date


def qualification_issue(cmo: dict, required_through: date) -> str | None:
    if cmo.get("qualification_status") != "Approved":
        return "Qualification status is not Approved"
    raw = cmo.get("qualification_expiry")
    if not isinstance(raw, str) or not raw:
        return "Qualification expiry is missing"
    try:
        expiry = date.fromisoformat(raw)
    except ValueError:
        return "Qualification expiry is invalid"
    if expiry.isoformat() != raw:
        return "Qualification expiry must use YYYY-MM-DD"
    if expiry < required_through:
        return "Qualification expires before the end of the launch window"
    return None
