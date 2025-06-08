"""Extract YARA rules from LLM responses."""

import re
from typing import List, Optional, Tuple


class YaraExtractor:
    """Extract YARA rules from LLM-generated text."""
    
    # Patterns for finding YARA rules in code blocks
    CODE_BLOCK_PATTERNS = [
        r'```yara\s*\n(.*?)```',
        r'```\s*\n(.*?)```',
        r'```yaml\s*\n(.*?)```',  # Common typo
        r'```YARA\s*\n(.*?)```',
        r'```rule\s*\n(.*?)```',  # Sometimes they start with rule
    ]
    
    # More robust patterns for finding complete YARA rules
    YARA_RULE_PATTERNS = [
        # Rule with imports (using manual brace counting)
        r'((?:import\s+"[^"]+"\s*\n)*\s*rule\s+\w+\s*\{.*?\}\s*$)',
        
        # Standard rule with balanced braces (most robust)
        r'(rule\s+\w+\s*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\})',
        
        # Rule with meta, strings, and condition sections (allow nested braces)
        r'(rule\s+\w+\s*\{.*?(?:meta:|strings:|condition:).*?\}\s*$)',
        
        # Fallback: any rule structure with basic components
        r'(rule\s+\w+[^{]*\{.*?condition:.*?\}\s*$)',
    ]
    
    # Pattern for detecting valid YARA rule structure
    VALID_RULE_STRUCTURE = re.compile(
        r'(?:(?:import\s+"[^"]+"\s*\n)*\s*)?rule\s+\w+\s*\{.*?condition:\s*.*?\}',
        re.DOTALL | re.IGNORECASE
    )
    
    # Indicators that no rule is needed
    NO_RULE_INDICATORS = [
        "not actionable",
        "cannot be detected",
        "no yara rule",
        "not possible",
        "cannot create",
        "not suitable",
        "beyond yara",
        "beyond the capabilities",
    ]
    
    @classmethod
    def extract_rules(cls, response: str) -> List[str]:
        """Extract all YARA rules from an LLM response.
        
        Args:
            response: The full LLM response
            
        Returns:
            List of extracted YARA rules
        """
        if not response:
            return []
        
        # Check if response indicates no rule is needed
        if cls._indicates_no_rule(response):
            return []
        
        rules = []
        
        # First try to extract from code blocks
        for pattern in cls.CODE_BLOCK_PATTERNS:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                extracted = cls._extract_rules_from_text(match)
                rules.extend(extracted)
        
        # If no rules found in code blocks, try direct extraction
        if not rules:
            rules.extend(cls._extract_rules_from_text(response))
        
        # Clean and validate rules, removing duplicates
        cleaned_rules = []
        seen_rules = set()
        seen_rule_bodies = set()
        
        for rule in rules:
            cleaned = cls._clean_rule(rule)
            if cleaned and cls._validate_basic_structure(cleaned):
                # Normalize for duplicate detection
                normalized = re.sub(r'\s+', ' ', cleaned.strip())
                # Extract just the rule body (without imports) for duplicate detection
                rule_body_match = re.search(r'(rule\s+\w+\s*\{[^}]*\})', cleaned, re.DOTALL)
                if rule_body_match:
                    rule_body = re.sub(r'\s+', ' ', rule_body_match.group(1).strip())
                    # If we've seen this rule body before, skip unless this version has imports
                    if rule_body in seen_rule_bodies and 'import' not in cleaned:
                        continue
                    seen_rule_bodies.add(rule_body)
                
                if normalized not in seen_rules:
                    seen_rules.add(normalized)
                    cleaned_rules.append(cleaned)
        
        return cleaned_rules
    
    @classmethod
    def _indicates_no_rule(cls, response: str) -> bool:
        """Check if response indicates no rule is needed."""
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in cls.NO_RULE_INDICATORS)
    
    @classmethod
    def _extract_rules_from_text(cls, text: str) -> List[str]:
        """Extract YARA rules from plain text using multiple regex patterns."""
        rules = []
        
        # Always try manual parsing first if there's a rule keyword
        if "rule " in text.lower():
            # Find all rule positions
            rule_positions = []
            text_lower = text.lower()
            pos = 0
            while True:
                pos = text_lower.find("rule ", pos)
                if pos == -1:
                    break
                rule_positions.append(pos)
                pos += 5
            
            # Extract each rule
            for i, start_pos in enumerate(rule_positions):
                # Determine end position (either next rule or end of text)
                end_pos = rule_positions[i + 1] if i + 1 < len(rule_positions) else len(text)
                rule_text = text[start_pos:end_pos]
                
                manual_rule = cls._extract_rule_manual_parsing(rule_text)
                if manual_rule and cls._is_valid_rule_structure(manual_rule):
                    rules.append(manual_rule)
        
        # If no rules found with manual parsing, try regex patterns
        if not rules:
            for pattern in cls.YARA_RULE_PATTERNS:
                matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    if cls._is_valid_rule_structure(match):
                        rules.append(match)
        
        return rules
    
    @classmethod
    def _extract_rule_manual_parsing(cls, text: str) -> Optional[str]:
        """Manually parse YARA rule with brace matching as fallback."""
        rule_start = text.lower().find("rule ")
        if rule_start == -1:
            return None
        
        # Find the actual start (preserve case)
        actual_start = rule_start
        while actual_start > 0 and text[actual_start - 1] in ' \t':
            actual_start -= 1
        
        # Check for imports before the rule
        import_start = actual_start
        lines_before = text[:actual_start].split('\n')
        for i in range(len(lines_before) - 1, -1, -1):
            line = lines_before[i].strip()
            if line.startswith('import '):
                import_start = text.find(lines_before[i])
            elif line and not line.startswith('import '):
                break
        
        # Find the matching closing brace
        brace_count = 0
        found_opening = False
        end_pos = rule_start
        in_string = False
        in_regex = False
        escape_next = False
        
        for i in range(rule_start, len(text)):
            char = text[i]
            
            # Handle escape sequences
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            # Handle string literals
            if char == '"' and not in_regex:
                in_string = not in_string
            
            # Handle regex literals
            if char == '/' and not in_string:
                in_regex = not in_regex
            
            # Only count braces outside of strings and regexes
            if not in_string and not in_regex:
                if char == '{':
                    brace_count += 1
                    found_opening = True
                elif char == '}':
                    brace_count -= 1
                    if found_opening and brace_count == 0:
                        end_pos = i + 1
                        break
        
        if end_pos > rule_start and found_opening:
            return text[import_start:end_pos]
        
        return None
    
    @classmethod
    def _is_valid_rule_structure(cls, rule: str) -> bool:
        """Check if extracted text has valid YARA rule structure."""
        if not rule or not rule.strip():
            return False
        
        # Use compiled regex for efficiency
        return bool(cls.VALID_RULE_STRUCTURE.search(rule))
    
    @classmethod
    def _clean_rule(cls, rule: str) -> str:
        """Clean and normalize a YARA rule."""
        # Remove leading/trailing whitespace
        rule = rule.strip()
        
        # Remove any remaining markdown artifacts
        rule = re.sub(r'^```.*?\n', '', rule, flags=re.MULTILINE)
        rule = re.sub(r'\n```$', '', rule)
        
        # Fix common indentation issues
        lines = rule.split('\n')
        if lines:
            # Find minimum indentation (excluding empty lines and rule declaration)
            min_indent = float('inf')
            for i, line in enumerate(lines[1:], 1):  # Skip first line
                if line.strip() and not line.strip().startswith('//'):
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)
            
            # Remove common indentation
            if min_indent != float('inf') and min_indent > 0:
                cleaned_lines = [lines[0]]  # Keep first line as-is
                for line in lines[1:]:
                    if line.strip():
                        cleaned_lines.append(line[min_indent:])
                    else:
                        cleaned_lines.append('')
                rule = '\n'.join(cleaned_lines)
        
        # Fix common syntax issues
        rule = cls._fix_common_syntax_issues(rule)
        
        return rule
    
    @classmethod
    def _fix_common_syntax_issues(cls, rule: str) -> str:
        """Fix common YARA syntax issues."""
        # Ensure proper rule declaration spacing
        rule = re.sub(r'rule\s+(\w+)\s*{', r'rule \1 {', rule)
        
        # Fix missing colons in section headers
        rule = re.sub(r'^\s*(strings|condition|meta)\s*$', r'\1:', rule, flags=re.MULTILINE)
        rule = re.sub(r'^\s*(strings|condition|meta)\s+(?!:)', r'\1:', rule, flags=re.MULTILINE)
        
        # Fix string definitions without proper spacing
        rule = re.sub(r'\$(\w+)=', r'$\1 =', rule)
        
        # Fix common quote issues
        rule = re.sub(r'(\$\w+\s*=\s*)"([^"]*)"', r'\1"\2"', rule)
        
        # Ensure proper section ordering (meta, strings, condition)
        rule = cls._normalize_section_order(rule)
        
        return rule
    
    @classmethod
    def _normalize_section_order(cls, rule: str) -> str:
        """Ensure sections are in proper order: meta, strings, condition."""
        # For rules with complex strings/regexes, skip normalization
        # to avoid breaking the rule structure
        if re.search(r'(/[^/\n]*[\{\}][^/\n]*/|"[^"\n]*[\{\}][^"\n]*")', rule):
            return rule
        
        lines = rule.split('\n')
        rule_header = []
        meta_lines = []
        strings_lines = []
        condition_lines = []
        current_section = None
        brace_count = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Track rule header
            if stripped.startswith('rule ') and '{' in stripped:
                rule_header.append(line)
                brace_count += line.count('{')
                continue
            elif not rule_header and not stripped:
                continue
            elif not rule_header:
                rule_header.append(line)
                continue
            
            # Track braces for end of rule
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0 and '}' in line:
                # End of rule
                if current_section == 'condition':
                    condition_lines.append(line)
                else:
                    condition_lines.append(line)  # Closing brace
                break
            
            # Determine section
            if stripped.startswith('meta:'):
                current_section = 'meta'
                meta_lines.append(line)
            elif stripped.startswith('strings:'):
                current_section = 'strings'
                strings_lines.append(line)
            elif stripped.startswith('condition:'):
                current_section = 'condition'
                condition_lines.append(line)
            else:
                # Add to current section
                if current_section == 'meta':
                    meta_lines.append(line)
                elif current_section == 'strings':
                    strings_lines.append(line)
                elif current_section == 'condition':
                    condition_lines.append(line)
                else:
                    # Default to rule header area
                    rule_header.append(line)
        
        # Reconstruct rule
        result = rule_header + meta_lines + strings_lines + condition_lines
        return '\n'.join(result)
    
    @classmethod
    def _validate_basic_structure(cls, rule: str) -> bool:
        """Validate basic YARA rule structure."""
        # Use our more sophisticated validation
        return cls._is_valid_rule_structure(rule)
    
    @classmethod
    def extract_single_rule(cls, response: str) -> Optional[str]:
        """Extract a single YARA rule from response (returns first valid rule)."""
        rules = cls.extract_rules(response)
        return rules[0] if rules else None