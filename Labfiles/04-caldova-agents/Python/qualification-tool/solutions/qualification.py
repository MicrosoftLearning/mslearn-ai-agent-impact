"""Instructor replacement: reuse the independently tested policy."""

from datetime import date

from policy import qualification_issue as check_qualification


def qualification_issue(cmo: dict, required_through: date) -> str | None:
    return check_qualification(cmo, required_through)
