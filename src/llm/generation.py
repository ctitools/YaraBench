"""Synthetic challenge generation for Level 2."""

import base64
import json
import random
from typing import List, Optional, Dict, Any

from ..models import Challenge, TestFile, ChallengeLevel
from ..utils import SeedGenerator


class SyntheticChallengeGenerator:
    """Generate synthetic YARA rule challenges using LLM.
    
    Creates Level 2 challenges that follow the same structure as Level 1
    but with LLM-generated content variations.
    """
    
    def __init__(self, llm_client):
        """Initialize the synthetic generator.
        
        Args:
            llm_client: LLM client for generation
        """
        self.llm_client = llm_client
        self.seed_generator = SeedGenerator()
        
        # Challenge templates that combine seed-based behavior with structured output
        self.challenge_templates = [
            {
                "type": "behavior_based",
                "prompt_template": """Based on this malware behavior: "{seed}"

Generate a YARA challenge with specific technical indicators. Respond with JSON only:
{{
  "description": "Challenge description mentioning specific strings, file paths, or network indicators",
  "primary_string": "main detection string (like domain, filename, or distinctive text)",
  "secondary_string": "supporting string for detection",
  "file_indicator": "file-related indicator (extension, path, or name)",
  "expected_keywords": ["yara", "keywords", "like", "pe", "filesize"]
}}

Make it realistic and specific enough for a YARA rule.""",
                "expected_keywords": []
            },
            {
                "type": "network_based",
                "prompt_template": """Based on this malware behavior: "{seed}"

Create a network-focused YARA challenge. Respond with JSON only:
{{
  "description": "Challenge description for network communication detection",
  "domain": "C2 domain name",
  "port": "port number",
  "protocol_string": "protocol-specific string or header",
  "mutex_name": "mutex or sync object name",
  "expected_keywords": []
}}

Focus on network communications and related artifacts.""",
                "expected_keywords": []
            },
            {
                "type": "file_system",
                "prompt_template": """Based on this malware behavior: "{seed}"

Create a file system focused YARA challenge. Respond with JSON only:
{{
  "description": "Challenge description for file system artifacts",
  "file_path": "specific file path or location",
  "file_extension": "file extension",
  "marker_string": "distinctive string in the file",
  "registry_key": "registry key if applicable",
  "expected_keywords": []
}}

Focus on file drops, modifications, and persistence mechanisms.""",
                "expected_keywords": []
            },
            {
                "type": "pe_analysis", 
                "prompt_template": """Based on this malware behavior: "{seed}"

Create a PE analysis YARA challenge that focuses on string-based detection. Respond with JSON only:
{{
  "description": "Challenge description for PE file analysis using string detection (avoid mentioning modules)",
  "packer": "packer or obfuscation method",
  "import_function": "suspicious import function",
  "section_name": "distinctive section name",
  "version_info": "version information string",
  "expected_keywords": []
}}

Focus on string-based detection rather than module-based analysis.""",
                "expected_keywords": []
            }
        ]
    
    def generate_challenges(self, count: int = 10) -> List[Challenge]:
        """Generate a list of synthetic challenges.
        
        Args:
            count: Number of challenges to generate
            
        Returns:
            List of generated challenges
        """
        challenges = []
        
        for i in range(count):
            try:
                challenge = self._generate_single_challenge(f"l2_synthetic_{i+1:03d}")
                if challenge:
                    challenges.append(challenge)
            except Exception as e:
                print(f"Failed to generate challenge {i+1}: {e}")
                continue
        
        return challenges
    
    def _generate_single_challenge(self, challenge_id: str) -> Optional[Challenge]:
        """Generate a single synthetic challenge.
        
        Args:
            challenge_id: Unique identifier for the challenge
            
        Returns:
            Generated challenge or None if failed
        """
        # Generate malware behavior seed (2-4 behaviors)
        seed = self.seed_generator.generate(random.randint(2, 4))
        
        # Select random template
        template = random.choice(self.challenge_templates)
        challenge_type = template["type"]
        
        # Generate challenge using LLM with seed + template
        try:
            challenge_data = self._generate_challenge_with_seed(seed, template)
            if not challenge_data:
                return None
                
            # Extract data from LLM response
            description = challenge_data.get("description", "")
            if not description:
                return None
                
            # Build expected strings from all values (excluding keywords and description)
            expected_strings = []
            expected_keywords = challenge_data.get("expected_keywords", template["expected_keywords"].copy())
            
            for key, value in challenge_data.items():
                if key not in ["description", "expected_keywords"] and isinstance(value, str):
                    expected_strings.append(value)
            
            # Generate sophisticated test files
            test_files = self._generate_sophisticated_test_files(challenge_type, challenge_data, seed)
            
            # All template-based challenges are actionable
            actionable = True
            
            return Challenge(
                id=challenge_id,
                level=ChallengeLevel.LEVEL2,
                actionable=actionable,
                description=description,
                expected_strings=expected_strings,
                expected_keywords=expected_keywords,
                test_files=test_files,
                metadata={
                    "seed": seed,
                    "template": challenge_type,
                    "generated": "true",
                    "type": "synthetic"
                }
            )
            
        except Exception as e:
            print(f"Failed to generate {challenge_type} challenge: {e}")
            return None
    
    def _generate_challenge_with_seed(self, seed: str, template: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate challenge data using seed and template.
        
        Args:
            seed: Malware behavior seed
            template: Challenge template with prompt
            
        Returns:
            Dictionary of challenge data or None if failed
        """
        prompt = template["prompt_template"].format(seed=seed)
        
        try:
            response = self.llm_client.generate_rule_description(prompt).strip()
            # Clean response and parse JSON
            clean_response = response.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_response)
        except Exception as e:
            print(f"Failed to generate challenge with seed: {e}")
            return None
    
    def _generate_sophisticated_test_files(self, challenge_type: str, challenge_data: Dict[str, Any], seed: str) -> List[TestFile]:
        """Generate sophisticated test files that incorporate the challenge indicators.
        
        Args:
            challenge_type: Type of challenge
            challenge_data: LLM-generated challenge data
            seed: Original malware behavior seed
            
        Returns:
            List of test files
        """
        test_files = []
        
        # Create sophisticated matching file based on challenge type
        if challenge_type == "behavior_based":
            # Combine multiple indicators in a realistic way
            indicators = [v for k, v in challenge_data.items() 
                         if k not in ["description", "expected_keywords"] and isinstance(v, str)]
            
            matching_content = f"Malware sample: {' | '.join(indicators[:2])} | Behavior: {seed.split(';')[0]}"
            test_files.append(TestFile(
                name="malware_sample.bin",
                content_b64=base64.b64encode(matching_content.encode()).decode(),
                should_match=True
            ))
            
        elif challenge_type == "network_based":
            # Network communication simulation
            domain = challenge_data.get("domain", "unknown.com")
            port = challenge_data.get("port", "80")
            protocol_string = challenge_data.get("protocol_string", "HTTP")
            mutex = challenge_data.get("mutex_name", "MutexDefault")
            
            network_content = f"Connecting to {domain}:{port} | Protocol: {protocol_string} | Mutex: {mutex} | {seed.split(';')[0]}"
            test_files.append(TestFile(
                name="network_comm.exe",
                content_b64=base64.b64encode(network_content.encode()).decode(), 
                should_match=True
            ))
            
        elif challenge_type == "file_system":
            # File system operation simulation
            file_path = challenge_data.get("file_path", "/tmp/unknown")
            extension = challenge_data.get("file_extension", ".tmp")
            marker = challenge_data.get("marker_string", "MARKER")
            reg_key = challenge_data.get("registry_key", "")
            
            fs_content = f"Dropping to: {file_path} | Extension: {extension} | Marker: {marker}"
            if reg_key:
                fs_content += f" | Registry: {reg_key}"
            fs_content += f" | Source: {seed.split(';')[0]}"
            
            test_files.append(TestFile(
                name="file_dropper.dll",
                content_b64=base64.b64encode(fs_content.encode()).decode(),
                should_match=True
            ))
            
        elif challenge_type == "pe_analysis":
            # PE file simulation
            packer = challenge_data.get("packer", "Unknown")
            import_func = challenge_data.get("import_function", "LoadLibrary")
            section = challenge_data.get("section_name", ".text")
            version = challenge_data.get("version_info", "1.0")
            
            pe_content = f"PE File | Packer: {packer} | Import: {import_func} | Section: {section} | Version: {version} | {seed.split(';')[0]}"
            test_files.append(TestFile(
                name="pe_sample.exe",
                content_b64=base64.b64encode(pe_content.encode()).decode(),
                should_match=True
            ))
        
        # Generate a sophisticated non-matching file that shares some structure but lacks key indicators
        non_matching_content = f"Legitimate software | Random data {random.randint(10000, 99999)} | Normal operation"
        test_files.append(TestFile(
            name="legitimate.exe",
            content_b64=base64.b64encode(non_matching_content.encode()).decode(),
            should_match=False
        ))
        
        # Add a second non-matching file with partial indicators (edge case)
        partial_indicators = list(challenge_data.values())[:1] if challenge_data.values() else ["benign"]
        partial_content = f"Partial match test: {partial_indicators[0] if partial_indicators else 'benign'} but missing other indicators {random.randint(1000, 9999)}"
        test_files.append(TestFile(
            name="partial_match.bin",
            content_b64=base64.b64encode(partial_content.encode()).decode(),
            should_match=False
        ))
        
        return test_files