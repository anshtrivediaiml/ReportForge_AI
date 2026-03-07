# Writer Agent - Complete Flow Documentation

## Overview

The **Writer Agent** is responsible for generating natural language documentation content for each section of the report based on the outline created by the Planner Agent. It takes the structured outline and project analysis, then writes comprehensive, project-specific content for each chapter and section.

---

## Input (What It Receives)

### 1. **Report Outline** (`report_outline.json` from Planner Agent)
- **Structure**: Chapters with sections, subsections
- **Content**: 
  - Chapter numbers and titles
  - Section numbers, titles, and descriptions
  - Diagram/table requirements (`needs_diagram`, `needs_table`)
  - Writing guidelines per section (`writing_guideline`)
  - Diagram types (if applicable)

### 2. **Codebase Structure** (`codebase_structure.json` from Parser Agent)
- **Project Information**:
  - Project name, type, technologies
  - Modules, use cases, project purpose
  - **Code Content**: All code files with actual code snippets
  - Capabilities, entry points
  - File structure with code snippets

---

## Processing Flow (Start to End)

### **Step 1: Initialize** (lines 21-28)
- Creates job-specific output directory: `outputs/intermediate/job_{job_id}/`
- Prevents content mixing between jobs

### **Step 2: Main Entry Point - `run()`** (lines 803-820)
- Calls `write_all_content()` to generate all chapters
- Returns complete content structure

### **Step 3: Generate All Content - `write_all_content()`** (lines 719-801)
- Iterates through each chapter in the outline
- For each chapter:
  - **Chapter 1 (Introduction)**: Calls `write_introduction()`
  - **Last Chapter (Conclusion)**: Calls `write_conclusion()`
  - **Middle Chapters**: Calls `write_section()` for each section
- Saves complete content to `chapters_content.json`

### **Step 4: Write Introduction - `write_introduction()`** (lines 81-207)

#### 4.1 Extract Code Snippets
- Calls `_extract_code_snippets()` to get actual code from project files
- Prioritizes main files (app.js, main.py, index.html, etc.)
- Limits: 3000 chars for main files, 2000 for others
- Returns formatted code snippets string

#### 4.2 Build Prompt
- Formats `WRITE_INTRODUCTION_PROMPT` with:
  - Project overview (name, type, technologies)
  - Introduction sections from outline
  - **Actual code content** from files
- Prepends isolation header with job_id, project name, sample files

#### 4.3 Call LLM
- Uses `llm_client.generate_json()` with:
  - System prompt: `WRITER_SYSTEM_PROMPT` (technical writer role)
  - User prompt: formatted introduction prompt
  - Temperature: 0.1 (for stable JSON)
- Expected JSON structure:
  ```json
  {
    "chapter_number": 1,
    "chapter_title": "Introduction",
    "sections": [
      {
        "number": "1.1",
        "title": "Project Overview",
        "content": "Paragraph text..."
      }
    ]
  }
  ```

#### 4.4 Validate and Fallback
- Validates JSON structure
- If invalid: Falls back to `_write_introduction_plain_text()`
- Retries up to 3 times before fallback

### **Step 5: Write Section - `write_section()`** (lines 277-431)

#### 5.1 Extract Relevant Code
- Extracts code snippets from project files
- Prioritizes main files (up to 3), then other files (up to 5)
- Formats code with file paths and content

#### 5.2 Build Prompt
- Formats `WRITE_SECTION_PROMPT` with:
  - Section number, title, description
  - Project context (name, type, technologies)
  - Relevant files list
  - **Actual code content** from files
- Prepends isolation header

#### 5.3 Call LLM
- Uses `llm_client.generate_json()` with:
  - System prompt: `WRITER_SYSTEM_PROMPT`
  - User prompt: formatted section prompt
  - Temperature: 0.1
- Expected JSON structure:
  ```json
  {
    "section_number": "2.1",
    "title": "Core Functionality",
    "content": "Paragraph text...",
    "subsections": [...],  // optional
    "table_data": [...],   // optional
    "mermaid_code": "...", // optional
    "figure_label": "Fig 2.1", // if diagram
    "figure_desc": "..."   // if diagram
  }
  ```

#### 5.4 Validate and Fallback
- Validates JSON structure
- If invalid: Falls back to `_write_section_plain_text()`
- Retries up to 3 times before fallback

### **Step 6: Write Conclusion - `write_conclusion()`** (lines 483-645)

#### 6.1 Extract Code Snippets
- Calls `_extract_code_snippets()` (max 3 files)
- Formats technologies and features as strings

#### 6.2 Build Prompt
- Formats `WRITE_CONCLUSION_PROMPT` with:
  - Project summary
  - Technologies used
  - Main features
  - Conclusion sections from outline
  - **Actual code content** from files
- Prepends isolation header

#### 6.3 Call LLM
- Uses `llm_client.generate_json()` with:
  - System prompt: `WRITER_SYSTEM_PROMPT`
  - User prompt: formatted conclusion prompt
  - Temperature: 0.1
- Expected JSON structure:
  ```json
  {
    "chapter_number": 4,
    "chapter_title": "Conclusion",
    "sections": [
      {
        "number": "",  // empty for conclusion
        "title": "Project Summary",
        "content": "Paragraph text..."
      }
    ]
  }
  ```

#### 6.4 Validate and Normalize
- Validates JSON structure
- Normalizes section numbers (empty strings for conclusion)
- If invalid: Falls back to `_write_conclusion_plain_text()`

### **Step 7: Save Output** (lines 793-795)
- Saves complete content to: `outputs/intermediate/job_{job_id}/chapters_content.json`
- Structure:
  ```json
  {
    "report_title": "...",
    "chapters": [
      {
        "chapter_number": 1,
        "chapter_title": "Introduction",
        "sections": [...]
      }
    ]
  }
  ```

---

## Key Methods

### **`_extract_code_snippets()`** (lines 30-79)
- **Purpose**: Extract actual code content from project files
- **Process**:
  1. Checks if `files` exist in project context
  2. Prioritizes main files (app.js, main.py, index.html, etc.)
  3. Limits code length: 3000 chars for main files, 2000 for others
  4. Formats as: `=== FILE: path ===\ncode\n=== END OF FILE ===`
- **Returns**: Formatted code snippets string

### **`write_introduction()`** (lines 81-207)
- **Purpose**: Generate introduction chapter content
- **Input**: Outline, codebase_structure
- **Output**: Chapter JSON with sections
- **Fallback**: `_write_introduction_plain_text()` if JSON parsing fails

### **`write_section()`** (lines 277-431)
- **Purpose**: Generate content for a single section
- **Input**: Section number, title, description, project context
- **Output**: Section JSON with content, optional table/diagram
- **Fallback**: `_write_section_plain_text()` if JSON parsing fails

### **`write_conclusion()`** (lines 483-645)
- **Purpose**: Generate conclusion chapter content
- **Input**: Outline, codebase_structure
- **Output**: Chapter JSON with sections (no section numbers)
- **Fallback**: `_write_conclusion_plain_text()` if JSON parsing fails

### **`write_all_content()`** (lines 719-801)
- **Purpose**: Generate content for all chapters
- **Process**:
  1. Iterates through outline chapters
  2. Calls appropriate method (introduction/section/conclusion)
  3. Collects all chapter content
  4. Saves to JSON file
- **Returns**: Complete content structure

---

## Key Prompts Used

### **`WRITE_SECTION_PROMPT`** (config/prompts.py:245-343)
- **Purpose**: Generate content for a single section
- **Key Instructions**:
  - Anti-hallucination rules (only use actual code)
  - Writing style guidelines (natural, varied)
  - Table/diagram decision logic
  - Paragraph length limits (100-150 words each)

### **`WRITE_INTRODUCTION_PROMPT`** (config/prompts.py:346-398)
- **Purpose**: Generate introduction chapter
- **Key Instructions**:
  - Use exact section titles from outline
  - Base content on actual code
  - 2-4 paragraphs per section (100-150 words each)

### **`WRITE_CONCLUSION_PROMPT`** (config/prompts.py:401-526)
- **Purpose**: Generate conclusion chapter
- **Key Instructions**:
  - Summarize only what was implemented
  - Realistic future work suggestions
  - 2-3 concise paragraphs per section

---

## Output Structure

### **`chapters_content.json`**
```json
{
  "report_title": "Calculator Web-Application: Technical Documentation",
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_title": "Introduction",
      "sections": [
        {
          "number": "1.1",
          "title": "Project Overview",
          "content": "Paragraph text...",
          "subsections": [...]  // optional
        }
      ]
    },
    {
      "chapter_number": 2,
      "chapter_title": "Implementation",
      "sections": [
        {
          "section_number": "2.1",
          "title": "Core Functionality",
          "content": "Paragraph text...",
          "table_data": [...],   // optional
          "mermaid_code": "...", // optional
          "figure_label": "Fig 2.1",
          "figure_desc": "..."
        }
      ]
    }
  ]
}
```

---

## Design Decisions

### **1. Code-First Approach**
- Always extracts actual code content from files
- Passes code snippets to LLM prompts
- Prevents hallucination by grounding content in actual code

### **2. Job Isolation**
- Each job has its own output directory
- Prevents content mixing between jobs
- Isolation headers in prompts with job_id

### **3. Retry Logic with Fallback**
- Retries JSON parsing up to 3 times
- Falls back to plain text generation if JSON fails
- Ensures pipeline never fails completely

### **4. Anti-Hallucination Safeguards**
- Explicit isolation warnings in prompts
- Code content always included
- Instructions to only describe what's in code
- No assumptions about missing features

### **5. Natural Writing Style**
- Varied sentence length and structure
- Natural transitions and observations
- Human-like flow, not robotic
- Paragraph length limits (100-150 words)

### **6. Optional Tables/Diagrams**
- LLM decides if table/diagram is needed
- No forced generation
- Only includes if LLM explicitly provides
- Tables must be meaningful and project-specific

---

## Data Flow Diagram

```
┌─────────────────────┐
│  Planner Agent      │
│  (report_outline)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Writer Agent       │
│  write_all_content()│
└──────────┬──────────┘
           │
           ├──► write_introduction()
           │    ├──► _extract_code_snippets()
           │    ├──► LLM (WRITE_INTRODUCTION_PROMPT)
           │    └──► _write_introduction_plain_text() [fallback]
           │
           ├──► write_section() [for each middle section]
           │    ├──► Extract relevant code
           │    ├──► LLM (WRITE_SECTION_PROMPT)
           │    └──► _write_section_plain_text() [fallback]
           │
           └──► write_conclusion()
                ├──► _extract_code_snippets()
                ├──► LLM (WRITE_CONCLUSION_PROMPT)
                └──► _write_conclusion_plain_text() [fallback]
           │
           ▼
┌─────────────────────┐
│  chapters_content   │
│  .json              │
└─────────────────────┘
```

---

## Code Files Involved

1. **`agents/writer_agent.py`**: Main Writer Agent implementation
2. **`config/prompts.py`**: LLM prompts (WRITE_SECTION_PROMPT, WRITE_INTRODUCTION_PROMPT, WRITE_CONCLUSION_PROMPT)
3. **`utils/llm_client.py`**: LLM client for API calls
4. **`outputs/intermediate/job_{job_id}/chapters_content.json`**: Output file

---

## Summary

The Writer Agent:
1. **Receives**: Report outline + Project analysis (with code content)
2. **Processes**: 
   - Extracts code snippets from project files
   - Builds prompts with code content and project context
   - Calls LLM to generate content for each section
   - Validates and falls back if needed
3. **Outputs**: Complete content structure with all chapters and sections, including optional tables and diagrams

This content is then passed to the Builder Agent to create the final DOCX document.

