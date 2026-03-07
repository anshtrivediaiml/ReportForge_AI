# Testing Parser Agent - Guide

## Overview

The Parser Agent is responsible for:
1. **Parsing Guidelines PDF** - Extracts formatting rules (fonts, spacing, numbering, etc.)
2. **Analyzing Project Structure** - Analyzes the uploaded project and identifies:
   - Project name
   - Project type (web app, CLI tool, library, etc.)
   - Main technologies
   - Key components
   - Architecture pattern
   - Complexity level

## What the Parser Agent Produces

### Output Files (in `outputs/intermediate/job_{job_id}/`):

1. **`guidelines_config.json`** - Extracted formatting rules from PDF:
   - Font family, sizes, styles
   - Page setup (margins, paper size)
   - Spacing rules
   - Numbering schemes
   - Headers/footers

2. **`codebase_structure.json`** - Analyzed project structure:
   - Project name and type
   - Technologies detected
   - File list with code snippets
   - Entry points
   - Architecture pattern
   - Suggested chapters

3. **`parser_output.json`** - Combined output (guidelines + codebase)

## How to Test

### Method 1: Command Line (Recommended)

```bash
# Test single project
python test_parser_agent.py --project path/to/project.zip --guidelines path/to/guidelines.pdf

# Test with custom job ID
python test_parser_agent.py --project path/to/project.zip --guidelines path/to/guidelines.pdf --job-id my_test_001

# Compare two projects
python test_parser_agent.py --compare project1.zip project2.zip --guidelines guidelines.pdf
```

### Method 2: Interactive Python Script

Create a simple test file:

```python
from test_parser_agent import test_parser_agent

# Test TreeZip project
test_parser_agent(
    project_zip_path="path/to/TreeZip-main.zip",
    guidelines_pdf_path="path/to/guidelines.pdf",
    job_id="test_treezip"
)
```

## What to Check

### ✅ Good Output Indicators:

1. **Project Name** - Should be specific to the project (not "temp extract" or "cli tool")
2. **Project Type** - Should match actual project (e.g., "web app" for TreeZip, not "CLI tool")
3. **Technologies** - Should reflect actual tech stack in the project
4. **Code Snippets** - Should have code content extracted (not just file paths)
5. **Files List** - Should list actual files from the project

### ❌ Problem Indicators:

1. **Generic Project Name** - "temp extract", "cli tool", "project" → Issue with name extraction
2. **Wrong Project Type** - CLI tool detected as web app → Issue with analysis
3. **No Code Snippets** - Files don't have `has_code: true` → Code extraction failed
4. **Missing Files** - Expected files not in the list → Extraction issue
5. **Same Output for Different Projects** → Content mixing issue

## Example Output Analysis

### For TreeZip Project:

**Expected:**
- Project Name: "TreeZip" or "Treezip Main" (not "temp extract")
- Project Type: "web app" or "browser-based application"
- Technologies: "JavaScript", "HTML", "Node.js"
- Files: Should include `app.js`, `index.html`, `package-lock.json`
- Code Snippets: Should have actual code from `app.js` and `index.html`

**If you see:**
- Project Type: "CLI tool" → ❌ Wrong analysis
- Technologies: "Python", "Express" → ❌ Hallucination
- No code snippets → ❌ Code extraction failed

## Debugging Tips

1. **Check extraction directory**: Look in `temp_extract/job_{job_id}/` to see what files were extracted
2. **Check code snippets**: Open `codebase_structure.json` and verify `code_snippet` fields exist
3. **Compare outputs**: Use `--compare` to see if different projects produce different outputs
4. **Check logs**: The script shows detailed logs of each step

## Next Steps After Testing

Once you verify parser agent works correctly:
1. Test Planner Agent - See what outline it generates
2. Test Writer Agent - See what content it writes
3. Test Builder Agent - See final document formatting

