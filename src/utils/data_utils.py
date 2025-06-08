"""Data processing utilities."""

import base64
from typing import List

from .text_utils import fix_base64_padding


def decode_base64_list(b64_list: List[str]) -> List[bytes]:
    """Decode a list of base64-encoded strings (with padding fixes).
    
    Args:
        b64_list: List of base64-encoded strings
        
    Returns:
        List of decoded byte strings (skips invalid entries)
    """
    decoded = []
    for b64 in b64_list:
        try:
            fixed = fix_base64_padding(b64)
            decoded.append(base64.b64decode(fixed))
        except Exception:
            # Skip invalid base64 strings
            continue
    return decoded