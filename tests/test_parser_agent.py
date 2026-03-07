"""
Test Script for Parser Agent
Tests the parser agent on different projects to analyze its output
"""
import sys
from pathlib import Path
import json
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.code_analyzer import analyze_project
from agents.parser_agent import ParserAgent
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")


def test_parser_agent(project_zip_path: str, guidelines_pdf_path: str, job_id: str = None):
    """
    Test parser agent on a specific project
    
    Args:
        project_zip_path: Path to project ZIP file
        guidelines_pdf_path: Path to guidelines PDF
        job_id: Optional job ID (defaults to timestamp-based)
    """
    if not job_id:
        import time
        job_id = f"test_{int(time.time())}"
    
    print("=" * 80)
    print(f"TESTING PARSER AGENT")
    print("=" * 80)
    print(f"Project ZIP: {project_zip_path}")
    print(f"Guidelines PDF: {guidelines_pdf_path}")
    print(f"Job ID: {job_id}")
    print("=" * 80)
    print()
    
    # Step 1: Analyze project structure
    print("STEP 1: Analyzing Project Structure...")
    print("-" * 80)
    try:
        project_analysis = analyze_project(project_zip_path, job_id=job_id)
        print(f"✅ Project Analysis Complete")
        print(f"   Project Name: {project_analysis.get('name', 'Unknown')}")
        print(f"   Files Found: {len(project_analysis.get('files', []))}")
        print(f"   Technologies: {', '.join(project_analysis.get('technologies', []))}")
        print(f"   Entry Points: {', '.join(project_analysis.get('entry_points', []))}")
        print(f"   Total Lines: {project_analysis.get('total_lines', 0)}")
        
        # Show sample files
        print(f"\n   Sample Files (first 10):")
        for i, file_info in enumerate(project_analysis.get('files', [])[:10], 1):
            file_path = file_info.get('path', str(file_info))
            lines = file_info.get('lines', 0)
            has_code = file_info.get('has_code', False)
            code_snippet_len = len(file_info.get('code_snippet', '')) if has_code else 0
            print(f"      {i}. {file_path} ({lines} lines, code: {'YES' if has_code else 'NO'}, snippet: {code_snippet_len} chars)")
        
        print()
    except Exception as e:
        print(f"❌ Project Analysis Failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Step 2: Run Parser Agent
    print("STEP 2: Running Parser Agent...")
    print("-" * 80)
    try:
        parser = ParserAgent(job_id=job_id)
        
        # Parse guidelines
        print("   Parsing guidelines PDF...")
        guidelines_config = parser.parse_guidelines(guidelines_pdf_path)
        print(f"   ✅ Guidelines parsed")
        
        # Analyze project structure with LLM
        print("   Analyzing project structure with LLM...")
        codebase_structure = parser.analyze_project_structure(project_analysis)
        print(f"   ✅ Project structure analyzed")
        
        # Get combined output
        result = {
            "guidelines": guidelines_config,
            "codebase": codebase_structure
        }
        
        print()
        print("=" * 80)
        print("PARSER AGENT OUTPUT SUMMARY")
        print("=" * 80)
        
        # Display Guidelines Config
        print("\n📋 GUIDELINES CONFIG:")
        print("-" * 80)
        fonts = guidelines_config.get('fonts', {})
        print(f"   Font Family: {fonts.get('family', 'N/A')}")
        chapter_font = fonts.get('chapter_heading', {})
        if isinstance(chapter_font, dict):
            print(f"   Chapter Heading: {chapter_font.get('size', 'N/A')}pt, Bold: {chapter_font.get('bold', False)}, All Caps: {chapter_font.get('all_caps', False)}")
        section_font = fonts.get('section_heading', {})
        if isinstance(section_font, dict):
            print(f"   Section Heading: {section_font.get('size', 'N/A')}pt, Bold: {section_font.get('bold', False)}, All Caps: {section_font.get('all_caps', False)}")
        print(f"   Page Setup: {guidelines_config.get('page_setup', {})}")
        print(f"   Spacing: {guidelines_config.get('spacing', {})}")
        print(f"   Numbering: {guidelines_config.get('numbering', {})}")
        
        # Display Codebase Structure
        print("\n📁 CODEBASE STRUCTURE:")
        print("-" * 80)
        print(f"   Project Name: {codebase_structure.get('name', 'Unknown')}")
        print(f"   Project Type: {codebase_structure.get('project_type', 'Unknown')}")
        print(f"   Main Technologies: {codebase_structure.get('main_technologies', [])}")
        print(f"   Key Components: {codebase_structure.get('key_components', [])}")
        print(f"   Architecture Pattern: {codebase_structure.get('architecture_pattern', 'N/A')}")
        print(f"   Complexity Level: {codebase_structure.get('complexity_level', 'N/A')}")
        print(f"   Suggested Chapters: {codebase_structure.get('suggested_chapters', [])}")
        
        # Show files with code snippets
        print(f"\n   Files with Code Snippets:")
        files_with_code = [f for f in codebase_structure.get('files', []) if f.get('has_code')]
        print(f"      Total: {len(files_with_code)} files have code snippets")
        for file_info in files_with_code[:5]:
            file_path = file_info.get('path', 'Unknown')
            code_len = len(file_info.get('code_snippet', ''))
            print(f"      - {file_path}: {code_len} characters of code")
        
        # Show sample code snippets
        if files_with_code:
            print(f"\n   Sample Code Snippet (first file):")
            first_file = files_with_code[0]
            code_snippet = first_file.get('code_snippet', '')
            if code_snippet:
                preview = code_snippet[:500] + "..." if len(code_snippet) > 500 else code_snippet
                print(f"      File: {first_file.get('path', 'Unknown')}")
                print(f"      Preview (first 500 chars):")
                print(f"      {'-' * 76}")
                for line in preview.split('\n')[:10]:
                    print(f"      {line}")
                print(f"      {'-' * 76}")
        
        # Output file locations
        output_dir = Path(f"outputs/intermediate/job_{job_id}")
        print(f"\n📂 OUTPUT FILES:")
        print("-" * 80)
        print(f"   Guidelines Config: {output_dir / 'guidelines_config.json'}")
        print(f"   Codebase Structure: {output_dir / 'codebase_structure.json'}")
        print(f"   Parser Output: {output_dir / 'parser_output.json'}")
        
        # Save detailed output for inspection
        output_dir = PROJECT_ROOT / "tests" / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"parser_test_output_{job_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\n   Full Output Saved: {output_file}")
        
        print()
        print("=" * 80)
        print("✅ PARSER AGENT TEST COMPLETE")
        print("=" * 80)
        
        return result
        
    except Exception as e:
        print(f"❌ Parser Agent Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_parser_outputs(project1_zip: str, project2_zip: str, guidelines_pdf: str):
    """
    Compare parser agent output for two different projects
    """
    print("\n" + "=" * 80)
    print("COMPARING TWO PROJECTS")
    print("=" * 80)
    
    import time
    job_id_1 = f"test_project1_{int(time.time())}"
    job_id_2 = f"test_project2_{int(time.time()) + 1}"
    
    print("\n📦 Testing Project 1...")
    result1 = test_parser_agent(project1_zip, guidelines_pdf, job_id_1)
    
    print("\n📦 Testing Project 2...")
    result2 = test_parser_agent(project2_zip, guidelines_pdf, job_id_2)
    
    if result1 and result2:
        print("\n" + "=" * 80)
        print("COMPARISON RESULTS")
        print("=" * 80)
        
        # Compare project names
        name1 = result1['codebase'].get('name', 'Unknown')
        name2 = result2['codebase'].get('name', 'Unknown')
        print(f"\nProject Names:")
        print(f"   Project 1: {name1}")
        print(f"   Project 2: {name2}")
        print(f"   ✅ Different" if name1 != name2 else "   ⚠️  Same (potential issue)")
        
        # Compare project types
        type1 = result1['codebase'].get('project_type', 'Unknown')
        type2 = result2['codebase'].get('project_type', 'Unknown')
        print(f"\nProject Types:")
        print(f"   Project 1: {type1}")
        print(f"   Project 2: {type2}")
        
        # Compare technologies
        tech1 = set(result1['codebase'].get('main_technologies', []))
        tech2 = set(result2['codebase'].get('main_technologies', []))
        print(f"\nTechnologies:")
        print(f"   Project 1: {', '.join(tech1)}")
        print(f"   Project 2: {', '.join(tech2)}")
        print(f"   Overlap: {', '.join(tech1 & tech2)}")
        print(f"   Unique to Project 1: {', '.join(tech1 - tech2)}")
        print(f"   Unique to Project 2: {', '.join(tech2 - tech1)}")
        
        # Compare file counts
        files1 = len(result1['codebase'].get('files', []))
        files2 = len(result2['codebase'].get('files', []))
        print(f"\nFile Counts:")
        print(f"   Project 1: {files1} files")
        print(f"   Project 2: {files2} files")
        
        # Check for code snippets
        code_files1 = len([f for f in result1['codebase'].get('files', []) if f.get('has_code')])
        code_files2 = len([f for f in result2['codebase'].get('files', []) if f.get('has_code')])
        print(f"\nFiles with Code Snippets:")
        print(f"   Project 1: {code_files1} files")
        print(f"   Project 2: {code_files2} files")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Parser Agent on different projects")
    parser.add_argument("--project", type=str, help="Path to project ZIP file")
    parser.add_argument("--guidelines", type=str, help="Path to guidelines PDF")
    parser.add_argument("--job-id", type=str, help="Optional job ID for testing", default=None)
    parser.add_argument("--compare", type=str, nargs=2, metavar=("PROJECT1", "PROJECT2"), 
                       help="Compare two projects (requires --guidelines)")
    
    args = parser.parse_args()
    
    if args.compare:
        if not args.guidelines:
            print("❌ Error: --guidelines required when using --compare")
            sys.exit(1)
        compare_parser_outputs(args.compare[0], args.compare[1], args.guidelines)
    else:
        if not args.project or not args.guidelines:
            print("❌ Error: --project and --guidelines are required")
            print("\nUsage examples:")
            print("  python test_parser_agent.py --project path/to/project.zip --guidelines path/to/guidelines.pdf")
            print("  python test_parser_agent.py --compare project1.zip project2.zip --guidelines guidelines.pdf")
            sys.exit(1)
        
        test_parser_agent(args.project, args.guidelines, args.job_id)
