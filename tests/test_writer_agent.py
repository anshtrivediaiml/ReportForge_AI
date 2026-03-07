"""
Test Script for Writer Agent
Tests the writer agent to analyze its output
"""
import sys
import argparse
from pathlib import Path
import json
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.writer_agent import WriterAgent
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")


def test_writer_agent(intermediate_dir: str, job_id: str = None):
    """
    Test writer agent using parser and planner output
    
    Args:
        intermediate_dir: Path to intermediate directory containing parser and planner output
                          (e.g., "outputs/intermediate/job_test_1767102617")
        job_id: Optional job ID (defaults to extracting from directory name)
    """
    intermediate_path = Path(intermediate_dir)
    
    # Extract job_id from directory name if not provided
    if not job_id:
        job_id = intermediate_path.name.replace("job_", "")
    
    print("=" * 80)
    print(f"TESTING WRITER AGENT")
    print("=" * 80)
    print(f"Intermediate Directory: {intermediate_dir}")
    print(f"Job ID: {job_id}")
    print("=" * 80)
    print()
    
    # Step 1: Load parser and planner output
    print("STEP 1: Loading Parser and Planner Output...")
    print("-" * 80)
    
    codebase_structure_path = intermediate_path / "codebase_structure.json"
    outline_path = intermediate_path / "report_outline.json"
    
    if not codebase_structure_path.exists():
        print(f"[ERROR] codebase_structure.json not found at: {codebase_structure_path}")
        print("   Please run the Parser Agent first to generate this file.")
        return
    
    if not outline_path.exists():
        print(f"[ERROR] report_outline.json not found at: {outline_path}")
        print("   Please run the Planner Agent first to generate this file.")
        return
    
    try:
        with open(codebase_structure_path, 'r', encoding='utf-8') as f:
            codebase_structure = json.load(f)
        print(f"[OK] Loaded codebase_structure.json")
        print(f"   Project: {codebase_structure.get('name', 'Unknown')}")
        print(f"   Type: {codebase_structure.get('project_type', 'Unknown')}")
        print(f"   Technologies: {', '.join(codebase_structure.get('main_technologies', []))}")
        print(f"   Code Files: {len(codebase_structure.get('code_content', {}))}")
        
        with open(outline_path, 'r', encoding='utf-8') as f:
            outline = json.load(f)
        print(f"[OK] Loaded report_outline.json")
        print(f"   Report Title: {outline.get('report_title', 'Unknown')}")
        print(f"   Total Chapters: {outline.get('_metadata', {}).get('total_chapters', 0)}")
        print(f"   Total Sections: {outline.get('_metadata', {}).get('total_sections', 0)}")
        
    except Exception as e:
        print(f"[ERROR] loading input files: {e}")
        return
    
    print()
    
    # Step 2: Run Writer Agent
    print("STEP 2: Running Writer Agent...")
    print("-" * 80)
    print("   This may take several minutes as it generates content for each section...")
    print()
    
    try:
        writer = WriterAgent(job_id=job_id)
        content = writer.write_all_content(outline, codebase_structure)
        
        print()
        print("=" * 80)
        print("WRITER AGENT OUTPUT SUMMARY")
        print("=" * 80)
        print()
        
        print("REPORT CONTENT:")
        print("-" * 80)
        print(f"   Report Title: {content.get('report_title', 'N/A')}")
        print(f"   Total Chapters: {len(content.get('chapters', []))}")
        
        total_sections = sum(len(ch.get('sections', [])) for ch in content.get('chapters', []))
        print(f"   Total Sections: {total_sections}")
        print()
        
        print("CHAPTERS:")
        print("-" * 80)
        for chapter in content.get('chapters', []):
            chapter_num = chapter.get('chapter_number', '?')
            chapter_title = chapter.get('chapter_title', 'Untitled')
            sections = chapter.get('sections', [])
            
            print(f"   Chapter {chapter_num}: {chapter_title}")
            print(f"      Sections: {len(sections)}")
            
            for section in sections[:2]:  # Show first 2 sections
                section_num = section.get('number', section.get('section_number', '?'))
                section_title = section.get('title', 'Untitled')
                content_preview = section.get('content', '')[:150] + "..." if len(section.get('content', '')) > 150 else section.get('content', '')
                has_table = section.get('table_data') is not None
                has_diagram = section.get('mermaid_code') is not None
                
                table_info = " [TABLE]" if has_table else ""
                diagram_info = f" [DIAGRAM]" if has_diagram else ""
                
                print(f"      {section_num}. {section_title}{table_info}{diagram_info}")
                print(f"         Content preview: {content_preview}")
            
            if len(sections) > 2:
                print(f"      ... and {len(sections) - 2} more sections")
            print()
        
        print("OUTPUT FILE:")
        print("-" * 80)
        output_path = intermediate_path / "chapters_content.json"
        print(f"   Saved to: {output_path}")
        print()
        
        # Save full output for inspection
        output_dir = PROJECT_ROOT / "tests" / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"writer_test_output_{job_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"   Full Output Saved: {output_file}")
        print()
        
        print("=" * 80)
        print("[OK] WRITER AGENT TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] running Writer Agent: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Writer Agent")
    parser.add_argument(
        "--intermediate-dir",
        type=str,
        required=True,
        help="Path to intermediate directory containing parser and planner output (e.g., outputs/intermediate/job_test_1767102617)"
    )
    parser.add_argument(
        "--job-id",
        type=str,
        default=None,
        help="Optional job ID (defaults to extracting from directory name)"
    )
    
    args = parser.parse_args()
    
    test_writer_agent(args.intermediate_dir, args.job_id)

