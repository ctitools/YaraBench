"""Seed generation for synthetic challenges."""

import random
from typing import List, Optional


class SeedGenerator:
    """Creates a high-level seed description by combining predefined sentence pieces."""
    
    def __init__(self, pieces: Optional[List[str]] = None):
        """Initialize with custom or default seed pieces.
        
        Args:
            pieces: List of malware behavior descriptions
        """
        self.pieces = pieces or [
            "injects malicious code into system processes",
            "communicates with a C2 server via HTTP",
            "encrypts user documents with AES-256",
            "modifies registry keys for persistence",
            "spawns hidden background threads",
            "captures screenshots periodically",
            "uses a custom encryption algorithm",
            "modifies system files to hide its presence",
            "creates mutex objects for synchronization",
            "drops additional payloads to temp directory",
            "establishes reverse shell connections",
            "hooks API calls for stealth operations",
            "compresses stolen data before exfiltration",
            "uses domain generation algorithms for C2",
            "patches system binaries in memory",
            "creates scheduled tasks for persistence"
        ]

    def generate(self, count: int = 3) -> str:
        """Generate a seed description by combining random pieces.
        
        Args:
            count: Number of behaviors to combine
            
        Returns:
            Formatted seed description
        """
        selected = random.sample(self.pieces, min(count, len(self.pieces)))
        return "; ".join(selected) + "."