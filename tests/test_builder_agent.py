"""
Test Script for Builder Agent
Tests the builder agent to analyze its output
"""
import sys
import argparse
from pathlib import Path
import json
from typing import Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.builder_agent import BuilderAgent
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>", level="INFO")


def test_builder_agent(intermediate_dir: str, job_id: str = None):
    """
    Test builder agent using writer, parser, and planner output
    
    Args:
        intermediate_dir: Path to intermediate directory containing parser, planner, and writer output
                          (e.g., "outputs/intermediate/job_test_1767100105")
        job_id: Optional job ID (defaults to extracting from directory name)
    """
    intermediate_path = Path(intermediate_dir)
    
    # Extract job_id from directory name if not provided
    if not job_id:
        job_id = intermediate_path.name.replace("job_", "")
    
    print("=" * 80)
    print("TESTING BUILDER AGENT")
    print("=" * 80)
    print(f"Intermediate Directory: {intermediate_dir}")
    print(f"Job ID: {job_id}")
    print("=" * 80)
    print()
    
    # Step 1: Load required input files
    print("STEP 1: Loading Input Files...")
    print("-" * 80)
    
    chapters_content_path = intermediate_path / "chapters_content.json"
    guidelines_config_path = intermediate_path / "guidelines_config.json"
    report_outline_path = intermediate_path / "report_outline.json"
    
    # Check if files exist
    if not chapters_content_path.exists():
        print(f"[ERROR] chapters_content.json not found at: {chapters_content_path}")
        print("        Run Writer Agent first to generate this file.")
        return
    
    if not guidelines_config_path.exists():
        print(f"[ERROR] guidelines_config.json not found at: {guidelines_config_path}")
        print("        Run Parser Agent first to generate this file.")
        return
    
    if not report_outline_path.exists():
        print(f"[ERROR] report_outline.json not found at: {report_outline_path}")
        print("        Run Planner Agent first to generate this file.")
        return
    
    # Load files
    try:
        with open(chapters_content_path, 'r', encoding='utf-8') as f:
            chapters_content = json.load(f)
        print(f"[OK] Loaded chapters_content.json")
        print(f"   Report Title: {chapters_content.get('report_title', 'N/A')}")
        print(f"   Total Chapters: {len(chapters_content.get('chapters', []))}")
        
        with open(guidelines_config_path, 'r', encoding='utf-8') as f:
            guidelines_config = json.load(f)
        print(f"[OK] Loaded guidelines_config.json")
        
        with open(report_outline_path, 'r', encoding='utf-8') as f:
            report_outline = json.load(f)
        print(f"[OK] Loaded report_outline.json")
        print(f"   Report Title: {report_outline.get('report_title', 'N/A')}")
        print(f"   Total Chapters: {len(report_outline.get('chapters', []))}")
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON file: {e}")
        return
    except Exception as e:
        print(f"[ERROR] Failed to load files: {e}")
        return
    
    print()
    
    # Step 2: Initialize and run Builder Agent
    print("STEP 2: Running Builder Agent...")
    print("-" * 80)
    print("   This may take several minutes as it generates diagrams and assembles the document...")
    print()
    
    try:
        builder = BuilderAgent(job_id=job_id)
        
        output_filename = f"Technical_Report_{job_id}.docx"
        output_path = builder.build_document(
            content=chapters_content,
            guidelines=guidelines_config,
            outline=report_outline,
            output_filename=output_filename
        )
        
        print()
        print("=" * 80)
        print("BUILDER AGENT OUTPUT SUMMARY")
        print("=" * 80)
        print()
        print("DOCUMENT GENERATED:")
        print("-" * 80)
        print(f"   Output Path: {output_path}")
        
        # Check if file exists and get size
        output_file = Path(output_path)
        if output_file.exists():
            file_size_kb = output_file.stat().st_size / 1024
            print(f"   File Size: {file_size_kb:.2f} KB")
            print(f"   File Exists: Yes")
        else:
            print(f"   File Exists: No (ERROR!)")
        
        print()
        print("DOCUMENT STRUCTURE:")
        print("-" * 80)
        print(f"   Report Title: {chapters_content.get('report_title', 'N/A')}")
        
        chapters = chapters_content.get('chapters', [])
        print(f"   Total Chapters: {len(chapters)}")
        
        total_sections = 0
        total_tables = 0
        total_figures = 0
        
        for chapter in chapters:
            chapter_num = chapter.get('chapter_number', '?')
            chapter_title = chapter.get('chapter_title', 'Unknown')
            sections = chapter.get('sections', [])
            total_sections += len(sections)
            
            # Count tables and figures in this chapter
            for section in sections:
                if section.get('table_data'):
                    total_tables += 1
                if section.get('mermaid_code'):
                    total_figures += 1
            
            print(f"   Chapter {chapter_num}: {chapter_title}")
            print(f"      Sections: {len(sections)}")
        
        print()
        print(f"   Total Sections: {total_sections}")
        print(f"   Total Tables: {total_tables}")
        print(f"   Total Figures: {total_figures}")
        
        print()
        print("=" * 80)
        print("[OK] BUILDER AGENT TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("[ERROR] BUILDER AGENT TEST FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Builder Agent")
    parser.add_argument(
        "--intermediate-dir",
        type=str,
        required=True,
        help="Path to intermediate directory containing parser, planner, and writer output (e.g., 'outputs/intermediate/job_test_1767100105')"
    )
    parser.add_argument(
        "--job-id",
        type=str,
        default=None,
        help="Optional job ID (defaults to extracting from directory name)"
    )
    
    args = parser.parse_args()
    
    test_builder_agent(args.intermediate_dir, args.job_id)

