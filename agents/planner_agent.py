"""
Planner Agent - Creates report structure and outline
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from utils.llm_client import llm_client
from config.prompts import (
    PLANNER_SYSTEM_PROMPT,
    CREATE_OUTLINE_PROMPT
)


class PlannerAgent:
    """Creates comprehensive report outline based on project analysis"""
    
    def __init__(self, output_dir: str = "outputs/intermediate", job_id: str = None):
        # Create job-specific output directory to prevent content mixing
        if job_id:
            self.output_dir = Path(output_dir) / f"job_{job_id}"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.job_id = job_id
    
    def create_outline(
        self, 
        codebase_structure: Dict[str, Any],
        guidelines_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create report outline with chapters and sections
        
        Args:
            codebase_structure: Analyzed project structure
            guidelines_config: Formatting guidelines
            
        Returns:
            Report outline with chapter/section hierarchy
        """
        logger.info("Creating report outline...")
        
        # Prepare enhanced project summary with all facts
        project_summary = {
            "name": codebase_structure.get("name", "Unknown Project"),
            "type": codebase_structure.get("project_type", "Software Project"),
            "technologies": codebase_structure.get("main_technologies", []),
            "components": codebase_structure.get("key_components", []),
            "complexity": codebase_structure.get("complexity_level", "moderate"),
            # Enhanced: Include modules, use cases, and code content
            "modules": codebase_structure.get("modules", []),
            "use_cases": codebase_structure.get("use_cases", []),
            "project_purpose": codebase_structure.get("project_purpose", ""),
            "code_content": codebase_structure.get("code_content", {}),
            "capabilities": codebase_structure.get("detected_capabilities", []),
            "entry_points": codebase_structure.get("entry_points_detected", [])
        }
        
        # Prepare guidelines summary
        guidelines_summary = {
            "has_structure": "chapters" in str(guidelines_config).lower(),
            "key_sections": guidelines_config.get("_metadata", {})
        }
        
        # Add explicit project isolation warning to the prompt
        project_name = project_summary.get("name", "Unknown Project")
        project_type = project_summary.get("type", "Unknown Type")
        
        # Get sample files for explicit identification
        sample_files = []
        if "files" in codebase_structure:
            sample_files = [f.get('path', str(f)) for f in codebase_structure["files"][:5]]
        sample_files_str = ", ".join(sample_files) if sample_files else "No files listed"
        
        # Create enhanced prompt with explicit project identification
        enhanced_project_summary = {
            **project_summary,
            "_isolation_note": f"THIS IS PROJECT: {project_name} ({project_type}). DO NOT mix with other projects.",
            "_job_id": self.job_id,
            "_sample_files": sample_files
        }
        
        prompt = CREATE_OUTLINE_PROMPT.format(
            project_analysis=json.dumps(enhanced_project_summary, indent=2),
            guidelines_summary=json.dumps(guidelines_summary, indent=2)
        )
        
        # Add explicit isolation instruction at the start with job_id and file samples
        isolation_header = f"""
🚨 CRITICAL PROJECT ISOLATION 🚨
JOB ID: {self.job_id}
PROJECT NAME: {project_name}
PROJECT TYPE: {project_type}
SAMPLE FILES: {sample_files_str}

YOU ARE CREATING AN OUTLINE FOR THIS SPECIFIC PROJECT ONLY. 
DO NOT REFERENCE, REUSE, OR MIX CONTENT FROM ANY OTHER PROJECTS.
EVERY PROJECT IS UNIQUE AND MUST BE DOCUMENTED INDEPENDENTLY.

"""
        prompt = isolation_header + prompt
        
        try:
            outline = llm_client.generate_json(
                prompt=prompt,
                system_prompt=PLANNER_SYSTEM_PROMPT,
                temperature=0.1  # Minimal temperature for maximum JSON stability
            )
            # Validate that outline is actually a dict
            if not isinstance(outline, dict):
                logger.error(f"LLM returned non-dict outline (type: {type(outline)}), using fallback")
                outline = self._build_fallback_outline(codebase_structure, guidelines_config)
        except Exception as e:
            # Hard fallback: build a deterministic outline to guarantee no pipeline failures
            logger.error(f"Failed to create outline via LLM: {e}")
            logger.warning("Falling back to deterministic outline generation.")
            outline = self._build_fallback_outline(codebase_structure, guidelines_config)
        else:
            # Validate minimal structure from LLM
            if not isinstance(outline, dict) or "chapters" not in outline:
                logger.warning("LLM outline missing 'chapters' or is not a dict; using fallback outline instead.")
                outline = self._build_fallback_outline(codebase_structure, guidelines_config)

        # Validate and fix outline - ensure we have enough chapters
        # Ensure outline is a dict and chapters is a list
        if not isinstance(outline, dict):
            logger.error("Outline is not a dict after all validation, using fallback")
            outline = self._build_fallback_outline(codebase_structure, guidelines_config)
        
        chapters = outline.get("chapters", [])
        # Ensure chapters is a list
        if not isinstance(chapters, list):
            logger.warning(f"Chapters is not a list (type: {type(chapters)}), converting to empty list")
            chapters = []
            outline["chapters"] = chapters
        if len(chapters) < 3:
            logger.warning(f"Outline only has {len(chapters)} chapters. Minimum 3 required. Enriching with fallback chapters...")
            # Merge with fallback to ensure we have middle chapters
            fallback = self._build_fallback_outline(codebase_structure, guidelines_config)
            fallback_chapters = fallback.get("chapters", [])
            
            # Keep introduction and conclusion from LLM if they exist, but add middle chapters from fallback
            intro_chapter = next((ch for ch in chapters if ch.get("number") == 1), None)
            conclusion_chapter = next((ch for ch in chapters if ch.get("number") == len(chapters)), None)
            
            # Get middle chapters from fallback (skip intro and conclusion)
            middle_chapters = [ch for ch in fallback_chapters if ch.get("number") not in [1, len(fallback_chapters)]]
            
            # Rebuild chapters list
            new_chapters = []
            if intro_chapter:
                new_chapters.append(intro_chapter)
            else:
                new_chapters.append(fallback_chapters[0])  # Use fallback intro
            
            # Add middle chapters
            for i, ch in enumerate(middle_chapters, start=2):
                ch["number"] = i
                # Renumber sections
                for j, sec in enumerate(ch.get("sections", []), 1):
                    sec["number"] = f"{i}.{j}"
                new_chapters.append(ch)
            
            # Add conclusion
            if conclusion_chapter:
                conclusion_chapter["number"] = len(new_chapters) + 1
                new_chapters.append(conclusion_chapter)
            else:
                last_fallback = fallback_chapters[-1]
                last_fallback["number"] = len(new_chapters) + 1
                new_chapters.append(last_fallback)
            
            outline["chapters"] = new_chapters
            chapters = new_chapters
            logger.info(f"Enriched outline to {len(chapters)} chapters")

        # POST-PROCESSING: Apply fact-driven hardening rules
        logger.info("Applying fact-driven hardening rules...")
        outline = self._harden_outline_with_facts(outline, codebase_structure)
        
        # Add metadata (for both LLM and fallback)
        outline["_metadata"] = {
            "project_name": project_summary["name"],
            "total_chapters": len(outline.get("chapters", [])),
            "total_sections": sum(
                len(ch.get("sections", [])) for ch in outline.get("chapters", [])
            ),
        }

        # Save outline
        output_path = self.output_dir / "report_outline.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(outline, f, indent=2)

        logger.success(
            f"Outline created: {outline['_metadata']['total_chapters']} chapters, "
            f"{outline['_metadata']['total_sections']} sections"
        )
        logger.info(f"Saved to: {output_path}")

        return outline

    def _harden_outline_with_facts(
        self,
        outline: Dict[str, Any],
        codebase_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply fact-driven hardening rules to prevent hallucination.
        This post-processes the outline to ensure it's grounded in facts.
        """
        # Extract facts from codebase_structure
        complexity = codebase_structure.get("complexity_level", "moderate")
        capabilities = codebase_structure.get("detected_capabilities", [])
        technologies = codebase_structure.get("main_technologies", [])
        backend_present = codebase_structure.get("backend_present", False)
        frontend_only = codebase_structure.get("frontend_only", False)
        use_cases = codebase_structure.get("use_cases", [])
        code_statistics = codebase_structure.get("code_statistics", {})
        directory_structure = codebase_structure.get("directory_structure", {})
        
        code_files = code_statistics.get("code_files", 0)
        dir_depth = directory_structure.get("depth", 0)
        
        # Determine allowed diagram types based on complexity
        if complexity == "simple":
            allowed_diagram_types = ["flowchart", "ui_layout", "interaction_flow"]
            max_chapters = 4
            max_sections_per_chapter = 3
        elif complexity == "moderate":
            allowed_diagram_types = ["flowchart", "ui_layout", "interaction_flow", "sequenceDiagram", "componentDiagram"]
            max_chapters = 6
            max_sections_per_chapter = 5
        else:  # complex
            allowed_diagram_types = ["flowchart", "ui_layout", "interaction_flow", "sequenceDiagram", "componentDiagram", "classDiagram", "architectureDiagram"]
            max_chapters = 8
            max_sections_per_chapter = 7
        
        # Fact-based conditions for diagrams and tables
        should_have_diagrams = len(capabilities) >= 2 or dir_depth > 0
        should_have_tables = len(technologies) > 1 or code_files > 1
        
        # Check for error handling in code (simplified check)
        code_content = codebase_structure.get("code_content", {})
        has_error_handling = False
        for file_data in code_content.values():
            code = file_data.get("code", "")
            if any(keyword in code.lower() for keyword in ["try", "catch", "error", "exception", "validate", "validation"]):
                has_error_handling = True
                break
        
        chapters = outline.get("chapters", [])
        hardened_chapters = []
        
        for chapter in chapters:
            chapter_num = chapter.get("number", 0)
            sections = chapter.get("sections", [])
            hardened_sections = []
            
            # Limit sections per chapter based on complexity
            sections = sections[:max_sections_per_chapter]
            
            for section in sections:
                section_title = section.get("title", "").lower()
                section_desc = section.get("description", "").lower()
                
                # 7️⃣ ENFORCE FORBIDDEN CHAPTERS: Remove backend-related sections if no backend
                if not backend_present and (
                    "backend" in section_title or "api" in section_title or 
                    "database" in section_title or "deployment" in section_title or
                    "security architecture" in section_title or "performance optimization" in section_title or
                    "server" in section_title or "rest" in section_title or "graphql" in section_title
                ):
                    logger.warning(f"Skipping backend-related section '{section.get('title')}' - no backend detected")
                    continue
                
                # 1️⃣ MAKE DIAGRAMS & TABLES FACT-CONDITIONAL
                needs_diagram = section.get("needs_diagram", False)
                needs_table = section.get("needs_table", False)
                
                if needs_diagram and not should_have_diagrams:
                    logger.info(f"Removing diagram requirement from section '{section.get('title')}' - insufficient facts")
                    needs_diagram = False
                
                if needs_table and not should_have_tables:
                    logger.info(f"Removing table requirement from section '{section.get('title')}' - insufficient facts")
                    needs_table = False
                
                # 3️⃣ RESTRICT DIAGRAM TYPES BASED ON COMPLEXITY
                diagram_type = section.get("diagram_type", "flowchart")
                if needs_diagram and diagram_type not in allowed_diagram_types:
                    logger.warning(f"Downgrading diagram type '{diagram_type}' to 'flowchart' for simple project")
                    diagram_type = "flowchart"
                
                # 5️⃣ FIX ERROR HANDLING SECTIONS
                if "error handling" in section_title and not has_error_handling:
                    section["title"] = section["title"].replace("Error Handling", "Limitations and Edge Cases")
                    section["description"] = section.get("description", "").replace(
                        "how the application handles", "the limitations of the current implementation and"
                    )
                    # Add explicit instruction about absence
                    if "writing_guideline" not in section:
                        section["writing_guideline"] = "Describe the absence of robust error handling. Mention that the current implementation lacks explicit error checking and discuss constraints."
                
                # 4️⃣ FIX USE CASE GENERATION
                if "use case" in section_title and not use_cases:
                    # Update description to be interaction-based
                    section["description"] = "Describe typical user interactions with the application. Focus on observable behaviors: user enters input, user clicks buttons, application updates display. Use conservative phrasing: 'Typical interactions include...'"
                    if "writing_guideline" not in section:
                        section["writing_guideline"] = "Focus on observable interactions only. Do not create educational, business, or productivity scenarios. Describe what the user can actually do based on the code."
                
                # 6️⃣ ADD WRITER SAFETY INSTRUCTIONS PER SECTION
                if "writing_guideline" not in section:
                    if complexity == "simple":
                        section["writing_guideline"] = "Focus on what the code currently does. Avoid architectural assumptions. Describe observed behavior only."
                    else:
                        section["writing_guideline"] = "Describe observed behavior only. Do not assume additional logic beyond what is present in the code."
                
                # Update section with hardened values
                hardened_section = {
                    **section,
                    "needs_diagram": needs_diagram,
                    "needs_table": needs_table,
                }
                if needs_diagram:
                    hardened_section["diagram_type"] = diagram_type
                else:
                    # Remove diagram_type if not needed
                    if "diagram_type" in hardened_section:
                        del hardened_section["diagram_type"]
                
                hardened_sections.append(hardened_section)
            
            # Limit chapters based on complexity
            if chapter_num <= max_chapters:
                hardened_chapter = {
                    **chapter,
                    "sections": hardened_sections
                }
                hardened_chapters.append(hardened_chapter)
            else:
                logger.info(f"Skipping chapter {chapter_num} - exceeds max chapters for {complexity} complexity")
        
        # Ensure we have at least 3 chapters (intro + middle + conclusion)
        if len(hardened_chapters) < 3:
            logger.warning(f"Only {len(hardened_chapters)} chapters after hardening. Minimum 3 required.")
            # Keep first (intro) and last (conclusion), add middle from fallback if needed
            if len(hardened_chapters) >= 2:
                # We have intro and conclusion, that's fine
                pass
            else:
                # Need to add fallback chapters
                fallback = self._build_fallback_outline(codebase_structure, {})
                fallback_chapters = fallback.get("chapters", [])
                # Take middle chapters from fallback
                for fb_ch in fallback_chapters[1:-1]:  # Skip intro and conclusion
                    if len(hardened_chapters) < max_chapters:
                        hardened_chapters.insert(-1, fb_ch)  # Insert before conclusion
        
        return {
            **outline,
            "chapters": hardened_chapters
        }
    
    def _build_fallback_outline(
        self,
        codebase_structure: Dict[str, Any],
        guidelines_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build a dynamic outline based on project structure analysis.
        This fallback analyzes the actual project to create relevant chapters and sections.
        NOW FACT-AWARE: Uses complexity, capabilities, technologies, and backend presence.
        """
        project_name = codebase_structure.get("name", "Software Project")
        project_type = codebase_structure.get("project_type", "Software Project")
        technologies = codebase_structure.get("main_technologies", [])
        complexity = codebase_structure.get("complexity_level", "moderate")
        capabilities = codebase_structure.get("detected_capabilities", [])
        backend_present = codebase_structure.get("backend_present", False)
        frontend_only = codebase_structure.get("frontend_only", False)
        use_cases = codebase_structure.get("use_cases", [])
        code_statistics = codebase_structure.get("code_statistics", {})
        directory_structure = codebase_structure.get("directory_structure", {})
        file_structure = codebase_structure.get("file_structure", {})
        
        code_files = code_statistics.get("code_files", 0)
        dir_depth = directory_structure.get("depth", 0)
        
        # 2️⃣ SCALE STRUCTURE BY COMPLEXITY LEVEL
        if complexity == "simple":
            max_chapters = 4
            max_sections_per_chapter = 3
            allowed_diagram_types = ["flowchart", "ui_layout", "interaction_flow"]
        elif complexity == "moderate":
            max_chapters = 6
            max_sections_per_chapter = 5
            allowed_diagram_types = ["flowchart", "ui_layout", "interaction_flow", "sequenceDiagram", "componentDiagram"]
        else:  # complex
            max_chapters = 8
            max_sections_per_chapter = 7
            allowed_diagram_types = ["flowchart", "ui_layout", "interaction_flow", "sequenceDiagram", "componentDiagram", "classDiagram", "architectureDiagram"]
        
        # 1️⃣ FACT-CONDITIONAL DIAGRAMS & TABLES
        should_have_diagrams = len(capabilities) >= 2 or dir_depth > 0
        should_have_tables = len(technologies) > 1 or code_files > 1
        
        # Check for error handling
        code_content = codebase_structure.get("code_content", {})
        has_error_handling = False
        for file_data in code_content.values():
            code = file_data.get("code", "")
            if any(keyword in code.lower() for keyword in ["try", "catch", "error", "exception", "validate", "validation"]):
                has_error_handling = True
                break
        
        # Analyze project structure to determine chapters
        chapters = []
        chapter_num = 1
        
        # Chapter 1: Introduction (always present)
        intro_sections = []
        intro_sections.append({
            "number": "1.1",
            "title": f"{project_name} Overview",
            "description": f"Provide context about {project_name}, its purpose, and significance.",
            "needs_diagram": False,
            "needs_table": False,
            "writing_guideline": "Focus on what the code currently does. Avoid architectural assumptions." if complexity == "simple" else "Describe observed behavior only."
        })
        intro_sections.append({
            "number": "1.2",
            "title": "Project Objectives",
            "description": f"Describe the goals and objectives of this {project_type.lower()} project.",
            "needs_diagram": False,
            "needs_table": False,
            "writing_guideline": "Focus on what the code currently does. Avoid architectural assumptions." if complexity == "simple" else "Describe observed behavior only."
        })
        
        # 4️⃣ FIX USE CASE GENERATION: Only add if use_cases exist, otherwise use interaction-based
        if use_cases:
            intro_sections.append({
                "number": "1.3",
                "title": "Use Cases",
                "description": "Describe the primary use cases for this project based on the detected use cases.",
                "needs_table": should_have_tables,
                "needs_diagram": False,
                "writing_guideline": "Use the provided use cases. Do not create additional scenarios."
            })
        else:
            intro_sections.append({
                "number": "1.3",
                "title": "Typical Interactions",
                "description": "Describe typical user interactions with the application. Focus on observable behaviors: user enters input, user clicks buttons, application updates display.",
                "needs_table": False,
                "needs_diagram": False,
                "writing_guideline": "Focus on observable interactions only. Use conservative phrasing: 'Typical interactions include...' Do not create educational, business, or productivity scenarios."
            })
        
        intro_sections.append({
            "number": f"1.{len(intro_sections) + 1}",
            "title": "Technologies Used",
            "description": f"List and explain the technologies used in {project_name}.",
            "needs_table": should_have_tables,
            "needs_diagram": False,
            "writing_guideline": "List only technologies that are actually present in the code."
        })
        
        chapters.append({
            "number": chapter_num,
            "title": "Introduction",
            "sections": intro_sections
        })
        chapter_num += 1
        
        # Analyze file structure to create technical chapters - PROJECT-SPECIFIC
        main_dirs = [k for k, v in file_structure.items() if isinstance(v, dict) and k not in ['__pycache__', '.git', 'node_modules']]
        main_files = [k for k in file_structure.keys() if not isinstance(file_structure.get(k), dict)]
        
        # Determine project-specific chapter title based on project type
        if "web" in project_type.lower() or "app" in project_type.lower():
            chapter2_title = f"{project_name} Architecture and Design"
        elif "cli" in project_type.lower() or "tool" in project_type.lower():
            chapter2_title = f"{project_name} Command Structure and Processing"
        elif "data" in project_type.lower() or "analysis" in project_type.lower():
            chapter2_title = f"{project_name} Data Processing Architecture"
        else:
            chapter2_title = f"{project_name} System Architecture"
        
        # Chapter 2: Project-specific architecture chapter
        # 7️⃣ ENFORCE FORBIDDEN CHAPTERS: Skip architecture chapter if no backend and frontend-only
        if (main_dirs or len(main_files) > 3) and not (frontend_only and not backend_present and complexity == "simple"):
            arch_sections = []
            
            # 1️⃣ FACT-CONDITIONAL DIAGRAMS
            diagram_type = "flowchart" if complexity == "simple" else allowed_diagram_types[0]
            arch_sections.append({
                "number": f"{chapter_num}.1",
                "title": f"{project_name} Overview and Design",
                "description": f"Explain the overall design approach for {project_name}." + (" Include a design diagram." if should_have_diagrams else ""),
                "needs_diagram": should_have_diagrams,
                "writing_guideline": "Focus on what the code currently does. Avoid architectural assumptions." if complexity == "simple" else "Describe observed behavior only."
            })
            if should_have_diagrams:
                arch_sections[-1]["diagram_type"] = diagram_type
            
            if main_dirs:
                dirs_list = ', '.join(main_dirs[:5])
                arch_sections.append({
                    "number": f"{chapter_num}.2",
                    "title": f"Component Structure: {dirs_list}",
                    "description": f"Describe the main components/modules of {project_name}: {dirs_list}.",
                    "needs_diagram": False,
                    "needs_table": False,
                    "writing_guideline": "Describe only the components that exist in the code."
                })
            
            if technologies and should_have_tables:
                tech_list = ', '.join(technologies[:5])
                arch_sections.append({
                    "number": f"{chapter_num}.{len(arch_sections) + 1}",
                    "title": f"Technology Stack: {tech_list}",
                    "description": f"List and explain the technologies used in {project_name}.",
                    "needs_table": True,
                    "needs_diagram": False,
                    "writing_guideline": "List only technologies that are actually present in the code."
                })
            
            # Limit sections per chapter
            arch_sections = arch_sections[:max_sections_per_chapter]
            
            if arch_sections:  # Only add chapter if we have sections
                chapters.append({
                    "number": chapter_num,
                    "title": chapter2_title,
                    "sections": arch_sections
                })
                chapter_num += 1
        
        # Chapter 3: Project-specific implementation chapter (ALWAYS create this)
        if "web" in project_type.lower():
            chapter3_title = f"{project_name} Implementation and Features"
        elif "cli" in project_type.lower():
            chapter3_title = f"{project_name} Functionality and Workflows"
        else:
            chapter3_title = f"{project_name} Core Implementation"
        
        impl_sections = []
        diagram_type = "flowchart" if complexity == "simple" else allowed_diagram_types[0]
        impl_sections.append({
            "number": f"{chapter_num}.1",
            "title": f"{project_name} Core Functionality",
            "description": f"Explain the main features and functionality of {project_name}." + (" Include a workflow diagram." if should_have_diagrams else ""),
            "needs_diagram": should_have_diagrams,
            "writing_guideline": "Focus on what the code currently does. Avoid architectural assumptions." if complexity == "simple" else "Describe observed behavior only."
        })
        if should_have_diagrams:
            impl_sections[-1]["diagram_type"] = diagram_type
        
        if main_dirs and should_have_diagrams:
            impl_sections.append({
                "number": f"{chapter_num}.2",
                "title": f"Module Implementation in {project_name}",
                "description": f"Describe how the main modules of {project_name} are implemented and interact.",
                "needs_diagram": should_have_diagrams,
                "diagram_type": diagram_type,
                "writing_guideline": "Describe only the modules that exist in the code."
            })
        else:
            impl_sections.append({
                "number": f"{chapter_num}.2",
                "title": f"{project_name} Key Features",
                "description": f"Describe the key features of {project_name}.",
                "needs_table": should_have_tables,
                "needs_diagram": False,
                "writing_guideline": "List only features that are actually implemented in the code."
            })
        
        # 5️⃣ FIX ERROR HANDLING SECTIONS
        if has_error_handling:
            impl_sections.append({
                "number": f"{chapter_num}.{len(impl_sections) + 1}",
                "title": "Error Handling",
                "description": "Discuss how the application handles errors and edge cases.",
                "needs_table": False,
                "needs_diagram": False,
                "writing_guideline": "Describe only the error handling mechanisms that are present in the code."
            })
        else:
            impl_sections.append({
                "number": f"{chapter_num}.{len(impl_sections) + 1}",
                "title": "Limitations and Edge Cases",
                "description": "Discuss the limitations of the current implementation and constraints. Mention that the current implementation lacks explicit error checking.",
                "needs_table": False,
                "needs_diagram": False,
                "writing_guideline": "Describe the absence of robust error handling. Mention that the current implementation lacks explicit error checking and discuss constraints."
            })
        
        # Add table only if facts support it
        if should_have_tables:
            impl_sections.append({
                "number": f"{chapter_num}.{len(impl_sections) + 1}",
                "title": f"{project_name} Implementation Summary",
                "description": f"Summarize the implementation approach and key decisions for {project_name}.",
                "needs_table": True,
                "needs_diagram": False,
                "writing_guideline": "Summarize only what is actually implemented."
            })
        
        # Limit sections per chapter
        impl_sections = impl_sections[:max_sections_per_chapter]
        
        chapters.append({
            "number": chapter_num,
            "title": chapter3_title,
            "sections": impl_sections
        })
        chapter_num += 1
        
        # Conclusion (always present) - Project-specific
        conclusion_sections = []
        conclusion_sections.append({
            "number": "",
            "title": f"{project_name} Summary",
            "description": f"Summarize what was accomplished in {project_name} and its value.",
            "needs_diagram": False,
            "needs_table": False,
            "writing_guideline": "Summarize only what was actually implemented."
        })
        conclusion_sections.append({
            "number": "",
            "title": f"{project_name} Future Enhancements",
            "description": f"Discuss potential enhancements and future directions for {project_name}.",
            "needs_table": should_have_tables,
            "needs_diagram": False,
            "writing_guideline": "Suggest enhancements that are realistic given the current implementation."
        })
        
        # Limit sections per chapter
        conclusion_sections = conclusion_sections[:max_sections_per_chapter]
        
        chapters.append({
            "number": chapter_num,
            "title": f"{project_name} Conclusion and Future Directions",
            "sections": conclusion_sections
        })
        
        outline: Dict[str, Any] = {
            "report_title": f"{project_name} Technical Documentation",
            "chapters": chapters
        }
        
        logger.info(f"Fallback outline created with {len(chapters)} chapters based on project analysis")
        return outline
    
    def validate_outline(self, outline: Dict[str, Any]) -> bool:
        """
        Validate outline structure
        
        Returns:
            True if valid, raises exception if invalid
        """
        logger.info("Validating outline...")
        
        required_fields = ["report_title", "chapters"]
        for field in required_fields:
            if field not in outline:
                raise ValueError(f"Outline missing required field: {field}")
        
        chapters = outline["chapters"]
        if not chapters:
            raise ValueError("Outline has no chapters")
        
        for i, chapter in enumerate(chapters, 1):
            # Check chapter structure
            if "number" not in chapter:
                raise ValueError(f"Chapter {i} missing 'number' field")
            if "title" not in chapter:
                raise ValueError(f"Chapter {i} missing 'title' field")
            if "sections" not in chapter:
                raise ValueError(f"Chapter {i} missing 'sections' field")
            
            # Check sections
            if not chapter["sections"]:
                logger.warning(f"Chapter {i} has no sections")
                continue
            
            for j, section in enumerate(chapter["sections"], 1):
                if "number" not in section:
                    raise ValueError(f"Chapter {i}, Section {j} missing 'number' field")
                if "title" not in section:
                    raise ValueError(f"Chapter {i}, Section {j} missing 'title' field")
        
        logger.success("Outline validation passed")
        return True
    
    def run(
        self,
        codebase_structure: Dict[str, Any],
        guidelines_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run complete planning pipeline
        
        Returns:
            Validated report outline
        """
        logger.info("=== PLANNER AGENT STARTED ===")
        
        outline = self.create_outline(codebase_structure, guidelines_config)
        
        # POST-PROCESSING: Ensure strict X.Y numbering
        logger.info("Post-processing outline numbering...")
        for i, chapter in enumerate(outline.get("chapters", []), 1):
            chapter["number"] = i
            for j, section in enumerate(chapter.get("sections", []), 1):
                section["number"] = f"{i}.{j}"
                
        self.validate_outline(outline)
        
        logger.success("=== PLANNER AGENT COMPLETED ===")
        
        return outline


# Convenience function
def create_report_outline(
    codebase_structure: Dict[str, Any],
    guidelines_config: Dict[str, Any],
    job_id: str = None
) -> Dict[str, Any]:
    """
    Create report outline
    
    Args:
        codebase_structure: Analyzed project structure
        guidelines_config: Formatting guidelines
        job_id: Optional job ID for isolated output directory
        
    Returns:
        Report outline
    """
    agent = PlannerAgent(job_id=job_id)
    return agent.run(codebase_structure, guidelines_config)