# Parser Agent Testing - Complete Guide

## 📋 Overview

The **Parser Agent** is the first agent in the pipeline. It:
1. **Extracts formatting rules** from the guidelines PDF
2. **Analyzes the project structure** and identifies key characteristics
3. **Extracts code content** from project files

## 🎯 What to Test

### Test 1: Single Project Analysis
Verify the parser correctly identifies:
- ✅ Project name (specific, not generic)
- ✅ Project type (matches actual project)
- ✅ Technologies (matches tech stack)
- ✅ Code snippets (actual code extracted)

### Test 2: Multiple Projects Comparison
Verify different projects produce:
- ✅ Different project names
- ✅ Different project types
- ✅ Different technologies
- ✅ Different code snippets

## 🚀 How to Run Tests

### Method 1: Simple Script (Recommended for First Test)

1. Edit `test_parser_simple.py`:
   ```python
   PROJECT_ZIP = "path/to/your/project.zip"
   GUIDELINES_PDF = "path/to/your/guidelines.pdf"
   ```

2. Run:
   ```bash
   python test_parser_simple.py
   ```

### Method 2: Command Line (Flexible)

```bash
# Test single project
python test_parser_agent.py --project "project.zip" --guidelines "guidelines.pdf"

# Test with custom job ID
python test_parser_agent.py --project "project.zip" --guidelines "guidelines.pdf" --job-id "test_001"

# Compare two projects
python test_parser_agent.py --compare "project1.zip" "project2.zip" --guidelines "guidelines.pdf"
```

## 📊 What the Output Shows

### Console Output:
```
================================================================================
TESTING PARSER AGENT
================================================================================
Project ZIP: path/to/project.zip
Guidelines PDF: path/to/guidelines.pdf
Job ID: test_1234567890
================================================================================

STEP 1: Analyzing Project Structure...
--------------------------------------------------------------------------------
✅ Project Analysis Complete
   Project Name: Treezip Main
   Files Found: 4
   Technologies: JavaScript, HTML, Node.js
   Entry Points: index.html, app.js
   Total Lines: 526

   Sample Files (first 10):
      1. TreeZip-main/app.js (150 lines, code: YES, snippet: 2000 chars)
      2. TreeZip-main/index.html (50 lines, code: YES, snippet: 1000 chars)
      ...

STEP 2: Running Parser Agent...
--------------------------------------------------------------------------------
   Parsing guidelines PDF...
   ✅ Guidelines parsed
   Analyzing project structure with LLM...
   ✅ Project structure analyzed

================================================================================
PARSER AGENT OUTPUT SUMMARY
================================================================================

📋 GUIDELINES CONFIG:
--------------------------------------------------------------------------------
   Font Family: Times New Roman
   Chapter Heading: 16pt, Bold: True, All Caps: True
   Section Heading: 14pt, Bold: True, All Caps: True
   ...

📁 CODEBASE STRUCTURE:
--------------------------------------------------------------------------------
   Project Name: Treezip Main
   Project Type: web app
   Main Technologies: ['JavaScript', 'HTML', 'Node.js']
   Key Components: ['app.js', 'index.html']
   Architecture Pattern: Single-page application
   Complexity Level: simple

   Files with Code Snippets:
      Total: 3 files have code snippets
      - TreeZip-main/app.js: 2000 characters of code
      - TreeZip-main/index.html: 1000 characters of code
      ...

📂 OUTPUT FILES:
--------------------------------------------------------------------------------
   Guidelines Config: outputs/intermediate/job_test_1234567890/guidelines_config.json
   Codebase Structure: outputs/intermediate/job_test_1234567890/codebase_structure.json
   Parser Output: outputs/intermediate/job_test_1234567890/parser_output.json

   Full Output Saved: parser_test_output_test_1234567890.json
```

## 🔍 Detailed Output Files

### 1. `guidelines_config.json`
Contains formatting rules extracted from PDF:
```json
{
  "fonts": {
    "family": "Times New Roman",
    "chapter_heading": {"size": 16, "bold": true, "all_caps": true},
    "section_heading": {"size": 14, "bold": true, "all_caps": true}
  },
  "page_setup": {...},
  "spacing": {...},
  "numbering": {...}
}
```

### 2. `codebase_structure.json`
Contains project analysis:
```json
{
  "name": "Treezip Main",
  "project_type": "web app",
  "main_technologies": ["JavaScript", "HTML"],
  "files": [
    {
      "path": "TreeZip-main/app.js",
      "lines": 150,
      "has_code": true,
      "code_snippet": "function generateTree() {...}"
    }
  ]
}
```

### 3. `parser_output.json`
Combined output (guidelines + codebase)

## ✅ Success Criteria

### For Each Project:
- [ ] Project name is specific (not "temp extract" or "cli tool")
- [ ] Project type matches actual project
- [ ] Technologies list matches actual tech stack
- [ ] Files list includes expected files
- [ ] Code files have `has_code: true`
- [ ] Code snippets contain actual code (check length > 0)

### For Different Projects:
- [ ] Different project names
- [ ] Different project types
- [ ] Different technologies
- [ ] Different code snippets

## ❌ Common Issues to Watch For

### Issue 1: Generic Project Name
**Symptom**: Name is "temp extract", "cli tool", "project"
**Check**: Look at `codebase_structure.json` → `name` field
**Fix**: Verify `_extract_project_name()` in `code_analyzer.py`

### Issue 2: Wrong Project Type
**Symptom**: Web app detected as "CLI tool" or vice versa
**Check**: Look at `codebase_structure.json` → `project_type` field
**Fix**: Verify LLM receives actual file list and code snippets

### Issue 3: No Code Snippets
**Symptom**: Files have `has_code: false` or empty `code_snippet`
**Check**: Look at `codebase_structure.json` → `files` array
**Fix**: Check code extraction in `code_analyzer.py` (lines 183-200)

### Issue 4: Same Output for Different Projects
**Symptom**: Two different projects produce identical analysis
**Check**: Use `--compare` flag to compare outputs
**Fix**: Verify job_id isolation and extraction directory cleanup

## 📝 Testing Checklist

### Before Testing:
- [ ] Have at least 2 different project ZIP files ready
- [ ] Have guidelines PDF ready
- [ ] Ensure Mistral API key is configured

### During Testing:
- [ ] Run test on Project 1
- [ ] Verify output files are created
- [ ] Check project name is correct
- [ ] Check code snippets exist
- [ ] Run test on Project 2
- [ ] Compare outputs (should be different)

### After Testing:
- [ ] Review `codebase_structure.json` for accuracy
- [ ] Verify code snippets contain actual code
- [ ] Check that different projects produce different outputs
- [ ] Document any issues found

## 🎯 Next Steps

Once Parser Agent is verified:
1. **Test Planner Agent** - Check outline generation
2. **Test Writer Agent** - Check content generation (with code snippets)
3. **Test Builder Agent** - Check document formatting
4. **Test Full Pipeline** - End-to-end report generation

## 📚 Related Files

- `test_parser_agent.py` - Main test script
- `test_parser_simple.py` - Simple interactive version
- `TEST_PARSER_GUIDE.md` - Detailed guide
- `PARSER_OUTPUT_ANALYSIS.md` - Output interpretation guide

