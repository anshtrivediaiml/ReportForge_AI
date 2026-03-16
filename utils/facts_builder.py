"""
Facts Builder - Deterministic fact extraction from project analysis
NO LLM CALLS - Pure computation only
"""
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter
from loguru import logger


def build_project_facts(project_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build deterministic facts from project analysis.
    NO LLM CALLS - This is pure computation.
    
    Args:
        project_analysis: Raw output from CodeAnalyzer
        
    Returns:
        Dictionary of computed facts that can be verified without LLM
    """
    logger.info("Building project facts (deterministic computation)...")
    
    files = project_analysis.get("files", [])
    directories = project_analysis.get("directories", [])
    file_types = project_analysis.get("file_types", {})
    
    # 1. File type counts (by extension)
    file_type_counts = dict(Counter(file_types))
    
    # 2. Directory structure analysis
    directory_depth = 0
    directory_names = []
    for dir_path in directories:
        parts = Path(dir_path).parts
        directory_depth = max(directory_depth, len(parts))
        directory_names.append(dir_path)
    
    # 3. Frontend/Backend indicators
    frontend_indicators = ['.html', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte']
    backend_indicators = ['.py', '.java', '.go', '.rs', '.php', '.rb', '.cpp', '.c']
    server_indicators = ['server.js', 'server.py', 'app.py', 'main.py', 'index.php', 'server.ts']
    api_indicators = ['api/', 'routes/', 'controllers/', 'endpoints/']
    
    frontend_files = sum(1 for f in files if any(f.get('extension', '').lower() == ext for ext in frontend_indicators))
    backend_files = sum(1 for f in files if any(f.get('extension', '').lower() == ext for ext in backend_indicators))
    
    # Check for server files
    has_server_file = any(
        any(indicator in f.get('name', '').lower() for indicator in server_indicators)
        for f in files
    )
    
    # Check for API directories
    has_api_structure = any(
        any(indicator in dir_name.lower() for indicator in api_indicators)
        for dir_name in directory_names
    )
    
    frontend_only = frontend_files > 0 and backend_files == 0 and not has_server_file
    backend_present = backend_files > 0 or has_server_file or has_api_structure
    fullstack = frontend_files > 0 and backend_present
    
    # 4. Entry point confidence
    entry_points = project_analysis.get("entry_points", [])
    entry_point_confidence = "high" if len(entry_points) > 0 else "low"
    
    # Check if entry points are actually present in files
    entry_point_files = [f for f in files if any(ep in f.get('path', '') for ep in entry_points)]
    if len(entry_point_files) == 0 and len(entry_points) > 0:
        entry_point_confidence = "medium"  # Listed but not found in files
    elif len(entry_point_files) > 0:
        entry_point_confidence = "high"
    
    # 5. Detected capabilities (from code snippets and file structure)
    capabilities = []
    
    # Check code snippets for capabilities
    for file_info in files:
        if not file_info.get('has_code'):
            continue
            
        code_snippet = file_info.get('code_snippet', '').lower()
        file_path = file_info.get('path', '').lower()
        extension = file_info.get('extension', '').lower()
        
        # DOM manipulation
        if any(keyword in code_snippet for keyword in ['document.', 'getelementbyid', 'queryselector', 'addeventlistener']):
            if 'DOM manipulation' not in capabilities:
                capabilities.append('DOM manipulation')
        
        # Forms
        if any(keyword in code_snippet for keyword in ['<form', 'form.', 'onsubmit', 'input', 'textarea']):
            if 'Forms' not in capabilities:
                capabilities.append('Forms')
        
        # Events
        if any(keyword in code_snippet for keyword in ['addeventlistener', 'onclick', 'onchange', 'event', 'handler']):
            if 'Event handling' not in capabilities:
                capabilities.append('Event handling')
        
        # APIs (fetch, axios, requests)
        if any(keyword in code_snippet for keyword in ['fetch(', 'axios.', 'requests.', 'http.', 'api']):
            if 'API calls' not in capabilities:
                capabilities.append('API calls')
        
        # Database
        if any(keyword in code_snippet for keyword in ['sql', 'database', 'db.', 'mongodb', 'mysql', 'postgres', 'sqlite']):
            if 'Database' not in capabilities:
                capabilities.append('Database')
        
        # File operations
        if any(keyword in code_snippet for keyword in ['fs.', 'open(', 'readfile', 'writefile', 'pathlib']):
            if 'File operations' not in capabilities:
                capabilities.append('File operations')
        
        # Routing
        if any(keyword in file_path for keyword in ['route', 'router', 'path']):
            if 'Routing' not in capabilities:
                capabilities.append('Routing')
        
        # State management
        if any(keyword in code_snippet for keyword in ['state', 'redux', 'context', 'store', 'useState']):
            if 'State management' not in capabilities:
                capabilities.append('State management')
    
    # 6. Technology detection (from file types and structure)
    detected_technologies = []
    
    if file_type_counts.get('.html', 0) > 0:
        detected_technologies.append('HTML')
    if file_type_counts.get('.css', 0) > 0:
        detected_technologies.append('CSS')
    if file_type_counts.get('.js', 0) > 0 or file_type_counts.get('.jsx', 0) > 0:
        detected_technologies.append('JavaScript')
    if file_type_counts.get('.ts', 0) > 0 or file_type_counts.get('.tsx', 0) > 0:
        detected_technologies.append('TypeScript')
    if file_type_counts.get('.py', 0) > 0:
        detected_technologies.append('Python')
    if file_type_counts.get('.java', 0) > 0:
        detected_technologies.append('Java')
    
    # Check for frameworks
    for file_info in files:
        file_path = file_info.get('path', '').lower()
        if 'react' in file_path or 'react' in file_info.get('name', '').lower():
            if 'React' not in detected_technologies:
                detected_technologies.append('React')
        if 'vue' in file_path or 'vue' in file_info.get('name', '').lower():
            if 'Vue' not in detected_technologies:
                detected_technologies.append('Vue')
        if 'angular' in file_path or 'angular' in file_info.get('name', '').lower():
            if 'Angular' not in detected_technologies:
                detected_technologies.append('Angular')
    
    # 7. Code statistics
    code_files = [f for f in files if f.get('has_code', False)]
    total_code_lines = sum(f.get('lines', 0) for f in code_files)
    avg_file_size = sum(f.get('size', 0) for f in files) / len(files) if files else 0
    
    # 8. Enhanced code content extraction - ALL code files for comprehensive analysis
    # This ensures the Planner and Writer have access to the entire codebase
    code_content = {}
    
    # Process ALL code files (no arbitrary limit)
    # This provides comprehensive project understanding for any domain
    for file_info in code_files:
        file_path = file_info.get('path', '')
        if not file_path:
            continue
        
        code = file_info.get('code_snippet', '')
        if code:
            # Include ALL code files with their snippets
            code_content[file_path] = {
                "name": file_info.get('name', 'unknown'),
                "path": file_path,
                "code": code,
                "lines": file_info.get('lines', 0),
                "extension": file_info.get('extension', ''),
                "is_entry_point": file_info.get('is_entry_point', False),
                "is_module": file_info.get('is_module', False)
            }
    
    logger.info(f"Extracted code content from {len(code_content)} files for comprehensive analysis")
    
    # 9. Extract and analyze README files for use cases
    readme_content = {}
    use_cases = []
    project_purpose = ""
    
    readme_files = [f for f in files if f.get('is_readme', False) or any(name in f.get('name', '').lower() for name in ['readme', 'read_me'])]
    for readme_file in readme_files:
        file_path = readme_file.get('path', '')
        # Try to get README content (prioritize readme_content field)
        readme_text = readme_file.get('readme_content', '')
        if not readme_text:
            # Fallback: try code_snippet if available
            readme_text = readme_file.get('code_snippet', '')
        
        if readme_text:
            readme_content[file_path] = readme_text[:5000]  # Limit README to 5000 chars
            
            # Extract use cases and purpose from README
            readme_lower = readme_text.lower()
            
            # Look for common patterns
            if 'use case' in readme_lower or 'usage' in readme_lower or 'example' in readme_lower:
                # Try to extract use case section
                lines = readme_text.split('\n')
                in_use_case_section = False
                use_case_lines = []
                for line in lines:
                    line_lower = line.lower()
                    if 'use case' in line_lower or 'usage' in line_lower or 'example' in line_lower or 'how to' in line_lower:
                        in_use_case_section = True
                        use_case_lines.append(line)
                    elif in_use_case_section and line.strip() and not line.startswith('#'):
                        use_case_lines.append(line)
                        if len(use_case_lines) > 15:  # Limit use case extraction
                            break
                    elif in_use_case_section and line.strip().startswith('#'):
                        # New section, stop collecting
                        break
                
                if use_case_lines:
                    use_cases.append('\n'.join(use_case_lines[:15]))
            
            # Extract project purpose from first paragraph or description
            if not project_purpose:
                # Look for description, about, or first meaningful paragraph
                lines = readme_text.split('\n')
                for i, line in enumerate(lines[:30]):  # Check first 30 lines
                    line_stripped = line.strip()
                    line_lower = line_stripped.lower()
                    # Skip headers and empty lines
                    if line_stripped and not line_stripped.startswith('#') and len(line_stripped) > 30:
                        # Found a meaningful line
                        project_purpose = line_stripped[:400]  # First meaningful line
                        break
                    
                    # Also check for "About" or "Description" sections
                    if ('about' in line_lower or 'description' in line_lower) and i < 10:
                        # Next non-header line is likely the description
                        for j in range(i+1, min(i+5, len(lines))):
                            next_line = lines[j].strip()
                            if next_line and not next_line.startswith('#') and len(next_line) > 30:
                                project_purpose = next_line[:400]
                                break
                        if project_purpose:
                            break
    
    # 9b. Fallback: Extract use cases and purpose from alternative sources if no README
    if not use_cases or not project_purpose:
        logger.info("No README found or incomplete. Attempting to extract purpose/use cases from alternative sources...")
        
        # Try to extract from package.json
        package_json_files = [f for f in files if f.get('name', '').lower() == 'package.json']
        for pkg_file in package_json_files:
            try:
                if pkg_file.get('has_code') and pkg_file.get('code_snippet'):
                    import json as json_module
                    pkg_data = json_module.loads(pkg_file.get('code_snippet', '{}'))
                    
                    # Extract description
                    if not project_purpose and pkg_data.get('description'):
                        project_purpose = pkg_data.get('description', '')[:400]
                        logger.info("Extracted project purpose from package.json")
                    
                    # Extract scripts as potential use cases
                    if not use_cases and pkg_data.get('scripts'):
                        scripts = pkg_data.get('scripts', {})
                        use_case_text = "Available commands:\n"
                        for script_name, script_cmd in list(scripts.items())[:5]:
                            use_case_text += f"- {script_name}: {script_cmd}\n"
                        use_cases.append(use_case_text)
                        logger.info("Extracted use cases from package.json scripts")
            except Exception as e:
                logger.debug(f"Could not parse package.json: {e}")
        
        # Try to extract from setup.py or pyproject.toml
        setup_files = [f for f in files if f.get('name', '').lower() in ['setup.py', 'pyproject.toml']]
        for setup_file in setup_files:
            try:
                if setup_file.get('has_code') and setup_file.get('code_snippet'):
                    setup_content = setup_file.get('code_snippet', '')
                    
                    # Look for description in setup.py
                    if not project_purpose:
                        import re
                        desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', setup_content, re.IGNORECASE)
                        if desc_match:
                            project_purpose = desc_match.group(1)[:400]
                            logger.info("Extracted project purpose from setup.py")
            except Exception as e:
                logger.debug(f"Could not parse setup file: {e}")
        
        # Try to extract from main entry point files (code comments, function names)
        if not project_purpose or not use_cases:
            main_files_with_code = [
                f for f in code_files
                if f.get('is_entry_point', False)
                or any(name in f.get('name', '').lower() for name in ['app', 'main', 'index'])
            ]
            
            for main_file in main_files_with_code[:3]:  # Check up to 3 main files
                # IMPORTANT: use a local variable name that does NOT shadow the outer code_content dict
                main_code = main_file.get('code_snippet', '')
                if not main_code:
                    continue
                
                # Extract comments that might describe purpose
                if not project_purpose:
                    lines = main_code.split('\n')
                    for line in lines[:50]:  # Check first 50 lines
                        # Look for comment lines that describe the project
                        if ('//' in line or '#' in line or '/*' in line) and len(line.strip()) > 20:
                            comment = line.split('//')[1] if '//' in line else (line.split('#')[1] if '#' in line else line.split('/*')[1] if '/*' in line else '')
                            comment = comment.strip()
                            # Skip very short or common comments
                            if len(comment) > 30 and not any(skip in comment.lower() for skip in ['todo', 'fixme', 'note:', 'copyright']):
                                project_purpose = comment[:400]
                                logger.info(f"Extracted project purpose from comments in {main_file.get('name', '')}")
                                break
                
                # Extract function names as potential use cases
                if not use_cases:
                    # Look for function definitions that suggest use cases
                    import re
                    func_patterns = [
                        r'function\s+(\w+)\s*\(',  # JavaScript
                        r'def\s+(\w+)\s*\(',       # Python
                        r'const\s+(\w+)\s*=\s*\(', # JavaScript arrow
                        r'(\w+)\s*:\s*function',   # JavaScript object method
                    ]
                    
                    found_functions = []
                    for pattern in func_patterns:
                        matches = re.findall(pattern, main_code, re.IGNORECASE)
                        found_functions.extend(matches)
                    
                    # Filter function names that suggest use cases
                    use_case_keywords = ['handle', 'process', 'generate', 'create', 'build', 'render', 'display', 
                                       'calculate', 'compute', 'analyze', 'parse', 'format', 'validate', 'transform']
                    relevant_functions = [f for f in found_functions if any(kw in f.lower() for kw in use_case_keywords)]
                    
                    if relevant_functions:
                        use_case_text = f"Key functions identified in {main_file.get('name', '')}:\n"
                        for func in relevant_functions[:5]:
                            use_case_text += f"- {func}()\n"
                        use_cases.append(use_case_text)
                        logger.info(f"Extracted use cases from function names in {main_file.get('name', '')}")
    
    # 10. Module/Component grouping
    modules = {}
    
    # Group files by directory structure (common module pattern)
    for file_info in code_files:
        file_path = file_info.get('path', '')
        if not file_path:
            continue
        
        path_parts = Path(file_path).parts
        if len(path_parts) > 1:
            # Use parent directory as module name
            module_name = path_parts[0]  # Top-level directory
        else:
            # Root-level file, use extension-based grouping
            ext = file_info.get('extension', '').lower()
            if ext in ['.js', '.jsx', '.ts', '.tsx']:
                module_name = 'javascript_modules'
            elif ext == '.py':
                module_name = 'python_modules'
            elif ext in ['.html', '.css']:
                module_name = 'frontend_files'
            else:
                module_name = 'other_files'
        
        if module_name not in modules:
            modules[module_name] = {
                "name": module_name,
                "files": [],
                "file_count": 0,
                "total_lines": 0,
                "capabilities": []
            }
        
        modules[module_name]["files"].append({
            "path": file_path,
            "name": file_info.get('name', ''),
            "lines": file_info.get('lines', 0),
            "is_entry_point": file_info.get('is_entry_point', False)
        })
        modules[module_name]["file_count"] += 1
        modules[module_name]["total_lines"] += file_info.get('lines', 0)
        
        # Add capabilities detected in this module
        code_snippet = file_info.get('code_snippet', '').lower()
        module_caps = modules[module_name]["capabilities"]
        if 'document.' in code_snippet or 'getelementbyid' in code_snippet:
            if 'DOM manipulation' not in module_caps:
                module_caps.append('DOM manipulation')
        if 'fetch(' in code_snippet or 'axios.' in code_snippet:
            if 'API calls' not in module_caps:
                module_caps.append('API calls')
        if 'class ' in code_snippet or 'function ' in code_snippet:
            if 'Object-oriented' not in module_caps:
                module_caps.append('Object-oriented')
    
    # Convert modules dict to list for JSON serialization
    modules_list = list(modules.values())
    
    # 11. Directory structure summary
    top_level_dirs = [d for d in directory_names if Path(d).parts[0] == Path(d).name]
    directory_structure_summary = {
        "depth": directory_depth,
        "top_level_count": len(top_level_dirs),
        "top_level_dirs": top_level_dirs[:10],  # Limit to 10
        "total_directories": len(directory_names)
    }
    
    report_support = _determine_report_support(
        file_type_counts=file_type_counts,
        frontend_only=frontend_only,
        backend_present=backend_present,
        fullstack=fullstack,
        entry_points=entry_points,
        entry_point_confidence=entry_point_confidence,
        capabilities=capabilities,
        technologies=detected_technologies,
        modules_count=len(modules_list),
        code_files=len(code_files),
        total_files=len(files)
    )

    # Build facts dictionary with enhanced content
    facts = {
        "project_name": project_analysis.get("name", "Unknown"),
        "file_type_counts": file_type_counts,
        "directory_structure": directory_structure_summary,
        "frontend_only": frontend_only,
        "backend_present": backend_present,
        "fullstack": fullstack,
        "entry_points_detected": entry_points,
        "entry_point_confidence": entry_point_confidence,
        "detected_capabilities": capabilities,
        "detected_technologies": detected_technologies,
        "code_statistics": {
            "total_files": len(files),
            "code_files": len(code_files),
            "total_lines": total_code_lines,
            "avg_file_size_bytes": int(avg_file_size)
        },
        # Enhanced: More comprehensive code content (5-10 files)
        "code_content": code_content,
        # New: Module/component analysis
        "modules": modules_list,
        # New: Use cases and project purpose from README
        "use_cases": use_cases,
        "project_purpose": project_purpose,
        "readme_files": list(readme_content.keys()),
        "supported_project_category": report_support["category"],
        "report_support_tier": report_support["tier"],
        "report_support_reasons": report_support["reasons"],
        "reduced_scope_recommended": report_support["reduced_scope_recommended"],
    }
    
    logger.success(f"Built project facts: {len(files)} files, {len(capabilities)} capabilities, {len(modules_list)} modules, {len(code_content)} code files extracted")
    return facts


def _determine_report_support(
    *,
    file_type_counts: Dict[str, int],
    frontend_only: bool,
    backend_present: bool,
    fullstack: bool,
    entry_points: List[str],
    entry_point_confidence: str,
    capabilities: List[str],
    technologies: List[str],
    modules_count: int,
    code_files: int,
    total_files: int,
) -> Dict[str, Any]:
    """Classify report support level and recommend reduced-scope mode when needed."""
    reasons: List[str] = []

    if fullstack:
        category = "Full-Stack Web Application"
    elif frontend_only:
        category = "Frontend Web Application"
    elif backend_present:
        category = "Backend Service"
    elif file_type_counts.get(".ipynb", 0) > 0:
        category = "Data Science Project"
    elif any(path.lower().endswith(("main.py", "__main__.py")) for path in entry_points):
        category = "CLI Tool"
    elif any(ext in file_type_counts for ext in [".py", ".js", ".ts", ".java", ".go", ".rs"]):
        category = "Library/Package"
    else:
        category = "Other"

    if code_files == 0:
        reasons.append("No source code files were detected in the uploaded project.")
        tier = "unsupported"
    else:
        tier = "full"

        if code_files < 3:
            reasons.append("The codebase is very small, so only a reduced-scope report is safe.")
            tier = "reduced"

        if modules_count == 0:
            reasons.append("No stable module structure was detected from the project layout.")
            tier = "reduced"

        if not capabilities:
            reasons.append("Deterministic analysis found limited observable capabilities in the code.")
            tier = "reduced"

        if entry_point_confidence == "low":
            reasons.append("Entry points could not be identified with high confidence.")
            tier = "reduced"

        if total_files > 12000:
            reasons.append("The project is very large, so the report should stay conservative and reduced in scope.")
            tier = "reduced"

    if category == "Other" and tier == "full":
        reasons.append("The project does not match a strong supported category, so reduced-scope reporting is safer.")
        tier = "reduced"

    if not technologies:
        reasons.append("No primary technologies were identified from deterministic analysis.")
        if tier == "full":
            tier = "reduced"

    return {
        "category": category,
        "tier": tier,
        "reasons": reasons,
        "reduced_scope_recommended": tier in {"reduced", "unsupported"},
    }
