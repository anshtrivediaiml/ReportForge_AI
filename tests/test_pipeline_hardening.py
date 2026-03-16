import shutil
import uuid
from pathlib import Path

import pytest

from agents.planner_agent import PlannerAgent
from agents.writer_agent import WriterAgent
from utils.facts_builder import build_project_facts


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def workspace_tmp_dir():
    base_dir = PROJECT_ROOT / "outputs" / "intermediate" / "pipeline_hardening_tests"
    base_dir.mkdir(parents=True, exist_ok=True)
    run_dir = base_dir / f"run_{uuid.uuid4().hex}"
    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        yield run_dir
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def test_build_project_facts_marks_sparse_project_as_reduced_scope():
    project_analysis = {
        "name": "Tiny Frontend",
        "files": [
            {
                "path": "src/main.tsx",
                "name": "main.tsx",
                "extension": ".tsx",
                "has_code": True,
                "code_snippet": "document.getElementById('root');",
                "lines": 12,
                "size": 240,
            }
        ],
        "directories": ["src"],
        "file_types": [".tsx"],
        "entry_points": ["src/main.tsx"],
    }

    facts = build_project_facts(project_analysis)

    assert facts["supported_project_category"] == "Frontend Web Application"
    assert facts["report_support_tier"] == "reduced"
    assert facts["reduced_scope_recommended"] is True
    assert facts["report_support_reasons"]


def test_planner_create_outline_uses_reduced_scope_path(workspace_tmp_dir):
    planner = PlannerAgent(output_dir=str(workspace_tmp_dir))
    codebase_structure = {
        "name": "Sparse Service",
        "supported_project_category": "Backend Service",
        "report_support_tier": "reduced",
        "report_support_reasons": ["Entry points could not be identified with high confidence."],
        "reduced_scope_recommended": True,
        "main_technologies": ["Python"],
        "modules": [{"name": "api"}],
        "entry_points_detected": [],
    }

    outline = planner.create_outline(codebase_structure, {})

    assert outline["report_title"] == "Sparse Service Reduced-Scope Technical Report"
    assert len(outline["chapters"]) == 3
    assert outline["chapters"][0]["title"] == "Project Overview"
    assert (workspace_tmp_dir / "report_outline.json").exists()


def test_writer_write_all_content_uses_reduced_scope_path(workspace_tmp_dir):
    writer = WriterAgent(output_dir=str(workspace_tmp_dir))
    outline = {
        "report_title": "Sparse Service Reduced-Scope Technical Report",
        "chapters": [
            {
                "number": 1,
                "title": "Project Overview",
                "sections": [
                    {"number": "1.1", "title": "Sparse Service Summary"},
                    {"number": "1.2", "title": "Detected Technologies and Entry Points"},
                ],
            },
            {
                "number": 2,
                "title": "Observed Structure and Implementation Facts",
                "sections": [
                    {"number": "2.1", "title": "Codebase Structure"},
                    {"number": "2.2", "title": "Verified Capabilities and Constraints"},
                ],
            },
            {
                "number": 3,
                "title": "Limitations and Recommended Next Analysis",
                "sections": [
                    {"number": "3.1", "title": "Current Analysis Limitations"},
                    {"number": "3.2", "title": "Suggested Next Steps"},
                ],
            },
        ],
    }
    codebase_structure = {
        "name": "Sparse Service",
        "supported_project_category": "Backend Service",
        "report_support_tier": "reduced",
        "report_support_reasons": ["The codebase is very small, so only a reduced-scope report is safe."],
        "reduced_scope_recommended": True,
        "main_technologies": ["Python"],
        "detected_capabilities": ["API calls"],
        "modules": [{"name": "api"}],
        "entry_points_detected": [],
        "code_statistics": {"code_files": 2},
    }

    content = writer.write_all_content(outline, codebase_structure)

    assert content["report_title"] == outline["report_title"]
    assert len(content["chapters"]) == 3
    assert all(chapter["sections"] for chapter in content["chapters"])
    assert all(section["content"] for chapter in content["chapters"] for section in chapter["sections"])
    assert (workspace_tmp_dir / "chapters_content.json").exists()
