# Parser Agent - Complete Flow Documentation

## Overview

The **Parser Agent** is the first stage of the report generation pipeline. It processes two main inputs:
1. **Project ZIP file** - Contains the source code to be documented
2. **Guidelines PDF** - Contains formatting rules for the final report

The Parser Agent extracts and structures information from both inputs, preparing them for the subsequent agents (Planner, Writer, Builder).

---

## High-Level Flow

```
User Input (ZIP + PDF)
    ↓
[Step 1] Extract & Analyze Project Structure (CodeAnalyzer)
    ↓
[Step 2] Parse Guidelines PDF (PDFParser)
    ↓
[Step 3] Extract Formatting Rules (LLM)
    ↓
[Step 4] Analyze Project with LLM (LLM)
    ↓
Output: guidelines_config.json + codebase_structure.json
```

---

## Detailed Flow Breakdown

### Entry Point

**File**: `test_parser_agent.py` (for testing) or `api/app/tasks/report_tasks.py` (in production)

**Function**: `test_parser_agent(project_zip_path, guidelines_pdf_path, job_id)`

**What happens**:
- Receives paths to project ZIP and guidelines PDF
- Creates a unique `job_id` for this analysis (prevents content mixing)
- Calls `analyze_project()` to process the ZIP file
- Creates `ParserAgent` instance
- Calls parser methods to process both inputs

---

## Step 1: Project Structure Analysis

### File: `utils/code_analyzer.py`

### Function: `analyze_project(project_zip_path, job_id)`

**Purpose**: Extract ZIP file, analyze project structure, and extract code snippets

**Flow**:

#### 1.1 Initialize CodeAnalyzer
```python
analyzer = CodeAnalyzer(project_path=project_zip_path, job_id=job_id)
```
- Stores project path and job_id
- Determines if input is a ZIP file

#### 1.2 Extract ZIP File (if needed)
**Method**: `extract_if_zip(extract_dir="temp_extract")`

**Location**: `utils/code_analyzer.py` lines 20-145

**What it does**:
1. **Create job-specific directory**:
   - Creates `temp_extract/job_{job_id}/` directory
   - This ensures each job has isolated extraction (prevents content mixing)

2. **Cleanup existing extraction**:
   - If directory exists, removes it completely
   - Prevents leftover files from previous runs

3. **Extract ZIP file**:
   - Opens ZIP file using `zipfile.ZipFile()`
   - Extracts files one by one (not using `extractall()`)
   - **Handles Windows long path issues**:
     - Skips files with paths > 200 characters (usually images/media)
     - Handles directory creation conflicts
     - Skips duplicate files
   - Creates parent directories as needed
   - Writes each file manually for better error control

4. **Verify extraction**:
   - Checks that files were extracted
   - Logs sample files for verification
   - Warns if suspicious files found (from previous projects)

**Output**: Path to extracted project directory

#### 1.3 Analyze Project Structure
**Method**: `analyze_structure()`

**Location**: `utils/code_analyzer.py` lines 163-350

**What it does**:

1. **Get project directory**:
   - If ZIP was extracted, uses extraction directory
   - If not ZIP, uses project path directly

2. **Extract project name**:
   - **Method**: `_extract_project_name(project_dir)`
   - **Location**: `utils/code_analyzer.py` lines 350-450
   - **Process**:
     - Tries to read `package.json` (for Node.js projects)
     - Tries to read `setup.py` or `pyproject.toml` (for Python projects)
     - Tries to read `README.md` for project name
     - Falls back to directory name (cleaned of UUIDs/job IDs)
     - Generates file-based hash name if all else fails
   - **Purpose**: Get meaningful project name (not "temp extract" or "cli tool")

3. **Walk through project files**:
   - Uses `project_dir.rglob("*")` to find all files
   - Skips hidden files (`.git`, `.env`, etc.)
   - Skips `__pycache__`, `node_modules`, etc.

4. **For each file**:
   - **Extract metadata**:
     - File path (relative to project root)
     - File name
     - File extension
     - File size
     - Line count (for code files)
   
   - **Extract code snippets** (for code files only):
     - **File types**: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.java`, `.cpp`, `.c`, `.html`, `.css`
     - **Method**: Reads file content
     - **Snippet size**:
       - Main files (`app.js`, `main.py`, `index.html`): First 2000 characters
       - Other files: First 1000 characters
     - **Stores**: `code_snippet` field with actual code content
     - **Purpose**: Provides actual code to LLM (prevents hallucination)

5. **Detect technologies**:
   - Checks for `package.json` → JavaScript/Node.js
   - Checks for `requirements.txt` → Python
   - Checks for `pom.xml` → Java
   - Checks file extensions → HTML, CSS, etc.

6. **Find entry points**:
   - Looks for `index.html`, `app.js`, `main.py`, `index.js`, etc.
   - Identifies main application files

7. **Python-specific analysis** (if Python files found):
   - **Method**: `analyze_python_file(file_path)`
   - **Location**: `utils/code_analyzer.py` lines 523-571
   - Uses AST (Abstract Syntax Tree) to extract:
     - Imports
     - Functions (names, arguments, docstrings)
     - Classes (names, methods, docstrings)

**Output**: Dictionary with:
```json
{
  "name": "Project Name",
  "files": [
    {
      "path": "relative/path/to/file.js",
      "name": "file.js",
      "extension": ".js",
      "lines": 150,
      "has_code": true,
      "code_snippet": "function generateTree() {...}"
    }
  ],
  "technologies": ["JavaScript", "HTML"],
  "entry_points": ["index.html", "app.js"],
  "total_lines": 526
}
```

---

## Step 2: Parse Guidelines PDF

### File: `agents/parser_agent.py`

### Method: `parse_guidelines(guidelines_path)`

**Location**: `agents/parser_agent.py` lines 30-101

**What it does**:

#### 2.1 Extract Text from PDF
**Function**: `parse_guidelines_pdf(guidelines_path)`

**File**: `utils/pdf_parser.py`

**Method**: `PDFParser.extract_structured()`

**Location**: `utils/pdf_parser.py` lines 36-83

**Process**:
1. Opens PDF using `pdfplumber.open()`
2. **Extracts text from each page**:
   - Iterates through all pages
   - Calls `page.extract_text()` for each page
   - Combines all text with page breaks

3. **Extracts tables** (if any):
   - Calls `page.extract_tables()` for each page
   - Stores table data with page numbers

4. **Extracts metadata**:
   - PDF title, author, subject (if available)

**Output**: Dictionary with:
```json
{
  "text": "Full extracted text from PDF...",
  "tables": [{"page": 1, "data": [...]}],
  "metadata": {"title": "...", "author": "..."},
  "pages": 10
}
```

#### 2.2 Truncate Text
- Limits to first 4000 characters (for faster LLM processing)
- Logs warning if truncation occurs

#### 2.3 Extract Formatting Rules with LLM
**Location**: `agents/parser_agent.py` lines 52-79

**Process**:
1. **Prepare prompt**:
   - Uses `PARSE_GUIDELINES_PROMPT` from `config/prompts.py`
   - Inserts extracted PDF text into prompt template

2. **Call LLM**:
   - **Function**: `llm_client.generate_json()`
   - **File**: `utils/llm_client.py`
   - **System prompt**: `PARSER_SYSTEM_PROMPT` (from `config/prompts.py`)
   - **Temperature**: 0.1 (low for consistent extraction)
   - **Timeout**: 300 seconds (5 minutes)

3. **LLM extracts structured formatting rules**:
   - Font family, sizes, styles
   - Page setup (margins, paper size)
   - Spacing rules
   - Numbering schemes
   - Headers/footers

4. **Add metadata**:
   - Source PDF path
   - Number of pages
   - Number of tables found

5. **Save to file**:
   - Saves to `outputs/intermediate/job_{job_id}/guidelines_config.json`

6. **Fallback** (if LLM fails):
   - Uses `_get_default_formatting()` method
   - Returns default academic formatting rules
   - Logs fallback reason

**Output**: Dictionary with formatting rules:
```json
{
  "fonts": {
    "family": "Times New Roman",
    "chapter_heading": {"size": 16, "bold": true, "all_caps": true},
    "section_heading": {"size": 14, "bold": true},
    "body_text": {"size": 12}
  },
  "page_setup": {
    "paper_size": "A4",
    "margins": {"left": "1.25in", "right": "1.0in", "top": "1.0in", "bottom": "1.0in"}
  },
  "spacing": {"line_spacing": 1.5, "paragraph_spacing": 12},
  "numbering": {"chapters": "numeric", "sections": "decimal"},
  "_metadata": {"source": "path/to/guidelines.pdf", "pages": 10}
}
```

---

## Step 3: Analyze Project Structure with LLM

### File: `agents/parser_agent.py`

### Method: `analyze_project_structure(project_analysis)`

**Location**: `agents/parser_agent.py` lines 165-249

**What it does**:

#### 3.1 Prepare Project Data
1. **Format file details**:
   - Takes first 20 files from project analysis
   - Creates formatted list: `"- path/to/file.js (150 lines)"`

2. **Get sample file names**:
   - Takes first 5 files for explicit project identification
   - Used in prompt to ensure LLM focuses on correct project

#### 3.2 Create Isolation Header
**Purpose**: Prevent content mixing between projects

**Content**:
```
🚨 CRITICAL PROJECT ISOLATION 🚨
JOB ID: {job_id}
PROJECT NAME: {project_name}
SAMPLE FILES: {sample_files}
TOTAL FILES: {file_count}

YOU ARE ANALYZING THIS SPECIFIC PROJECT ONLY. DO NOT REFERENCE OR MIX CONTENT FROM ANY OTHER PROJECTS.
```

#### 3.3 Prepare LLM Prompt
**Prompt template**: `ANALYZE_PROJECT_PROMPT` from `config/prompts.py`

**Includes**:
- Project name
- File count
- Technologies detected
- Entry points
- File details (first 20 files)
- Isolation header (with job_id and sample files)

#### 3.4 Call LLM
**Function**: `llm_client.generate_json()`

**Parameters**:
- **Prompt**: Formatted `ANALYZE_PROJECT_PROMPT` with project data
- **System prompt**: `PARSER_SYSTEM_PROMPT`
- **Temperature**: 0.1 (low for consistent analysis)

**LLM analyzes**:
- Project type (web app, CLI tool, library, etc.)
- Main technologies
- Key components
- Architecture pattern
- Complexity level
- Suggested chapters (for report structure)

#### 3.5 Merge Results
- Merges LLM analysis with original project analysis
- Preserves all file information and code snippets

#### 3.6 Save to File
- Saves to `outputs/intermediate/job_{job_id}/codebase_structure.json`

#### 3.7 Fallback (if LLM fails)
- Uses original project analysis
- Adds minimal enrichment (project_type, technologies, etc.)
- Logs fallback reason

**Output**: Enriched project analysis:
```json
{
  "name": "Project Name",
  "project_type": "web app",
  "main_technologies": ["JavaScript", "HTML"],
  "key_components": ["app.js", "index.html"],
  "architecture_pattern": "Single-page application",
  "complexity_level": "simple",
  "files": [...],
  "technologies": [...],
  "entry_points": [...]
}
```

---

## Step 4: Combine Outputs

### Method: `run(guidelines_path, project_analysis)`

**Location**: `agents/parser_agent.py` lines 251-280

**What it does**:
1. Calls `parse_guidelines()` → Gets formatting rules
2. Calls `analyze_project_structure()` → Gets enriched project analysis
3. Combines both into single result:
   ```json
   {
     "guidelines": {...formatting rules...},
     "codebase": {...project analysis...}
   }
   ```
4. Saves combined output to `outputs/intermediate/job_{job_id}/parser_output.json`

---

## Output Files

All outputs are saved in: `outputs/intermediate/job_{job_id}/`

### 1. `guidelines_config.json`
- Formatting rules extracted from PDF
- Font specifications, page setup, spacing, numbering

### 2. `codebase_structure.json`
- Enriched project analysis
- Project type, technologies, components, architecture
- File list with code snippets

### 3. `parser_output.json`
- Combined output (guidelines + codebase)
- Used by next agent (Planner Agent)

---

## Key Code Files and Their Roles

### 1. `utils/code_analyzer.py`
**Role**: Project structure extraction and code snippet extraction

**Key Classes/Methods**:
- `CodeAnalyzer.__init__()` - Initialize analyzer
- `CodeAnalyzer.extract_if_zip()` - Extract ZIP file (lines 20-145)
- `CodeAnalyzer.analyze_structure()` - Analyze project structure (lines 163-350)
- `CodeAnalyzer._extract_project_name()` - Extract meaningful project name (lines 350-450)
- `CodeAnalyzer._get_code_snippets()` - Extract code content from files (lines 400-450)
- `CodeAnalyzer.analyze_python_file()` - AST analysis for Python files (lines 523-571)
- `analyze_project()` - Convenience function (lines 575-583)

### 2. `agents/parser_agent.py`
**Role**: Orchestrates parsing of guidelines and project analysis

**Key Classes/Methods**:
- `ParserAgent.__init__()` - Initialize parser with job_id (lines 21-28)
- `ParserAgent.parse_guidelines()` - Parse PDF and extract formatting rules (lines 30-101)
- `ParserAgent.analyze_project_structure()` - Analyze project with LLM (lines 165-249)
- `ParserAgent.run()` - Complete parsing pipeline (lines 251-280)
- `ParserAgent._get_default_formatting()` - Fallback formatting rules (lines 103-163)
- `parse_inputs()` - Convenience function (lines 284-297)

### 3. `utils/pdf_parser.py`
**Role**: Extract text and structure from PDF files

**Key Classes/Methods**:
- `PDFParser.__init__()` - Initialize PDF parser (lines 13-16)
- `PDFParser.extract_text()` - Extract plain text (lines 18-34)
- `PDFParser.extract_structured()` - Extract text + tables + metadata (lines 36-83)
- `parse_guidelines_pdf()` - Convenience function (lines 109-117)

### 4. `utils/llm_client.py`
**Role**: Interface to LLM (Mistral API)

**Key Methods**:
- `LLMClient.generate_json()` - Generate structured JSON from prompt
- Handles API calls, retries, error handling

### 5. `config/prompts.py`
**Role**: LLM prompt templates

**Key Prompts**:
- `PARSER_SYSTEM_PROMPT` - System prompt for parser agent
- `PARSE_GUIDELINES_PROMPT` - Prompt for extracting formatting rules
- `ANALYZE_PROJECT_PROMPT` - Prompt for analyzing project structure

---

## Critical Design Decisions

### 1. Job-Specific Directories
**Why**: Prevents content mixing between different projects

**Implementation**:
- Extraction: `temp_extract/job_{job_id}/`
- Output: `outputs/intermediate/job_{job_id}/`

**Location**: 
- `CodeAnalyzer.extract_if_zip()` - line 25
- `ParserAgent.__init__()` - line 24

### 2. Code Snippet Extraction
**Why**: Provides actual code to LLM, preventing hallucination

**Implementation**:
- Extracts first 2000 chars from main files
- Extracts first 1000 chars from other code files
- Stored in `code_snippet` field

**Location**: `utils/code_analyzer.py` lines 183-200

### 3. Project Name Extraction
**Why**: Ensures meaningful project names (not "temp extract")

**Implementation**:
- Reads `package.json`, `setup.py`, `README.md`
- Cleans UUIDs and job IDs from names
- Falls back to file-based hash if needed

**Location**: `utils/code_analyzer.py` lines 350-450

### 4. Windows Long Path Handling
**Why**: Windows has 260 character path limit

**Implementation**:
- Skips files with paths > 200 characters
- Handles directory creation conflicts
- Skips duplicate files

**Location**: `utils/code_analyzer.py` lines 90-145

### 5. Isolation Headers in Prompts
**Why**: Reinforces project isolation to LLM

**Implementation**:
- Adds explicit isolation header with job_id
- Includes sample file names
- Warns against mixing content

**Location**: `agents/parser_agent.py` lines 197-208

---

## Error Handling

### 1. ZIP Extraction Errors
- **Long paths**: Skips files gracefully
- **Directory conflicts**: Checks if directory exists before creating
- **Duplicate files**: Skips if file already exists

### 2. PDF Parsing Errors
- **PDF not found**: Raises `FileNotFoundError`
- **Corrupted PDF**: Logs error and raises exception

### 3. LLM Errors
- **Timeout**: Falls back to default formatting (for guidelines)
- **API errors**: Logs error and uses fallback
- **Invalid JSON**: Logs error and uses fallback

### 4. Project Analysis Errors
- **No files found**: Raises `ValueError`
- **LLM failure**: Uses original project analysis with minimal enrichment

---

## Data Flow Summary

```
Input:
  - Project ZIP: "project.zip"
  - Guidelines PDF: "guidelines.pdf"
  - Job ID: "job_123"

Step 1: CodeAnalyzer
  ZIP → Extract → temp_extract/job_123/
  → Walk files → Extract code snippets
  → Detect technologies → Find entry points
  → Output: project_analysis dict

Step 2: PDFParser
  PDF → Extract text → Extract tables
  → Output: pdf_data dict

Step 3: ParserAgent.parse_guidelines()
  pdf_data["text"] → LLM → Formatting rules
  → Save: guidelines_config.json

Step 4: ParserAgent.analyze_project_structure()
  project_analysis → LLM → Enriched analysis
  → Save: codebase_structure.json

Step 5: ParserAgent.run()
  Combine guidelines + codebase
  → Save: parser_output.json

Output:
  - outputs/intermediate/job_123/guidelines_config.json
  - outputs/intermediate/job_123/codebase_structure.json
  - outputs/intermediate/job_123/parser_output.json
```

---

## Next Steps

After Parser Agent completes, the output is passed to:
1. **Planner Agent** - Creates report outline/structure
2. **Writer Agent** - Generates content for each section
3. **Builder Agent** - Assembles final DOCX document

---

## Testing

To test the Parser Agent:

```bash
python test_parser_agent.py --project "project.zip" --guidelines "guidelines.pdf"
```

This will:
1. Run the complete parser agent flow
2. Show detailed output in console
3. Save all output files
4. Display summary of results

