"""
Intelligent document segmentation engine.
Segments documents into logical sections with metadata tagging.
"""
from typing import Dict, List
import re
from loguru import logger


class SegmentationEngine:
    """Intelligent document segmentation with hierarchical structure analysis."""
    
    def __init__(self):
        """Initialize segmentation engine."""
        self.header_patterns = [
            r'^#+\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headers
            r'^(\d+\.)+\s+(.+)$',  # Numbered sections (1.1, 1.1.1)
            r'^([IVXLCDM]+)\.\s+(.+)$',  # Roman numerals
        ]
        logger.info("Segmentation engine initialized")
    
    async def segment_document(self, text: str, tables: List = None) -> List[Dict]:
        """
        Segment document into logical sections.
        
        Args:
            text: Extracted document text
            tables: List of extracted tables
            
        Returns:
            List of document segments with metadata
        """
        logger.info("Starting document segmentation")
        
        segments = []
        lines = text.split('\n')
        
        current_section = {
            "type": "header",
            "level": 0,
            "title": "Document Start",
            "content": "",
            "line_start": 0,
            "line_end": 0,
            "metadata": {}
        }
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                continue
            
            # Check if line is a header
            header_info = self._detect_header(line)
            
            if header_info:
                # Save previous section
                if current_section["content"]:
                    current_section["line_end"] = i - 1
                    current_section["confidence"] = self._calculate_confidence(current_section)
                    segments.append(current_section.copy())
                
                # Start new section
                current_section = {
                    "type": "header",
                    "level": header_info["level"],
                    "title": header_info["title"],
                    "content": "",
                    "line_start": i,
                    "line_end": i,
                    "metadata": header_info
                }
            else:
                # Add to current section content
                current_section["content"] += line + "\n"
        
        # Add final section
        if current_section["content"]:
            current_section["line_end"] = len(lines) - 1
            current_section["confidence"] = self._calculate_confidence(current_section)
            segments.append(current_section)
        
        # Classify section types
        segments = self._classify_sections(segments)
        
        # Add table segments
        if tables:
            segments.extend(self._create_table_segments(tables))
        
        logger.info(f"Segmentation complete: {len(segments)} segments created")
        return segments
    
    def _detect_header(self, line: str) -> Dict:
        """Detect if a line is a header and extract metadata."""
        # Check for numbered sections
        numbered_match = re.match(r'^((\d+\.)+)\s+(.+)$', line)
        if numbered_match:
            section_num = numbered_match.group(1)
            title = numbered_match.group(3)
            level = section_num.count('.')
            return {
                "level": level,
                "title": title,
                "section_number": section_num,
                "type": "numbered"
            }
        
        # Check for ALL CAPS (likely header)
        if line.isupper() and len(line) > 3 and len(line) < 100:
            return {
                "level": 1,
                "title": line,
                "type": "caps"
            }
        
        # Check for Roman numerals
        roman_match = re.match(r'^([IVXLCDM]+)\.\s+(.+)$', line)
        if roman_match:
            return {
                "level": 2,
                "title": roman_match.group(2),
                "section_number": roman_match.group(1),
                "type": "roman"
            }
        
        return None
    
    def _classify_sections(self, segments: List[Dict]) -> List[Dict]:
        """Classify section types based on content."""
        financial_keywords = ['revenue', 'profit', 'loss', 'assets', 'liabilities', 'equity', 'cash flow']
        note_keywords = ['note', 'footnote', 'reference']
        
        for segment in segments:
            content_lower = segment["content"].lower()
            
            # Check for financial data
            if any(keyword in content_lower for keyword in financial_keywords):
                segment["semantic_type"] = "financial_data"
            
            # Check for notes
            elif any(keyword in content_lower for keyword in note_keywords):
                segment["semantic_type"] = "footnote"
            
            # Check for introduction
            elif segment["line_start"] < 50 and any(word in content_lower for word in ['introduction', 'overview', 'summary']):
                segment["semantic_type"] = "introduction"
            
            # Default to paragraph
            else:
                segment["semantic_type"] = "paragraph"
        
        return segments
    
    def _create_table_segments(self, tables: List) -> List[Dict]:
        """Create segments for extracted tables."""
        table_segments = []
        
        for i, table in enumerate(tables):
            segment = {
                "type": "table",
                "level": 0,
                "title": f"Table {i+1}",
                "content": str(table),
                "table_data": table,
                "semantic_type": "table",
                "confidence": 0.95,
                "metadata": {
                    "row_count": len(table) if isinstance(table, list) else 0,
                    "col_count": len(table[0]) if isinstance(table, list) and table else 0
                }
            }
            table_segments.append(segment)
        
        return table_segments
    
    def _calculate_confidence(self, segment: Dict) -> float:
        """Calculate confidence score for segment classification."""
        confidence = 0.7  # Base confidence
        
        # Higher confidence for headers with section numbers
        if segment.get("metadata", {}).get("section_number"):
            confidence += 0.2
        
        # Higher confidence for longer content
        if len(segment.get("content", "")) > 100:
            confidence += 0.1
        
        return min(confidence, 1.0)
