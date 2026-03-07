# Test Scripts

This directory contains all test scripts for individual agents in the report generation system.

## Test Files

- **`test_full_pipeline.py`** ⭐ - **End-to-End Integration Test** - Tests the complete pipeline (Parser → Planner → Writer → Builder) with validation
- **`test_parser_agent.py`** - Tests the Parser Agent (project structure analysis, code extraction, guidelines parsing)
- **`test_parser_simple.py`** - Simplified quick test for Parser Agent
- **`test_planner_agent.py`** - Tests the Planner Agent (report outline generation)
- **`test_writer_agent.py`** - Tests the Writer Agent (content generation for report sections)
- **`test_builder_agent.py`** - Tests the Builder Agent (DOCX document assembly)

## Test Outputs

The `outputs/` subdirectory contains JSON output files from test runs:
- `parser_test_output_*.json` - Parser Agent test outputs
- `planner_test_output_*.json` - Planner Agent test outputs
- `writer_test_output_*.json` - Writer Agent test outputs

## Running Tests

### End-to-End Pipeline Test (Recommended)
Tests the complete flow: Parser → Planner → Writer → Builder

```bash
# Full pipeline test (includes Builder)
python tests/test_full_pipeline.py \
    --project "testing_projects/SIMPLE-CALCULATOR--main.zip" \
    --guidelines "inputs/user_12/03199eb8-4f37-41c3-ab0d-59be1bc6a88b/guidelines.pdf"

# Faster test (skips Builder Agent)
python tests/test_full_pipeline.py \
    --project "testing_projects/SIMPLE-CALCULATOR--main.zip" \
    --guidelines "inputs/user_12/03199eb8-4f37-41c3-ab0d-59be1bc6a88b/guidelines.pdf" \
    --skip-builder

# Save results to JSON
python tests/test_full_pipeline.py \
    --project "testing_projects/SIMPLE-CALCULATOR--main.zip" \
    --guidelines "inputs/user_12/03199eb8-4f37-41c3-ab0d-59be1bc6a88b/guidelines.pdf" \
    --save-results
```

### Individual Agent Tests

#### Parser Agent
```bash
python tests/test_parser_agent.py --project "path/to/project.zip" --guidelines "path/to/guidelines.pdf"
```

#### Planner Agent
```bash
python tests/test_planner_agent.py --intermediate-dir "outputs/intermediate/job_<job_id>"
```

#### Writer Agent
```bash
python tests/test_writer_agent.py --intermediate-dir "outputs/intermediate/job_<job_id>"
```

#### Builder Agent
```bash
python tests/test_builder_agent.py --intermediate-dir "outputs/intermediate/job_<job_id>"
```

## Test Outputs

- Individual agent test outputs: `tests/outputs/`
- End-to-end test results: `tests/outputs/e2e_test_results_*.json`
- Intermediate files: `outputs/intermediate/job_<job_id>/`
- Final documents: `outputs/final/job_<job_id>/`

## Notes

- All test scripts use the `outputs/intermediate/` directory for input/output
- Test outputs are saved in `tests/outputs/` for reference
- For individual tests, run in order: Parser → Planner → Writer → Builder
- End-to-end test runs all agents automatically and validates data flow

