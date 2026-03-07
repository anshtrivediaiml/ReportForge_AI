# Project Structure

This document describes the organized structure of the report generation system.

## Directory Structure

```
report_generator_ai/
├── agents/                    # Core agent implementations
│   ├── parser_agent.py        # Project analysis and extraction
│   ├── planner_agent.py       # Report outline generation
│   ├── writer_agent.py        # Content generation
│   └── builder_agent.py      # DOCX document assembly
│
├── tests/                     # Test scripts and outputs
│   ├── test_parser_agent.py   # Parser Agent tests
│   ├── test_parser_simple.py  # Quick Parser test
│   ├── test_planner_agent.py  # Planner Agent tests
│   ├── test_writer_agent.py   # Writer Agent tests
│   ├── test_builder_agent.py  # Builder Agent tests
│   ├── outputs/               # Test output JSON files
│   └── README.md              # Test documentation
│
├── docs/                      # Documentation
│   ├── agents/                # Agent-specific documentation
│   │   ├── PARSER_AGENT_FLOW.md
│   │   ├── WRITER_AGENT_FLOW.md
│   │   ├── BUILDER_AGENT_FLOW.md
│   │   ├── PARSER_AGENT_TESTING_SUMMARY.md
│   │   ├── PARSER_OUTPUT_ANALYSIS.md
│   │   ├── TEST_PARSER_GUIDE.md
│   │   └── QUICK_START_PARSER_TEST.md
│   ├── DEVELOPMENT.md
│   ├── GOOGLE_OAUTH_SETUP.md
│   ├── FIXES_SUMMARY.md
│   ├── IMPLEMENTATION_STATUS.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── PROJECT_PROMPT.md
│   ├── UX_IMPROVEMENTS.md
│   └── PROJECT_STRUCTURE.md   # This file
│
├── utils/                     # Utility modules
│   ├── code_analyzer.py       # Project structure analysis
│   ├── facts_builder.py       # Deterministic facts generation
│   ├── llm_client.py          # LLM API client
│   ├── pdf_parser.py          # PDF guidelines parsing
│   ├── docx_generator.py      # DOCX document generation
│   └── logger.py              # Logging configuration
│
├── config/                    # Configuration
│   └── prompts.py             # LLM prompt templates
│
├── api/                       # API server (FastAPI)
│   ├── app/                   # Application code
│   ├── alembic/               # Database migrations
│   └── tests/                 # API tests
│
├── web/                       # Frontend (React/TypeScript)
│   └── src/                   # Source files
│
├── outputs/                   # Production outputs
│   ├── intermediate/          # Intermediate JSON files
│   └── final/                 # Final DOCX documents
│
├── inputs/                    # User input files
│   └── user_*/                # User-specific inputs
│
├── testing_projects/          # Test project ZIP files
│
├── temp_extract/              # Temporary extraction directory
│
├── scripts/                   # Utility scripts
│   ├── dev.sh
│   └── setup.sh
│
├── logs/                      # Log files
│
├── requirements.txt           # Python dependencies
└── README.md                  # Main project README
```

## Key Changes

### Test Scripts Organization
- **Before**: Test scripts scattered in root directory
- **After**: All test scripts organized in `tests/` directory
- Test outputs saved to `tests/outputs/` subdirectory
- All test scripts updated with correct path references

### Documentation Organization
- **Before**: Documentation files scattered in root
- **After**: 
  - Agent-specific docs in `docs/agents/`
  - General project docs in `docs/`
  - Clear separation of concerns

### File Organization
- Test output JSON files moved to `tests/outputs/`
- Agent flow documentation grouped in `docs/agents/`
- Project documentation consolidated in `docs/`

## Running Tests

All test scripts are now in the `tests/` directory. Use the following commands:

```bash
# Parser Agent
python tests/test_parser_agent.py --project "path/to/project.zip" --guidelines "path/to/guidelines.pdf"

# Planner Agent
python tests/test_planner_agent.py --intermediate-dir "outputs/intermediate/job_<job_id>"

# Writer Agent
python tests/test_writer_agent.py --intermediate-dir "outputs/intermediate/job_<job_id>"

# Builder Agent
python tests/test_builder_agent.py --intermediate-dir "outputs/intermediate/job_<job_id>"
```

## Notes

- All test scripts have been updated to use correct relative paths
- Test outputs are automatically saved to `tests/outputs/`
- Documentation is organized by topic and agent
- The structure is scalable for future additions


