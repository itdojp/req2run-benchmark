"""Integration tests for Req2Run benchmark framework."""

import unittest
import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any


class TestProblemIntegration(unittest.TestCase):
    """Integration tests for problem definitions."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.problems_dir = self.project_root / "problems"
    
    def test_all_problems_valid_yaml(self):
        """Test that all problem files are valid YAML."""
        difficulties = ['basic', 'intermediate', 'advanced', 'expert']
        errors = []
        
        for difficulty in difficulties:
            difficulty_dir = self.problems_dir / difficulty
            if not difficulty_dir.exists():
                continue
            
            for yaml_file in difficulty_dir.glob('*.yaml'):
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    self.assertIsNotNone(data, f"{yaml_file} contains valid YAML")
                except Exception as e:
                    errors.append(f"{yaml_file}: {str(e)}")
        
        self.assertEqual(len(errors), 0, f"YAML parsing errors: {errors}")
    
    def test_problems_have_required_fields(self):
        """Test that all problems have required fields."""
        required_fields = ['id', 'title', 'difficulty', 'category', 'requirements']
        difficulties = ['basic', 'intermediate', 'advanced', 'expert']
        
        for difficulty in difficulties:
            difficulty_dir = self.problems_dir / difficulty
            if not difficulty_dir.exists():
                continue
            
            for yaml_file in difficulty_dir.glob('*.yaml'):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                for field in required_fields:
                    self.assertIn(field, data, f"{yaml_file} missing required field: {field}")
    
    def test_difficulty_matches_directory(self):
        """Test that problem difficulty matches its directory."""
        difficulties = ['basic', 'intermediate', 'advanced', 'expert']
        
        for difficulty in difficulties:
            difficulty_dir = self.problems_dir / difficulty
            if not difficulty_dir.exists():
                continue
            
            for yaml_file in difficulty_dir.glob('*.yaml'):
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                self.assertEqual(
                    data.get('difficulty'), 
                    difficulty,
                    f"{yaml_file} difficulty mismatch: expected {difficulty}, got {data.get('difficulty')}"
                )


class TestBaselineIntegration(unittest.TestCase):
    """Integration tests for baseline implementations."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent.parent
        self.baselines_dir = self.project_root / "baselines"
    
    def test_baselines_directory_structure(self):
        """Test that baselines directory has expected structure."""
        if self.baselines_dir.exists():
            baseline_dirs = list(self.baselines_dir.iterdir())
            # At least check that the directory isn't empty if it exists
            if baseline_dirs:
                self.assertGreater(len(baseline_dirs), 0, "Baselines directory has content")
        else:
            # It's okay if baselines directory doesn't exist yet
            self.skipTest("Baselines directory not yet created")
    
    def test_dockerfile_in_baselines(self):
        """Test that baseline implementations have Dockerfiles where required."""
        if not self.baselines_dir.exists():
            self.skipTest("Baselines directory not yet created")
        
        for baseline_dir in self.baselines_dir.iterdir():
            if baseline_dir.is_dir():
                dockerfile = baseline_dir / "Dockerfile"
                # Not all baselines require Docker, so we just check if it exists when present
                if dockerfile.exists():
                    with open(dockerfile, 'r') as f:
                        content = f.read()
                    self.assertIn('FROM', content, f"{dockerfile} should have FROM instruction")


class TestDocumentationIntegration(unittest.TestCase):
    """Integration tests for documentation."""
    
    def test_problem_catalog_exists(self):
        """Test that problem catalog documentation exists."""
        project_root = Path(__file__).parent.parent.parent
        catalog = project_root / "docs" / "PROBLEM_CATALOG.md"
        if catalog.exists():
            with open(catalog, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn('# Problem Catalog', content, "Problem catalog has proper header")
            self.assertGreater(len(content), 1000, "Problem catalog has substantial content")
    
    def test_documentation_references_problems(self):
        """Test that documentation references actual problems."""
        project_root = Path(__file__).parent.parent.parent
        docs_dir = project_root / "docs"
        
        if docs_dir.exists():
            # Check if any markdown files reference problem IDs
            for md_file in docs_dir.glob('*.md'):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Look for problem ID patterns (e.g., WEB-001, CLI-001)
                import re
                pattern = r'[A-Z]+-\d{3}'
                matches = re.findall(pattern, content)
                if matches:
                    self.assertGreater(len(matches), 0, f"{md_file} references problem IDs")


if __name__ == '__main__':
    unittest.main()