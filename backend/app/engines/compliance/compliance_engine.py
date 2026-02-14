"""
Core compliance validation engine.
Validates documents against regulatory frameworks with explainable AI.
"""
from typing import Dict, List
from loguru import logger
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.engines.compliance.rule_loader import RuleLoader


class ComplianceEngine:
    """Compliance validation engine with AI-powered gap detection."""
    
    def __init__(self):
        """Initialize compliance engine."""
        self.rule_loader = RuleLoader()
        
        # Initialize LLM client
        if settings.LLM_PROVIDER == "openai":
            self.llm_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.llm_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        logger.info(f"Compliance engine initialized with {settings.LLM_PROVIDER}")
    
    async def validate_document(
        self,
        segments: List[Dict],
        framework: str,
        document_text: str
    ) -> List[Dict]:
        """
        Validate document against compliance rules using BATCH processing.
        
        Args:
            segments: Document segments from segmentation engine
            framework: Regulatory framework (ind_as, sebi, rbi)
            document_text: Full document text
            
        Returns:
            List of validation results
        """
        logger.info(f"Starting BATCH compliance validation for framework: {framework}")
        
        # Load rules for framework
        rules = self.rule_loader.load_rules(framework)
        
        if not rules:
            logger.warning(f"No rules found for framework: {framework}")
            return []
        
        # BATCH VALIDATION - Process all rules in 1-2 API calls
        validation_results = await self._batch_validate_rules(rules, segments, document_text)
        
        logger.info(f"Batch validation complete: {len(validation_results)} rules checked")
        return validation_results
    
    async def _validate_rule(
        self,
        rule: Dict,
        segments: List[Dict],
        document_text: str
    ) -> Dict:
        """Validate a single compliance rule."""
        
        # Find relevant segments
        relevant_segments = self._find_relevant_segments(rule, segments)
        
        # Prepare context for LLM
        context = self._prepare_context(rule, relevant_segments, document_text)
        
        # Use LLM to validate
        validation = await self._llm_validate(rule, context)
        
        return {
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "rule_description": rule.get("description"),
            "framework": rule.get("framework"),
            "status": validation["status"],
            "severity": validation["severity"],
            "confidence_score": validation["confidence"],
            "finding_summary": validation["summary"],
            "finding_details": validation["details"],
            "affected_sections": [s["title"] for s in relevant_segments],
            "evidence": validation.get("evidence", []),
            "remediation_required": validation.get("remediation_required", "no"),
            "remediation_suggestions": validation.get("remediation", ""),
            "ai_explanation": validation.get("explanation", "")
        }
    
    def _find_relevant_segments(self, rule: Dict, segments: List[Dict]) -> List[Dict]:
        """Find document segments relevant to a compliance rule."""
        relevant = []
        
        # Get keywords from rule
        keywords = rule.get("keywords", [])
        
        for segment in segments:
            content_lower = segment.get("content", "").lower()
            title_lower = segment.get("title", "").lower()
            
            # Check if any keyword matches
            if any(keyword.lower() in content_lower or keyword.lower() in title_lower for keyword in keywords):
                relevant.append(segment)
        
        return relevant
    
    def _prepare_context(self, rule: Dict, segments: List[Dict], full_text: str) -> str:
        """Prepare context for LLM validation."""
        context_parts = [
            f"Compliance Rule: {rule.get('name')}",
            f"Description: {rule.get('description')}",
            f"Requirements: {rule.get('requirements', 'N/A')}",
            "\nRelevant Document Sections:"
        ]
        
        for segment in segments[:5]:  # Limit to top 5 relevant segments
            context_parts.append(f"\n--- {segment.get('title')} ---")
            context_parts.append(segment.get('content', '')[:500])  # Limit content length
        
        return "\n".join(context_parts)
    
    async def _batch_validate_rules(
        self,
        rules: List[Dict],
        segments: List[Dict],
        document_text: str
    ) -> List[Dict]:
        """Validate ALL rules in a single batch API call."""
        import json
        
        logger.info(f"Batch validating {len(rules)} rules in single API call")
        
        # Prepare rules JSON
        rules_json = json.dumps([{
            "id": r.get("id"),
            "name": r.get("name"),
            "description": r.get("description"),
            "requirements": r.get("requirements", ""),
            "severity": r.get("severity", "medium")
        } for r in rules], indent=2)
        
        # Truncate document if too long (keep first 8000 chars)
        doc_sample = document_text[:8000] if len(document_text) > 8000 else document_text
        
        prompt = f"""You are a compliance expert. Validate this financial document against ALL {len(rules)} rules at once.

RULES TO VALIDATE:
{rules_json}

DOCUMENT TEXT:
{doc_sample}

TASK: For EACH rule, determine compliance status.

Return a JSON array with exactly {len(rules)} objects, one for each rule, in the SAME ORDER as the rules above.

Each object must have:
{{
  "rule_id": "string",
  "status": "compliant" | "non_compliant" | "partial",
  "severity": "critical" | "high" | "medium" | "low" | "info",
  "confidence": 0.0-1.0,
  "summary": "brief finding (1-2 sentences)",
  "details": "detailed analysis",
  "evidence": ["quote1", "quote2"],
  "remediation_required": "yes" | "no",
  "remediation": "suggestions if needed",
  "explanation": "your reasoning"
}}

Return ONLY the JSON array, no other text."""

        try:
            if settings.LLM_PROVIDER == "openai":
                response = await self.llm_client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a compliance validation expert. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"} if "gpt-4" in settings.LLM_MODEL else None
                )
                result_text = response.choices[0].message.content
            else:
                response = await self.llm_client.messages.create(
                    model=settings.LLM_MODEL,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
            
            # Parse JSON response
            import json
            import re
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                results_array = json.loads(json_match.group())
            else:
                # Try parsing entire response
                results_array = json.loads(result_text)
            
            # Map results to rules
            validation_results = []
            for i, rule in enumerate(rules):
                if i < len(results_array):
                    llm_result = results_array[i]
                    validation_results.append({
                        "rule_id": rule.get("id"),
                        "rule_name": rule.get("name"),
                        "rule_description": rule.get("description"),
                        "framework": rule.get("framework"),
                        "status": llm_result.get("status", "partial"),
                        "severity": llm_result.get("severity", "medium"),
                        "confidence_score": llm_result.get("confidence", 0.7),
                        "finding_summary": llm_result.get("summary", ""),
                        "finding_details": llm_result.get("details", ""),
                        "affected_sections": [],
                        "evidence": llm_result.get("evidence", []),
                        "remediation_required": llm_result.get("remediation_required", "no"),
                        "remediation_suggestions": llm_result.get("remediation", ""),
                        "ai_explanation": llm_result.get("explanation", "")
                    })
                else:
                    # Fallback if not enough results
                    validation_results.append(self._create_fallback_result(rule))
            
            logger.info(f"Batch validation successful: {len(validation_results)} results")
            return validation_results
            
        except Exception as e:
            logger.error(f"Batch validation failed: {e}, falling back to individual validation")
            # Fallback to individual validation
            validation_results = []
            for rule in rules:
                result = await self._validate_rule(rule, segments, document_text)
                validation_results.append(result)
            return validation_results
    
    def _create_fallback_result(self, rule: Dict) -> Dict:
        """Create fallback result if batch validation fails."""
        return {
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "rule_description": rule.get("description"),
            "framework": rule.get("framework"),
            "status": "pending",
            "severity": "medium",
            "confidence_score": 0.0,
            "finding_summary": "Validation pending",
            "finding_details": "",
            "affected_sections": [],
            "evidence": [],
            "remediation_required": "no",
            "remediation_suggestions": "",
            "ai_explanation": "Batch validation incomplete"
        }
    
    async def _llm_validate(self, rule: Dict, context: str) -> Dict:
        """Use LLM to validate compliance rule."""
        
        prompt = f"""You are a compliance expert analyzing a financial document against regulatory requirements.

{context}

Task: Determine if the document complies with the following requirement:
{rule.get('description')}

Provide your analysis in the following format:
1. Status: COMPLIANT, NON_COMPLIANT, or PARTIAL
2. Severity: CRITICAL, HIGH, MEDIUM, LOW, or INFO
3. Confidence: 0.0 to 1.0
4. Summary: Brief finding summary (1-2 sentences)
5. Details: Detailed findings
6. Evidence: Specific quotes or references from the document
7. Remediation Required: yes or no
8. Remediation: Specific suggestions if remediation is required
9. Explanation: Explain your reasoning

Be thorough and specific in your analysis."""

        try:
            if settings.LLM_PROVIDER == "openai":
                response = await self.llm_client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a compliance validation expert."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=settings.TEMPERATURE,
                    max_tokens=settings.MAX_TOKENS
                )
                result_text = response.choices[0].message.content
            else:
                # Anthropic
                response = await self.llm_client.messages.create(
                    model=settings.LLM_MODEL,
                    max_tokens=settings.MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
            
            # Parse LLM response
            return self._parse_llm_response(result_text)
        
        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return {
                "status": "pending",
                "severity": "medium",
                "confidence": 0.0,
                "summary": f"Validation failed: {str(e)}",
                "details": {},
                "explanation": "Error during validation"
            }
    
    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse LLM response into structured format."""
        # Simple parsing - in production, use more robust parsing
        result = {
            "status": "partial",
            "severity": "medium",
            "confidence": 0.7,
            "summary": "",
            "details": {},
            "evidence": [],
            "remediation_required": "no",
            "remediation": "",
            "explanation": response_text
        }
        
        # Extract status
        if "COMPLIANT" in response_text.upper() and "NON_COMPLIANT" not in response_text.upper():
            result["status"] = "compliant"
        elif "NON_COMPLIANT" in response_text.upper() or "NON-COMPLIANT" in response_text.upper():
            result["status"] = "non_compliant"
        
        # Extract severity
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            if severity in response_text.upper():
                result["severity"] = severity.lower()
                break
        
        # Extract summary (first few sentences)
        lines = response_text.split('\n')
        summary_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        if summary_lines:
            result["summary"] = summary_lines[0][:200]
        
        return result
