"""
Parser Agent - Extracts and structures formatting rules from guidelines
"""
import json
from pathlib import Path
from typing import Dict, Any
from loguru import logger

from utils.llm_client import llm_client
from utils.pdf_parser import parse_guidelines_pdf
from utils.facts_builder import build_project_facts
from config.prompts import (
    PARSER_SYSTEM_PROMPT,
    PARSE_GUIDELINES_PROMPT,
    ANALYZE_PROJECT_PROMPT
)


class ParserAgent:
    """Extracts formatting rules and analyzes project structure"""
    
    def __init__(self, output_dir: str = "outputs/intermediate", job_id: str = None):
        # Create job-specific output directory to prevent content mixing
        if job_id:
            self.output_dir = Path(output_dir) / f"job_{job_id}"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.job_id = job_id
    
    def parse_guidelines(self, guidelines_path: str) -> Dict[str, Any]:
        """
        Extract formatting specifications from guidelines PDF
        
        Args:
            guidelines_path: Path to guidelines PDF
            
        Returns:
            Structured formatting rules
        """
        logger.info("Parsing guidelines document...")
        
        # Extract text from PDF
        pdf_data = parse_guidelines_pdf(guidelines_path)
        guidelines_text = pdf_data["text"]
        
        # Truncate to manageable size (4000 chars for faster processing)
        max_chars = 4000
        if len(guidelines_text) > max_chars:
            logger.warning(f"Guidelines text truncated from {len(guidelines_text)} to {max_chars} chars")
            guidelines_text = guidelines_text[:max_chars]
        
        # Use LLM to extract structured formatting rules
        prompt = PARSE_GUIDELINES_PROMPT.format(
            guidelines_text=guidelines_text
        )
        
        try:
            logger.info("Requesting formatting rules from LLM (this may take 2-3 minutes)...")
            formatting_rules = llm_client.generate_json(
                prompt=prompt,
                system_prompt=PARSER_SYSTEM_PROMPT,
                temperature=0.1,
                timeout=300  # 5 minutes timeout
            )
            
            # Add metadata
            formatting_rules["_metadata"] = {
                "source": str(guidelines_path),
                "pages": pdf_data["pages"],
                "tables_found": len(pdf_data["tables"])
            }
            
            # Save to file
            output_path = self.output_dir / "guidelines_config.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(formatting_rules, f, indent=2)
            
            logger.success(f"Guidelines parsed successfully: {output_path}")
            return formatting_rules
            
        except Exception as e:
            logger.error(f"Failed to parse guidelines with LLM: {e}")
            logger.warning("Using fallback default formatting rules...")
            
            # Fallback to default formatting
            formatting_rules = self._get_default_formatting()
            formatting_rules["_metadata"] = {
                "source": str(guidelines_path),
                "pages": pdf_data["pages"],
                "tables_found": len(pdf_data["tables"]),
                "fallback": True,
                "reason": str(e)
            }
            
            # Save fallback
            output_path = self.output_dir / "guidelines_config.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(formatting_rules, f, indent=2)
            
            logger.info(f"Fallback guidelines saved: {output_path}")
            return formatting_rules
    
    def _get_default_formatting(self) -> Dict[str, Any]:
        """
        Get default formatting rules based on common academic standards
        
        Returns:
            Default formatting specification
        """
        return {
            "page_setup": {
                "paper_size": "A4",
                "margins": {
                    "left": "1.25in",
                    "right": "1.0in",
                    "top": "1.0in",
                    "bottom": "1.0in"
                },
                "orientation": "portrait"
            },
            "fonts": {
                "family": "Times New Roman",
                "chapter_heading": {
                    "size": 16,
                    "bold": True,
                    "all_caps": True
                },
                "section_heading": {
                    "size": 14,
                    "bold": True,
                    "all_caps": True
                },
                "subsection_heading": {
                    "size": 12,
                    "bold": True,
                    "all_caps": False
                },
                "body_text": {
                    "size": 12,
                    "bold": False
                }
            },
            "spacing": {
                "line_spacing": 1.5,
                "paragraph_spacing_before": 12,
                "paragraph_spacing_after": 12,
                "heading_spacing_before": 24,
                "heading_spacing_after": 12
            },
            "numbering": {
                "chapters": "numeric",
                "sections": "decimal",
                "figures": "Fig. {chapter}.{number}",
                "tables": "Table {chapter}.{number}"
            },
            "headers_footers": {
                "header_left": "Student ID",
                "header_right": "Chapter Name",
                "footer_left": "Institution Name",
                "footer_center": "{page}",
                "footer_right": "Department"
            }
        }
    
    def analyze_project_structure(self, project_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze project structure to understand project type and components
        
        STEP 1: Build deterministic facts (NO LLM)
        STEP 2: Use LLM only for classification/labeling
        
        Args:
            project_analysis: Raw project structure from CodeAnalyzer
            
        Returns:
            Enriched project analysis with facts + LLM labels
        """
        logger.info("Analyzing project structure...")
        
        # STEP 1: Build deterministic facts (NO LLM CALLS)
        project_facts = build_project_facts(project_analysis)
        
        # Save facts to file
        facts_path = self.output_dir / "project_facts.json"
        with open(facts_path, 'w', encoding='utf-8') as f:
            json.dump(project_facts, f, indent=2)
        logger.success(f"Project facts saved: {facts_path}")
        
        # STEP 2: Prepare structured summary for LLM (NOT raw file lists)
        # Include comprehensive project information but keep it structured
        facts_summary = {
            "file_types": project_facts["file_type_counts"],
            "entry_points": project_facts["entry_points_detected"],
            "capabilities": project_facts["detected_capabilities"],
            "technologies": project_facts["detected_technologies"],
            "frontend_only": project_facts["frontend_only"],
            "backend_present": project_facts["backend_present"],
            "fullstack": project_facts["fullstack"],
            "directory_structure": project_facts["directory_structure"],
            "code_statistics": project_facts["code_statistics"],
            # Include module information for better understanding
            "modules_count": len(project_facts.get("modules", [])),
            "modules": project_facts.get("modules", [])[:10],  # Top 10 modules for LLM prompt
            "code_files_count": len(project_facts.get("code_content", {})),
            # Include sample code (first 3 files) for LLM context, full code_content available in facts
            "sample_code_files": list(project_facts.get("code_content", {}).keys())[:3]
        }
        
        # Format facts summary as compact string
        import json as json_module
        facts_summary_str = json_module.dumps(facts_summary, indent=2)
        
        # STEP 3: Call LLM ONLY for classification (not fact inference)
        prompt = ANALYZE_PROJECT_PROMPT.format(
            project_name=project_facts["project_name"],
            project_facts=facts_summary_str
        )
        
        # Add isolation header
        isolation_header = f"""
🚨 CRITICAL PROJECT ISOLATION 🚨
JOB ID: {self.job_id}
PROJECT NAME: {project_facts["project_name"]}

YOU ARE CLASSIFYING THIS SPECIFIC PROJECT ONLY. DO NOT REFERENCE OR MIX CONTENT FROM ANY OTHER PROJECTS.
EVERY PROJECT IS UNIQUE AND MUST BE ANALYZED INDEPENDENTLY.

"""
        prompt = isolation_header + prompt
        
        try:
            # LLM only returns labels, not facts
            llm_labels = llm_client.generate_json(
                prompt=prompt,
                system_prompt=PARSER_SYSTEM_PROMPT,
                temperature=0.1
            )
            
            # STEP 4: Merge facts + labels, but LOCK facts (don't let LLM override)
            result = {
                **project_analysis,  # Original analysis (includes files with code snippets)
                **project_facts,      # Deterministic facts (LOCKED) - includes modules, use_cases, code_content
                # LLM labels (can be overridden if they contradict facts)
                "project_type": llm_labels.get("project_type", "Software Project"),
                "architecture_pattern": llm_labels.get("architecture_pattern", "Unknown"),
                "complexity_level": llm_labels.get("complexity_level", "moderate")
            }
            
            # CRITICAL: Validate LLM output doesn't contradict facts
            # If LLM says "no entry points" but facts show entry points, override
            if not llm_labels.get("key_components") and project_facts["entry_points_detected"]:
                logger.warning("LLM output contradicts facts: entry points detected but not listed. Overriding...")
                result["key_components"] = project_facts["entry_points_detected"]
            else:
                result["key_components"] = llm_labels.get("key_components", project_facts["entry_points_detected"])
            
            # If LLM says different technologies, use facts
            if llm_labels.get("main_technologies") != project_facts["detected_technologies"]:
                logger.warning("LLM technologies differ from facts. Using facts...")
                result["main_technologies"] = project_facts["detected_technologies"]
            else:
                result["main_technologies"] = llm_labels.get("main_technologies", project_facts["detected_technologies"])
            
            # Calculate confidence score based on fact support
            confidence_score = _calculate_confidence(project_facts, llm_labels)
            result["classification_confidence"] = confidence_score
            
            # Log comprehensive analysis summary
            total_code_files = len(project_facts.get("code_content", {}))
            total_modules = len(project_facts.get("modules", []))
            logger.info(f"📊 Comprehensive analysis complete: {total_code_files} code files, {total_modules} modules analyzed")
            logger.info(f"   Code content available for Planner/Writer: {total_code_files} files with code snippets")
            
            # Propagate analysis warnings from project_analysis if present
            if "analysis_warnings" in project_analysis:
                result["analysis_warnings"] = project_analysis["analysis_warnings"]
            
            # Save to file
            output_path = self.output_dir / "codebase_structure.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            logger.success(f"Project structure analyzed: {output_path}")
            logger.info(f"Classification confidence: {confidence_score:.2f}")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to analyze project structure with LLM: {e}")
            logger.info("Using facts-only analysis as fallback...")
            # Fallback: use facts only with default labels
            result = {
                **project_analysis,
                **project_facts,
                "project_type": "Software Project",
                "architecture_pattern": "Unknown",
                "complexity_level": "moderate",
                "main_technologies": project_facts["detected_technologies"],
                "key_components": project_facts["entry_points_detected"],
                "classification_confidence": 0.5  # Low confidence for fallback
            }
            
            # Propagate analysis warnings from project_analysis if present
            if "analysis_warnings" in project_analysis:
                result["analysis_warnings"] = project_analysis["analysis_warnings"]
            
            # Save fallback result
            output_path = self.output_dir / "codebase_structure.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            logger.success(f"Project structure saved (fallback): {output_path}")
            return result


def _calculate_confidence(project_facts: Dict[str, Any], llm_labels: Dict[str, Any]) -> float:
    """
    Calculate confidence score (0-1) based on how well facts support LLM classification
    
    Higher confidence = more facts support the classification
    """
    score = 0.5  # Base score
    
    # More entry points = higher confidence
    if len(project_facts["entry_points_detected"]) > 0:
        score += 0.1
    
    # More capabilities detected = higher confidence
    if len(project_facts["detected_capabilities"]) > 0:
        score += 0.1
    
    # More technologies detected = higher confidence
    if len(project_facts["detected_technologies"]) > 0:
        score += 0.1
    
    # Code files present = higher confidence
    if project_facts["code_statistics"]["code_files"] > 0:
        score += 0.1
    
    # LLM classification matches facts = higher confidence
    if project_facts["frontend_only"] and "frontend" in llm_labels.get("project_type", "").lower():
        score += 0.1
    elif project_facts["backend_present"] and "backend" in llm_labels.get("architecture_pattern", "").lower():
        score += 0.1
    
    return min(1.0, score)
    
    def run(
        self, 
        guidelines_path: str, 
        project_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run complete parsing pipeline
        
        Returns:
            Dictionary with both guidelines and project analysis
        """
        logger.info("=== PARSER AGENT STARTED ===")
        
        guidelines_config = self.parse_guidelines(guidelines_path)
        codebase_structure = self.analyze_project_structure(project_analysis)
        
        result = {
            "guidelines": guidelines_config,
            "codebase": codebase_structure
        }
        
        # Save combined output
        output_path = self.output_dir / "parser_output.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.success(f"=== PARSER AGENT COMPLETED ===")
        logger.info(f"Output saved to: {output_path}")
        
        return result


# Convenience function
def parse_inputs(guidelines_path: str, project_analysis: Dict[str, Any], job_id: str = None) -> Dict[str, Any]:
    """
    Run parser agent on inputs
    
    Args:
        guidelines_path: Path to guidelines PDF
        project_analysis: Project structure from CodeAnalyzer
        job_id: Optional job ID for isolated output directory
        
    Returns:
        Parsed and structured data
    """
    agent = ParserAgent(job_id=job_id)
    return agent.run(guidelines_path, project_analysis)