"""
Test Script for Planner Agent
Tests the planner agent to analyze its output
"""
import sys
import argparse
from pathlib import Path
import json
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.planner_agent import PlannerAgent
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")


def test_planner_agent(intermediate_dir: str, job_id: str = None):
    """
    Test planner agent using parser output
    
    Args:
        intermediate_dir: Path to intermediate directory containing parser output
                          (e.g., "outputs/intermediate/job_test_1767102617")
        job_id: Optional job ID (defaults to extracting from directory name)
    """
    intermediate_path = Path(intermediate_dir)
    
    # Extract job_id from directory name if not provided
    if not job_id:
        job_id = intermediate_path.name.replace("job_", "")
    
    print("=" * 80)
    print(f"TESTING PLANNER AGENT")
    print("=" * 80)
    print(f"Intermediate Directory: {intermediate_dir}")
    print(f"Job ID: {job_id}")
    print("=" * 80)
    print()
    
    # Step 1: Load parser output
    print("STEP 1: Loading Parser Output...")
    print("-" * 80)
    
    codebase_structure_path = intermediate_path / "codebase_structure.json"
    guidelines_config_path = intermediate_path / "guidelines_config.json"
    
    if not codebase_structure_path.exists():
        print(f"[ERROR] codebase_structure.json not found at: {codebase_structure_path}")
        print("   Please run the Parser Agent first to generate this file.")
        return
    
    if not guidelines_config_path.exists():
        print(f"[ERROR] guidelines_config.json not found at: {guidelines_config_path}")
        print("   Please run the Parser Agent first to generate this file.")
        return
    
    try:
        with open(codebase_structure_path, 'r', encoding='utf-8') as f:
            codebase_structure = json.load(f)
        print(f"[OK] Loaded codebase_structure.json")
        print(f"   Project: {codebase_structure.get('name', 'Unknown')}")
        print(f"   Type: {codebase_structure.get('project_type', 'Unknown')}")
        print(f"   Technologies: {', '.join(codebase_structure.get('main_technologies', []))}")
        print(f"   Modules: {len(codebase_structure.get('modules', []))}")
        print(f"   Code Files: {len(codebase_structure.get('code_content', {}))}")
        
        with open(guidelines_config_path, 'r', encoding='utf-8') as f:
            guidelines_config = json.load(f)
        print(f"[OK] Loaded guidelines_config.json")
        print(f"   Font: {guidelines_config.get('font_family', 'Unknown')}")
        print(f"   Chapter Heading: {guidelines_config.get('chapter_heading', {}).get('size', 'Unknown')}pt")
        
    except Exception as e:
        print(f"[ERROR] loading parser output: {e}")
        return
    
    print()
    
    # Step 2: Run Planner Agent
    print("STEP 2: Running Planner Agent...")
    print("-" * 80)
    
    try:
        planner = PlannerAgent(job_id=job_id)
        outline = planner.create_outline(codebase_structure, guidelines_config)
        
        print()
        print("=" * 80)
        print("PLANNER AGENT OUTPUT SUMMARY")
        print("=" * 80)
        print()
        
        print("REPORT OUTLINE:")
        print("-" * 80)
        print(f"   Report Title: {outline.get('report_title', 'N/A')}")
        print(f"   Total Chapters: {outline.get('_metadata', {}).get('total_chapters', 0)}")
        print(f"   Total Sections: {outline.get('_metadata', {}).get('total_sections', 0)}")
        print()
        
        print("CHAPTERS:")
        print("-" * 80)
        for chapter in outline.get('chapters', []):
            chapter_num = chapter.get('number', '?')
            chapter_title = chapter.get('title', 'Untitled')
            sections = chapter.get('sections', [])
            
            print(f"   Chapter {chapter_num}: {chapter_title}")
            print(f"      Sections: {len(sections)}")
            
            for section in sections[:3]:  # Show first 3 sections
                section_num = section.get('number', '?')
                section_title = section.get('title', 'Untitled')
                needs_diagram = section.get('needs_diagram', False)
                needs_table = section.get('needs_table', False)
                
                diagram_info = f" [DIAGRAM: {section.get('diagram_type', 'flowchart')}]" if needs_diagram else ""
                table_info = " [TABLE]" if needs_table else ""
                
                print(f"      {section_num}. {section_title}{diagram_info}{table_info}")
            
            if len(sections) > 3:
                print(f"      ... and {len(sections) - 3} more sections")
            print()
        
        print("OUTPUT FILE:")
        print("-" * 80)
        output_path = intermediate_path / "report_outline.json"
        print(f"   Saved to: {output_path}")
        print()
        
        # Save full output for inspection
        output_dir = PROJECT_ROOT / "tests" / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"planner_test_output_{job_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(outline, f, indent=2)
        print(f"   Full Output Saved: {output_file}")
        print()
        
        print("=" * 80)
        print("[OK] PLANNER AGENT TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"[ERROR] running Planner Agent: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Planner Agent")
    parser.add_argument(
        "--intermediate-dir",
        type=str,
        required=True,
        help="Path to intermediate directory containing parser output (e.g., outputs/intermediate/job_test_1767102617)"
    )
    parser.add_argument(
        "--job-id",
        type=str,
        default=None,
        help="Optional job ID (defaults to extracting from directory name)"
    )
    
    args = parser.parse_args()
    
    test_planner_agent(args.intermediate_dir, args.job_id)

