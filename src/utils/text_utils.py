"""Text processing utilities."""

import base64
import re


def clean_text_output(text: str) -> str:
    """Remove markdown formatting and code blocks from any text output."""
    # Remove markdown code block formatting
    if "```" in text:
        lines = text.split("\n")
        clean_lines = []
        in_code_block = False
        
        for line in lines:
            # Skip lines that only contain backticks or language identifiers
            if line.strip().startswith("```") and (len(line.strip()) <= 10):
                in_code_block = not in_code_block
                continue
            clean_lines.append(line)
        
        text = "\n".join(clean_lines)
    
    # Remove surrounding backticks
    text = text.strip()
    if text.startswith("`") and text.endswith("`"):
        text = text[1:-1]
    
    # Clean up each line (strip trailing/leading whitespace)
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    
    return "\n".join(cleaned_lines)


def fix_base64_padding(b64_string: str) -> str:
    """Add padding to base64 string if needed."""
    # First clean any markdown formatting
    b64_string = clean_text_output(b64_string)
    
    # Remove any whitespace, newlines, or quotes that might be present
    b64_string = b64_string.strip().replace('\n', '').replace('\r', '').replace('"', '').replace("'", '')
    
    # Remove any non-base64 characters
    b64_string = re.sub(r'[^A-Za-z0-9+/=]', '', b64_string)
    
    # Add padding if needed
    missing_padding = len(b64_string) % 4
    if missing_padding:
        b64_string += '=' * (4 - missing_padding)
    
    return b64_string