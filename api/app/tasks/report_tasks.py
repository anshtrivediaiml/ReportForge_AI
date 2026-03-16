"""
Celery Tasks for Report Generation
"""
import sys
import os
import time
import threading
from pathlib import Path

# Add the report generator path to sys.path
REPORT_GENERATOR_PATH = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(REPORT_GENERATOR_PATH))

from celery import Task
from datetime import datetime
from uuid import UUID
from app.core.celery_app import celery_app
from app.utils.time_utils import get_accurate_utc_time
from app.services.websocket_service import broadcast_progress_sync
from app.services.job_service import sync_user_storage_usage, update_job_status
from app.schemas.job import JobUpdate
from app.schemas.websocket import ProgressUpdate, LogMessage, ErrorMessage
from app.models import Job, JobStatus, Stage
from sqlalchemy.orm import Session
from app.database import SessionLocal
from typing import Optional

# Import existing pipeline
from agents.parser_agent import ParserAgent
from agents.planner_agent import PlannerAgent
from agents.writer_agent import WriterAgent
from agents.builder_agent import BuilderAgent
# Import from code_analyzer at module level to avoid UnboundLocalError
# Use explicit import to avoid scoping issues
import utils.code_analyzer as code_analyzer_module


class ReportTask(Task):
    """Custom Celery task with error handling"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        # Extract job_id from args (first argument: job_id)
        # When bind=True, args[0] is the first positional arg (job_id)
        job_id = args[0] if args and len(args) > 0 else None
        
        if job_id:
            db = SessionLocal()
            try:
                job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id
                update_job_status(
                    db,
                    job_uuid,
                    JobUpdate(
                        status=JobStatus.FAILED,
                        error_message=str(exc),
                        error_traceback=str(einfo)
                    )
                )
            finally:
                db.close()
            
            # Broadcast error
            error_msg = ErrorMessage(
                job_id=str(job_id),
                stage=Stage.PARSER,
                message=f"Generation failed: {str(exc)}",
                error=str(exc),
                timestamp=get_accurate_utc_time()
            )
            # Use mode='json' to serialize datetime objects
            broadcast_progress_sync(str(job_id), error_msg.model_dump(mode='json'))


@celery_app.task(
    bind=True, 
    base=ReportTask,
    autoretry_for=(Exception,),
    max_retries=0,  # Disable automatic retries - task should only run once
    retry_backoff=False,
    ignore_result=True  # Don't store results to save memory
)
def generate_report_task(self, job_id: str, guidelines_path: str, project_path: str, user_id: Optional[int] = None, **kwargs):
    """
    Main report generation task with detailed progress tracking
    
    Args:
        self: Celery task instance (auto-provided when bind=True)
        job_id: UUID of the job (str)
        guidelines_path: Path to guidelines PDF file (str)
        project_path: Path to project ZIP file (str)
        user_id: User ID for tracking (int or None for backward compatibility)
    
    When called via apply_async, pass exactly 4 arguments:
    [job_id, guidelines_path, project_path, user_id]
    """
    db = SessionLocal()
    job_uuid = UUID(job_id) if isinstance(job_id, str) else job_id
    
    def send_update(stage: str, progress: int, message: str, **details):
        """Helper to send progress updates"""
        update_data = ProgressUpdate(
            job_id=job_id,
            stage=Stage(stage),
            progress=progress,
            message=message,
            timestamp=datetime.utcnow(),
            **details
        )
        
        # Broadcast via WebSocket
        broadcast_progress_sync(job_id, update_data.model_dump(mode='json'))
        
        # Update database
        update_dict = {
            "current_stage": Stage(stage),
            "progress": progress,
            **{k: v for k, v in details.items() if k in [
                'files_analyzed', 'chapters_created', 'sections_written', 
                'total_sections', 'pages_generated'
            ]}
        }
        
        if progress == 100 and stage == "complete":
            update_dict["status"] = JobStatus.COMPLETED
        
        update_job_status(db, job_uuid, JobUpdate(**update_dict))
        
        # Log to console
        print(f"[{job_id}] [{stage}] {progress}% - {message}")
    
    def send_log(agent: str, level: str, message: str):
        """Helper to send log entries"""
        log_data = LogMessage(
            job_id=job_id,
            agent=agent,
            level=level,
            message=message,
            timestamp=datetime.utcnow()
        )
        broadcast_progress_sync(job_id, log_data.model_dump(mode='json'))
        print(f"[{job_id}] [{agent}] [{level.upper()}] {message}")
    
    try:
        # Update job to processing - SEND IMMEDIATELY
        update_job_status(db, job_uuid, JobUpdate(
            status=JobStatus.PROCESSING,
            current_stage=Stage.PARSER,
            progress=0
        ))
        send_update('parser', 0, 'Starting report generation...')
        send_log('parser', 'info', 'Report generation started')
        
        # ============ STAGE 1: PARSER AGENT ============
        send_update('parser', 0, 'Initializing Parser Agent...')
        send_log('parser', 'info', 'Starting parser agent...')
        
        # Create job-specific output directory to prevent content mixing
        parser = ParserAgent(job_id=job_id)
        
        # Step 1: Analyze project structure first (with job-specific extraction)
        send_update('parser', 5, 'Analyzing project structure...')
        send_log('parser', 'info', f'Scanning project files from: {project_path} (job: {job_id})')
        send_log('parser', 'info', 'Using job-specific extraction directory to prevent content mixing')
        # Use module.attribute to avoid UnboundLocalError
        project_analysis = code_analyzer_module.analyze_project(project_path, job_id=job_id)
        
        # Log project name to verify it's the correct project
        project_name = project_analysis.get('name', 'Unknown')
        files_count = len(project_analysis.get('files', []))
        file_list = project_analysis.get('files', [])[:10]  # First 10 files for verification
        
        send_log('parser', 'info', f'🔍 PROJECT ANALYSIS RESULTS:')
        send_log('parser', 'info', f'   Project name extracted: {project_name}')
        send_log('parser', 'info', f'   Project path analyzed: {project_path}')
        send_log('parser', 'info', f'   Job ID: {job_id}')
        send_log('parser', 'info', f'   Files found: {files_count}')
        send_log('parser', 'info', f'   Sample files: {[f.get("path", str(f)) for f in file_list[:5]]}')
        
        # CRITICAL: Log the actual ZIP file name to verify we're analyzing the right file
        from pathlib import Path
        zip_name = Path(project_path).name if project_path else "Unknown"
        send_log('parser', 'info', f'   Source ZIP file: {zip_name}')
        
        # CRITICAL: Comprehensive validation and auto-fix of project analysis
        forbidden_names = ['temp extract', 'temp_extract', 'weekend wizard', 'cli tool', 'mcp protocol', 'temp', 'extract', 'project']
        
        # Validate and auto-fix project name if needed
        original_project_name = project_name
        if any(forbidden in project_name.lower() for forbidden in forbidden_names):
            send_log('parser', 'warning', f'⚠️  Project name "{project_name}" appears to be generic or from a previous project')
            send_log('parser', 'info', 'Attempting to extract correct project name from files...')
            
            # Re-analyze to get better name - use the same analyzer instance
            # The project_dir is already extracted, so we can use it directly
            from pathlib import Path
            extract_base = Path("temp_extract")
            if job_id:
                project_dir = extract_base / f"job_{job_id}"
            else:
                import time
                project_dir = extract_base / f"temp_{int(time.time())}"
            
            # Re-analyze project to get correct name
            send_log('parser', 'info', f'Re-analyzing project from: {project_path}')
            # Use module.attribute to avoid UnboundLocalError
            re_analysis = code_analyzer_module.analyze_project(project_path, job_id=job_id)
            new_project_name = re_analysis.get('name', '')
            
            if new_project_name and new_project_name.lower() not in [f.lower() for f in forbidden_names]:
                project_name = new_project_name
                project_analysis['name'] = project_name
                project_analysis['files'] = re_analysis.get('files', project_analysis.get('files', []))
                send_log('parser', 'success', f'✅ Fixed project name: "{original_project_name}" → "{project_name}"')
            else:
                # Last resort: use file-based unique identifier
                # Use module.attribute to avoid UnboundLocalError
                analyzer = code_analyzer_module.CodeAnalyzer(project_path, job_id=job_id)
                project_dir = analyzer.extract_if_zip("temp_extract")
                better_name = analyzer._generate_file_based_name(project_dir)
                project_name = better_name
                project_analysis['name'] = project_name
                send_log('parser', 'warning', f'⚠️  Using file-based identifier: "{project_name}"')
        
        # Validate file count is reasonable
        if files_count < 1:
            error_msg = f"Project has no files (count: {files_count}). Cannot generate report."
            send_log('parser', 'error', f'❌ {error_msg}')
            send_update('parser', 0, 'Project validation failed', error=error_msg)
            raise ValueError(error_msg)
        elif files_count > 10000:
            send_log('parser', 'warning', f'⚠️  Very large project detected: {files_count} files')
        
        # Final validation: ensure we have a valid project name
        if not project_name or project_name.lower() in [f.lower() for f in forbidden_names]:
            error_msg = f"Cannot determine valid project name. Extracted: '{project_name}'. Cannot proceed."
            send_log('parser', 'error', f'❌ {error_msg}')
            send_update('parser', 0, 'Project validation failed', error=error_msg)
            raise ValueError(error_msg)
        
        send_log('parser', 'success', f'✅ Project validated: "{project_name}" with {files_count} files')
        
        # CRITICAL: Ensure project_analysis has the correct name before proceeding
        project_analysis['name'] = project_name
        send_log('parser', 'info', f'🔒 Locked project name to: "{project_name}" for this job')
        
        send_update('parser', 15, f'Project structure analyzed: {files_count} files found', files_analyzed=files_count)
        
        # Step 2: Parse guidelines PDF
        send_update('parser', 20, 'Reading guidelines PDF...')
        send_log('parser', 'info', 'Extracting text from guidelines PDF...')
        
        send_update('parser', 30, 'Extracting formatting rules from guidelines...')
        send_log('parser', 'info', 'Parsing guidelines document with LLM (this may take 2-3 minutes)...')
        guidelines_config = parser.parse_guidelines(guidelines_path)
        
        send_log('parser', 'success', 'Guidelines parsed successfully')
        send_update('parser', 50, 'Guidelines parsing complete')
        
        # Step 3: Analyze project structure with LLM
        send_update('parser', 60, 'Analyzing codebase structure with LLM...')
        send_log('parser', 'info', f'🔍 Processing project structure for: "{project_name}" (job: {job_id})')
        send_log('parser', 'info', f'📁 Project files being analyzed: {[f.get("path", str(f)) for f in project_analysis.get("files", [])[:5]]}')
        send_log('parser', 'info', '🚫 LLM will analyze ONLY this project - no mixing with other projects')
        codebase_structure = parser.analyze_project_structure(project_analysis)
        
        project_type = codebase_structure.get('project_type', 'Unknown')
        technologies = codebase_structure.get('main_technologies', [])
        send_log('parser', 'success', f'Detected project type: {project_type} for project: {project_name}')
        if technologies:
            send_log('parser', 'info', f'Main technologies: {", ".join(technologies)}')
        
        # CRITICAL: Verify project name matches after LLM analysis
        llm_project_name = codebase_structure.get('name', '')
        if llm_project_name != project_name:
            send_log('parser', 'warning', f'Project name mismatch! LLM returned: {llm_project_name}, Expected: {project_name}')
            # Force correct project name to prevent mixing
            codebase_structure['name'] = project_name
            send_log('parser', 'info', f'Forced project name to: {project_name} to prevent content mixing')
        
        # Additional validation: ensure project type makes sense
        project_type = codebase_structure.get('project_type', 'Unknown')
        if project_type.lower() in ['cli tool', 'temp extract'] and 'cli tool' not in project_name.lower() and 'temp extract' not in project_name.lower():
            send_log('parser', 'warning', f'Project type "{project_type}" may not match project name "{project_name}"')
        
        send_update('parser', 80, 'Codebase analysis complete')
        
        # CRITICAL: Final verification before combining results
        final_project_name = codebase_structure.get('name', project_name)
        if final_project_name != project_name:
            send_log('parser', 'warning', f'⚠️  Project name changed during analysis: {project_name} → {final_project_name}')
            # Use the validated name, not the LLM's suggestion
            codebase_structure['name'] = project_name
            final_project_name = project_name
            send_log('parser', 'info', f'🔒 Using validated project name: "{project_name}"')
        
        # Combine results
        parsed_data = {
            "guidelines": guidelines_config,
            "codebase": codebase_structure
        }
        
        # CRITICAL: Ensure codebase has correct project name
        parsed_data['codebase']['name'] = project_name

        support_tier = parsed_data['codebase'].get('report_support_tier', 'full')
        support_category = parsed_data['codebase'].get('supported_project_category', 'Other')
        support_reasons = parsed_data['codebase'].get('report_support_reasons', [])
        reduced_scope_mode = parsed_data['codebase'].get('reduced_scope_recommended', False)

        send_log('parser', 'info', f'Pipeline support category: {support_category}')
        send_log('parser', 'info', f'Pipeline support tier: {support_tier}')
        for reason in support_reasons:
            send_log('parser', 'warning', f'Reduced-scope reason: {reason}')

        send_update('parser', 100, 'Parser analysis complete', 
                   files_analyzed=files_count,
                   project_type=project_type)
        send_log('parser', 'success', f'=== PARSER AGENT COMPLETED === Project: "{project_name}"')
        
        # ============ STAGE 2: PLANNER AGENT ============
        send_update('planner', 0, 'Initializing Planner Agent...')
        send_log('planner', 'info', 'Starting planner agent...')
        
        # Use job-specific output directory
        planner = PlannerAgent(job_id=job_id)
        
        # Step 1: Prepare project summary
        send_update('planner', 10, 'Preparing project summary...')
        send_log('planner', 'info', 'Analyzing codebase structure for chapter planning...')
        
        # Step 2: Create outline
        planner_project_name = parsed_data['codebase'].get('name', project_name)
        if reduced_scope_mode:
            send_update('planner', 20, 'Creating reduced-scope outline from deterministic facts...')
            send_log('planner', 'warning', f'Using reduced-scope outline mode for project: "{planner_project_name}"')
            outline = planner.build_reduced_scope_outline(parsed_data['codebase'])
        else:
            send_update('planner', 20, 'Generating chapter outline with LLM...')
            send_log('planner', 'info', f'📋 Creating report structure for project: "{planner_project_name}" (job: {job_id})')
            send_log('planner', 'info', f'📁 Project files: {len(parsed_data["codebase"].get("files", []))} files')
            send_log('planner', 'info', '🚫 LLM will create outline based ONLY on this project - no mixing with other projects')
            send_log('planner', 'info', 'Creating report structure and chapter outline (this may take 2-3 minutes)...')
            outline = planner.create_outline(parsed_data['codebase'], parsed_data['guidelines'])
        
        # Verify outline is for the correct project
        report_title = outline.get('report_title', '')
        send_log('planner', 'info', f'Generated report title: {report_title}')
        if project_name.lower() not in report_title.lower() and 'temp extract' not in project_name.lower():
            send_log('planner', 'warning', f'Report title may not match project name! Title: {report_title}, Project: {project_name}')
        
        send_log('planner', 'success', 'Chapter outline generated')
        send_update('planner', 60, 'Chapter outline generated')
        
        # Step 3: Post-processing and validation
        send_update('planner', 70, 'Post-processing outline...')
        send_log('planner', 'info', 'Validating and numbering chapters and sections...')
        
        # Post-process numbering
        for i, chapter in enumerate(outline.get("chapters", []), 1):
            chapter["number"] = i
            for j, section in enumerate(chapter.get("sections", []), 1):
                section["number"] = f"{i}.{j}"
        
        planner.validate_outline(outline)
        
        chapters_count = len(outline.get('chapters', []))
        total_sections = sum(len(ch.get('sections', [])) for ch in outline.get('chapters', []))
        
        send_log('planner', 'success', f'Created outline with {chapters_count} chapters')
        send_log('planner', 'info', f'Total sections to write: {total_sections}')
        
        # Log chapter details
        for chapter in outline.get('chapters', []):
            chapter_num = chapter.get('number', '?')
            chapter_title = chapter.get('title', 'Unknown')
            sections_count = len(chapter.get('sections', []))
            send_log('planner', 'info', f'Chapter {chapter_num}: {chapter_title} ({sections_count} sections)')
        
        send_update('planner', 100, 'Report structure created',
                   chapters_created=chapters_count,
                   total_sections=total_sections)
        send_log('planner', 'success', '=== PLANNER AGENT COMPLETED ===')
        
        # ============ STAGE 3: WRITER AGENT ============
        send_update('writer', 0, 'Initializing Writer Agent...')
        send_log('writer', 'info', f'Starting content generation for {total_sections} sections...')
        
        # Use job-specific output directory
        writer = WriterAgent(job_id=job_id)
        
        if reduced_scope_mode:
            send_update('writer', 10, 'Generating reduced-scope content from deterministic facts...')
            send_log('writer', 'warning', 'Using reduced-scope content generation mode.')
            content = writer.build_reduced_scope_content(outline, parsed_data['codebase'])
            sections_written = sum(len(chapter.get('sections', [])) for chapter in content.get('chapters', []))
            send_update('writer', 100, 'Reduced-scope content generation complete',
                       sections_written=sections_written,
                       total_sections=total_sections)
            send_log('writer', 'success', f'Reduced-scope content generated for {sections_written} sections')
        else:
            # Manually write content to track progress in real-time
            content = {
                "report_title": outline.get("report_title", "Technical Report"),
                "chapters": []
            }
            
            chapters = outline.get("chapters", [])
            base_progress = 5  # Start at 5%
            progress_range = 90  # Writer goes from 5% to 95% (0-100% within writer stage)
            
            sections_written = 0
            
            # Write each chapter with progress tracking
            for chapter_idx, chapter_info in enumerate(chapters):
                chapter_num = chapter_info["number"]
                chapter_title = chapter_info["title"]
                
                # Calculate progress: 5% + (chapter_index / total_chapters) * 90%
                chapter_progress = base_progress + int((chapter_idx / len(chapters)) * progress_range)
                send_update('writer', chapter_progress, f'Writing Chapter {chapter_num}: {chapter_title}...')
                send_log('writer', 'info', f'Writing Chapter {chapter_num}: {chapter_title}...')
                
                # Handle special chapters
                if chapter_num == 1:
                    # Introduction
                    send_log('writer', 'info', f'Writing Introduction chapter (Chapter {chapter_num})...')
                    chapter_content = writer.write_introduction(outline, parsed_data['codebase'])
                    send_log('writer', 'success', f'Chapter {chapter_num} (Introduction) completed')
                
                elif chapter_num == len(chapters):
                    # Conclusion (last chapter)
                    send_log('writer', 'info', f'Writing Conclusion chapter (Chapter {chapter_num})...')
                    chapter_content = writer.write_conclusion(outline, parsed_data['codebase'])
                    send_log('writer', 'success', f'Chapter {chapter_num} (Conclusion) completed')
                
                else:
                    # Regular chapters - write sections one by one
                    chapter_content = {
                        "chapter_number": chapter_num,
                        "chapter_title": chapter_title,
                        "sections": []
                    }
                    
                    sections = chapter_info.get("sections", [])
                    for section_idx, section_info in enumerate(sections):
                        section_num = section_info["number"]
                        section_title = section_info["title"]
                        
                        # Progress = chapter_base + (section_index / total_sections_in_chapter) * chapter_range
                        chapter_base = base_progress + int((chapter_idx / len(chapters)) * progress_range)
                        chapter_range = int((1 / len(chapters)) * progress_range)
                        section_progress = chapter_base + int((section_idx / len(sections)) * chapter_range)
                        
                        send_update('writer', section_progress,
                                  f'Writing Chapter {chapter_num}, Section {section_num}: {section_title}...',
                                  sections_written=sections_written,
                                  total_sections=total_sections)
                        send_log('writer', 'info', f'Writing Chapter {chapter_num}, Section {section_num}: {section_title}...')
                        
                        section = writer.write_section(
                            section_number=section_info["number"],
                            section_title=section_info["title"],
                            section_description=section_info.get("description", ""),
                            project_context=parsed_data['codebase'],
                            chapter_context=chapter_title
                        )
                        
                        chapter_content["sections"].append(section)
                        sections_written += 1
                        
                        # Update progress after each section
                        section_progress_after = chapter_base + int(((section_idx + 1) / len(sections)) * chapter_range)
                        send_update('writer', section_progress_after,
                                  f'Completed Section {section_num}: {section_title}',
                                  sections_written=sections_written,
                                  total_sections=total_sections)
                        send_log('writer', 'success', f'Section {section_num} completed: {section_title}')
                
                content["chapters"].append(chapter_content)
                
                # Update progress after chapter completion
                chapter_complete_progress = base_progress + int(((chapter_idx + 1) / len(chapters)) * progress_range)
                send_update('writer', chapter_complete_progress,
                          f'Chapter {chapter_num} completed: {chapter_title}',
                          sections_written=sections_written,
                          total_sections=total_sections)
                send_log('writer', 'success', f'Chapter {chapter_num} completed: {chapter_title}')
        
        # Final update
        send_update('writer', 100, 'Content generation complete',
                   sections_written=sections_written,
                   total_sections=total_sections)
        send_log('writer', 'success', f'All {sections_written} sections written successfully')
        
        # ============ STAGE 4: BUILDER AGENT ============
        send_update('builder', 0, 'Initializing Builder Agent...')
        send_log('builder', 'info', 'Starting builder agent...')
        
        # Use job-specific output directory
        builder = BuilderAgent(job_id=job_id)
        
        # Create document
        send_update('builder', 5, 'Creating document structure...')
        send_log('builder', 'info', 'Initializing DOCX document with formatting guidelines...')
        from utils.docx_generator import DOCXGenerator
        doc = DOCXGenerator(parsed_data['guidelines'])
        doc.figures_list = []
        doc.tables_list = []
        
        # Add title page
        send_update('builder', 10, 'Adding title page...')
        send_log('builder', 'info', 'Adding title page...')
        builder._add_title_page(doc, content)
        doc.add_page_break()
        send_log('builder', 'success', 'Title page added')
        
        # Add table of contents
        send_update('builder', 15, 'Adding table of contents...')
        send_log('builder', 'info', 'Generating table of contents...')
        doc.add_table_of_contents(outline)
        doc.add_page_break()
        send_log('builder', 'success', 'Table of contents added')
        
        # First pass: Collect figures and tables
        send_update('builder', 20, 'Collecting figures and tables...')
        send_log('builder', 'info', 'Scanning chapters for figures and tables...')
        temp_doc = DOCXGenerator(parsed_data['guidelines'])
        temp_doc.figures_list = []
        temp_doc.tables_list = []
        
        content_chapters = content.get('chapters', [])
        for chapter in content_chapters:
            builder._add_chapter(temp_doc, chapter, collect_only=True)
        
        # Add List of Figures
        if temp_doc.figures_list:
            send_update('builder', 25, 'Adding list of figures...')
            send_log('builder', 'info', f'Adding list of {len(temp_doc.figures_list)} figures...')
            doc.figures_list = temp_doc.figures_list
            builder._add_list_of_figures(doc)
            doc.add_page_break()
            send_log('builder', 'success', 'List of figures added')
        
        # Add List of Tables
        if temp_doc.tables_list:
            send_update('builder', 30, 'Adding list of tables...')
            send_log('builder', 'info', f'Adding list of {len(temp_doc.tables_list)} tables...')
            doc.tables_list = temp_doc.tables_list
            builder._add_list_of_tables(doc)
            doc.add_page_break()
            send_log('builder', 'success', 'List of tables added')
        
        # Second pass: Add all chapters with progress tracking
        base_progress = 35
        chapter_progress_range = 55  # 35-90% for chapters
        
        for chapter_idx, chapter in enumerate(content_chapters):
            chapter_num = chapter.get('chapter_number', chapter_idx + 1)
            chapter_title = chapter.get('chapter_title', f'Chapter {chapter_num}')
            sections_count = len(chapter.get('sections', []))
            
            # Calculate progress: 35% + (chapter_index / total_chapters) * 55%
            chapter_progress = base_progress + int((chapter_idx / len(content_chapters)) * chapter_progress_range)
            send_update('builder', chapter_progress, f'Adding Chapter {chapter_num}: {chapter_title}...')
            send_log('builder', 'info', f'Adding Chapter {chapter_num}: {chapter_title}...')
            
            # Track sections within chapter
            sections = chapter.get('sections', [])
            for section_idx, section in enumerate(sections):
                section_num = section.get('number', f'{chapter_num}.{section_idx + 1}')
                section_title = section.get('title', f'Section {section_num}')
                
                section_progress = chapter_progress + int(((section_idx + 1) / len(sections)) * (chapter_progress_range / len(content_chapters)))
                send_update('builder', min(section_progress, base_progress + chapter_progress_range - 5),
                          f'Formatting Chapter {chapter_num}, Section {section_num}: {section_title}...')
                send_log('builder', 'info', f'Formatting Section {section_num}: {section_title}...')
            
            builder._add_chapter(doc, chapter)
            doc.add_page_break()
            
            send_log('builder', 'success', f'Chapter {chapter_num} added with {sections_count} sections')
            send_update('builder', base_progress + int(((chapter_idx + 1) / len(content_chapters)) * chapter_progress_range),
                      f'Chapter {chapter_num} completed: {chapter_title}',
                      pages_generated=chapter_idx + 1)
        
        # Add references section
        send_update('builder', 90, 'Adding references section...')
        send_log('builder', 'info', 'Generating references section...')
        codebase_info = {
            "name": content.get("report_title", "Technical Report"),
            "technologies": []
        }
        for chapter in content.get("chapters", []):
            for section in chapter.get("sections", []):
                content_text = section.get("content", "").lower()
                if "python" in content_text:
                    codebase_info["technologies"].append("Python")
                if "javascript" in content_text or "node" in content_text:
                    codebase_info["technologies"].append("JavaScript")
        
        builder._add_references_section(doc, content, outline, codebase_info)
        send_log('builder', 'success', 'References section added')
        
        # Add headers/footers
        send_update('builder', 95, 'Applying formatting guidelines...')
        send_log('builder', 'info', 'Adding headers and footers...')
        doc.add_header_footer()
        send_log('builder', 'success', 'Headers and footers added')
        
        # Save document (in job-specific directory)
        send_update('builder', 98, 'Saving document...')
        send_log('builder', 'info', 'Saving final document...')
        output_filename = f"Report_{job_id[:8]}.docx"
        output_path = builder.output_dir / output_filename
        doc.save(str(output_path))
        
        # Log the job-specific output path for debugging
        send_log('builder', 'info', f'Document saved to job-specific directory: {output_path}')
        
        # Convert output_path to string and Path object for filename extraction
        from pathlib import Path as PathLib
        output_path_obj = PathLib(output_path) if not isinstance(output_path, PathLib) else output_path
        output_path_str = str(output_path_obj)
        
        # Get file size for metrics
        try:
            file_size = output_path_obj.stat().st_size
            send_log('builder', 'success', f'Document saved: {output_filename} ({file_size / 1024:.1f} KB)')
        except:
            send_log('builder', 'success', f'Document saved: {output_filename}')
        
        send_log('builder', 'success', '=== BUILDER AGENT COMPLETED ===')
        send_update('builder', 100, 'Document assembly complete')
        
        # ============ STAGE 5: COMPLETE ============
        send_update('complete', 100, 'Report generated successfully! 🎉',
                   sections_written=sections_written,
                   total_sections=total_sections,
                   chapters_created=chapters_count,
                   files_analyzed=files_count)
        
        send_log('complete', 'success', '✨ Report generation completed successfully')
        
        # Update final job status
        update_job_status(
            db,
            job_uuid,
            JobUpdate(
                status=JobStatus.COMPLETED,
                current_stage=Stage.COMPLETE,
                progress=100,
                output_path=output_path_str,
                output_filename=output_filename
            )
        )

        if user_id is not None:
            sync_user_storage_usage(db, user_id, commit=False)
            db.commit()
        
        # Task completed successfully - return result
        result = {
            'status': 'success',
            'output_path': output_path_str,
            'metrics': {
                'files_analyzed': files_count,
                'chapters_created': chapters_count,
                'sections_written': sections_written
            }
        }
        
        # Log completion
        send_log('complete', 'success', 'Task completed and worker is now idle')
        print(f"[{job_id}] ✅ Task completed successfully. Worker is now idle.")
        
        return result
        
    except Exception as e:
        # CRITICAL: Update job status to FAILED FIRST to ensure database consistency
        try:
            # Get current stage for error reporting
            current_job = db.query(Job).filter(Job.id == job_uuid).first()
            if current_job and current_job.current_stage:
                error_stage = current_job.current_stage.value
            else:
                error_stage = 'planner'  # Default to planner if unknown
            
            # Update job status to FAILED immediately
            update_job_status(
                db,
                job_uuid,
                JobUpdate(
                    status=JobStatus.FAILED,
                    error_message=str(e),
                    current_stage=Stage(error_stage) if error_stage else None
                )
            )
            db.commit()  # Commit immediately to ensure status is saved
        except Exception as db_error:
            print(f"[{job_id}] Failed to update job status to FAILED: {db_error}")
            # Continue to send error message even if DB update fails
        
        # Send error log
        send_log('error', 'error', f'Error: {str(e)}')
        
        # Broadcast error via WebSocket using ErrorMessage schema
        # Use the error_stage we determined above
        error_msg = ErrorMessage(
            job_id=job_id,
            stage=Stage(error_stage) if error_stage else Stage.PARSER,
            message=f'Generation failed: {str(e)}',
            error=str(e),
            timestamp=datetime.utcnow()
        )
        broadcast_progress_sync(job_id, error_msg.model_dump(mode='json'))
        
        # Log error and task completion
        print(f"[{job_id}] Task failed with error: {str(e)}")
        print(f"[{job_id}] Task execution ended. Worker is now idle.")

        if user_id is not None:
            try:
                sync_user_storage_usage(db, user_id, commit=False)
                db.commit()
            except Exception as storage_error:
                print(f"[{job_id}] Failed to sync storage usage after task failure: {storage_error}")

        # Re-raise to mark task as failed (but don't retry due to max_retries=0)
        raise
    finally:
        # Always close database connection
        try:
            db.close()
        except:
            pass
        # Log that worker is idle
        print(f"[{job_id}] Database connection closed. Worker ready for next task.")

