"""Basic unit tests for CI/CD pipeline validation."""

import unittest
import os
import yaml
from pathlib import Path


class TestBasicFunctionality(unittest.TestCase):
    """Basic tests to ensure CI/CD pipeline works."""
    
    def test_import_basic_modules(self):
        """Test that basic Python modules can be imported."""
        import sys
        import json
        import datetime
        self.assertTrue(True, "Basic imports successful")
    
    def test_project_structure_exists(self):
        """Test that essential project directories exist."""
        project_root = Path(__file__).parent.parent.parent
        self.assertTrue(project_root.exists(), "Project root exists")
        self.assertTrue((project_root / "problems").exists(), "Problems directory exists")
        self.assertTrue((project_root / "docs").exists(), "Docs directory exists")
    
    def test_yaml_parsing(self):
        """Test that YAML parsing works correctly."""
        test_yaml = """
        test:
          key: value
          number: 123
        """
        data = yaml.safe_load(test_yaml)
        self.assertEqual(data['test']['key'], 'value')
        self.assertEqual(data['test']['number'], 123)


class TestProblemSchemaValidation(unittest.TestCase):
    """Tests for problem schema validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.problems_dir = self.project_root / "problems"
        self.schema_file = self.problems_dir / "schema" / "problem-schema.yaml"
    
    def test_schema_file_exists(self):
        """Test that the problem schema file exists."""
        self.assertTrue(self.schema_file.exists(), f"Schema file exists at {self.schema_file}")
    
    def test_schema_is_valid_yaml(self):
        """Test that the schema file is valid YAML."""
        if self.schema_file.exists():
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)
            self.assertIsNotNone(schema, "Schema loaded successfully")
            self.assertIn('type', schema, "Schema has type field")
    
    def test_problem_files_exist(self):
        """Test that problem files exist in expected directories."""
        difficulties = ['basic', 'intermediate', 'advanced', 'expert']
        problem_count = 0
        
        for difficulty in difficulties:
            difficulty_dir = self.problems_dir / difficulty
            if difficulty_dir.exists():
                yaml_files = list(difficulty_dir.glob('*.yaml'))
                problem_count += len(yaml_files)
        
        self.assertGreater(problem_count, 0, "At least one problem file exists")


class TestDocumentation(unittest.TestCase):
    """Tests for documentation structure."""
    
    def test_docs_directory_exists(self):
        """Test that documentation directory exists."""
        project_root = Path(__file__).parent.parent.parent
        docs_dir = project_root / "docs"
        self.assertTrue(docs_dir.exists(), "Documentation directory exists")
    
    def test_readme_exists(self):
        """Test that README.md exists in project root."""
        project_root = Path(__file__).parent.parent.parent
        readme = project_root / "README.md"
        self.assertTrue(readme.exists(), "README.md exists in project root")


if __name__ == '__main__':
    unittest.main()