"""
End-to-End Integration Test for Full Report Generation Pipeline

Tests the complete flow: Parser → Planner → Writer → Builder
Validates that all agents work together correctly and data flows properly.
"""
import sys
import argparse
import time
from pathlib import Path
import json
from typing import Dict, Any, Optional
import os
import traceback

# Fix Windows encoding issues
if sys.platform == "win32":
    # Set UTF-8 encoding for stdout/stderr on Windows
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')
    # Set environment variable for subprocesses
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.parser_agent import ParserAgent
from agents.planner_agent import PlannerAgent
from agents.writer_agent import WriterAgent
from agents.builder_agent import BuilderAgent
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


class PipelineValidator:
    """Validates outputs at each stage of the pipeline"""
    
    @staticmethod
    def validate_parser_output(parser_output: Dict[str, Any], job_id: str) -> tuple[bool, list[str]]:
        """Validate Parser Agent output"""
        errors = []
        
        # Check required keys
        required_keys = ["guidelines", "codebase"]
        for key in required_keys:
            if key not in parser_output:
                errors.append(f"Missing required key: {key}")
        
        # Validate guidelines
        if "guidelines" in parser_output:
            guidelines = parser_output["guidelines"]
            if not isinstance(guidelines, dict):
                errors.append("Guidelines must be a dict")
            # Check for any formatting-related keys (formatting_rules, formatting, etc.)
            elif not any(key in guidelines for key in ["formatting_rules", "formatting", "page_setup", "styles"]):
                errors.append("Guidelines missing formatting configuration")
        
        # Validate codebase
        if "codebase" in parser_output:
            codebase = parser_output["codebase"]
            if not isinstance(codebase, dict):
                errors.append("Codebase must be a dict")
            elif not codebase.get("name"):
                errors.append("Codebase missing project name")
            elif not codebase.get("files"):
                errors.append("Codebase missing files list")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_planner_output(outline: Dict[str, Any], job_id: str) -> tuple[bool, list[str]]:
        """Validate Planner Agent output"""
        errors = []
        
        # Check required keys
        if "report_title" not in outline:
            errors.append("Missing report_title")
        if "chapters" not in outline:
            errors.append("Missing chapters")
        
        # Validate chapters
        chapters = outline.get("chapters", [])
        if not isinstance(chapters, list):
            errors.append("Chapters must be a list")
        elif len(chapters) == 0:
            errors.append("No chapters generated")
        else:
            # Validate each chapter
            for i, chapter in enumerate(chapters):
                if not isinstance(chapter, dict):
                    errors.append(f"Chapter {i+1} is not a dict")
                elif "title" not in chapter:
                    errors.append(f"Chapter {i+1} missing title")
                elif "sections" not in chapter:
                    errors.append(f"Chapter {i+1} missing sections")
                elif not isinstance(chapter.get("sections"), list):
                    errors.append(f"Chapter {i+1} sections must be a list")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_writer_output(content: Dict[str, Any], job_id: str) -> tuple[bool, list[str]]:
        """Validate Writer Agent output"""
        errors = []
        
        # Check required keys
        if "report_title" not in content:
            errors.append("Missing report_title")
        if "chapters" not in content:
            errors.append("Missing chapters")
        
        # Validate chapters
        chapters = content.get("chapters", [])
        if not isinstance(chapters, list):
            errors.append("Chapters must be a list")
        elif len(chapters) == 0:
            errors.append("No chapters generated")
        else:
            # Validate each chapter
            for i, chapter in enumerate(chapters):
                if not isinstance(chapter, dict):
                    errors.append(f"Chapter {i+1} is not a dict")
                elif "chapter_title" not in chapter:
                    errors.append(f"Chapter {i+1} missing chapter_title")
                elif "sections" not in chapter:
                    errors.append(f"Chapter {i+1} missing sections")
                else:
                    sections = chapter.get("sections", [])
                    for j, section in enumerate(sections):
                        if not isinstance(section, dict):
                            errors.append(f"Chapter {i+1}, Section {j+1} is not a dict")
                        elif "title" not in section:
                            errors.append(f"Chapter {i+1}, Section {j+1} missing title")
                        elif "content" not in section:
                            errors.append(f"Chapter {i+1}, Section {j+1} missing content")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_builder_output(output_path: str, job_id: str) -> tuple[bool, list[str]]:
        """Validate Builder Agent output"""
        errors = []
        
        output_file = Path(output_path)
        if not output_file.exists():
            errors.append(f"Output file does not exist: {output_path}")
        else:
            # Check file size (should be > 0)
            file_size = output_file.stat().st_size
            if file_size == 0:
                errors.append("Output file is empty")
            elif file_size < 1000:  # Less than 1KB is suspicious
                errors.append(f"Output file is suspiciously small: {file_size} bytes")
            
            # Check file extension
            if output_file.suffix != ".docx":
                errors.append(f"Output file has wrong extension: {output_file.suffix}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_data_flow(parser_output: Dict, planner_output: Dict, writer_output: Dict) -> tuple[bool, list[str]]:
        """Validate that data flows correctly between agents"""
        errors = []
        
        # Check project name consistency
        parser_name = parser_output.get("codebase", {}).get("name", "")
        planner_title = planner_output.get("report_title", "")
        writer_title = writer_output.get("report_title", "")
        
        # Project name should appear in report titles (case-insensitive)
        if parser_name and parser_name.lower() not in planner_title.lower():
            errors.append(f"Project name '{parser_name}' not found in planner report title")
        
        if parser_name and parser_name.lower() not in writer_title.lower():
            errors.append(f"Project name '{parser_name}' not found in writer report title")
        
        # Check chapter count consistency
        planner_chapters = len(planner_output.get("chapters", []))
        writer_chapters = len(writer_output.get("chapters", []))
        
        if planner_chapters != writer_chapters:
            errors.append(f"Chapter count mismatch: Planner={planner_chapters}, Writer={writer_chapters}")
        
        # Check section count consistency (approximate)
        planner_sections = sum(len(ch.get("sections", [])) for ch in planner_output.get("chapters", []))
        writer_sections = sum(len(ch.get("sections", [])) for ch in writer_output.get("chapters", []))
        
        if planner_sections != writer_sections:
            errors.append(f"Section count mismatch: Planner={planner_sections}, Writer={writer_sections}")
        
        return len(errors) == 0, errors


def test_full_pipeline(
    project_zip_path: str,
    guidelines_pdf_path: str,
    job_id: Optional[str] = None,
    skip_builder: bool = False
) -> Dict[str, Any]:
    """
    Test the complete report generation pipeline
    
    Args:
        project_zip_path: Path to project ZIP file
        guidelines_pdf_path: Path to guidelines PDF
        job_id: Optional job ID (defaults to timestamp-based)
        skip_builder: Skip Builder Agent (faster testing)
    
    Returns:
        Test results dictionary
    """
    # Generate job ID if not provided
    if not job_id:
        job_id = f"e2e_test_{int(time.time())}"
    
    print("=" * 80)
    print("END-TO-END PIPELINE INTEGRATION TEST")
    print("=" * 80)
    print(f"Project ZIP: {project_zip_path}")
    print(f"Guidelines PDF: {guidelines_pdf_path}")
    print(f"Job ID: {job_id}")
    print(f"Skip Builder: {skip_builder}")
    print("=" * 80)
    print()
    
    validator = PipelineValidator()
    results = {
        "job_id": job_id,
        "stages": {},
        "overall_success": False,
        "errors": [],
        "warnings": []
    }
    
    start_time = time.time()
    
    try:
        # ============ STAGE 1: PARSER AGENT ============
        print("=" * 80)
        print("STAGE 1: PARSER AGENT")
        print("=" * 80)
        stage_start = time.time()
        
        parser = ParserAgent(job_id=job_id)
        
        # Step 1: Analyze project structure
        print("\n[1.1] Analyzing project structure...")
        from utils.code_analyzer import analyze_project
        project_analysis = analyze_project(project_zip_path, job_id=job_id)
        print(f"[OK] Project analyzed: {project_analysis.get('name', 'Unknown')} ({len(project_analysis.get('files', []))} files)")
        
        # Step 2: Parse guidelines
        print("\n[1.2] Parsing guidelines PDF...")
        guidelines_config = parser.parse_guidelines(guidelines_pdf_path)
        # Defensive check: ensure guidelines_config is a dict
        if not isinstance(guidelines_config, dict):
            raise TypeError(f"Guidelines config must be a dict, got {type(guidelines_config).__name__}: {str(guidelines_config)[:100]}")
        # Count formatting rules (check various possible keys)
        rules_count = 0
        if isinstance(guidelines_config.get('formatting_rules'), dict):
            rules_count = len(guidelines_config.get('formatting_rules', {}))
        elif isinstance(guidelines_config.get('formatting_rules'), list):
            rules_count = len(guidelines_config.get('formatting_rules', []))
        print(f"[OK] Guidelines parsed: {rules_count} rules extracted")
        
        # Step 3: Analyze project structure with LLM
        print("\n[1.3] Analyzing codebase structure with LLM...")
        codebase_structure = parser.analyze_project_structure(project_analysis)
        print(f"[OK] Codebase analyzed: {codebase_structure.get('project_type', 'Unknown')} project")
        
        # Combine results
        parser_output = {
            "guidelines": guidelines_config,
            "codebase": codebase_structure
        }
        
        # Validate parser output
        is_valid, errors = validator.validate_parser_output(parser_output, job_id)
        if not is_valid:
            results["errors"].extend([f"Parser: {e}" for e in errors])
            raise ValueError(f"Parser validation failed: {errors}")
        
        stage_time = time.time() - stage_start
        results["stages"]["parser"] = {
            "success": True,
            "time_seconds": round(stage_time, 2),
            "project_name": codebase_structure.get("name", "Unknown"),
            "files_analyzed": len(project_analysis.get("files", [])),
            "project_type": codebase_structure.get("project_type", "Unknown")
        }
        print(f"\n[OK] PARSER AGENT COMPLETED in {stage_time:.2f}s")
        
        # ============ STAGE 2: PLANNER AGENT ============
        print("\n" + "=" * 80)
        print("STAGE 2: PLANNER AGENT")
        print("=" * 80)
        stage_start = time.time()
        
        planner = PlannerAgent(job_id=job_id)
        
        print("\n[2.1] Creating report outline...")
        outline = planner.create_outline(codebase_structure, guidelines_config)
        
        chapters_count = len(outline.get("chapters", []))
        sections_count = sum(len(ch.get("sections", [])) for ch in outline.get("chapters", []))
        print(f"[OK] Outline created: {chapters_count} chapters, {sections_count} sections")
        print(f"   Report Title: {outline.get('report_title', 'N/A')}")
        
        # Validate planner output
        is_valid, errors = validator.validate_planner_output(outline, job_id)
        if not is_valid:
            results["errors"].extend([f"Planner: {e}" for e in errors])
            raise ValueError(f"Planner validation failed: {errors}")
        
        stage_time = time.time() - stage_start
        results["stages"]["planner"] = {
            "success": True,
            "time_seconds": round(stage_time, 2),
            "chapters": chapters_count,
            "sections": sections_count,
            "report_title": outline.get("report_title", "N/A")
        }
        print(f"\n[OK] PLANNER AGENT COMPLETED in {stage_time:.2f}s")
        
        # ============ STAGE 3: WRITER AGENT ============
        print("\n" + "=" * 80)
        print("STAGE 3: WRITER AGENT")
        print("=" * 80)
        stage_start = time.time()
        
        writer = WriterAgent(job_id=job_id)
        
        print("\n[3.1] Generating content for all sections...")
        content = writer.run(outline, codebase_structure)
        
        writer_chapters = len(content.get("chapters", []))
        writer_sections = sum(len(ch.get("sections", [])) for ch in content.get("chapters", []))
        print(f"[OK] Content generated: {writer_chapters} chapters, {writer_sections} sections")
        
        # Validate writer output
        is_valid, errors = validator.validate_writer_output(content, job_id)
        if not is_valid:
            results["errors"].extend([f"Writer: {e}" for e in errors])
            raise ValueError(f"Writer validation failed: {errors}")
        
        stage_time = time.time() - stage_start
        results["stages"]["writer"] = {
            "success": True,
            "time_seconds": round(stage_time, 2),
            "chapters": writer_chapters,
            "sections": writer_sections
        }
        print(f"\n[OK] WRITER AGENT COMPLETED in {stage_time:.2f}s")
        
        # ============ STAGE 4: DATA FLOW VALIDATION ============
        print("\n" + "=" * 80)
        print("STAGE 4: DATA FLOW VALIDATION")
        print("=" * 80)
        
        is_valid, errors = validator.validate_data_flow(parser_output, outline, content)
        if not is_valid:
            results["warnings"].extend([f"Data Flow: {e}" for e in errors])
            print(f"⚠️  Data flow warnings: {errors}")
        else:
            print("[OK] Data flow validation passed")
        
        results["stages"]["data_flow"] = {
            "success": is_valid,
            "warnings": errors
        }
        
        # ============ STAGE 5: BUILDER AGENT ============
        if not skip_builder:
            print("\n" + "=" * 80)
            print("STAGE 5: BUILDER AGENT")
            print("=" * 80)
            stage_start = time.time()
            
            builder = BuilderAgent(job_id=job_id)
            
            print("\n[5.1] Building DOCX document...")
            output_filename = f"Technical_Report_{job_id}.docx"
            output_path = builder.build_document(
                content=content,
                guidelines=guidelines_config,
                outline=outline,
                output_filename=output_filename
            )
            
            print(f"[OK] Document built: {output_path}")
            
            # Validate builder output
            is_valid, errors = validator.validate_builder_output(output_path, job_id)
            if not is_valid:
                results["errors"].extend([f"Builder: {e}" for e in errors])
                raise ValueError(f"Builder validation failed: {errors}")
            
            # Get file size
            file_size = Path(output_path).stat().st_size
            file_size_kb = file_size / 1024
            
            stage_time = time.time() - stage_start
            results["stages"]["builder"] = {
                "success": True,
                "time_seconds": round(stage_time, 2),
                "output_path": output_path,
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size_kb, 2)
            }
            print(f"\n[OK] BUILDER AGENT COMPLETED in {stage_time:.2f}s")
            print(f"   Output: {output_path}")
            print(f"   Size: {file_size_kb:.2f} KB")
        else:
            print("\n[SKIP] BUILDER AGENT SKIPPED (use without --skip-builder to test)")
            results["stages"]["builder"] = {
                "success": None,
                "skipped": True
            }
        
        # ============ FINAL RESULTS ============
        total_time = time.time() - start_time
        results["overall_success"] = len(results["errors"]) == 0
        results["total_time_seconds"] = round(total_time, 2)
        
        print("\n" + "=" * 80)
        print("PIPELINE TEST RESULTS")
        print("=" * 80)
        print(f"Overall Success: {'[OK] YES' if results['overall_success'] else '[FAIL] NO'}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Errors: {len(results['errors'])}")
        print(f"Warnings: {len(results['warnings'])}")
        print()
        
        if results["errors"]:
            print("ERRORS:")
            for error in results["errors"]:
                print(f"  [ERROR] {error}")
            print()
        
        if results["warnings"]:
            print("WARNINGS:")
            for warning in results["warnings"]:
                print(f"  [WARN] {warning}")
            print()
        
        print("STAGE TIMINGS:")
        for stage_name, stage_data in results["stages"].items():
            if stage_data.get("time_seconds"):
                print(f"  {stage_name.upper()}: {stage_data['time_seconds']}s")
        print()
        
        return results
        
    except Exception as e:
        total_time = time.time() - start_time
        results["overall_success"] = False
        results["total_time_seconds"] = round(total_time, 2)
        results["errors"].append(f"Pipeline failed: {str(e)}")
        
        print("\n" + "=" * 80)
        print("PIPELINE TEST FAILED")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print(f"Time: {total_time:.2f}s")
        print("\nFull traceback:")
        print(traceback.format_exc())
        print()
        
        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="End-to-End Pipeline Integration Test")
    parser.add_argument(
        "--project",
        type=str,
        required=True,
        help="Path to project ZIP file"
    )
    parser.add_argument(
        "--guidelines",
        type=str,
        required=True,
        help="Path to guidelines PDF file"
    )
    parser.add_argument(
        "--job-id",
        type=str,
        default=None,
        help="Optional job ID (defaults to timestamp-based)"
    )
    parser.add_argument(
        "--skip-builder",
        action="store_true",
        help="Skip Builder Agent (faster testing)"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save test results to JSON file"
    )
    
    args = parser.parse_args()
    
    # Validate input files
    project_path = Path(args.project)
    guidelines_path = Path(args.guidelines)
    
    if not project_path.exists():
        print(f"[ERROR] Project file not found: {args.project}")
        sys.exit(1)
    
    if not guidelines_path.exists():
        print(f"[ERROR] Guidelines file not found: {args.guidelines}")
        sys.exit(1)
    
    # Run test
    results = test_full_pipeline(
        project_zip_path=str(project_path),
        guidelines_pdf_path=str(guidelines_path),
        job_id=args.job_id,
        skip_builder=args.skip_builder
    )
    
    # Save results if requested
    if args.save_results:
        output_dir = PROJECT_ROOT / "tests" / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"e2e_test_results_{results['job_id']}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Test results saved to: {output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)


if __name__ == "__main__":
    main()

