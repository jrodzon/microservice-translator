"""
Project analysis tool for translation.

This module provides tools for analyzing project structure and
identifying key components for translation.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

from project_translator.utils import get_logger

console = Console()
logger = get_logger("project_analysis")


class ProjectAnalysisTool:
    """Tool for analyzing project structure and components."""
    
    def __init__(self, source_path: str):
        """
        Initialize project analysis tool.
        
        Args:
            source_path: Path to the source project directory
        """
        self.source_path = Path(source_path).resolve()
        logger.info(f"ProjectAnalysisTool initialized - Source: {self.source_path}")
    
    def analyze_project(self) -> Dict[str, Any]:
        """
        Perform comprehensive project analysis.
        
        Returns:
            Dictionary with project analysis results
        """
        try:
            analysis = {
                "project_type": self._detect_project_type(),
                "main_files": self._find_main_files(),
                "dependencies": self._find_dependencies(),
                "configuration_files": self._find_config_files(),
                "api_endpoints": self._find_api_endpoints(),
                "docker_config": self._analyze_docker_config(),
                "test_files": self._find_test_files(),
                "documentation": self._find_documentation()
            }
            
            logger.info("Project analysis completed successfully")
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            error_msg = f"Error analyzing project: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _detect_project_type(self) -> str:
        """Detect the type of project based on files present."""
        if (self.source_path / "package.json").exists():
            return "Node.js"
        elif (self.source_path / "requirements.txt").exists():
            return "Python"
        elif (self.source_path / "pom.xml").exists():
            return "Java Maven"
        elif (self.source_path / "build.gradle").exists():
            return "Java Gradle"
        elif (self.source_path / "Cargo.toml").exists():
            return "Rust"
        elif (self.source_path / "go.mod").exists():
            return "Go"
        elif (self.source_path / "composer.json").exists():
            return "PHP"
        else:
            return "Unknown"
    
    def _find_main_files(self) -> List[Dict[str, Any]]:
        """Find main application files."""
        main_files = []
        
        # Common main file patterns
        patterns = [
            "main.py", "app.py", "server.py", "index.py",
            "main.js", "app.js", "server.js", "index.js",
            "main.go", "main.rs", "main.java",
            "index.php", "app.php"
        ]
        
        for pattern in patterns:
            file_path = self.source_path / pattern
            if file_path.exists():
                main_files.append({
                    "name": pattern,
                    "path": str(file_path.relative_to(self.source_path)),
                    "type": "main_file"
                })
        
        return main_files
    
    def _find_dependencies(self) -> Dict[str, List[str]]:
        """Find dependency files and parse them."""
        dependencies = {}
        
        # Python
        req_file = self.source_path / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                dependencies["python"] = deps
            except Exception as e:
                logger.warning(f"Error reading requirements.txt: {e}")
        
        # Node.js
        package_file = self.source_path / "package.json"
        if package_file.exists():
            try:
                with open(package_file, 'r') as f:
                    package_data = json.load(f)
                deps = list(package_data.get("dependencies", {}).keys())
                dependencies["nodejs"] = deps
            except Exception as e:
                logger.warning(f"Error reading package.json: {e}")
        
        return dependencies
    
    def _find_config_files(self) -> List[Dict[str, Any]]:
        """Find configuration files."""
        config_files = []
        
        # Common config file patterns
        patterns = [
            "config.json", "config.yaml", "config.yml",
            "settings.json", "settings.yaml", "settings.yml",
            ".env", "environment.json",
            "docker-compose.yml", "docker-compose.yaml"
        ]
        
        for pattern in patterns:
            file_path = self.source_path / pattern
            if file_path.exists():
                config_files.append({
                    "name": pattern,
                    "path": str(file_path.relative_to(self.source_path)),
                    "type": "config_file"
                })
        
        return config_files
    
    def _find_api_endpoints(self) -> List[Dict[str, Any]]:
        """Find API endpoint definitions."""
        endpoints = []
        
        # Look for common API files
        api_files = [
            "app.py", "main.py", "server.py", "routes.py",
            "app.js", "server.js", "routes.js", "index.js"
        ]
        
        for api_file in api_files:
            file_path = self.source_path / api_file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Simple endpoint detection (can be enhanced)
                    if "@app.route" in content or "app.get" in content or "app.post" in content:
                        endpoints.append({
                            "file": api_file,
                            "type": "api_file",
                            "framework": self._detect_framework(content)
                        })
                except Exception as e:
                    logger.warning(f"Error analyzing {api_file}: {e}")
        
        return endpoints
    
    def _detect_framework(self, content: str) -> str:
        """Detect the web framework used."""
        if "from flask import" in content or "Flask(" in content:
            return "Flask"
        elif "from fastapi import" in content or "FastAPI(" in content:
            return "FastAPI"
        elif "from django" in content:
            return "Django"
        elif "express" in content.lower():
            return "Express.js"
        elif "koa" in content.lower():
            return "Koa.js"
        else:
            return "Unknown"
    
    def _analyze_docker_config(self) -> Dict[str, Any]:
        """Analyze Docker configuration."""
        docker_config = {
            "has_dockerfile": False,
            "has_docker_compose": False,
            "port": None,
            "base_image": None
        }
        
        # Check for Dockerfile
        dockerfile = self.source_path / "Dockerfile"
        if dockerfile.exists():
            docker_config["has_dockerfile"] = True
            try:
                with open(dockerfile, 'r') as f:
                    content = f.read()
                
                # Extract port information
                if "EXPOSE" in content:
                    for line in content.split('\n'):
                        if line.strip().startswith('EXPOSE'):
                            port = line.strip().split()[1]
                            docker_config["port"] = port
                            break
                
                # Extract base image
                for line in content.split('\n'):
                    if line.strip().startswith('FROM'):
                        base_image = line.strip().split()[1]
                        docker_config["base_image"] = base_image
                        break
                        
            except Exception as e:
                logger.warning(f"Error analyzing Dockerfile: {e}")
        
        # Check for docker-compose
        compose_files = ["docker-compose.yml", "docker-compose.yaml"]
        for compose_file in compose_files:
            file_path = self.source_path / compose_file
            if file_path.exists():
                docker_config["has_docker_compose"] = True
                break
        
        return docker_config
    
    def _find_test_files(self) -> List[Dict[str, Any]]:
        """Find test files."""
        test_files = []
        
        # Common test file patterns
        patterns = [
            "test_*.py", "*_test.py", "tests.py",
            "test_*.js", "*_test.js", "tests.js",
            "*.test.js", "*.spec.js"
        ]
        
        for pattern in patterns:
            for file_path in self.source_path.rglob(pattern):
                if file_path.is_file():
                    test_files.append({
                        "name": file_path.name,
                        "path": str(file_path.relative_to(self.source_path)),
                        "type": "test_file"
                    })
        
        return test_files
    
    def _find_documentation(self) -> List[Dict[str, Any]]:
        """Find documentation files."""
        doc_files = []
        
        # Common documentation patterns
        patterns = [
            "README.md", "README.rst", "README.txt",
            "CHANGELOG.md", "CHANGELOG.rst",
            "LICENSE", "LICENSE.txt", "LICENSE.md",
            "docs/", "documentation/"
        ]
        
        for pattern in patterns:
            file_path = self.source_path / pattern
            if file_path.exists():
                doc_files.append({
                    "name": pattern,
                    "path": str(file_path.relative_to(self.source_path)),
                    "type": "documentation"
                })
        
        return doc_files
    
    def get_translation_plan(self, target_language: str) -> Dict[str, Any]:
        """
        Generate a translation plan for the target language.
        
        Args:
            target_language: Target programming language
            
        Returns:
            Dictionary with translation plan
        """
        try:
            analysis = self.analyze_project()
            if not analysis["success"]:
                return analysis
            
            project_info = analysis["analysis"]
            
            # Generate translation plan based on project type and target language
            plan = {
                "source_language": project_info["project_type"],
                "target_language": target_language,
                "translation_steps": self._generate_translation_steps(project_info, target_language),
                "key_files": self._identify_key_files(project_info),
                "dependencies_mapping": self._map_dependencies(project_info, target_language),
                "configuration_changes": self._plan_config_changes(project_info, target_language)
            }
            
            logger.info(f"Translation plan generated for {project_info['project_type']} -> {target_language}")
            return {
                "success": True,
                "plan": plan
            }
            
        except Exception as e:
            error_msg = f"Error generating translation plan: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _generate_translation_steps(self, project_info: Dict[str, Any], target_language: str) -> List[str]:
        """Generate translation steps based on project analysis."""
        steps = [
            "1. Analyze source project structure and dependencies",
            "2. Set up target language project structure",
            "3. Translate main application files",
            "4. Translate configuration files",
            "5. Update Docker configuration for target language",
            "6. Translate test files",
            "7. Update documentation",
            "8. Verify API compatibility"
        ]
        
        return steps
    
    def _identify_key_files(self, project_info: Dict[str, Any]) -> List[str]:
        """Identify key files that need translation."""
        key_files = []
        
        # Add main files
        for main_file in project_info["main_files"]:
            key_files.append(main_file["path"])
        
        # Add config files
        for config_file in project_info["configuration_files"]:
            key_files.append(config_file["path"])
        
        # Add API files
        for api_file in project_info["api_endpoints"]:
            key_files.append(api_file["file"])
        
        return key_files
    
    def _map_dependencies(self, project_info: Dict[str, Any], target_language: str) -> Dict[str, List[str]]:
        """Map dependencies from source to target language."""
        # This would contain mapping logic for different language pairs
        # For now, return a placeholder
        return {
            "source_dependencies": list(project_info["dependencies"].keys()),
            "target_dependencies": f"Equivalent {target_language} dependencies to be determined"
        }
    
    def _plan_config_changes(self, project_info: Dict[str, Any], target_language: str) -> List[str]:
        """Plan configuration changes needed for target language."""
        changes = [
            f"Update Dockerfile to use {target_language} base image",
            f"Update dependency management for {target_language}",
            "Update port configuration if needed",
            "Update build and run commands"
        ]
        
        return changes
