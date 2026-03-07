# Builder Agent - Complete Flow Documentation

## Overview

The **Builder Agent** is the final stage in the report generation pipeline. It takes the structured content from the Writer Agent, formatting guidelines from the Parser Agent, and the report outline from the Planner Agent, then assembles them into a professionally formatted DOCX document.

**Key Responsibility**: Transform JSON content into a Word document with proper formatting, diagrams, tables, and academic structure.

---

## Entry Point and Initialization

### File Location
- **Main Agent**: `agents/builder_agent.py`
- **DOCX Generator Utility**: `utils/docx_generator.py`

### Initialization
```python
BuilderAgent(output_dir="outputs/final", job_id=None)
```

**Parameters:**
- `output_dir`: Directory where final DOCX files are saved (default: `outputs/final`)
- `job_id`: Optional job identifier for isolated output directories (prevents content mixing)

**Initialization Steps:**
1. Creates job-specific output directory: `outputs/final/job_{job_id}/`
2. Initializes `generated_diagrams` dictionary to track and prevent duplicate diagrams
3. Sets up logging context

---

## Main Processing Flow

### 1. Entry Method: `build_document()`

**Signature:**
```python
build_document(
    content: Dict[str, Any],      # From WriterAgent (chapters_content.json)
    guidelines: Dict[str, Any],    # From ParserAgent (guidelines_config.json)
    outline: Dict[str, Any],       # From PlannerAgent (report_outline.json)
    output_filename: str = "Technical_Report.docx"
) -> str
```

**Returns:** Path to generated DOCX file

### 2. Document Assembly Sequence

The Builder Agent follows this **strict sequence**:

```
1. Create DOCXGenerator instance (applies formatting from guidelines)
   ↓
2. Add Title Page
   ↓
3. Add Page Break
   ↓
4. Add Table of Contents (from outline)
   ↓
5. Add Page Break
   ↓
6. FIRST PASS: Process all chapters (collect_only=True)
   - Collects all figures and tables for Lists
   ↓
7. Add List of Figures (if any figures exist)
   ↓
8. Add Page Break
   ↓
9. Add List of Tables (if any tables exist)
   ↓
10. Add Page Break
   ↓
11. SECOND PASS: Process all chapters (normal mode)
    - Adds actual content, tables, diagrams
    - Adds page break after each chapter
   ↓
12. Add References Section (AI-generated)
   ↓
13. Add Headers/Footers (with page numbers)
   ↓
14. Save Document
```

---

## Key Components and Processing

### A. Title Page (`_add_title_page()`)

**What it adds:**
- Report title (from `content["report_title"]`)
- Subtitle: "Technical Documentation"
- Author info: "Prepared by: Student Name"
- Student ID: "22AIML056" (hardcoded)
- Institution: "CSPIT"
- Department: "Department of Artificial Intelligence & Machine Learning"

**Formatting:**
- Uses `doc.add_chapter_heading(0, title)` for title
- Adds spacing paragraphs between elements
- All centered alignment

**Note:** Author/Student info is currently hardcoded - could be made configurable.

---

### B. Table of Contents (`add_table_of_contents()`)

**Location:** `utils/docx_generator.py`

**What it does:**
- Creates a Word-native TOC field (user can update via Word's References menu)
- Extracts chapter and section structure from `outline`
- Formats as hierarchical list:
  ```
  Chapter 1: Introduction
    1.1. Section Title
    1.2. Another Section
  Chapter 2: Architecture
    2.1. Component Overview
  ```

**Implementation:**
- Uses Word's built-in TOC field (not manually generated)
- User must update TOC in Word after opening document
- Alternative: Could generate manual TOC with page numbers (future enhancement)

---

### C. Chapter Processing (`_add_chapter()`)

**Two Modes:**

#### Mode 1: Collect Only (`collect_only=True`)
- **Purpose:** First pass to collect all figures and tables for Lists
- **What it does:**
  - Processes sections to extract `figure_label`, `figure_desc`, `table_label`, `table_title`
  - Populates `doc.figures_list` and `doc.tables_list`
  - **Does NOT add content to document**

#### Mode 2: Normal Mode (`collect_only=False`)
- **Purpose:** Second pass to actually add content
- **What it does:**
  - Adds chapter heading (numbered or conclusion-style)
  - Processes all sections in the chapter
  - Adds page break after chapter

**Chapter Heading Logic:**
- **Regular chapters:** `doc.add_chapter_heading(chapter_num, chapter_title)`
- **Conclusion chapters:** `doc.add_conclusion_heading(chapter_title)` (no number)
- Detection: Checks if "conclusion" is in chapter title (case-insensitive)

---

### D. Section Processing (`_add_section()`)

**Input Structure:**
```python
section = {
    "number": "2.1",                    # or "section_number"
    "title": "Section Title",
    "content": "Paragraph text...",
    "table_data": [["Header1", "Header2"], ["Row1", "Row2"]],  # Optional
    "mermaid_code": "graph TD\nA-->B",  # Optional
    "figure_label": "Fig 2.1",          # Optional
    "figure_desc": "Description",       # Optional
    "subsections": [...]                # Optional
}
```

**Processing Steps:**

1. **Section Heading**
   - Adds section heading with number and title
   - Conclusion sections: Forces empty section number

2. **Content Paragraphs**
   - Splits content by `\n\n` (paragraph breaks)
   - **Handles Lists:**
     - Detects bullet points (`•`, `-`, `*`) or numbered lists (`1.`, `2.`)
     - Converts to Word list format (`List Bullet` style)
   - **Handles Long Paragraphs:**
     - If paragraph > 150 words OR > 800 characters:
       - Calls `_split_long_paragraph()` to split at sentence boundaries
       - Creates 2-3 shorter paragraphs (100-150 words each)

3. **Table Addition** (if `table_data` exists)
   - Generates table label: `section.get("table_label")` or `f"Table {section_num}"`
   - Generates table title: `section.get("table_title")` or `f"Summary for {section_title}"`
   - Calls `doc.add_table(table_data, title, table_label)`
   - Tracks in `doc.tables_list` for List of Tables

4. **Diagram Generation** (if `mermaid_code` exists)
   - Cleans Mermaid code (removes markdown blocks, validates syntax)
   - Calls `_generate_diagram()` to convert to PNG image
   - If successful: Adds figure with `doc.add_figure(image_path, fig_label, fig_desc)`
   - If duplicate: Skips silently (no placeholder)
   - If failed: Skips silently (no placeholder)
   - Tracks in `doc.figures_list` for List of Figures

5. **Subsections** (if `subsections` exists)
   - Processes each subsection with proper numbering (e.g., "2.1.1", "2.1.2")
   - Calls `_add_subsection()` for each

---

### E. Subsection Processing (`_add_subsection()`)

**What it does:**
- Adds subsection heading with proper numbering
- Processes content paragraphs (same as sections)
- Splits long paragraphs automatically

**Numbering Logic:**
- If section number exists: `subsection_num = f"{section_num}.{idx}"`
- Example: Section "2.1" → Subsections "2.1.1", "2.1.2", "2.1.3"

---

### F. Paragraph Splitting (`_split_long_paragraph()`)

**Purpose:** Split paragraphs > 150 words into 2-3 shorter paragraphs for readability

**Algorithm:**
1. Split by sentence boundaries (`[.!?]\s+`)
2. Group sentences into paragraphs of ~100-150 words
3. If sentence splitting fails, try splitting at conjunctions:
   - "However,", "Moreover,", "Furthermore,", "Additionally,", etc.
4. Last resort: Split at middle point (space or punctuation)

**Returns:** List of paragraph strings

---

### G. Diagram Generation (`_generate_diagram()`)

**This is one of the most complex parts of the Builder Agent.**

#### Input
- `mermaid_code`: Raw Mermaid diagram code (may contain markdown blocks)
- `section_num`: Section identifier for tracking

#### Processing Steps

1. **Clean Mermaid Code** (`_clean_mermaid_code()`)
   - Removes markdown code blocks (````mermaid ... ```)
   - Removes leading/trailing quotes
   - Fixes JSON escape sequences (`\n`, `\"`)
   - Validates diagram type (graph, flowchart, sequenceDiagram, etc.)
   - Fixes arrow syntax (`-->`, `->->`)
   - Shortens node labels to max 18 characters
   - Shortens node IDs to max 15 characters
   - Ensures valid Mermaid syntax

2. **Ensure Readable Labels** (`_ensure_readable_labels()`)
   - Post-processes cleaned code
   - Shortens any remaining long labels
   - Ensures node IDs are short and valid

3. **Duplicate Detection** (`_normalize_mermaid_code()`)
   - Normalizes Mermaid code to detect structural duplicates
   - Extracts just node IDs and connections (ignores labels)
   - Compares normalized structure
   - **Simple diagrams (≤4 nodes):** Strict duplicate detection
   - **Complex diagrams (>4 nodes):** Allows 30% variation
   - If duplicate found: Returns `"DUPLICATE"` (skipped)

4. **Multi-Service Diagram Generation**
   The Builder Agent tries multiple services in order (with fallbacks):

   **Service Order:**
   ```
   1. mermaid.ink (base64 URL encoding)
   2. mermaid.live (alternative Mermaid renderer)
   3. kroki.io (zlib compression + base64)
   4. plantuml.com (Mermaid → PlantUML conversion)
   5. quickchart.io (skipped - not implemented)
   6. Python fallback (matplotlib/graphviz) - only if matplotlib available
   ```

   **Service Details:**

   - **mermaid.ink** (`_try_mermaid_ink()`)
     - Encodes Mermaid code as base64url (no padding)
     - URL: `https://mermaid.ink/img/{encoded}`
     - Validates PNG response (checks `\x89PNG` header)
     - Saves to: `diagram_{section_num}.png`

   - **mermaid.live** (`_try_mermaid_live()`)
     - Alternative Mermaid renderer
     - Tries multiple endpoints:
       - `https://mermaid.live/api/png?code={encoded}`
       - `https://mermaid.ink/img/{encoded_b64}`
       - `https://api.mermaid.ink/svg/{encoded_b64}`
     - Validates PNG response

   - **kroki.io** (`_try_kroki()`)
     - Compresses Mermaid code with zlib (level 9)
     - Base64 encodes compressed data
     - URL: `https://kroki.io/mermaid/png/{encoded}`
     - Validates PNG response

   - **plantuml.com** (`_try_plantuml()`)
     - Converts Mermaid flowchart to PlantUML syntax (`_mermaid_to_plantuml()`)
     - Only works for simple flowcharts (graph/flowchart types)
     - Extracts nodes and edges
     - Generates PlantUML code
     - URL: `https://www.plantuml.com/plantuml/png/{encoded}`
     - Validates PNG response

   - **Python Fallback** (`_try_simple_diagram_fallback()`)
     - **Option 1:** Graphviz (if available)
       - Creates graph using `graphviz` library
       - Renders to PNG
     - **Option 2:** Matplotlib (if Graphviz unavailable)
       - Creates simple diagram with nodes and edges
       - Arranges nodes in grid or tree layout
       - Draws with matplotlib
       - Saves to PNG

5. **Result Handling**
   - **Success:** Returns path to PNG file
   - **Duplicate:** Returns `"DUPLICATE"` (skipped silently)
   - **Failure:** Returns `None` (skipped silently, no placeholder)

**Diagram File Naming:**
- Format: `diagram_{section_num.replace('.', '_')}.png`
- Example: Section "2.1" → `diagram_2_1.png`
- Saved in: `outputs/final/job_{job_id}/`

---

### H. List of Figures (`_add_list_of_figures()`)

**When added:** After TOC, before Chapter 1 (if any figures exist)

**Format:**
```
LIST OF FIGURES

Fig. 2.1. HTML Structure Overview
Fig. 2.2. CSS Styling Architecture
Fig. 3.1. JavaScript Logic Flow
```

**Implementation:**
- Iterates through `doc.figures_list`
- Formats each entry: `Fig. {label} {description}`
- Centered heading, left-aligned entries
- 11pt font, 6pt spacing after

---

### I. List of Tables (`_add_list_of_tables()`)

**When added:** After List of Figures (if any tables exist)

**Format:**
```
LIST OF TABLES

Table 2.1. HTML Elements Summary
Table 3.1. JavaScript Functions Overview
```

**Implementation:**
- Iterates through `doc.tables_list`
- Formats each entry: `Table {label} {title}`
- Centered heading, left-aligned entries
- 11pt font, 6pt spacing after

---

### J. References Section (`_add_references_section()`)

**What it does:**
- Generates academic references using LLM
- Extracts technologies from content (Python, JavaScript, API, Database)
- Calls LLM with `GENERATE_REFERENCES_PROMPT`
- Formats references in hanging indent style

**Reference Format:**
```
[1] Author, A. (Year). Title. Publisher.
[2] Another Reference...
```

**Implementation:**
- Uses `llm_client.generate_json()` with `GENERATE_REFERENCES_PROMPT`
- Handles malformed JSON responses (nested structures, strings, etc.)
- Formats each reference with:
  - Hanging indent (0.5" left, -0.5" hanging)
  - Bold reference number: `[1]`
  - Regular text for citation
  - 11pt font, 6pt spacing after

**Fallback:** If LLM fails, adds placeholder: "References will be added here."

---

### K. Headers and Footers (`add_header_footer()`)

**Location:** `utils/docx_generator.py`

**What it adds:**
- **Header:** Student ID (e.g., "22AIML056") - right-aligned
- **Footer:** Page number (centered)

**Implementation:**
- Uses Word fields for page numbers (auto-updating)
- Applies to all sections in document

---

## DOCXGenerator Utility Class

**Location:** `utils/docx_generator.py`

**Purpose:** Handles all Word document formatting and structure

### Key Methods

#### `__init__(guidelines)`
- Creates new Word document
- Applies page setup (margins, A4 size)
- Configures styles (fonts, spacing, typography)

#### `add_chapter_heading(chapter_num, title)`
- Adds centered chapter heading
- Applies font from guidelines (size, bold)
- Format: "CHAPTER {num}: {title}"

#### `add_conclusion_heading(title)`
- Adds conclusion heading (no chapter number)
- Centered, bold, uppercase

#### `add_section_heading(section_num, title, is_conclusion=False)`
- Adds section heading
- Format: "{section_num}. {title}"
- Left-aligned, bold

#### `add_subsection_heading(subsection_num, title)`
- Adds subsection heading
- Format: "{subsection_num}. {title}"
- Left-aligned, bold, smaller font

#### `add_paragraph(text)`
- Adds body paragraph
- Applies normal style (Times New Roman, 12pt, justified)
- Handles empty text (skips)

#### `add_table(data, title=None, table_label=None)`
- Creates Word table from 2D array
- First row = headers (bold, centered)
- Data rows = regular text
- Adds table label above: "Table {label}. {title}"
- Tracks in `tables_list`

#### `add_figure(image_path, label, description)`
- Inserts PNG image into document
- Centers image
- Adds caption below: "Fig. {label}. {description}"
- Tracks in `figures_list`

#### `add_table_of_contents(outline)`
- Creates Word-native TOC field
- Extracts structure from outline
- User must update TOC in Word

#### `add_page_break()`
- Inserts page break

#### `add_header_footer(student_id="22AIML056")`
- Adds header with student ID
- Adds footer with page number

---

## Input Data Structures

### Content (from WriterAgent)
```json
{
  "report_title": "Project Name: Technical Documentation",
  "chapters": [
    {
      "chapter_number": 1,
      "chapter_title": "Introduction",
      "sections": [
        {
          "number": "1.1",
          "title": "Project Overview",
          "content": "Paragraph text...",
          "table_data": [["Header1", "Header2"], ["Row1", "Row2"]],
          "mermaid_code": "graph TD\nA-->B",
          "figure_label": "Fig 1.1",
          "figure_desc": "Description",
          "subsections": [
            {
              "title": "Subsection Title",
              "content": "Content..."
            }
          ]
        }
      ]
    }
  ]
}
```

### Guidelines (from ParserAgent)
```json
{
  "page_setup": {
    "margins": {
      "top": "1.0in",
      "bottom": "1.0in",
      "left": "1.25in",
      "right": "1.0in"
    }
  },
  "fonts": {
    "family": "Times New Roman",
    "body_text": {"size": 12},
    "chapter_heading": {"size": 16, "bold": true},
    "section_heading": {"size": 14, "bold": true}
  },
  "spacing": {
    "line_spacing": 1.5,
    "paragraph_spacing_after": 12
  }
}
```

### Outline (from PlannerAgent)
```json
{
  "report_title": "Project Name: Technical Documentation",
  "chapters": [
    {
      "number": 1,
      "title": "Introduction",
      "sections": [
        {
          "number": "1.1",
          "title": "Project Overview"
        }
      ]
    }
  ]
}
```

---

## Output

### Generated Files

1. **DOCX Document**
   - Location: `outputs/final/job_{job_id}/Technical_Report.docx`
   - Format: Microsoft Word document (.docx)
   - Contains: Title page, TOC, Lists, Chapters, References

2. **Diagram Images** (if any)
   - Location: `outputs/final/job_{job_id}/diagram_{section_num}.png`
   - Format: PNG images
   - Embedded in DOCX document

### Document Structure

```
Title Page
---
Page Break
---
Table of Contents
---
Page Break
---
List of Figures (if any)
---
Page Break
---
List of Tables (if any)
---
Page Break
---
Chapter 1: Introduction
  Section 1.1: Project Overview
    [Content paragraphs]
    [Table if any]
    [Figure if any]
    Subsection 1.1.1: Details
      [Content]
  Section 1.2: Use Cases
---
Page Break
---
Chapter 2: Architecture
  [Sections...]
---
Page Break
---
References
  [1] Reference 1
  [2] Reference 2
```

---

## Key Design Decisions

### 1. Two-Pass Processing
- **Why:** Need to collect all figures/tables before generating Lists
- **First Pass:** Collect metadata only
- **Second Pass:** Add actual content

### 2. Silent Diagram Failures
- **Why:** Better to skip failed diagrams than show placeholders
- **Behavior:** If diagram generation fails, section continues without diagram
- **No error messages in document**

### 3. Duplicate Diagram Detection
- **Why:** Prevents showing same diagram multiple times
- **Method:** Normalizes Mermaid code structure (ignores labels)
- **Simple diagrams:** Strict duplicate detection
- **Complex diagrams:** Allows slight variations

### 4. Multiple Diagram Services
- **Why:** Reliability - if one service fails, try another
- **Order:** Fastest/most reliable first, fallbacks last
- **Python fallback:** Only if matplotlib/graphviz available

### 5. Paragraph Splitting
- **Why:** Long paragraphs are hard to read
- **Threshold:** 150 words OR 800 characters
- **Method:** Split at sentence boundaries or conjunctions

### 6. Hardcoded Author Info
- **Current:** Student name and ID are hardcoded
- **Future:** Could be made configurable via guidelines or user input

---

## Error Handling

### Diagram Generation Failures
- **Behavior:** Silently skips (no placeholder, no error in document)
- **Logging:** Warnings logged for debugging
- **Fallback:** Tries multiple services before giving up

### Malformed JSON (References)
- **Behavior:** Attempts to parse nested structures, strings, lists
- **Fallback:** Adds placeholder text if parsing fails

### Missing Data
- **Tables:** If `table_data` is empty or invalid, skips table
- **Diagrams:** If `mermaid_code` is empty/invalid, skips diagram
- **Sections:** If section is not a dict, logs warning and skips

---

## Dependencies

### Required
- `python-docx`: Word document creation
- `requests`: HTTP requests for diagram services
- `base64`, `zlib`: Encoding/compression for diagram services

### Optional
- `matplotlib`: Python-based diagram fallback
- `graphviz`: Graph diagram generation (better than matplotlib)

---

## Future Enhancement Opportunities

1. **Configurable Author Info**
   - Extract from guidelines or user input
   - Support multiple authors

2. **Manual TOC Generation**
   - Generate TOC with actual page numbers
   - Update automatically during build

3. **Better Diagram Error Handling**
   - Show placeholder for failed diagrams
   - Log errors in document appendix

4. **Table of Contents Auto-Update**
   - Use Word fields to auto-update TOC
   - Include page numbers

5. **Custom Styles**
   - Support custom Word styles from guidelines
   - Better typography control

6. **Image Optimization**
   - Compress diagram images
   - Support SVG diagrams

7. **Cross-References**
   - Add "see Figure X" references in text
   - Auto-link table/figure references

8. **Bibliography Management**
   - Support multiple citation styles (APA, MLA, IEEE)
   - Better reference formatting

---

## Testing

### Test Command
```bash
python test_builder_agent.py --intermediate-dir "outputs/intermediate/job_{job_id}"
```

### What to Test
1. Document structure (title page, TOC, chapters, references)
2. Formatting (fonts, spacing, margins)
3. Table generation and formatting
4. Diagram generation (multiple services)
5. Duplicate diagram detection
6. Long paragraph splitting
7. Subsection numbering
8. List of Figures/Tables generation
9. References generation (LLM)
10. Error handling (malformed data, failed diagrams)

---

## Summary

The Builder Agent is responsible for the **final assembly** of the technical report. It:

1. **Takes structured content** from Writer Agent
2. **Applies formatting** from Parser Agent guidelines
3. **Uses outline structure** from Planner Agent
4. **Generates diagrams** from Mermaid code (multiple services)
5. **Creates tables** from structured data
6. **Assembles document** with proper academic structure
7. **Outputs DOCX file** ready for use

**Key Strengths:**
- Robust diagram generation with multiple fallbacks
- Proper academic document structure
- Automatic formatting from guidelines
- Duplicate detection to avoid redundancy

**Key Limitations:**
- Hardcoded author/student info
- TOC requires manual update in Word
- Silent diagram failures (no user feedback)
- Limited error recovery

---

**Last Updated:** 2026-01-01
**Version:** 1.0

