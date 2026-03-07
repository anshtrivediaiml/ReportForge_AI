# End-to-End Integration Testing Guide

## Overview

The end-to-end integration test (`tests/test_full_pipeline.py`) validates the complete report generation pipeline by running all agents in sequence and verifying that data flows correctly between them.

## What It Tests

### 1. **Complete Pipeline Execution**
   - Parser Agent: Project analysis and guidelines parsing
   - Planner Agent: Report outline generation
   - Writer Agent: Content generation for all sections
   - Builder Agent: DOCX document assembly

### 2. **Output Validation**
   - **Parser Output**: Validates project structure, guidelines config, and codebase analysis
   - **Planner Output**: Validates report outline, chapters, and sections
   - **Writer Output**: Validates generated content for all chapters and sections
   - **Builder Output**: Validates final DOCX document exists and has reasonable size

### 3. **Data Flow Validation**
   - Project name consistency across all stages
   - Chapter count consistency (Planner → Writer)
   - Section count consistency (Planner → Writer)
   - Report title consistency

### 4. **Performance Metrics**
   - Tracks execution time for each stage
   - Reports total pipeline execution time
   - Identifies bottlenecks

## Running the Test

### Basic Usage

```bash
python tests/test_full_pipeline.py \
    --project "testing_projects/SIMPLE-CALCULATOR--main.zip" \
    --guidelines "inputs/user_12/03199eb8-4f37-41c3-ab0d-59be1bc6a88b/guidelines.pdf"
```

### Options

- `--project`: Path to project ZIP file (required)
- `--guidelines`: Path to guidelines PDF file (required)
- `--job-id`: Optional job ID (defaults to timestamp-based)
- `--skip-builder`: Skip Builder Agent for faster testing
- `--save-results`: Save detailed test results to JSON file

### Examples

#### Full Pipeline Test (Recommended)
```bash
python tests/test_full_pipeline.py \
    --project "testing_projects/SIMPLE-CALCULATOR--main.zip" \
    --guidelines "inputs/user_12/03199eb8-4f37-41c3-ab0d-59be1bc6a88b/guidelines.pdf" \
    --save-results
```

#### Fast Test (Skip Builder)
```bash
python tests/test_full_pipeline.py \
    --project "testing_projects/SIMPLE-CALCULATOR--main.zip" \
    --guidelines "inputs/user_12/03199eb8-4f37-41c3-ab0d-59be1bc6a88b/guidelines.pdf" \
    --skip-builder
```

#### With Custom Job ID
```bash
python tests/test_full_pipeline.py \
    --project "testing_projects/SIMPLE-CALCULATOR--main.zip" \
    --guidelines "inputs/user_12/03199eb8-4f37-41c3-ab0d-59be1bc6a88b/guidelines.pdf" \
    --job-id "my_test_001"
```

## Test Output

### Console Output

The test provides detailed console output showing:
- Progress for each stage
- Validation results
- Timing information
- Errors and warnings
- Final summary

### JSON Results (with `--save-results`)

When `--save-results` is used, a detailed JSON file is saved to `tests/outputs/e2e_test_results_<job_id>.json`:

```json
{
  "job_id": "e2e_test_1234567890",
  "overall_success": true,
  "total_time_seconds": 245.67,
  "stages": {
    "parser": {
      "success": true,
      "time_seconds": 45.23,
      "project_name": "Simple Calculator",
      "files_analyzed": 4,
      "project_type": "Web Application"
    },
    "planner": {
      "success": true,
      "time_seconds": 12.45,
      "chapters": 4,
      "sections": 11,
      "report_title": "Simple Calculator: Technical Documentation"
    },
    "writer": {
      "success": true,
      "time_seconds": 156.78,
      "chapters": 4,
      "sections": 11
    },
    "builder": {
      "success": true,
      "time_seconds": 31.21,
      "output_path": "outputs/final/job_e2e_test_1234567890/Technical_Report_e2e_test_1234567890.docx",
      "file_size_kb": 131.89
    },
    "data_flow": {
      "success": true,
      "warnings": []
    }
  },
  "errors": [],
  "warnings": []
}
```

## Validation Checks

### Parser Validation
- ✅ Guidelines config has formatting rules
- ✅ Codebase has project name
- ✅ Codebase has files list
- ✅ Project structure is valid

### Planner Validation
- ✅ Report title exists
- ✅ Chapters list exists and is non-empty
- ✅ Each chapter has title and sections
- ✅ Sections are properly structured

### Writer Validation
- ✅ Report title exists
- ✅ Chapters list exists and is non-empty
- ✅ Each chapter has title and sections
- ✅ Each section has title and content

### Builder Validation
- ✅ Output file exists
- ✅ Output file is not empty
- ✅ Output file has reasonable size (>1KB)
- ✅ Output file has .docx extension

### Data Flow Validation
- ✅ Project name appears in report titles
- ✅ Chapter counts match (Planner → Writer)
- ✅ Section counts match (Planner → Writer)

## Interpreting Results

### Success Indicators
- `overall_success: true` - All stages completed successfully
- `errors: []` - No validation errors
- All stages show `success: true`

### Warning Indicators
- `warnings: [...]` - Non-critical issues (e.g., data flow inconsistencies)
- These don't fail the test but indicate potential issues

### Failure Indicators
- `overall_success: false` - One or more stages failed
- `errors: [...]` - Validation errors that need attention
- Any stage with `success: false`

## Troubleshooting

### Common Issues

1. **Parser Fails**
   - Check project ZIP file is valid
   - Verify guidelines PDF is readable
   - Check LLM API key is configured

2. **Planner Fails**
   - Verify parser output is valid
   - Check intermediate files exist
   - Review LLM response format

3. **Writer Fails**
   - Verify planner outline is valid
   - Check section structure
   - Review content generation

4. **Builder Fails**
   - Verify writer content is valid
   - Check diagram generation services
   - Review DOCX generation

### Debug Mode

For more detailed logging, modify the logger level in `test_full_pipeline.py`:

```python
logger.add(sys.stdout, level="DEBUG")  # Change from "INFO" to "DEBUG"
```

## WebSocket Testing

**Note**: WebSocket updates are tested through the API integration. To test WebSocket functionality:

1. Start the API server:
   ```bash
   cd api
   python run.py
   ```

2. Start Celery worker:
   ```bash
   celery -A app.core.celery_app worker --loglevel=info
   ```

3. Use the API to start a job and monitor WebSocket updates via the frontend or a WebSocket client.

The end-to-end test focuses on agent functionality and data flow, not WebSocket communication (which requires the full API stack).

## Best Practices

1. **Run Before Major Changes**: Always run the E2E test before deploying changes
2. **Use Real Projects**: Test with actual project files, not mock data
3. **Save Results**: Use `--save-results` to track performance over time
4. **Check Warnings**: Review warnings even if the test passes
5. **Monitor Timing**: Track execution times to identify performance regressions

## Integration with CI/CD

The test can be integrated into CI/CD pipelines:

```bash
# Exit code 0 on success, 1 on failure
python tests/test_full_pipeline.py \
    --project "$PROJECT_ZIP" \
    --guidelines "$GUIDELINES_PDF" \
    --skip-builder  # Faster for CI
```

Exit codes:
- `0`: Test passed
- `1`: Test failed


