# Parser Agent Output Analysis Guide

## Understanding Parser Agent Output

The Parser Agent produces three main outputs that you should analyze:

---

## 1. Guidelines Config (`guidelines_config.json`)

### What It Contains:
- **Font specifications** (family, sizes, styles)
- **Page setup** (margins, paper size, orientation)
- **Spacing rules** (line spacing, paragraph spacing)
- **Numbering schemes** (chapters, sections, figures, tables)
- **Headers/footers** configuration

### What to Check:
✅ **Good**: 
- Font family extracted correctly (e.g., "Times New Roman")
- Chapter heading: 16pt, bold, all caps
- Section heading: 14pt, bold, all caps
- Proper margins and spacing values

❌ **Problems**:
- Missing or default values only
- Font family not extracted
- Incorrect heading sizes

### Example Good Output:
```json
{
  "fonts": {
    "family": "Times New Roman",
    "chapter_heading": {
      "size": 16,
      "bold": true,
      "all_caps": true
    },
    "section_heading": {
      "size": 14,
      "bold": true,
      "all_caps": true
    }
  },
  "page_setup": {
    "paper_size": "A4",
    "margins": {
      "left": "1.25in",
      "right": "1.0in",
      "top": "1.0in",
      "bottom": "1.0in"
    }
  }
}
```

---

## 2. Codebase Structure (`codebase_structure.json`)

### What It Contains:
- **Project metadata** (name, type, technologies)
- **File list** with code snippets
- **Architecture analysis** (pattern, complexity)
- **Component identification**

### Critical Fields to Check:

#### A. Project Name
```json
"name": "Treezip Main"  // ✅ Good - specific to project
"name": "temp extract"  // ❌ Bad - generic name
```

#### B. Project Type
```json
"project_type": "web app"           // ✅ Good - matches actual project
"project_type": "CLI tool"           // ❌ Bad - wrong type for web app
```

#### C. Technologies
```json
"main_technologies": ["JavaScript", "HTML", "Node.js"]  // ✅ Good - actual tech stack
"main_technologies": ["Python", "Express"]              // ❌ Bad - not in project
```

#### D. Files with Code Snippets
```json
"files": [
  {
    "path": "TreeZip-main/app.js",
    "lines": 150,
    "has_code": true,              // ✅ Must be true
    "code_snippet": "function..."  // ✅ Must contain actual code
  }
]
```

**Critical Check**: Every code file should have:
- `"has_code": true`
- `"code_snippet"` field with actual code content (not empty)

---

## 3. Comparison Test Results

### When Testing Two Different Projects:

#### ✅ Good Results:
- **Different project names** for different projects
- **Different project types** (e.g., "web app" vs "CLI tool")
- **Different technologies** lists
- **Different file lists**
- **Different code snippets**

#### ❌ Problem Indicators:
- **Same project name** for different projects → Name extraction issue
- **Same project type** for different projects → Analysis issue
- **Same technologies** for different projects → Not analyzing correctly
- **Same code snippets** → Content mixing issue

---

## Quick Test Checklist

Run this checklist for each project you test:

- [ ] Project name is specific (not "temp extract" or "cli tool")
- [ ] Project type matches actual project (web app, CLI, library, etc.)
- [ ] Technologies list matches actual tech stack
- [ ] Files list includes expected files
- [ ] Code files have `has_code: true`
- [ ] Code snippets contain actual code (not empty)
- [ ] Different projects produce different outputs

---

## Common Issues and Fixes

### Issue 1: Generic Project Name
**Symptom**: Name is "temp extract", "cli tool", "project"
**Fix**: Check `_extract_project_name()` in `code_analyzer.py`
**Test**: Verify it reads package.json, setup.py, README.md

### Issue 2: Wrong Project Type
**Symptom**: Web app detected as CLI tool
**Fix**: Check `ANALYZE_PROJECT_PROMPT` in `prompts.py`
**Test**: Verify LLM receives actual file list and code snippets

### Issue 3: No Code Snippets
**Symptom**: Files have `has_code: false` or missing `code_snippet`
**Fix**: Check code extraction in `code_analyzer.py` line 183-200
**Test**: Verify files are being read and content extracted

### Issue 4: Same Output for Different Projects
**Symptom**: Two different projects produce identical analysis
**Fix**: Check job_id isolation, extraction directory cleanup
**Test**: Use `--compare` flag to compare outputs

---

## Testing Workflow

1. **Test Single Project**:
   ```bash
   python test_parser_agent.py --project project1.zip --guidelines guidelines.pdf
   ```

2. **Check Output Files**:
   - Open `outputs/intermediate/job_{job_id}/codebase_structure.json`
   - Verify project name, type, technologies
   - Check code snippets exist

3. **Test Another Project**:
   ```bash
   python test_parser_agent.py --project project2.zip --guidelines guidelines.pdf
   ```

4. **Compare Results**:
   ```bash
   python test_parser_agent.py --compare project1.zip project2.zip --guidelines guidelines.pdf
   ```

5. **Verify Differences**:
   - Project names should be different
   - Project types should match actual projects
   - Technologies should reflect each project
   - Code snippets should be different

---

## Next Steps

Once Parser Agent is verified:
1. Test **Planner Agent** - Check outline generation
2. Test **Writer Agent** - Check content generation
3. Test **Builder Agent** - Check document formatting
4. Test **Full Pipeline** - End-to-end report generation

