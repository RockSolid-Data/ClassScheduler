from typing import List


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

def array_to_mask(flags: List[int]) -> int:
    mask = 0
    for idx, flag in enumerate(flags):  # Mon..Sun
        if flag:
            mask |= (1 << idx)
    return mask

def mask_to_array(mask: int) -> List[int]:
    return [1 if (mask & (1 << idx)) else 0 for idx in range(7)]

def is_allowed(weekday, mask):
    return bool(mask & (1 << weekday))
