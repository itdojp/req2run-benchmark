"""
Req2Run API Module
Provides programmatic access to benchmark problems and validation.
"""

import os
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union


class Req2RunAPI:
    """Main API class for interacting with Req2Run Benchmark"""
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        Initialize the API.
        
        Args:
            repo_path: Path to req2run-benchmark repository.
                      If None, uses REQ2RUN_BENCHMARK_REPO environment variable.
        """
        if repo_path:
            self.repo_path = Path(repo_path)
        else:
            env_path = os.getenv("REQ2RUN_BENCHMARK_REPO")
            if not env_path:
                # Try to find repository in common locations
                possible_paths = [
                    Path.cwd(),
                    Path.cwd().parent,
                    Path.home() / "req2run-benchmark",
                    Path("/opt/req2run-benchmark"),
                ]
                
                for path in possible_paths:
                    if (path / "problems").exists():
                        self.repo_path = path
                        break
                else:
                    raise ValueError(
                        "Repository not found. Please set REQ2RUN_BENCHMARK_REPO "
                        "environment variable or provide repo_path parameter."
                    )
            else:
                self.repo_path = Path(env_path)
        
        # Validate repository structure
        self.problems_dir = self.repo_path / "problems"
        if not self.problems_dir.exists():
            raise ValueError(f"Problems directory not found at {self.problems_dir}")
        
        self.schema_path = self.problems_dir / "schema" / "problem-schema.yaml"
        self._schema = None
        self._cache = {}
    
    def list_problems(
        self,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        format: str = 'dict'
    ) -> Union[List[Dict], str]:
        """
        List available problems with optional filtering.
        
        Args:
            difficulty: Filter by difficulty level ('basic', 'intermediate', 'advanced', 'expert')
            category: Filter by category ('cli_tool', 'web_api', etc.)
            format: Output format ('dict', 'json', 'yaml')
        
        Returns:
            List of problem dictionaries or formatted string
        """
        cache_key = f"list_{difficulty}_{category}"
        if cache_key in self._cache:
            problems = self._cache[cache_key]
        else:
            problems = []
            
            # Determine which difficulties to search
            if difficulty:
                if difficulty not in ['basic', 'intermediate', 'advanced', 'expert']:
                    raise ValueError(f"Invalid difficulty: {difficulty}")
                search_dirs = [self.problems_dir / difficulty]
            else:
                search_dirs = [
                    self.problems_dir / d
                    for d in ['basic', 'intermediate', 'advanced', 'expert']
                    if (self.problems_dir / d).exists()
                ]
            
            # Search and filter
            for diff_dir in search_dirs:
                if not diff_dir.exists():
                    continue
                    
                for problem_file in diff_dir.glob("*.yaml"):
                    try:
                        with open(problem_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            
                            # Apply category filter if specified
                            if category and data.get('category') != category:
                                continue
                            
                            problems.append({
                                'id': data.get('id'),
                                'title': data.get('title'),
                                'difficulty': data.get('difficulty'),
                                'category': data.get('category'),
                                'path': str(problem_file)
                            })
                    except Exception as e:
                        print(f"Warning: Failed to load {problem_file}: {e}")
            
            self._cache[cache_key] = problems
        
        # Format output
        if format == 'json':
            return json.dumps(problems, indent=2, ensure_ascii=False)
        elif format == 'yaml':
            return yaml.dump(problems, allow_unicode=True)
        else:
            return problems
    
    def get_problem(self, problem_id: str) -> Optional[Dict]:
        """
        Retrieve a specific problem by ID.
        
        Args:
            problem_id: Problem identifier (e.g., 'CLI-001')
        
        Returns:
            Problem dictionary or None if not found
        """
        # Check cache
        if problem_id in self._cache:
            return self._cache[problem_id]
        
        # Search for problem
        for difficulty in ['basic', 'intermediate', 'advanced', 'expert']:
            problem_file = self.problems_dir / difficulty / f"{problem_id}.yaml"
            if problem_file.exists():
                try:
                    with open(problem_file, 'r', encoding='utf-8') as f:
                        problem = yaml.safe_load(f)
                        self._cache[problem_id] = problem
                        return problem
                except Exception as e:
                    print(f"Error loading problem {problem_id}: {e}")
                    return None
        
        return None
    
    def validate_problem(self, problem_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a problem file against the schema.
        
        Args:
            problem_path: Path to problem YAML file
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        try:
            # Load problem file
            with open(problem_path, 'r', encoding='utf-8') as f:
                problem = yaml.safe_load(f)
            
            # Check required fields
            required_fields = ['id', 'title', 'difficulty', 'category', 'requirements']
            for field in required_fields:
                if field not in problem:
                    errors.append(f"Missing required field: {field}")
            
            # Validate difficulty
            if 'difficulty' in problem:
                valid_difficulties = ['basic', 'intermediate', 'advanced', 'expert']
                if problem['difficulty'] not in valid_difficulties:
                    errors.append(f"Invalid difficulty: {problem['difficulty']}")
            
            # Validate requirements structure
            if 'requirements' in problem:
                if not isinstance(problem['requirements'], dict):
                    errors.append("Requirements must be a dictionary")
                elif 'functional' not in problem['requirements']:
                    errors.append("Requirements must include 'functional' section")
            
            # Validate ID format
            if 'id' in problem:
                import re
                if not re.match(r'^[A-Z]+-\d{3}$', problem['id']):
                    errors.append(f"Invalid ID format: {problem['id']} (expected: XXX-###)")
            
        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {e}")
        except FileNotFoundError:
            errors.append(f"File not found: {problem_path}")
        except Exception as e:
            errors.append(f"Unexpected error: {e}")
        
        return len(errors) == 0, errors
    
    def get_schema(self) -> Optional[Dict]:
        """
        Get the problem schema definition.
        
        Returns:
            Schema dictionary or None if not found
        """
        if self._schema:
            return self._schema
        
        if self.schema_path.exists():
            try:
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    self._schema = yaml.safe_load(f)
                    return self._schema
            except Exception as e:
                print(f"Error loading schema: {e}")
        
        return None
    
    def get_categories(self) -> List[str]:
        """
        Get list of all available problem categories.
        
        Returns:
            List of category strings
        """
        categories = set()
        
        for problem in self.list_problems():
            if problem.get('category'):
                categories.add(problem['category'])
        
        return sorted(list(categories))
    
    def get_difficulties(self) -> List[str]:
        """
        Get list of available difficulty levels.
        
        Returns:
            List of difficulty strings
        """
        difficulties = []
        
        for diff in ['basic', 'intermediate', 'advanced', 'expert']:
            if (self.problems_dir / diff).exists():
                difficulties.append(diff)
        
        return difficulties
    
    def export_problems(self, output_file: str, format: str = 'json') -> str:
        """
        Export all problems to a file.
        
        Args:
            output_file: Output file path
            format: Export format ('json', 'yaml', 'csv')
        
        Returns:
            Path to exported file
        """
        problems = self.list_problems()
        
        if format == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(problems, f, indent=2, ensure_ascii=False)
        elif format == 'yaml':
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(problems, f, allow_unicode=True)
        elif format == 'csv':
            import csv
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if problems:
                    writer = csv.DictWriter(f, fieldnames=problems[0].keys())
                    writer.writeheader()
                    writer.writerows(problems)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return output_file
    
    def search_problems(self, query: str) -> List[Dict]:
        """
        Search problems by title or description.
        
        Args:
            query: Search query string
        
        Returns:
            List of matching problems
        """
        query_lower = query.lower()
        matching = []
        
        for problem_summary in self.list_problems():
            problem = self.get_problem(problem_summary['id'])
            if problem:
                # Search in title
                if query_lower in problem.get('title', '').lower():
                    matching.append(problem_summary)
                    continue
                
                # Search in description if available
                if 'description' in problem:
                    if query_lower in problem['description'].lower():
                        matching.append(problem_summary)
        
        return matching


# Convenience functions for direct usage
def list_problems(difficulty=None, category=None):
    """Convenience function to list problems"""
    api = Req2RunAPI()
    return api.list_problems(difficulty=difficulty, category=category)


def get_problem(problem_id):
    """Convenience function to get a specific problem"""
    api = Req2RunAPI()
    return api.get_problem(problem_id)


def validate_problem(problem_path):
    """Convenience function to validate a problem"""
    api = Req2RunAPI()
    return api.validate_problem(problem_path)


if __name__ == "__main__":
    # Example usage
    try:
        api = Req2RunAPI()
        
        # List all problems
        problems = api.list_problems()
        print(f"Total problems: {len(problems)}")
        
        # List basic problems
        basic = api.list_problems(difficulty='basic')
        print(f"Basic problems: {len(basic)}")
        
        # Get specific problem
        problem = api.get_problem('CLI-001')
        if problem:
            print(f"Found: {problem['title']}")
        
        # Get categories
        categories = api.get_categories()
        print(f"Categories: {categories}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Please set REQ2RUN_BENCHMARK_REPO environment variable")