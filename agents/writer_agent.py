"""
Writer Agent - Generates natural language documentation content
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from utils.llm_client import llm_client
from config.prompts import (
    WRITER_SYSTEM_PROMPT,
    WRITE_SECTION_PROMPT,
    WRITE_INTRODUCTION_PROMPT,
    WRITE_CONCLUSION_PROMPT
)


class WriterAgent:
    """Generates comprehensive documentation content for each section"""
    
    def __init__(self, output_dir: str = "outputs/intermediate", job_id: str = None):
        # Create job-specific output directory to prevent content mixing
        if job_id:
            self.output_dir = Path(output_dir) / f"job_{job_id}"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.job_id = job_id
    
    def _extract_code_snippets(self, project_context: Dict[str, Any], max_files: int = 5) -> str:
        """
        Extract actual code content from project files
        
        Args:
            project_context: Project context with files
            max_files: Maximum number of files to include
            
        Returns:
            Formatted code snippets string
        """
        code_snippets = []
        
        if "files" not in project_context:
            return "NO CODE CONTENT AVAILABLE - Only file paths are known."
        
        # Prioritize main files
        main_file_names = ['app.js', 'main.js', 'index.js', 'app.py', 'main.py', 'index.html', 'app.ts', 'main.ts', 'index.ts']
        
        main_files = []
        other_files = []
        
        for file_info in project_context["files"]:
            if isinstance(file_info, dict) and file_info.get("has_code") and file_info.get("code_snippet"):
                file_name = file_info.get("name", "")
                file_path = file_info.get("path", file_name)
                code_content = file_info.get("code_snippet", "")
                
                file_data = {
                    "path": file_path,
                    "name": file_name,
                    "code": code_content[:3000] if file_name.lower() in [m.lower() for m in main_file_names] else code_content[:2000]
                }
                
                if file_name.lower() in [m.lower() for m in main_file_names]:
                    main_files.append(file_data)
                else:
                    other_files.append(file_data)
        
        # Combine main files first, then others
        selected_files = (main_files[:3] + other_files[:max_files-3])[:max_files]
        
        for file_data in selected_files:
            code_snippets.append(f"""
=== FILE: {file_data['path']} ===
{file_data['code']}
=== END OF FILE ===
""")
        
        return "\n".join(code_snippets) if code_snippets else "NO CODE CONTENT AVAILABLE - Only file paths are known."
    
    def write_introduction(
        self,
        outline: Dict[str, Any],
        codebase_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Write introduction chapter based on the outline
        
        Returns:
            Chapter content with sections
        """
        logger.info("Writing Introduction chapter...")
        
        # Find the introduction chapter from outline
        intro_chapter = None
        for chapter in outline.get("chapters", []):
            if chapter.get("number") == 1 or "introduction" in chapter.get("title", "").lower():
                intro_chapter = chapter
                break
        
        if not intro_chapter:
            logger.warning("No introduction chapter found in outline, using fallback")
            intro_chapter = {
                "number": 1,
                "title": "Introduction",
                "sections": [
                    {"number": "1.1", "title": "Project Overview", "description": "Overview of the project"},
                    {"number": "1.2", "title": "Objectives", "description": "Project objectives"},
                    {"number": "1.3", "title": "Report Scope", "description": "Scope of the report"}
                ]
            }
        
        project_overview = {
            "name": codebase_structure.get("name", "Project"),
            "type": codebase_structure.get("project_type", "Software Project"),
            "technologies": codebase_structure.get("main_technologies", []),
            "description": f"A {codebase_structure.get('project_type', 'software')} project"
        }
        
        # Format introduction sections for the prompt
        intro_sections_text = json.dumps(intro_chapter.get("sections", []), indent=2)
        
        # Get sample files for explicit identification
        sample_files = []
        if "files" in codebase_structure:
            sample_files = [f.get('path', str(f)) for f in codebase_structure["files"][:5]]
        sample_files_str = ", ".join(sample_files) if sample_files else "No files listed"
        
        # Extract code snippets for introduction
        code_snippets = self._extract_code_snippets(codebase_structure, max_files=3)
        
        prompt = WRITE_INTRODUCTION_PROMPT.format(
            project_overview=json.dumps(project_overview, indent=2),
            introduction_sections=intro_sections_text,
            chapter_title=intro_chapter.get("title", "Introduction"),
            actual_code_content=code_snippets
        )
        
        # Add explicit isolation instruction with job_id and file samples
        isolation_header = f"""
🚨 CRITICAL PROJECT ISOLATION 🚨
JOB ID: {self.job_id}
PROJECT NAME: {project_overview.get("name", "Unknown")}
PROJECT TYPE: {project_overview.get("type", "Unknown")}
CHAPTER: Introduction
SAMPLE FILES: {sample_files_str}

YOU ARE WRITING THE INTRODUCTION FOR THIS SPECIFIC PROJECT ONLY.
DO NOT REFERENCE, REUSE, OR MIX CONTENT FROM ANY OTHER PROJECTS.
EVERY PROJECT IS UNIQUE AND MUST BE DOCUMENTED INDEPENDENTLY.

"""
        prompt = isolation_header + prompt
        
        # Retry logic with plain text fallback
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                chapter = llm_client.generate_json(
                    prompt=prompt,
                    system_prompt=WRITER_SYSTEM_PROMPT,
                    temperature=0.1
                )
                # Validate that chapter is a dict
                if not isinstance(chapter, dict):
                    logger.warning(f"LLM returned non-dict chapter (type: {type(chapter)}), using plain text fallback")
                    return self._write_introduction_plain_text(outline, codebase_structure)
                
                # Ensure numbering key exists
                chapter["chapter_number"] = chapter.get("chapter_number", 1)
                
                # Ensure sections is a list
                sections = chapter.get('sections', [])
                if not isinstance(sections, list):
                    logger.warning(f"Chapter sections is not a list (type: {type(sections)}), setting to empty list")
                    chapter['sections'] = []
                    sections = []
                
                # Validate that sections have usable content, with type-safe handling
                valid_sections = []
                for sec in sections:
                    if not isinstance(sec, dict):
                        logger.warning(f"Section has invalid type {type(sec)}, skipping")
                        continue
                    
                    raw_content = sec.get("content", "")
                    if isinstance(raw_content, dict):
                        # Flatten dict content to a string for safe processing
                        from pprint import pformat
                        content_text = pformat(raw_content)
                    else:
                        content_text = str(raw_content)
                    
                    if not content_text.strip():
                        logger.warning(f"Section {sec.get('number', 'unknown')} has no content, skipping")
                        continue
                    
                    sec["content"] = content_text
                    valid_sections.append(sec)
                
                if not valid_sections:
                    logger.warning("Introduction chapter has no valid sections with content, using plain text fallback")
                    return self._write_introduction_plain_text(outline, codebase_structure)
                
                chapter['sections'] = valid_sections
                
                # POST-PROCESSING: Apply hardening rules to each section
                intro_chapter_from_outline = None
                for ch in outline.get("chapters", []):
                    if ch.get("number") == 1 or "introduction" in ch.get("title", "").lower():
                        intro_chapter_from_outline = ch
                        break
                
                for section in valid_sections:
                    section_num = section.get("number", "")
                    # Find corresponding outline section for writing_guideline
                    outline_section = None
                    if intro_chapter_from_outline:
                        for sec in intro_chapter_from_outline.get("sections", []):
                            if sec.get("number") == section_num:
                                outline_section = sec
                                break
                    
                    if outline_section:
                        section["writing_guideline"] = outline_section.get("writing_guideline", "")
                    
                    section = self._harden_section_content(section, "", codebase_structure)
                
                logger.success(f"Introduction written: {len(valid_sections)} sections")
                return chapter
                
            except ValueError as e:
                if ("Invalid JSON" in str(e) or "Invalid control" in str(e)):
                    if attempt < max_attempts - 1:
                        logger.warning(f"JSON parse failed, attempt {attempt + 1}/{max_attempts}, retrying...")
                        continue
                    else:
                        logger.warning("All JSON attempts failed, using plain text fallback for introduction...")
                        return self._write_introduction_plain_text(outline, codebase_structure)
                else:
                    raise
            except Exception as e:
                logger.error(f"Failed to write introduction: {e}")
                raise
    
    def _write_introduction_plain_text(self, outline: Dict[str, Any], codebase_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback for introduction using plain text - uses outline sections"""
        logger.info("Generating introduction with plain text mode")
        
        # Find introduction chapter from outline
        intro_chapter = None
        for chapter in outline.get("chapters", []):
            if chapter.get("number") == 1 or "introduction" in chapter.get("title", "").lower():
                intro_chapter = chapter
                break
        
        if not intro_chapter:
            logger.warning("No introduction chapter in outline, creating minimal structure")
            intro_chapter = {
                "number": 1,
                "title": "Introduction",
                "sections": [
                    {"number": "1.1", "title": "Project Overview", "description": "Overview"},
                    {"number": "1.2", "title": "Objectives", "description": "Objectives"},
                    {"number": "1.3", "title": "Report Scope", "description": "Scope"}
                ]
            }
        
        project_name = codebase_structure.get("name", "the project")
        project_type = codebase_structure.get("project_type", "software project")
        
        sections = []
        for section_info in intro_chapter.get("sections", []):
            section_num = section_info.get("number", "1.1")
            section_title = section_info.get("title", "Section")
            section_desc = section_info.get("description", "")
            
            prompt = f"""Write 2-3 paragraphs for the '{section_title}' section of an introduction chapter.

Project: {project_name} ({project_type})
Section Description: {section_desc}

Write professionally without JSON format. Just the paragraph text."""
            
            try:
                content = llm_client.generate(
                    prompt=prompt,
                    system_prompt="You are a technical writer.",
                    temperature=0.5,
                    timeout=600
                )
                
                sections.append({
                    "number": section_num,
                    "title": section_title,
                    "content": content.strip()
                })
                logger.success(f"Section {section_num} written")
                
            except Exception as e:
                logger.warning(f"Failed to generate section {section_num}, using placeholder")
                sections.append({
                    "number": section_num,
                    "title": section_title,
                    "content": f"This section covers {section_desc or section_title.lower()}."
                })
        
        return {
            "chapter_number": 1,
            "chapter_title": intro_chapter.get("title", "Introduction"),
            "sections": sections
        }
    
    def write_section(
        self,
        section_number: str,
        section_title: str,
        section_description: str,
        project_context: Dict[str, Any],
        chapter_context: str = "",
        writing_guideline: str = ""
    ) -> Dict[str, Any]:
        """
        Write individual section content
        
        Args:
            section_number: Section number (e.g., "2.1")
            section_title: Section title
            section_description: What the section should cover
            project_context: Project information
            chapter_context: Context about the chapter
            
        Returns:
            Section content
        """
        logger.info(f"Writing section {section_number}: {section_title}")
        
        # CRITICAL: Extract actual code content from project files
        relevant_files = []
        code_snippets = []
        
        if "files" in project_context:
            # Prioritize main files (entry points, app files, etc.)
            main_file_names = ['app.js', 'main.js', 'index.js', 'app.py', 'main.py', 'index.html', 'app.ts', 'main.ts']
            
            # First pass: collect main files with code
            main_files = []
            other_files = []
            
            for file_info in project_context["files"]:
                if isinstance(file_info, dict):
                    file_path = file_info.get("path") or file_info.get("name") or str(file_info)
                    file_name = file_info.get("name", "")
                    
                    # Check if this file has code content
                    if file_info.get("has_code") and file_info.get("code_snippet"):
                        code_content = file_info.get("code_snippet", "")
                        if file_name.lower() in [m.lower() for m in main_file_names]:
                            main_files.append({
                                "path": file_path,
                                "name": file_name,
                                "code": code_content[:3000]  # Limit to 3000 chars per file
                            })
                        else:
                            other_files.append({
                                "path": file_path,
                                "name": file_name,
                                "code": code_content[:2000]  # Limit to 2000 chars for other files
                            })
                    else:
                        # File without code snippet - just add path
                        relevant_files.append(f"- {file_path}")
            
            # Add main files first (up to 3), then other files (up to 5)
            for file_data in (main_files[:3] + other_files[:5]):
                code_snippets.append(f"""
=== FILE: {file_data['path']} ===
{file_data['code']}
=== END OF FILE ===
""")
                relevant_files.append(f"- {file_data['path']} (code provided below)")
        
        # Format code snippets for prompt
        code_content_section = "\n".join(code_snippets) if code_snippets else "NO CODE CONTENT AVAILABLE - Only file paths are known."
        
        # Add explicit project identification to prevent mixing
        project_name = project_context.get("name", "Project")
        project_type = project_context.get("project_type", "Software")
        
        # Get sample files for explicit identification
        sample_files_str = ", ".join(relevant_files[:5]) if relevant_files else "No files listed"
        
        enhanced_project_context = {
            "name": project_name,
            "technologies": project_context.get("main_technologies", []),
            "type": project_type,
            "_isolation_note": f"THIS IS PROJECT: {project_name} ({project_type}). Write ONLY about this project.",
            "_job_id": self.job_id
        }
        
        # Add writing_guideline to prompt if provided
        guideline_instruction = ""
        if writing_guideline:
            guideline_instruction = f"\n\n🔴 CRITICAL WRITING CONSTRAINT 🔴\n{writing_guideline}\nThis is a MANDATORY constraint, not a suggestion. You MUST follow this guideline exactly.\n"
        
        prompt = WRITE_SECTION_PROMPT.format(
            section_number=section_number,
            section_title=section_title,
            section_description=section_description,
            project_context=json.dumps(enhanced_project_context, indent=2),
            relevant_files="\n".join(relevant_files) if relevant_files else "No specific files",
            actual_code_content=code_content_section
        ) + guideline_instruction
        
        # Add explicit isolation instruction at the start with job_id and file samples
        isolation_header = f"""
🚨 CRITICAL PROJECT ISOLATION 🚨
JOB ID: {self.job_id}
PROJECT NAME: {project_name}
PROJECT TYPE: {project_type}
SECTION: {section_number} - {section_title}
SAMPLE FILES: {sample_files_str}

YOU ARE WRITING CONTENT FOR THIS SPECIFIC PROJECT ONLY.
DO NOT REFERENCE, REUSE, OR MIX CONTENT FROM ANY OTHER PROJECTS.
EVERY PROJECT IS UNIQUE AND MUST BE DOCUMENTED INDEPENDENTLY.

"""
        prompt = isolation_header + prompt
        
        # Retry logic with fallback to plain text
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                section = llm_client.generate_json(
                    prompt=prompt,
                    system_prompt=WRITER_SYSTEM_PROMPT,
                    temperature=0.1
                )
                
                # Validate that section is a dict
                if not isinstance(section, dict):
                    logger.warning(f"LLM returned non-dict section (type: {type(section)}), using plain text fallback")
                    return self._write_section_plain_text(
                        section_number, section_title, section_description, project_context
                    )
                
                # Ensure numbering key exists for builder compatibility
                section["number"] = section.get("section_number", section_number)

                # If model supplied a diagram/table, keep it; otherwise do NOT inject placeholders.
                # This prevents stray placeholders when LLM doesn't intend a diagram.
                
                # Store writing_guideline in section for post-processing
                if writing_guideline:
                    section["writing_guideline"] = writing_guideline
                
                # POST-PROCESSING: Apply hardening rules
                section = self._harden_section_content(section, section_description, project_context)
                
                word_count = len(section.get("content", "").split())
                logger.success(f"Section written: {word_count} words")
                
                return section
                
            except ValueError as e:
                if "Invalid JSON" in str(e) or "Invalid control" in str(e):
                    if attempt < max_attempts - 1:
                        logger.warning(f"JSON parse failed, attempt {attempt + 1}/{max_attempts}, retrying...")
                        continue
                    else:
                        # Final fallback: use plain text generation
                        logger.warning("All JSON attempts failed, using plain text fallback...")
                        return self._write_section_plain_text(
                            section_number, section_title, section_description, project_context
                        )
                else:
                    raise
            except Exception as e:
                logger.error(f"Failed to write section {section_number}: {e}")
                raise
    
    def _harden_section_content(
        self,
        section: Dict[str, Any],
        section_description: str,
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post-process section content to eliminate speculation and enforce evidence-based writing.
        This is a MANDATORY safety pass that removes speculative language.
        """
        content = section.get("content", "")
        if not content:
            return section
        
        # Get writing guideline from outline if available
        writing_guideline = section.get("writing_guideline", "")
        section_title = section.get("title", "").lower()
        
        # 3️⃣ SPECIAL HANDLING FOR FUTURE ENHANCEMENTS
        # Future sections are explicitly hypothetical - do NOT apply speculative rewriting
        is_future_section = "future" in section_title or "enhancement" in section_title
        if is_future_section:
            # Only remove mechanical repetition, don't apply speculative bans
            content = self._remove_repetition(content)
            section["content"] = content
            # Process subsections
            if "subsections" in section and isinstance(section["subsections"], list):
                for subsection in section["subsections"]:
                    if isinstance(subsection, dict) and "content" in subsection:
                        subsection["content"] = self._remove_repetition(subsection["content"])
            return section
        
        # 1️⃣ BAN SPECULATIVE LANGUAGE
        speculative_terms = [
            r'\blikely\b', r'\bprobably\b', r'\bappears to\b', r'\bseems to\b',
            r'\bwould\b', r'\bcould\b', r'\bmight\b', r'\btypically\b',
            r'\bpresumably\b', r'\bpossibly\b', r'\bperhaps\b', r'\bmay\b',
            r'\bsuggests\b', r'\bimplies\b', r'\bindicates\b'
        ]
        
        import re
        sentences = re.split(r'[.!?]+\s+', content)
        hardened_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # Check for speculative terms
            has_speculation = any(re.search(term, sentence, re.IGNORECASE) for term in speculative_terms)
            
            if has_speculation:
                # Try to rewrite the sentence to be factual
                # Remove speculative qualifiers and make direct statements
                sentence_cleaned = sentence
                for term in speculative_terms:
                    pattern = re.compile(term, re.IGNORECASE)
                    sentence_cleaned = pattern.sub('', sentence_cleaned)
                
                # If sentence becomes too vague after removing speculation, make it explicitly about absence
                if len(sentence_cleaned.strip()) < 20 or 'would' in sentence.lower() or 'could' in sentence.lower():
                    # Replace with explicit absence statement (NOT failure description)
                    if 'error' in sentence.lower() or 'validation' in sentence.lower():
                        sentence_cleaned = "The current implementation does not include logic to intercept invalid expressions."
                    elif 'feature' in sentence.lower() or 'functionality' in sentence.lower():
                        sentence_cleaned = "This feature is not explicitly implemented in the current codebase."
                    else:
                        # Skip speculative sentences entirely
                        logger.warning(f"Removed speculative sentence: {sentence[:50]}...")
                        continue
                else:
                    sentence_cleaned = sentence_cleaned.strip()
                    # Clean up double spaces
                    sentence_cleaned = re.sub(r'\s+', ' ', sentence_cleaned)
                    # Ensure sentence starts with capital
                    if sentence_cleaned:
                        sentence_cleaned = sentence_cleaned[0].upper() + sentence_cleaned[1:] if len(sentence_cleaned) > 1 else sentence_cleaned.upper()
                
                hardened_sentences.append(sentence_cleaned)
            else:
                hardened_sentences.append(sentence)
        
        # Rejoin sentences
        hardened_content = '. '.join(hardened_sentences)
        # Fix spacing after periods
        hardened_content = re.sub(r'\.\s*\.', '.', hardened_content)
        hardened_content = re.sub(r'\.\s+\.', '. ', hardened_content)
        
        # 1️⃣ DISTINGUISH ABSENCE FROM OBSERVED FAILURE
        # Replace over-assertive failure claims with absence statements
        # Only replace if the sentence describes a consequence, not if it's conditional/hypothetical
        failure_claims = [
            (r'will\s+throw\s+(?:an?\s+)?(?:unhandled\s+)?exception', 'does not include logic to handle'),
            (r'throws?\s+(?:an?\s+)?(?:unhandled\s+)?exception\s+(?:when|if|for)', 'does not include logic to handle'),
            (r'will\s+crash', 'does not include logic to prevent'),
            (r'crashes?\s+(?:when|if|for)', 'does not include logic to prevent'),
            (r'will\s+produce\s+incorrect\s+results?', 'does not include validation to ensure'),
            (r'produces?\s+incorrect\s+results?\s+(?:when|if|for)', 'does not include validation to ensure'),
            (r'fails?\s+silently\s+(?:when|if|for)', 'does not provide feedback for'),
            (r'disrupts?\s+the\s+user\s+experience\s+(?:when|if|for)', 'does not include safeguards to maintain')
        ]
        for pattern, replacement in failure_claims:
            hardened_content = re.sub(pattern, replacement, hardened_content, flags=re.IGNORECASE)
        
        # Also catch standalone failure claims (not conditional)
        standalone_failures = [
            (r'\bthrows?\s+(?:an?\s+)?(?:unhandled\s+)?exception\b(?!\s+(?:when|if|would|could))', 'does not include logic to handle exceptions'),
            (r'\bcrashes?\b(?!\s+(?:when|if|would|could))', 'does not include logic to prevent crashes'),
        ]
        for pattern, replacement in standalone_failures:
            # Only replace if it's in a sentence about the application/implementation
            if re.search(r'(?:application|implementation|system)', hardened_content, re.IGNORECASE):
                hardened_content = re.sub(pattern, replacement, hardened_content, flags=re.IGNORECASE)
        
        # 2️⃣ REMOVE MECHANICAL REPETITION
        hardened_content = self._remove_repetition(hardened_content)
        
        # 2️⃣ ENFORCE WRITING_GUIDELINE
        if writing_guideline:
            # Check if content violates guideline
            guideline_lower = writing_guideline.lower()
            
            if "avoid architectural assumptions" in guideline_lower:
                # Remove architectural language
                architectural_terms = [
                    r'\barchitecture\b', r'\bdesigned to\b', r'\bintended to\b',
                    r'\bstrategy\b', r'\bpattern\b', r'\bframework\b'
                ]
                for term in architectural_terms:
                    pattern = re.compile(term, re.IGNORECASE)
                    if pattern.search(hardened_content):
                        # Replace with observational language
                        hardened_content = pattern.sub('implementation', hardened_content)
            
            if "observable interactions only" in guideline_lower:
                # Remove speculative interaction descriptions
                speculative_interaction = [
                    r'\busers may\b', r'\busers can\b', r'\busers might\b'
                ]
                for term in speculative_interaction:
                    pattern = re.compile(term, re.IGNORECASE)
                    hardened_content = pattern.sub('the interface allows', hardened_content)
        
        # 3️⃣ REMOVE SUBJECTIVE PRAISE (but allow grounded UI descriptions)
        praise_phrases = [
            r'\belegant\b', r'\bintuitive\b', r'\buser-friendly\b',
            r'\bseamless\b', r'\bsmooth\b', r'\bpolished\b'
        ]
        for phrase in praise_phrases:
            pattern = re.compile(phrase, re.IGNORECASE)
            if pattern.search(hardened_content):
                # Replace with factual description
                hardened_content = pattern.sub('functional', hardened_content)
        
        # 4️⃣ ALLOW GROUNDED UI DESCRIPTIONS
        # These are observable from HTML/CSS, so they're acceptable:
        # "follows a familiar calculator layout" - OK (observable)
        # "uses a grid-based arrangement" - OK (observable)
        # "maintains consistent spacing" - OK (observable from CSS)
        # No changes needed here - these are already acceptable
        
        # 5️⃣ PRESERVE HUMAN RHYTHM
        # After all safety passes, ensure natural sentence variation
        hardened_content = self._preserve_human_rhythm(hardened_content)
        
        # 6️⃣ FINAL MICRO-FIXES (PRECISION DISCIPLINE PASS)
        # Apply after all existing hardening - this is the final freeze pass
        hardened_content = self._apply_final_micro_fixes(hardened_content)
        
        # Update section content
        section["content"] = hardened_content
        
        # Process subsections if present
        if "subsections" in section and isinstance(section["subsections"], list):
            for subsection in section["subsections"]:
                if isinstance(subsection, dict) and "content" in subsection:
                    # Create a temporary section dict for hardening with writing_guideline
                    temp_subsection = {"content": subsection["content"], "title": subsection.get("title", "")}
                    if writing_guideline:
                        temp_subsection["writing_guideline"] = writing_guideline
                    hardened_subsection = self._harden_section_content(
                        temp_subsection, section_description, project_context
                    )
                    subsection["content"] = hardened_subsection.get("content", subsection["content"])
        
        # Also apply final micro-fixes to table_data if present (for consequence claims in tables)
        if "table_data" in section and isinstance(section["table_data"], list):
            for row in section["table_data"]:
                if isinstance(row, list):
                    for cell_idx, cell in enumerate(row):
                        if isinstance(cell, str):
                            row[cell_idx] = self._apply_final_micro_fixes(cell)
        
        return section
    
    def _remove_repetition(self, content: str) -> str:
        """
        Remove mechanical repetition while preserving natural human rhythm.
        Detects repeated or near-identical sentences and collapses them.
        """
        import re
        sentences = re.split(r'[.!?]+\s+', content)
        if len(sentences) < 2:
            return content
        
        # Track seen sentences (normalized for comparison)
        seen_sentences = []
        unique_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # Normalize sentence for comparison (lowercase, remove extra spaces)
            normalized = re.sub(r'\s+', ' ', sentence.lower().strip())
            
            # Check if this sentence is too similar to a previous one (80% similarity)
            is_duplicate = False
            for seen in seen_sentences:
                # Simple similarity check: if sentences share most words, consider duplicate
                seen_words = set(seen.split())
                current_words = set(normalized.split())
                if len(seen_words) > 0 and len(current_words) > 0:
                    similarity = len(seen_words & current_words) / max(len(seen_words), len(current_words))
                    if similarity > 0.8:  # 80% word overlap
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                seen_sentences.append(normalized)
                unique_sentences.append(sentence)
            else:
                logger.info(f"Removed duplicate sentence: {sentence[:50]}...")
        
        # Rejoin sentences
        result = '. '.join(unique_sentences)
        # Fix spacing
        result = re.sub(r'\.\s*\.', '.', result)
        result = re.sub(r'\.\s+\.', '. ', result)
        return result
    
    def _preserve_human_rhythm(self, content: str) -> str:
        """
        Preserve natural human rhythm after hardening.
        Mixes sentence lengths, allows mild redundancy, avoids overly formal tone.
        """
        import re
        sentences = re.split(r'[.!?]+\s+', content)
        if len(sentences) < 2:
            return content
        
        # Ensure sentence length variation (don't make all sentences the same length)
        # This is already handled by the LLM, but we can verify
        
        # Remove overly formal transitions if they appear too frequently
        formal_transitions = [r'\bconsequently\b', r'\bfurthermore\b', r'\bmoreover\b']
        transition_count = sum(1 for trans in formal_transitions for sent in sentences if re.search(trans, sent, re.IGNORECASE))
        
        # If too many formal transitions, replace some with simpler ones
        if transition_count > len(sentences) * 0.3:  # More than 30% of sentences
            # Replace some formal transitions with simpler ones
            content = re.sub(r'\bconsequently\b', 'as a result', content, flags=re.IGNORECASE, count=2)
            content = re.sub(r'\bfurthermore\b', 'additionally', content, flags=re.IGNORECASE, count=2)
        
        return content
    
    def _apply_final_micro_fixes(self, content: str) -> str:
        """
        FINAL CLEANUP PASS: Strict elimination of consequence verbs, UI experiential language, and grammar errors.
        This is the final freeze pass - fixes ONLY the three specified issues without any other modifications.
        """
        import re
        
        # 1️⃣ CONSEQUENCE VERB ELIMINATION (CONTEXT-AWARE)
        # Apply consequence patterns, then fix incorrect replacements of legitimate actions
        
        # Comprehensive consequence verb patterns
        consequence_patterns = [
            # "may/might/can/will/would/could cause"
            (r'\b(?:may|might|can|will|would|could)\s+(?:cause|causes|caused)\s+', 'does not include logic to prevent '),
            # "result in / results in / resulted in"
            (r'\b(?:may|might|can|will|would|could)?\s*(?:result\s+in|results\s+in|resulted\s+in)\s+', 'does not include logic to prevent '),
            # "produce / produces / produced"
            (r'\b(?:may|might|can|will|would|could)?\s*(?:produce|produces|produced)\s+(?:incorrect|invalid|NaN|Infinity|errors?)', 
             'does not include validation to ensure '),
            # "lead to / leads to / led to"
            (r'\b(?:may|might|can|will|would|could)?\s*(?:lead\s+to|leads\s+to|led\s+to)\s+', 'does not include safeguards to prevent '),
            # "throw / throws / thrown (exceptions)"
            (r'\b(?:may|might|can|will|would|could)?\s*(?:throw|throws|thrown)\s+(?:an?\s+)?(?:unhandled\s+)?exceptions?', 
             'does not include logic to handle exceptions'),
            # "crash / crashes / crashed"
            (r'\b(?:may|might|can|will|would|could)?\s*(?:crash|crashes|crashed)\s*', 'does not include logic to prevent crashes'),
            # "error / errors" as outcomes (when used as consequences)
            (r'\b(?:runtime\s+)?errors?\s+(?:may|might|can|will|would|could)?\s+(?:occur|be\s+thrown|result)', 
             'error handling is not implemented'),
            # "NaN" or "Infinity" as results
            (r'\b(?:produces?|returns?)\s+(?:NaN|Infinity)', 
             'does not include validation to prevent invalid numeric results'),
            # "fail / fails / failed"
            (r'\b(?:may|might|can|will|would|could)?\s*(?:fail|fails|failed)\s+(?:silently|to\s+handle|to\s+validate)', 
             'does not provide feedback for'),
            # "trigger / triggers / triggered" - ONLY in error contexts
            # (We fix legitimate uses below)
            # "generate / generates / generated"
            (r'\b(?:may|might|can|will|would|could)?\s*(?:generate|generates|generated)\s+(?:errors?|exceptions?)', 
             'does not include logic to prevent '),
            # "exposes ... to potential runtime errors" or "exposes ... to errors"
            (r'\bexposes?\s+(?:the\s+)?(?:application|implementation|system)\s+to\s+(?:potential\s+)?(?:runtime\s+)?errors?', 
             'does not include logic to prevent runtime errors'),
        ]
        
        # Apply consequence patterns
        for pattern, replacement in consequence_patterns:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Catch context-specific consequence phrases
        context_consequences = [
            # "invalid input may cause"
            (r'\binvalid\s+(?:input|expressions?|values?)\s+(?:may|might|can|will|would|could)?\s*(?:cause|result\s+in|trigger)', 
             'invalid input is not intercepted by'),
            # "malformed expressions may cause"
            (r'\bmalformed\s+(?:expressions?|input)\s+(?:may|might|can|will|would|could)?\s*(?:cause|result\s+in)', 
             'malformed expressions are not intercepted by'),
            # "application/system may crash/fail"
            (r'\b(?:application|implementation|system)\s+(?:may|might|can|will|would|could)?\s*(?:crash|fail|throw)', 
             'does not include safeguards to prevent'),
        ]
        for pattern, replacement in context_consequences:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Also catch standalone consequence verbs in error context
        if re.search(r'(?:error|validation|input|invalid|exception|crash|fail)', content, re.IGNORECASE):
            # Remove standalone "cause", "result in", etc. when clearly about consequences
            standalone_verbs = [
                (r'\bcause\s+(?:runtime\s+)?errors?', 'does not include logic to prevent errors'),
                (r'\bresult\s+in\s+incorrect', 'does not include validation to ensure correct'),
                (r'\bproduces?\s+NaN', 'does not include validation to prevent NaN'),
                (r'\bproduces?\s+Infinity', 'does not include validation to prevent Infinity'),
                # "Runtime errors for" (common in table cells)
                (r'\bRuntime\s+errors?\s+for', 'does not include logic to prevent errors for'),
                (r'\bruntime\s+errors?\s+for', 'does not include logic to prevent errors for'),
            ]
            for pattern, replacement in standalone_verbs:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Catch "may not gracefully handle" in Future Enhancements or anywhere
        content = re.sub(r'\bmay\s+not\s+gracefully\s+handle', 'does not include logic to handle gracefully', content, flags=re.IGNORECASE)
        
        # CRITICAL FIX: Remove incorrect "does not include logic to prevent" replacements for legitimate actions
        # These should describe what code DOES, not what it fails to prevent
        legitimate_action_fixes = [
            # "does not include logic to prevent a callback function" -> "triggers/calls a callback function"
            (r'\bdoes\s+not\s+include\s+logic\s+to\s+prevent\s+(?:a\s+)?callback\s+function', 'triggers a callback function', re.IGNORECASE),
            # "does not include logic to prevent an evaluation" -> "triggers/performs an evaluation"  
            (r'\bdoes\s+not\s+include\s+logic\s+to\s+prevent\s+(?:an\s+)?evaluation', 'triggers an evaluation', re.IGNORECASE),
            # "does not include logic to prevent an update" -> "triggers an update"
            (r'\bdoes\s+not\s+include\s+logic\s+to\s+prevent\s+(?:an\s+)?update', 'triggers an update', re.IGNORECASE),
            # "does not include logic to prevent real time" -> "updates in real time"
            (r'\bdoes\s+not\s+include\s+logic\s+to\s+prevent\s+real\s+time', 'updates in real time', re.IGNORECASE),
            # "does not include logic to prevent a function" -> "calls/triggers a function"
            (r'\bdoes\s+not\s+include\s+logic\s+to\s+prevent\s+(?:a\s+)?function', 'triggers a function', re.IGNORECASE),
            # "does not include logic to prevent an operation" -> "performs an operation"
            (r'\bdoes\s+not\s+include\s+logic\s+to\s+prevent\s+(?:an\s+)?operation', 'performs an operation', re.IGNORECASE),
            # Fix broken "does not include logic to prevent logic to prepare"
            (r'\bdoes\s+not\s+include\s+logic\s+to\s+prevent\s+logic\s+to\s+prepare', 'prepares', re.IGNORECASE),
        ]
        for pattern, replacement, flags in legitimate_action_fixes:
            content = re.sub(pattern, replacement, content, flags=flags)
        
        # Fix merged words from consequence replacements (e.g., "typesdoes" -> "types does")
        content = re.sub(r'(\w+)(does\s+not\s+include)', r'\1 \2', content, flags=re.IGNORECASE)
        content = re.sub(r'(\w+)(does\s+not\s+provide)', r'\1 \2', content, flags=re.IGNORECASE)
        content = re.sub(r'(\w+)(does\s+not\s+prevent)', r'\1 \2', content, flags=re.IGNORECASE)
        
        # 2️⃣ UI EXPERIENTIAL LANGUAGE PURGE (ABSOLUTE)
        # Remove ALL experiential, aesthetic, or subjective UI language
        
        # Check if content is about UI/interface/design
        is_ui_context = bool(re.search(r'(?:interface|ui|design|layout|appearance|styling|user\s+experience|button|display|screen)', content, re.IGNORECASE))
        
        if is_ui_context:
            # ABSOLUTELY FORBIDDEN terms (even mild ones)
            forbidden_ui_terms = [
                (r'\bvisually\s+(?:distinct|appealing|pleasing|clear)', ''),
                (r'\bvisually\b', ''),
                (r'\bfocused\s+experience\b', 'layout'),
                (r'\btactile\b', ''),
                (r'\bfeel\s+(?:of|like)', ''),
                (r'\bfeels?\s+(?:responsive|engaging|smooth|polished)', ''),
                (r'\bfeeling\b', ''),
                (r'\bengaging\b', ''),
                (r'\bappealing\b', ''),
                (r'\bvisual\s+appeal\b', ''),
                (r'\bmodern\b', ''),
                (r'\bminimalist\b', ''),
                (r'\bminimalism\b', ''),
                (r'\belegant\b', ''),
                (r'\bintuitive\b', ''),
                (r'\buser-friendly\b', ''),
                (r'\bsmooth\b', 'consistent'),
                (r'\bpolished\b', ''),
                (r'\bwell-designed\b', ''),
                (r'\bclean\s+design\b', 'consistent layout'),
                (r'\bprofessional\s+appearance\b', 'consistent styling'),
                (r'\baesthetically\s+(?:pleasing|appealing)', ''),
                (r'\baesthetic\b', ''),
                (r'\baesthetically\b', ''),
                (r'\bpleasing\s+(?:to\s+the\s+eye|visually)', ''),
                (r'\bintuitively\b', ''),
            ]
            
            for pattern, replacement in forbidden_ui_terms:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            
            # Fix broken phrases with missing words (e.g., "creating a , aesthetic" -> "creating a")
            content = re.sub(r',\s*,', ',', content)  # Fix double commas
            content = re.sub(r'\b(\w+)\s+,\s+aesthetic\b', r'\1', content, flags=re.IGNORECASE)
            content = re.sub(r',\s+aesthetic\b', '', content, flags=re.IGNORECASE)  # Handle ", aesthetic" standalone
            content = re.sub(r'\bis\s+,\s+', 'is ', content, flags=re.IGNORECASE)
            # Fix "creating a , slightly" -> "creating a slightly" (comma before word after article)
            # Only fix commas that are clearly artifacts from word removal (after "a", "an", "the")
            content = re.sub(r'\b(a|an|the)\s+,\s+(\w+)', r'\1 \2', content, flags=re.IGNORECASE)
            # Fix "clean and styling" -> "clean styling" (missing word after "and")
            content = re.sub(r'\bclean\s+and\s+styling\b', 'clean styling', content, flags=re.IGNORECASE)
            # Fix "professional ." -> "professional appearance."
            content = re.sub(r'\bprofessional\s+\.', 'professional appearance.', content, flags=re.IGNORECASE)
            # Also fix standalone leading commas before words (but preserve in lists/numbers)
            # Only if it's clearly a broken phrase (comma followed by lowercase word at start of phrase)
            content = re.sub(r'\s+,\s+([a-z])', r' \1', content)  # Fix spacing before comma + lowercase word
            
            # Clean up double spaces created by removals
            content = re.sub(r'\s{2,}', ' ', content)
        
        # 3️⃣ STRICT GRAMMAR CORRECTION (NO STYLE CHANGES)
        # Fix ONLY clear grammar errors: missing verbs, broken clauses, subject-verb agreement
        
        sentences = re.split(r'[.!?]+\s+', content)
        fixed_sentences = []
        
        for sentence in sentences:
            if not sentence.strip():
                fixed_sentences.append(sentence)
                continue
            
            sentence_lower = sentence.lower().strip()
            words = sentence.split()
            fixed_sentence = sentence
            
            # Fix ONLY objectively broken English patterns
            
            # Pattern 1: Missing "that" in noun phrases (e.g., "application implementation performs" -> "application implementation that performs")
            # Only fix when it's clearly a noun phrase followed by a verb without "that"
            # Match: "[adj]? application/system/tool/service implementation performs" -> add "that"
            missing_that_fixes = [
                # Pattern: (optional article/adjective) + noun + implementation/application + verb
                # Generic pattern - works for any project type (web, backend, CLI, etc.)
                (r'\b((?:a|an|the|browser-based|web-based|standalone)\s+)?(application|system|tool|service|module|component|framework)\s+(implementation|application|system)\s+(performs?|processes?|handles?|displays?|shows?|demonstrates?|provides?|uses?|includes?|supports?|allows?)\s+', 
                 r'\1\2 \3 that \4 ', re.IGNORECASE),
            ]
            for pattern, replacement, flags in missing_that_fixes:
                # Only fix if "that" doesn't already exist before the verb
                if not re.search(r'\b(?:implementation|application|system|tool|service)\s+that\s+(?:performs?|processes?|handles?)', fixed_sentence, flags=re.IGNORECASE):
                    fixed_sentence = re.sub(pattern, replacement, fixed_sentence, flags=flags)
            
            # Pattern 1b: Subject-verb agreement (e.g., "implementation perform" -> "implementation performs")
            subject_verb_fixes = [
                (r'\b(implementation|application|system|tool)\s+that\s+(perform|process|handle|display|show)\s+', 
                 r'\1 that \2s ', re.IGNORECASE),
                (r'\b(implementation|application|system)\s+(perform|process|handle|display|show)\s+', 
                 r'\1 \2s ', re.IGNORECASE),
                (r'\b(implementations|applications|systems)\s+(performs|processes|handles|displays|shows)\s+', 
                 r'\1 perform ', re.IGNORECASE),
                # "application include" -> "application includes"
                (r'\b(application|implementation|system|project)\s+include\s+', 
                 r'\1 includes ', re.IGNORECASE),
                # "a user click" -> "a user clicks" or "users click"
                (r'\ba\s+user\s+click\s+', 'users click ', re.IGNORECASE),
                # "text overflow" -> "text overflows"
                (r'\btext\s+overflow\s+', 'text overflows ', re.IGNORECASE),
            ]
            for pattern, replacement, flags in subject_verb_fixes:
                fixed_sentence = re.sub(pattern, replacement, fixed_sentence, flags=flags)
            
            # Pattern 2: "allows [verb]" -> "allows users to [verb]"
            allows_fixes = [
                # "the interface allows [verb]" -> "the interface allows users to [verb]"
                (r'\b(the\s+interface|the\s+application|the\s+system)\s+allows\s+(click|verify|input|perform|select|enter|view|access|use|choose)\s+', 
                 r'\1 allows users to \2 ', re.IGNORECASE),
                # "allows [verb]" -> "allows users to [verb]" (standalone)
                (r'\ballows?\s+(click|verify|input|perform|select|enter|view|access|use|choose)\s+', 
                 r'allows users to \1 ', re.IGNORECASE),
            ]
            for pattern, replacement, flags in allows_fixes:
                # Only apply if "users to" doesn't already exist
                if not re.search(r'\ballows\s+users\s+to', fixed_sentence, flags=re.IGNORECASE):
                    fixed_sentence = re.sub(pattern, replacement, fixed_sentence, flags=flags)
            
            # Pattern 2b: Broken clauses - fix only if clearly broken (avoid over-correction)
            # Fix "has a application" -> "has an application" or "application uses"
            fixed_sentence = re.sub(r'\bhas\s+a\s+(application|implementation)\s+(uses?|performs?|handles?)', 
                                   r'\1 \2', fixed_sentence, flags=re.IGNORECASE)
            
            # Fix "separates has a" -> "separates the"
            fixed_sentence = re.sub(r'\bseparates\s+has\s+a\s+', 'separates the ', fixed_sentence, flags=re.IGNORECASE)
            
            # Fix "operator buttons be from" -> "operator buttons are distinguished from"
            fixed_sentence = re.sub(r'\boperator\s+buttons\s+be\s+from\s+digit', 
                                   'operator buttons are distinguished from digit', fixed_sentence, flags=re.IGNORECASE)
            
            # Fix standard broken clauses (but be more careful)
            broken_clause_fixes = [
                # Only fix if there's no verb between noun and article
                (r'\b(application|implementation|system)\s+fail\s+(silently)', 
                 r'\1 fails silently', re.IGNORECASE),
            ]
            for pattern, replacement, flags in broken_clause_fixes:
                if re.search(pattern, fixed_sentence, flags):
                    fixed_sentence = re.sub(pattern, replacement, fixed_sentence, flags=flags)
            
            # Pattern 2c: Broken phrases with "keeps has" (generic - works for any context)
            fixed_sentence = re.sub(r'\bkeeps\s+has\s+(?:a\s+)?\w+\s+\w+\b', 'keeps', fixed_sentence, flags=re.IGNORECASE)
            fixed_sentence = re.sub(r'\bkeeps\s+has\b', 'keeps', fixed_sentence, flags=re.IGNORECASE)
            
            # Pattern 2d: Missing "does not" (e.g., "interface not scale" -> "interface does not scale")
            missing_does_not = [
                (r'\b(interface|application|implementation|system|codebase)\s+not\s+(scale|align|implement|provide)', 
                 r'\1 does not \2', re.IGNORECASE),
                (r'\bwhich\s+not\s+align\b', 'which does not align', re.IGNORECASE),
            ]
            for pattern, replacement, flags in missing_does_not:
                fixed_sentence = re.sub(pattern, replacement, fixed_sentence, flags=flags)
            
            # Pattern 2e: Missing verb in "that be difficult" -> "that may be difficult" or "that is difficult"
            fixed_sentence = re.sub(r'\bthat\s+be\s+difficult\b', 'that may be difficult', fixed_sentence, flags=re.IGNORECASE)
            
            # Pattern 3: Missing space after period before capital (but not in abbreviations)
            fixed_sentence = re.sub(r'\.([A-Z])', r'. \1', fixed_sentence)
            
            # DO NOT fix:
            # - Sentence rhythm variations
            # - Mild redundancy
            # - Intentional fragments
            # - Stylistic choices
            
            fixed_sentences.append(fixed_sentence)
        
        content = '. '.join(fixed_sentences)
        
        # Final spacing cleanup (only technical fixes)
        content = re.sub(r'\.\s*\.', '.', content)
        content = re.sub(r'\.\s+\.', '. ', content)
        content = re.sub(r'\s{2,}', ' ', content)
        
        return content.strip()
    
    def _write_section_plain_text(
        self,
        section_number: str,
        section_title: str,
        section_description: str,
        project_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback: Generate section content as plain text without JSON parsing
        """
        logger.info(f"Using plain text generation for {section_number}")
        
        simple_prompt = f"""Write 2-3 paragraphs about: {section_title}

Context: This is for a {project_context.get('project_type', 'software')} project called {project_context.get('name', 'the project')}.

What to cover: {section_description}

Write clear, professional paragraphs. Do NOT use JSON format. Just write the text content directly."""
        
        try:
            content = llm_client.generate(
                prompt=simple_prompt,
                system_prompt="You are a technical writer. Write clear, professional documentation in paragraph form.",
                temperature=0.5,
                timeout=600
            )
            
            # Clean up the content
            content = content.strip()
            
            logger.success(f"Plain text section generated: {len(content.split())} words")
            
            return {
                "section_number": section_number,
                "title": section_title,
                "content": content,
                "word_count": len(content.split())
            }
            
        except Exception as e:
            logger.error(f"Plain text generation also failed: {e}")
            # Ultimate fallback: return placeholder
            return {
                "section_number": section_number,
                "title": section_title,
                "content": f"This section covers {section_title.lower()}. [Content generation failed - please review manually]",
                "word_count": 10
            }
    
    def write_conclusion(
        self,
        outline: Dict[str, Any],
        codebase_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Write conclusion chapter based on the outline
        
        Returns:
            Chapter content with sections
        """
        logger.info("Writing Conclusion chapter...")
        
        # Find the conclusion chapter from outline
        conclusion_chapter = None
        for chapter in outline.get("chapters", []):
            if "conclusion" in chapter.get("title", "").lower() or chapter.get("number") == len(outline.get("chapters", [])):
                conclusion_chapter = chapter
                break
        
        if not conclusion_chapter:
            logger.warning("No conclusion chapter found in outline, using fallback")
            conclusion_chapter = {
                "number": len(outline.get("chapters", [])) or 1,
                "title": "Conclusion",
                "sections": [
                    {"number": "", "title": "Project Summary", "description": "Summary of achievements"},
                    {"number": "", "title": "Future Work", "description": "Future enhancements"}
                ]
            }
        
        project_summary = {
            "name": codebase_structure.get("name", "Project"),
            "type": codebase_structure.get("project_type", "Software Project"),
            "achievements": f"Developed a complete {codebase_structure.get('project_type', 'software')} solution"
        }
        
        technologies = codebase_structure.get("main_technologies", [])
        features = codebase_structure.get("key_components", [])
        
        # Extract code snippets for conclusion
        code_snippets = self._extract_code_snippets(codebase_structure, max_files=3)
        
        # Convert to strings if they're dicts
        def to_string_list(items):
            """Convert list items to strings, handling both strings and dicts"""
            result = []
            for item in items:
                if isinstance(item, dict):
                    # Extract name or description from dict
                    result.append(item.get("name") or item.get("description") or str(item))
                elif isinstance(item, str):
                    result.append(item)
                else:
                    result.append(str(item))
            return result
        
        technologies_str = ", ".join(to_string_list(technologies)) if technologies else "N/A"
        features_str = ", ".join(to_string_list(features)) if features else "Core functionality"
        
        # Format conclusion sections for the prompt
        conclusion_sections_text = json.dumps(conclusion_chapter.get("sections", []), indent=2)
        last_chapter_num = conclusion_chapter.get("number", len(outline.get("chapters", [])) or 1)
        
        # Get sample files for explicit identification
        sample_files = []
        if "files" in codebase_structure:
            sample_files = [f.get('path', str(f)) for f in codebase_structure["files"][:5]]
        sample_files_str = ", ".join(sample_files) if sample_files else "No files listed"
        
        prompt = WRITE_CONCLUSION_PROMPT.format(
            project_summary=json.dumps(project_summary, indent=2),
            technologies=technologies_str,
            features=features_str,
            conclusion_sections=conclusion_sections_text,
            chapter_number=last_chapter_num,
            chapter_title=conclusion_chapter.get("title", "Conclusion"),
            actual_code_content=code_snippets
        )
        
        # Add explicit isolation instruction with job_id and file samples
        isolation_header = f"""
🚨 CRITICAL PROJECT ISOLATION 🚨
JOB ID: {self.job_id}
PROJECT NAME: {project_summary.get("name", "Unknown")}
PROJECT TYPE: {project_summary.get("type", "Unknown")}
CHAPTER: Conclusion
SAMPLE FILES: {sample_files_str}

YOU ARE WRITING THE CONCLUSION FOR THIS SPECIFIC PROJECT ONLY.
DO NOT REFERENCE, REUSE, OR MIX CONTENT FROM ANY OTHER PROJECTS.
EVERY PROJECT IS UNIQUE AND MUST BE DOCUMENTED INDEPENDENTLY.

"""
        prompt = isolation_header + prompt

        # Retry logic with plain text fallback
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                chapter = llm_client.generate_json(
                    prompt=prompt,
                    system_prompt=WRITER_SYSTEM_PROMPT,
                    temperature=0.1
                )
                # Validate that chapter is a dict
                if not isinstance(chapter, dict):
                    logger.warning(f"LLM returned non-dict conclusion chapter (type: {type(chapter)}), using plain text fallback")
                    return self._write_conclusion_plain_text(codebase_structure, outline)
                
                # Normalise chapter metadata
                last_chapter_num = len(outline.get("chapters", [])) or 1
                chapter["chapter_number"] = last_chapter_num
                chapter["chapter_title"] = chapter.get("chapter_title", "CONCLUSION")

                # Get conclusion chapter from outline for writing_guidelines
                conclusion_chapter_from_outline = None
                for ch in outline.get("chapters", []):
                    if "conclusion" in ch.get("title", "").lower() or ch.get("number") == len(outline.get("chapters", [])):
                        conclusion_chapter_from_outline = ch
                        break

                # Normalise sections: ensure proper titles and blank numbering in conclusion
                normalised_sections = []
                sections = chapter.get("sections", [])
                if not isinstance(sections, list):
                    logger.warning(f"Conclusion chapter sections is not a list (type: {type(sections)}), setting to empty list")
                    sections = []
                    chapter["sections"] = []
                
                for idx, sec in enumerate(sections, start=1):
                    # Ensure sec is a dict
                    if not isinstance(sec, dict):
                        logger.warning(f"Section {idx} is not a dict (type: {type(sec)}), skipping")
                        continue
                    title = sec.get("title") or sec.get("section_name", "Section")
                    content = sec.get("content", "")
                    
                    # Create section dict for hardening
                    section_dict = {
                        "number": "",
                        "title": title,
                        "content": content,
                        "table_data": sec.get("table_data"),
                        "mermaid_code": sec.get("mermaid_code"),
                        "figure_label": sec.get("figure_label"),
                        "figure_desc": sec.get("figure_desc"),
                    }
                    
                    # Find writing_guideline from outline
                    outline_section = None
                    if conclusion_chapter_from_outline:
                        for outline_sec in conclusion_chapter_from_outline.get("sections", []):
                            if outline_sec.get("title", "") == title:
                                outline_section = outline_sec
                                break
                    
                    if outline_section:
                        section_dict["writing_guideline"] = outline_section.get("writing_guideline", "")
                    
                    # Apply hardening (Future Enhancements will be handled specially)
                    hardened_section = self._harden_section_content(section_dict, "", codebase_structure)
                    
                    normalised_sections.append(hardened_section)

                chapter["sections"] = normalised_sections

                logger.success(f"Conclusion written: {len(chapter.get('sections', []))} sections")
                return chapter
                
            except ValueError as e:
                if ("Invalid JSON" in str(e) or "Invalid control" in str(e)):
                    if attempt < max_attempts - 1:
                        logger.warning(f"JSON parse failed, attempt {attempt + 1}/{max_attempts}, retrying...")
                        continue
                    else:
                        logger.warning("All JSON attempts failed, using plain text fallback for conclusion...")
                        return self._write_conclusion_plain_text(codebase_structure, outline)
                else:
                    raise
            except Exception as e:
                logger.error(f"Failed to write conclusion: {e}")
                raise
    
    def _write_conclusion_plain_text(
        self, 
        codebase_structure: Dict[str, Any],
        outline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback for conclusion using plain text - uses outline sections"""
        logger.info("Generating conclusion with plain text mode")
        
        # Find conclusion chapter from outline
        conclusion_chapter = None
        for chapter in outline.get("chapters", []):
            if "conclusion" in chapter.get("title", "").lower() or chapter.get("number") == len(outline.get("chapters", [])):
                conclusion_chapter = chapter
                break
        
        if not conclusion_chapter:
            logger.warning("No conclusion chapter in outline, creating minimal structure")
            conclusion_chapter = {
                "number": len(outline.get("chapters", [])) or 1,
                "title": "Conclusion",
                "sections": [
                    {"number": "", "title": "Project Summary", "description": "Summary"},
                    {"number": "", "title": "Future Work", "description": "Future enhancements"}
                ]
            }
        
        project_name = codebase_structure.get("name", "the project")
        last_chapter_num = conclusion_chapter.get("number", len(outline.get("chapters", [])) or 1)
        
        sections = []
        for section_info in conclusion_chapter.get("sections", []):
            section_title = section_info.get("title", "Section")
            section_desc = section_info.get("description", "")
            
            prompt = f"""Write 2-3 CONCISE paragraphs (200-300 words total) for the '{section_title}' section of a conclusion chapter.

Project: {project_name}
Section Description: {section_desc}

CRITICAL: Keep it brief and focused. Write 2-3 paragraphs maximum, 100-150 words each. Be concise and reflective.

Write professionally without JSON format. Just the paragraph text."""
            
            try:
                content = llm_client.generate(
                    prompt=prompt,
                    system_prompt="You are a technical writer.",
                    temperature=0.5,
                    timeout=600
                )
                
                sections.append({
                    "number": "",  # empty string => no numeric prefix in heading
                    "title": section_title,
                    "content": content.strip()
                })
                logger.success(f"Section {section_title} written")
                
            except Exception as e:
                logger.warning(f"Failed to generate section {section_title}, using placeholder")
                sections.append({
                    "number": "",
                    "title": section_title,
                    "content": f"This section covers {section_desc or section_title.lower()}."
                })
        
        return {
            "chapter_number": last_chapter_num,
            "chapter_title": conclusion_chapter.get("title", "Conclusion"),
            "sections": sections
        }
    
    def write_all_content(
        self,
        outline: Dict[str, Any],
        codebase_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate content for all chapters and sections
        
        Returns:
            Complete content structure
        """
        logger.info("Generating all content...")
        
        content = {
            "report_title": outline.get("report_title", "Technical Report"),
            "chapters": []
        }
        
        chapters = outline.get("chapters", [])
        
        for chapter_info in chapters:
            chapter_num = chapter_info["number"]
            chapter_title = chapter_info["title"]
            
            logger.info(f"\n--- Chapter {chapter_num}: {chapter_title} ---")
            
            # Handle special chapters
            if chapter_num == 1:
                # Introduction
                chapter_content = self.write_introduction(outline, codebase_structure)
            
            elif chapter_num == len(chapters):
                # Conclusion (last chapter)
                chapter_content = self.write_conclusion(outline, codebase_structure)
            
            else:
                # Regular chapters
                chapter_content = {
                    "chapter_number": chapter_num,
                    "chapter_title": chapter_title,
                    "sections": []
                }
                
                for section_info in chapter_info.get("sections", []):
                    # Pass writing_guideline to write_section
                    writing_guideline = section_info.get("writing_guideline", "")
                    
                    section = self.write_section(
                        section_number=section_info["number"],
                        section_title=section_info["title"],
                        section_description=section_info.get("description", ""),
                        project_context=codebase_structure,
                        chapter_context=chapter_title,
                        writing_guideline=writing_guideline
                    )

                    # Only add table/diagram if LLM explicitly provided them
                    # DO NOT force generation - let LLM decide based on content needs
                    # The outline's needs_table/needs_diagram are just suggestions, not requirements
                    
                    # Check if LLM provided table or diagram - if not, don't generate fallbacks
                    has_llm_table = section.get("table_data") is not None
                    has_llm_diagram = section.get("mermaid_code") is not None
                    
                    # Only generate fallback if outline explicitly requires AND LLM didn't provide
                    # But be very conservative - only for truly essential cases
                    section_desc = section_info.get("description", "").lower()
                    section_title_lower = section_info.get("title", "").lower()
                    
                    # REMOVED: No forced table/diagram generation
                    # Only use tables/diagrams if LLM explicitly provides them
                    # The outline's needs_table/needs_diagram are just suggestions, not requirements

                    chapter_content["sections"].append(section)
            
            content["chapters"].append(chapter_content)
        
        # Save content
        output_path = self.output_dir / "chapters_content.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        total_sections = sum(len(ch.get("sections", [])) for ch in content["chapters"])
        logger.success(f"All content generated: {len(content['chapters'])} chapters, {total_sections} sections")
        logger.info(f"Saved to: {output_path}")
        
        return content
    
    def run(
        self,
        outline: Dict[str, Any],
        codebase_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run complete writing pipeline
        
        Returns:
            Complete report content
        """
        logger.info("=== WRITER AGENT STARTED ===")
        
        content = self.write_all_content(outline, codebase_structure)
        
        logger.success("=== WRITER AGENT COMPLETED ===")
        
        return content


# Convenience function
def write_report_content(
    outline: Dict[str, Any],
    codebase_structure: Dict[str, Any],
    job_id: str = None
) -> Dict[str, Any]:
    """
    Generate all report content
    
    Args:
        outline: Report structure from PlannerAgent
        codebase_structure: Project analysis from ParserAgent
        job_id: Optional job ID for isolated output directory
        
    Returns:
        Complete report content
    """
    agent = WriterAgent(job_id=job_id)
    return agent.run(outline, codebase_structure)