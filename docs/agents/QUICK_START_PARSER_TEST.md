# Quick Start: Testing Parser Agent

## Fastest Way to Test

### Option 1: Simple Script (Easiest)

1. Open `test_parser_simple.py`
2. Change these two lines:
   ```python
   PROJECT_ZIP = "path/to/your/project.zip"      # ← Change this
   GUIDELINES_PDF = "path/to/your/guidelines.pdf"  # ← Change this
   ```
3. Run: `python test_parser_simple.py`

### Option 2: Command Line

```bash
# Navigate to project root
cd C:\Users\AnshTrivedi\Documents\report_generator_ai

# Test a project
python test_parser_agent.py --project "path/to/project.zip" --guidelines "path/to/guidelines.pdf"
```

## What You'll See

The script will show:
1. ✅ Project analysis results (name, files, technologies)
2. ✅ Guidelines parsing results (fonts, formatting)
3. ✅ Codebase structure analysis (project type, components)
4. ✅ Code snippet extraction status
5. ✅ Output file locations

## Output Files Location

After running, check:
- `outputs/intermediate/job_{job_id}/guidelines_config.json`
- `outputs/intermediate/job_{job_id}/codebase_structure.json`
- `parser_test_output_{job_id}.json` (in project root)

## Quick Verification

After running, ask yourself:
1. ✅ Is the project name correct? (not "temp extract")
2. ✅ Is the project type correct? (matches actual project)
3. ✅ Are technologies correct? (matches actual tech stack)
4. ✅ Do files have code snippets? (check `has_code: true`)

If all ✅ → Parser Agent is working correctly!
If any ❌ → Check the specific issue and fix it.

