"""
Simple Interactive Test for Parser Agent
Just modify the paths below and run: python test_parser_simple.py
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.test_parser_agent import test_parser_agent

# ============================================
# CONFIGURE YOUR TEST HERE
# ============================================

# Path to your project ZIP file
PROJECT_ZIP = "path/to/your/project.zip"  # CHANGE THIS

# Path to your guidelines PDF
GUIDELINES_PDF = "path/to/your/guidelines.pdf"  # CHANGE THIS

# Optional: Custom job ID (leave None for auto-generated)
JOB_ID = None  # e.g., "test_treezip_001"

# ============================================
# RUN THE TEST
# ============================================

if __name__ == "__main__":
    # Check if paths are configured
    if "path/to/your" in PROJECT_ZIP or "path/to/your" in GUIDELINES_PDF:
        print("❌ Please configure PROJECT_ZIP and GUIDELINES_PDF in the script first!")
        print(f"\nCurrent values:")
        print(f"  PROJECT_ZIP: {PROJECT_ZIP}")
        print(f"  GUIDELINES_PDF: {GUIDELINES_PDF}")
        sys.exit(1)
    
    # Check if files exist
    if not Path(PROJECT_ZIP).exists():
        print(f"❌ Project ZIP not found: {PROJECT_ZIP}")
        sys.exit(1)
    
    if not Path(GUIDELINES_PDF).exists():
        print(f"❌ Guidelines PDF not found: {GUIDELINES_PDF}")
        sys.exit(1)
    
    # Run the test
    print("Starting Parser Agent Test...")
    print(f"Project: {PROJECT_ZIP}")
    print(f"Guidelines: {GUIDELINES_PDF}")
    print()
    
    result = test_parser_agent(PROJECT_ZIP, GUIDELINES_PDF, JOB_ID)
    
    if result:
        print("\n✅ Test completed successfully!")
        print("\nTo view detailed output:")
        if JOB_ID:
            print(f"  - Check: outputs/intermediate/job_{JOB_ID}/")
        else:
            print("  - Check: outputs/intermediate/job_*/ (latest)")
        print("  - Full JSON: parser_test_output_*.json")
    else:
        print("\n❌ Test failed. Check the error messages above.")

