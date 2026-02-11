"""
Compliance rule loader.
Loads and manages compliance rules from JSON configuration files.
"""
import json
import os
from typing import Dict, List
from pathlib import Path
from loguru import logger

from app.core.config import settings


class RuleLoader:
    """Load and manage compliance rules from configuration files."""
    
    def __init__(self):
        """Initialize rule loader."""
        self.rules_path = Path(settings.COMPLIANCE_RULES_PATH)
        self.rules_cache = {}
        logger.info(f"Rule loader initialized with path: {self.rules_path}")
    
    def load_rules(self, framework: str) -> List[Dict]:
        """
        Load compliance rules for a specific framework.
        
        Args:
            framework: Framework name (ind_as, sebi, rbi, companies_act)
            
        Returns:
            List of compliance rules
        """
        # Check cache
        if framework in self.rules_cache:
            logger.debug(f"Loading {framework} rules from cache")
            return self.rules_cache[framework]
        
        # Load from file
        rule_file = self.rules_path / f"{framework}_rules.json"
        
        if not rule_file.exists():
            logger.warning(f"Rule file not found: {rule_file}")
            return []
        
        try:
            with open(rule_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            # Cache rules
            self.rules_cache[framework] = rules
            logger.info(f"Loaded {len(rules)} rules for {framework}")
            
            return rules
        
        except Exception as e:
            logger.error(f"Failed to load rules from {rule_file}: {e}")
            return []
    
    def get_rule_by_id(self, framework: str, rule_id: str) -> Dict:
        """Get a specific rule by ID."""
        rules = self.load_rules(framework)
        
        for rule in rules:
            if rule.get("id") == rule_id:
                return rule
        
        return None
    
    def get_all_frameworks(self) -> List[str]:
        """Get list of all available frameworks."""
        frameworks = []
        
        for file in self.rules_path.glob("*_rules.json"):
            framework = file.stem.replace("_rules", "")
            frameworks.append(framework)
        
        return frameworks
