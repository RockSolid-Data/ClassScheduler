def format_phone_for_display(digits) -> str:
    """Return a human-friendly phone representation from a digits-ish input.

    Rules:
    - Normalize to digits only for safety (do not preserve '+').
    - 10 digits -> (XXX) XXX-XXXX
    - 7 digits  -> XXX-XXXX
    - Other lengths -> return the digit string as-is.
    """
    s = ''.join(c for c in str(digits or '') if c.isdigit())
    if len(s) == 10:
        return f"({s[0:3]}) {s[3:6]}-{s[6:10]}"
    if len(s) == 7:
        return f"{s[0:3]}-{s[3:7]}"
    return s
