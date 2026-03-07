
"""
Code analysis utility for extracting project structure
"""
import ast
import zipfile
from pathlib import Path
from typing import Dict, List, Any
from loguru import logger


class CodeAnalyzer:
    """Analyze project structure and extract metadata"""
    
    def __init__(self, project_path: str, job_id: str = None):
        self.project_path = Path(project_path)
        self.is_zip = self.project_path.suffix == '.zip'
        self.job_id = job_id  # For job-specific extraction directory
        
    def extract_if_zip(self, extract_dir: str) -> Path:
        """Extract ZIP file if needed - uses job-specific directory to prevent conflicts"""
        if self.is_zip:
            # Create job-specific extraction directory to prevent content mixing
            if self.job_id:
                extract_path = Path(extract_dir) / f"job_{self.job_id}"
            else:
                # Fallback: use timestamp-based directory to prevent conflicts
                import time
                extract_path = Path(extract_dir) / f"temp_{int(time.time())}"
            
            # CRITICAL: Clean up any existing extraction for this job to prevent mixing
            if extract_path.exists():
                import shutil
                logger.warning(f"⚠️  Existing extraction directory found: {extract_path}")
                logger.info(f"Cleaning up existing extraction directory to prevent content mixing...")
                
                # Get list of files before cleanup for verification
                existing_files = list(extract_path.rglob("*"))
                logger.info(f"Found {len(existing_files)} existing files/directories to remove")
                
                # Aggressive cleanup - remove everything
                shutil.rmtree(extract_path, ignore_errors=True)
                
                # Wait a moment for filesystem to sync
                import time
                time.sleep(0.5)
                
                # Verify cleanup succeeded
                if extract_path.exists():
                    # Try one more time with force
                    try:
                        import os
                        for root, dirs, files in os.walk(extract_path, topdown=False):
                            for name in files:
                                try:
                                    os.remove(os.path.join(root, name))
                                except:
                                    pass
                            for name in dirs:
                                try:
                                    os.rmdir(os.path.join(root, name))
                                except:
                                    pass
                        extract_path.rmdir()
                    except:
                        pass
                    
                    if extract_path.exists():
                        logger.error(f"❌ Failed to clean up extraction directory: {extract_path}")
                        raise RuntimeError(f"Cannot proceed: extraction directory still exists after cleanup: {extract_path}")
                
                logger.success(f"✅ Successfully cleaned up extraction directory")
            
            extract_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"📦 Extracting project ZIP to job-specific directory: {extract_path}")
            logger.info(f"📄 Source ZIP: {self.project_path}")
            logger.info(f"🆔 Job ID: {self.job_id}")
            
            # Extract ZIP with handling for long paths on Windows
            with zipfile.ZipFile(self.project_path, 'r') as zip_ref:
                # Extract files one by one to handle long paths gracefully
                extracted_count = 0
                skipped_count = 0
                max_path_length = 200  # Conservative limit for Windows (260 - buffer)
                
                for file_info in zip_ref.infolist():
                    # CRITICAL: Skip directory entries in ZIP
                    # ZIP files include directory entries (paths ending with '/')
                    # These must NOT be written as files, or they create zero-byte files
                    # that mask real directories and break filesystem logic
                    if file_info.is_dir():
                        continue
                    
                    try:
                        # Calculate full extraction path
                        full_path = extract_path / file_info.filename
                        path_str = str(full_path)
                        
                        # Check if path is too long for Windows (skip image/media files with long names)
                        if len(path_str) > max_path_length:
                            # Skip files with paths that are too long (usually images or non-code files)
                            # These aren't needed for code analysis anyway
                            logger.debug(f"Skipping file with long path ({len(path_str)} chars): {file_info.filename[:60]}...")
                            skipped_count += 1
                            continue
                        
                        # Create parent directories if needed
                        parent_dir = full_path.parent
                        try:
                            # Check if parent exists and is a directory
                            if parent_dir.exists():
                                if not parent_dir.is_dir():
                                    # Parent exists but is a file - skip this file
                                    logger.warning(f"⚠️  Skipping file: parent path exists as file: {parent_dir}")
                                    skipped_count += 1
                                    continue
                            else:
                                # Create directory if it doesn't exist
                                parent_dir.mkdir(parents=True, exist_ok=True)
                        except OSError as dir_error:
                            # Handle Windows-specific directory creation issues
                            error_msg = str(dir_error)
                            if "Cannot create a file when that file already exists" in error_msg:
                                # Check if it's actually a directory (might be a race condition)
                                if parent_dir.exists() and parent_dir.is_dir():
                                    # It's fine, directory already exists
                                    pass
                                else:
                                    # There's a conflict - skip this file
                                    logger.warning(f"⚠️  Skipping file due to directory conflict: {file_info.filename[:60]}...")
                                    skipped_count += 1
                                    continue
                            else:
                                # Re-raise if it's a different error
                                raise
                        
                        # Skip if target file already exists (avoid overwriting)
                        if full_path.exists() and full_path.is_file():
                            logger.debug(f"File already exists, skipping: {file_info.filename[:60]}...")
                            skipped_count += 1
                            continue
                        
                        # Extract the file
                        try:
                            with zip_ref.open(file_info) as source:
                                with open(full_path, 'wb') as target:
                                    target.write(source.read())
                            extracted_count += 1
                        except (OSError, IOError) as file_error:
                            # Handle file write errors
                            error_msg = str(file_error)
                            if "Cannot create a file when that file already exists" in error_msg:
                                logger.debug(f"File already exists, skipping: {file_info.filename[:60]}...")
                                skipped_count += 1
                                continue
                            raise
                        
                    except (OSError, FileNotFoundError) as e:
                        # Handle Windows path length issues and other extraction errors
                        error_msg = str(e)
                        if "No such file or directory" in error_msg:
                            # This usually means the path is too long or has invalid characters
                            logger.warning(f"⚠️  Skipping file due to path issue: {file_info.filename[:60]}...")
                            skipped_count += 1
                            continue
                        else:
                            # Re-raise if it's a different error
                            logger.error(f"Error extracting {file_info.filename}: {e}")
                            raise
                
                if skipped_count > 0:
                    logger.warning(f"⚠️  Skipped {skipped_count} files due to path length limitations (Windows 260 char limit)")
                    logger.info(f"   (These are usually image/media files and not needed for code analysis)")
                logger.info(f"📦 Extracted {extracted_count} files successfully")
            
            # CRITICAL: Verify extraction succeeded and contains files
            extracted_files = list(extract_path.rglob("*"))
            extracted_dirs = [f for f in extracted_files if f.is_dir()]
            extracted_files_only = [f for f in extracted_files if f.is_file()]
            
            if len(extracted_files_only) == 0:
                logger.error(f"❌ Extraction failed: No files found in {extract_path}")
                raise ValueError(f"ZIP extraction resulted in no files. Check if ZIP is valid.")
            
            # Log sample files for verification
            sample_files = [str(f.relative_to(extract_path)) for f in extracted_files_only[:10]]
            logger.success(f"✅ Extracted {len(extracted_files_only)} files and {len(extracted_dirs)} directories to {extract_path} (job: {self.job_id})")
            logger.info(f"📋 Sample extracted files: {sample_files}")
            
            # CRITICAL: Verify no leftover files from previous projects
            suspicious_patterns = ['mcp_client.py', 'mcp_server.py', 'core/cli.py', 'core/chat.py']
            found_suspicious = [f for f in sample_files if any(pattern in f.lower() for pattern in suspicious_patterns)]
            if found_suspicious and self.job_id:
                logger.warning(f"⚠️  Found files that might be from previous project: {found_suspicious}")
                logger.warning(f"⚠️  This might indicate content mixing. Job ID: {self.job_id}")
            
            return extract_path
        
        logger.info(f"Using project directory directly (not a ZIP): {self.project_path}")
        return self.project_path
    
    def analyze_structure(self) -> Dict[str, Any]:
        """
        Analyze project directory structure
        
        Returns:
            Project metadata including files, technologies, and structure
        """
        project_dir = self.extract_if_zip("temp_extract")
        
        # CRITICAL: Verify extraction directory is correct
        logger.info(f"Analyzing project from directory: {project_dir} (job: {self.job_id})")
        if not project_dir.exists():
            raise ValueError(f"Project directory does not exist: {project_dir}")
        
        # CRITICAL: Detect and handle single top-level directory (GitHub ZIP pattern)
        project_dir = self._detect_actual_project_root(project_dir)
        
        # Try to find the actual project name from the extracted directory structure
        # Look for common project indicators (package.json, setup.py, README, etc.)
        project_name = self._extract_project_name(project_dir)
        
        # If we couldn't find a good name, clean the directory name
        if not project_name or project_name.lower() in ['temp', 'extract', 'project', 'temp_extract', 'temp extract']:
            project_name = self._clean_project_name(project_dir.name, project_dir)
        
        # CRITICAL: Validate project name - reject generic, job/test placeholders, or previous project names
        forbidden_names = ['temp extract', 'temp_extract', 'weekend wizard', 'cli tool', 'mcp protocol', 'temp', 'extract', 'project']
        forbidden_patterns = ['job_', 'test_', 'temp_', 'temp-']
        
        # Check for job/test placeholders
        has_placeholder = any(pattern in project_name.lower() for pattern in forbidden_patterns) if project_name else False
        has_forbidden = any(forbidden in project_name.lower() for forbidden in forbidden_names) if project_name else False
        
        if has_placeholder or has_forbidden:
            logger.warning(f"Project name '{project_name}' appears to be generic, placeholder, or from a previous project!")
            logger.warning(f"Attempting to extract better name from project files...")
            # Try to get a better name from the actual project structure
            project_name = self._extract_better_name_from_files(project_dir, project_name)
            logger.info(f"Updated project name to: {project_name}")
        
        # FINAL VALIDATION: If still invalid, set to "Unknown Project"
        if not project_name or has_placeholder or any(forbidden in project_name.lower() for forbidden in forbidden_names):
            logger.error(f"CRITICAL: Project name '{project_name}' is still invalid after all attempts!")
            logger.error("Setting project name to 'Unknown Project'")
            project_name = "Unknown Project"
        
        logger.info(f"Identified project name: {project_name} (from directory: {project_dir.name}, job: {self.job_id})")
        
        structure = {
            "name": project_name,
            "files": [],
            "directories": [],
            "technologies": [],
            "file_types": {},
            "total_lines": 0,
            "entry_points": []
        }
        
        # Walk through directory using STRICT filesystem checks
        # NEVER infer file vs directory from extension, size, or name
        for item in project_dir.rglob("*"):
            # STRICT: Use is_file() check only - never infer from extension or name
            if item.is_file():
                # Skip hidden files and common excludes
                if item.name.startswith('.') or '__pycache__' in str(item):
                    continue
                
                rel_path = item.relative_to(project_dir)
                file_info = {
                    "path": str(rel_path),
                    "name": item.name,
                    "extension": item.suffix,
                    "size": item.stat().st_size
                }
                
                structure["files"].append(file_info)
                
                # Count file types
                ext = item.suffix
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                # Detect technologies
                self._detect_technology(item, structure)
                
                # Extract README content (even if not a code file)
                if any(name in item.name.lower() for name in ['readme', 'read_me']):
                    try:
                        with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                            readme_content = f.read()
                            file_info["readme_content"] = readme_content
                            file_info["is_readme"] = True
                            lines = len(readme_content.splitlines())
                            file_info["lines"] = lines
                            structure["total_lines"] += lines
                    except Exception as e:
                        logger.warning(f"Failed to read README file {item}: {e}")
                
                # Count lines and extract code content for code files
                if ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.html', '.css']:
                    try:
                        with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = len(content.splitlines())
                            structure["total_lines"] += lines
                            file_info["lines"] = lines
                            
                            # CRITICAL: Extract actual code content for ALL code files
                            # Only extract for project files (not node_modules, etc.)
                            if not any(exclude in str(rel_path) for exclude in ['node_modules', '.git', '__pycache__', 'venv', 'env', 'dist', 'build', '.next', '.nuxt']):
                                # Enhanced: Extract code content from ALL files for comprehensive analysis
                                # Strategy: Extract more from important files, but include ALL files
                                # Main files: 8000 chars, important files: 5000 chars, others: 3000 chars
                                if item.name in ['app.js', 'main.js', 'index.js', 'app.py', 'main.py', 'index.html', 'app.ts', 'main.ts', 'index.ts']:
                                    max_chars = 8000  # Main entry points get extensive context
                                elif any(keyword in item.name.lower() for keyword in ['component', 'module', 'service', 'controller', 'util', 'helper', 'config', 'handler', 'router', 'api']):
                                    max_chars = 5000  # Important modules get substantial context
                                else:
                                    max_chars = 3000  # All other code files get good context
                                
                                if len(content) > max_chars:
                                    # Take first 60% and last 40% to preserve important parts (imports/definitions and main logic)
                                    first_part = int(max_chars * 0.6)
                                    last_part = max_chars - first_part
                                    file_info["code_snippet"] = content[:first_part] + "\n\n... [code truncated] ...\n\n" + content[-last_part:]
                                else:
                                    file_info["code_snippet"] = content  # Full content for smaller files
                                
                                # Mark as having code for later analysis
                                file_info["has_code"] = True
                                
                                # Mark file importance for module grouping
                                if item.name in ['app.js', 'main.js', 'index.js', 'app.py', 'main.py', 'index.html']:
                                    file_info["is_entry_point"] = True
                                elif any(keyword in item.name.lower() for keyword in ['component', 'module', 'service', 'controller', 'handler', 'router']):
                                    file_info["is_module"] = True
                    except Exception as e:
                        logger.warning(f"Failed to read file {item}: {e}")
                        pass
            
            elif item.is_dir() and not item.name.startswith('.'):
                structure["directories"].append(str(item.relative_to(project_dir)))
        
        # Identify entry points
        structure["entry_points"] = self._find_entry_points(project_dir)
        
        # Count code files with extracted content
        code_files_count = len([f for f in structure['files'] if f.get('has_code', False)])
        logger.info(f"Analyzed project: {len(structure['files'])} total files, {code_files_count} code files with content extracted, {structure['total_lines']} total lines")
        
        # RECURSIVE SAFETY FALLBACK: If no code files detected, try descending one level
        code_files = [f for f in structure['files'] if f.get('has_code', False)]
        if len(code_files) == 0:
            # Check if there's exactly one directory that we might have missed
            top_level_dirs = [item for item in project_dir.iterdir() if item.is_dir() and not item.name.startswith('.')]
            
            if len(top_level_dirs) == 1:
                logger.warning("⚠️  No code files detected at current level. Attempting recursive fallback...")
                nested_dir = top_level_dirs[0]
                logger.info(f"   Descending into: {nested_dir.name}")
                
                # Re-run analysis on nested directory (max depth = 1, prevent infinite recursion)
                nested_structure = self._analyze_directory_structure(nested_dir, project_name)
                
                # If nested analysis found code files, use that structure
                nested_code_files = [f for f in nested_structure.get('files', []) if f.get('has_code', False)]
                if len(nested_code_files) > 0:
                    logger.success(f"✅ Found {len(nested_code_files)} code files in nested directory. Using nested structure.")
                    # Update project_dir for entry point detection
                    project_dir = nested_dir
                    structure = nested_structure
                    structure["name"] = project_name  # Preserve project name
                    # Re-detect entry points from correct root
                    structure["entry_points"] = self._find_entry_points(project_dir)
                else:
                    # Still no code files, add warning
                    structure['analysis_warnings'] = [
                        "No source code files detected. The provided ZIP may be incomplete or incorrectly structured."
                    ]
                    logger.warning("⚠️  No source code files detected even after recursive fallback")
            else:
                # No single directory to descend into, add warning
                structure['analysis_warnings'] = [
                    "No source code files detected. The provided ZIP may be incomplete or incorrectly structured."
                ]
                logger.warning("⚠️  No source code files detected in project structure")
        
        return structure
    
    def _analyze_directory_structure(self, project_dir: Path, project_name: str) -> Dict[str, Any]:
        """
        Analyze a specific directory structure (helper for recursive fallback).
        This is a refactored version of the main analysis logic.
        
        Args:
            project_dir: Directory to analyze
            project_name: Project name to use
            
        Returns:
            Project structure dictionary
        """
        structure = {
            "name": project_name,
            "files": [],
            "directories": [],
            "technologies": [],
            "file_types": {},
            "total_lines": 0,
            "entry_points": []
        }
        
        # Walk through directory using STRICT filesystem checks
        for item in project_dir.rglob("*"):
            # STRICT: Use is_file() check only
            if item.is_file():
                # Skip hidden files and common excludes
                if item.name.startswith('.') or '__pycache__' in str(item):
                    continue
                
                rel_path = item.relative_to(project_dir)
                file_info = {
                    "path": str(rel_path),
                    "name": item.name,
                    "extension": item.suffix,
                    "size": item.stat().st_size
                }
                
                structure["files"].append(file_info)
                
                # Count file types
                ext = item.suffix
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                # Detect technologies
                self._detect_technology(item, structure)
                
                # Count lines and extract code content for code files
                if ext in ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.html', '.css']:
                    try:
                        with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = len(content.splitlines())
                            structure["total_lines"] += lines
                            file_info["lines"] = lines
                            
                            # Extract code content
                            if not any(exclude in str(rel_path) for exclude in ['node_modules', '.git', '__pycache__', 'venv', 'env']):
                                max_chars = 2000 if item.name in ['app.js', 'main.js', 'index.js', 'app.py', 'main.py', 'index.html', 'app.ts', 'main.ts'] else 1000
                                if len(content) > max_chars:
                                    file_info["code_snippet"] = content[:max_chars] + "\n\n... [code truncated] ...\n\n" + content[-500:]
                                else:
                                    file_info["code_snippet"] = content
                                
                                file_info["has_code"] = True
                    except Exception as e:
                        logger.warning(f"Failed to read file {item}: {e}")
                        pass
            
            # STRICT: Use is_dir() check only
            elif item.is_dir() and not item.name.startswith('.'):
                structure["directories"].append(str(item.relative_to(project_dir)))
        
        return structure
    
    def _detect_actual_project_root(self, extracted_dir: Path) -> Path:
        """
        Detect if extracted directory contains a single top-level directory.
        If so, treat that directory as the actual project root.
        
        This handles GitHub ZIP pattern: project-name-main/
        
        Uses STRICT filesystem checks: Path.is_dir() and Path.is_file() only.
        
        Args:
            extracted_dir: Directory after ZIP extraction
            
        Returns:
            Actual project root directory
        """
        # CRITICAL: Use STRICT filesystem checks - never infer from extensions or names
        # Get top-level items using ONLY filesystem checks
        top_level_items = []
        try:
            for item in extracted_dir.iterdir():
                # Skip hidden items
                if item.name.startswith('.'):
                    continue
                # STRICT: Use filesystem checks only
                if item.is_dir() or item.is_file():
                    top_level_items.append(item)
        except (OSError, PermissionError) as e:
            logger.warning(f"Error reading directory {extracted_dir}: {e}")
            return extracted_dir
        
        # STRICT: Classify using ONLY filesystem checks
        top_level_dirs = [item for item in top_level_items if item.is_dir()]
        top_level_files = [item for item in top_level_items if item.is_file()]
        
        # Check for CODE files at root level (not all files)
        # Non-code files like README.md, .gitignore should NOT block root switching
        code_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.html', '.css', '.go', '.rs', '.php', '.rb', '.swift', '.kt']
        root_code_files = [
            f for f in top_level_files 
            if f.is_file() and any(f.suffix.lower() == ext for ext in code_extensions)
        ]
        
        # RELAXED Condition: Exactly one top-level directory AND no CODE files at root
        # Non-code files (README, .gitignore, etc.) are ignored
        if len(top_level_dirs) == 1 and len(root_code_files) == 0:
            single_dir = top_level_dirs[0]
            # Verify it's actually a directory (defensive check)
            if not single_dir.is_dir():
                logger.warning(f"Expected directory but got file: {single_dir}")
                return extracted_dir
            
            logger.info(f"📁 Detected single top-level directory '{single_dir.name}/'. Switching project root.")
            logger.info(f"   Original root: {extracted_dir}")
            logger.info(f"   New root: {single_dir}")
            logger.info(f"   Top-level files (non-code): {[f.name for f in top_level_files]}")
            return single_dir
        
        # No adjustment needed
        return extracted_dir
    
    def _detect_technology(self, file_path: Path, structure: Dict):
        """Detect technologies from files"""
        tech_indicators = {
            'package.json': 'Node.js',
            'requirements.txt': 'Python',
            'pom.xml': 'Java/Maven',
            'build.gradle': 'Java/Gradle',
            'Gemfile': 'Ruby',
            'composer.json': 'PHP',
            'go.mod': 'Go',
            'Cargo.toml': 'Rust',
            'next.config.js': 'Next.js',
            'tailwind.config.js': 'Tailwind CSS',
            'tsconfig.json': 'TypeScript'
        }
        
        if file_path.name in tech_indicators:
            tech = tech_indicators[file_path.name]
            if tech not in structure["technologies"]:
                structure["technologies"].append(tech)
    
    def _find_entry_points(self, project_dir: Path) -> List[str]:
        """Find main entry point files"""
        entry_files = [
            'main.py', 'app.py', '__main__.py',
            'index.js', 'index.ts', 'main.js',
            'Main.java', 'index.html'
        ]
        
        found = []
        for entry in entry_files:
            matches = list(project_dir.rglob(entry))
            for match in matches:
                found.append(str(match.relative_to(project_dir)))
        
        return found
    
    def _extract_project_name(self, project_dir: Path) -> str:
        """
        Extract project name from common project files (package.json, setup.py, README, etc.)
        Improved to avoid job/test placeholders.
        """
        # Check for package.json (Node.js/JavaScript projects)
        package_json = project_dir / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'name' in data:
                        # Clean extracted name to remove markdown/extra characters
                        name = self._clean_project_name(data['name'])
                        # Reject job/test placeholders
                        if not any(placeholder in name.lower() for placeholder in ['job_', 'test_', 'temp_', 'temp-']):
                            return name
            except:
                pass
        
        # Check for setup.py (Python projects)
        setup_py = project_dir / "setup.py"
        if setup_py.exists():
            try:
                with open(setup_py, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for name= in setup.py
                    import re
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        # Clean extracted name to remove markdown/extra characters
                        name = self._clean_project_name(match.group(1))
                        # Reject job/test placeholders
                        if not any(placeholder in name.lower() for placeholder in ['job_', 'test_', 'temp_', 'temp-']):
                            return name
            except:
                pass
        
        # Check for pyproject.toml
        pyproject = project_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, 'r', encoding='utf-8') as f:
                    content = f.read()
                    import re
                    match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                    if match:
                        # Clean extracted name to remove markdown/extra characters
                        name = self._clean_project_name(match.group(1))
                        # Reject job/test placeholders
                        if not any(placeholder in name.lower() for placeholder in ['job_', 'test_', 'temp_', 'temp-']):
                            return name
            except:
                pass
        
        # Check for README files - extract name from first line
        for readme_file in ['README.md', 'README.txt', 'README', 'readme.md']:
            readme_path = project_dir / readme_file
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        first_line = f.readline().strip()
                        # Remove markdown headers
                        first_line = first_line.lstrip('#').strip()
                        if first_line and len(first_line) > 3:
                            # Clean first line to remove markdown/extra characters
                            name = self._clean_project_name(first_line[:50])  # Limit length
                            # Reject job/test placeholders
                            if not any(placeholder in name.lower() for placeholder in ['job_', 'test_', 'temp_', 'temp-']):
                                return name
                except:
                    pass
        
        # Use directory name as fallback, but clean it first
        dir_name = self._clean_project_name(project_dir.name)
        # Reject job/test placeholders
        if dir_name and not any(placeholder in dir_name.lower() for placeholder in ['job_', 'test_', 'temp_', 'temp-']):
            return dir_name
        
        return None
    
    def _extract_better_name_from_files(self, project_dir: Path, fallback_name: str) -> str:
        """
        Extract a better project name by analyzing actual project files
        """
        # Look for the root directory name (first non-hidden, non-temp directory)
        for item in project_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['temp', 'tmp', 'extract', '__pycache__', 'node_modules', '.git', 'venv', 'env']:
                # Check if this directory has project files
                has_project_files = any(
                    (item / f).exists() 
                    for f in ['package.json', 'setup.py', 'pyproject.toml', 'README.md', 'main.py', 'app.py', 'index.js']
                )
                if has_project_files:
                    clean_name = self._clean_project_name(item.name)
                    if clean_name and clean_name.lower() not in ['temp', 'extract', 'project']:
                        logger.info(f"Found better project name from directory: {clean_name}")
                        return clean_name
        
        # If still no good name, use a descriptive name based on file types
        python_files = list(project_dir.rglob("*.py"))
        js_files = list(project_dir.rglob("*.js"))
        if python_files:
            # Look for main.py or app.py to get a hint
            for f in python_files:
                if f.name in ['main.py', 'app.py']:
                    # Try to extract name from the file's directory
                    parent_name = self._clean_project_name(f.parent.name)
                    if parent_name and parent_name.lower() not in ['temp', 'extract', 'project', 'src', 'lib']:
                        return parent_name
            return "Python Project"
        elif js_files:
            return "JavaScript Project"
        
        # Last resort: use a sanitized version of the directory name
        clean_name = self._clean_project_name(project_dir.name, project_dir)
        if clean_name and clean_name.lower() not in ['temp', 'extract', 'project']:
            return clean_name
        
        # If still no good name, generate file-based unique identifier
        return self._generate_file_based_name(project_dir)
    
    def _clean_project_name(self, name: str, project_dir: Path = None) -> str:
        """
        Clean project name by removing UUIDs, job IDs, and sanitizing
        
        Examples:
            "3DF91233-C234-4DFA-A900-04FC7D0A1A06_project" -> "Project"
            "abc123_project" -> "Project"
            "my-project" -> "My Project"
        """
        import re
        
        # Remove UUID patterns (e.g., "3DF91233-C234-4DFA-A900-04FC7D0A1A06")
        uuid_pattern = r'[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}'
        name = re.sub(uuid_pattern, '', name, flags=re.IGNORECASE)
        
        # Remove job ID patterns (e.g., "abc123def456")
        job_id_pattern = r'[a-f0-9]{8,}'
        name = re.sub(job_id_pattern, '', name, flags=re.IGNORECASE)
        
        # Remove common prefixes/suffixes
        name = re.sub(r'^[a-f0-9]+[-_]?', '', name, flags=re.IGNORECASE)  # Remove hex prefixes
        name = re.sub(r'[-_][a-f0-9]+$', '', name, flags=re.IGNORECASE)  # Remove hex suffixes
        
        # Remove simple markdown/emphasis characters (e.g., **Name**, `Name`)
        name = name.replace('*', ' ')
        name = name.replace('`', ' ')
        
        # Remove underscores and hyphens, replace with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Clean up multiple spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        # If name is empty or too short after cleaning, try to find a better name from project files
        if (not name or len(name) < 2) and project_dir:
            try:
                # Look for package.json, setup.py, or similar
                for config_file in ['package.json', 'setup.py', 'pyproject.toml', 'README.md']:
                    config_path = project_dir / config_file
                    if config_path.exists():
                        if config_file == 'package.json':
                            import json
                            with open(config_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                extracted_name = data.get('name', '')
                                if extracted_name and len(extracted_name) > 2:
                                    name = extracted_name
                                    break
                        elif config_file == 'setup.py':
                            # Try to extract name from setup.py (basic parsing)
                            with open(config_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                                if match:
                                    extracted_name = match.group(1)
                                    if extracted_name and len(extracted_name) > 2:
                                        name = extracted_name
                                        break
                        elif config_file == 'pyproject.toml':
                            with open(config_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
                                if match:
                                    extracted_name = match.group(1)
                                    if extracted_name and len(extracted_name) > 2:
                                        name = extracted_name
                                        break
            except Exception as e:
                logger.debug(f"Failed to extract name from config files: {e}")
            
            # Final fallback
            if not name or len(name) < 2:
                name = None  # Return None to trigger file-based name generation
        
        # Capitalize properly if we have a name
        if name and len(name) >= 2:
            name = name.title()
        
        return name
    
    def analyze_python_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Analyze Python file using AST
        
        Returns:
            Functions, classes, imports, and docstrings
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            analysis = {
                "imports": [],
                "functions": [],
                "classes": [],
                "docstring": ast.get_docstring(tree)
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        analysis["imports"].append(f"{module}.{alias.name}")
                
                elif isinstance(node, ast.FunctionDef):
                    analysis["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node)
                    })
                
                elif isinstance(node, ast.ClassDef):
                    analysis["classes"].append({
                        "name": node.name,
                        "docstring": ast.get_docstring(node),
                        "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    })
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")
            return {}
    
    def _generate_file_based_name(self, project_dir: Path) -> str:
        """
        Generate a unique project name based on file structure hash.
        This ensures each project gets a unique identifier even if name extraction fails.
        """
        import hashlib
        
        # Get first 10 non-hidden files and create a hash
        files = []
        for item in project_dir.rglob("*"):
            if item.is_file() and not item.name.startswith('.'):
                files.append(str(item.relative_to(project_dir)))
                if len(files) >= 10:
                    break
        
        # Create hash from file paths
        file_string = "|".join(sorted(files))
        file_hash = hashlib.md5(file_string.encode()).hexdigest()[:8]
        
        # Try to get a descriptive prefix from file types
        python_files = list(project_dir.rglob("*.py"))
        js_files = list(project_dir.rglob("*.js"))
        html_files = list(project_dir.rglob("*.html"))
        
        if python_files:
            prefix = "Python"
        elif js_files:
            prefix = "JavaScript"
        elif html_files:
            prefix = "Web"
        else:
            prefix = "Project"
        
        project_name = f"{prefix} Project {file_hash}"
        logger.info(f"Generated file-based project name: {project_name}")
        return project_name


def analyze_project(project_path: str, job_id: str = None) -> Dict[str, Any]:
    """
    Convenience function to analyze project
    
    Args:
        project_path: Path to project ZIP or directory
        job_id: Optional job ID for isolated extraction directory
    
    Returns:
        Complete project structure and metadata
    """
    analyzer = CodeAnalyzer(project_path, job_id=job_id)
    return analyzer.analyze_structure()