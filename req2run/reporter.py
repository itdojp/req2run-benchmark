"""
Report generation for Req2Run evaluation results
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
import base64

logger = logging.getLogger(__name__)


class Reporter:
    """Generate evaluation reports in various formats"""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize reporter with template directory

        Args:
            template_dir: Directory containing report templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.template_dir = template_dir
        self._ensure_templates()

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Register custom filters
        self.env.filters["percentage"] = lambda x: f"{x*100:.1f}%"
        self.env.filters["round"] = lambda x, n=2: round(x, n)
        self.env.filters["timestamp"] = lambda x: datetime.fromisoformat(x).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    def generate_html_report(
        self, results: List[Dict[str, Any]], output_path: str
    ) -> None:
        """
        Generate HTML report

        Args:
            results: List of evaluation results
            output_path: Path to save HTML report
        """
        # Prepare data
        report_data = self._prepare_report_data(results)

        # Generate charts
        charts = self._generate_charts(report_data)

        # Render template
        template = self.env.get_template("report.html")
        html_content = template.render(
            title="Req2Run Evaluation Report",
            timestamp=datetime.now().isoformat(),
            results=results,
            summary=report_data["summary"],
            charts=charts,
            problems=report_data["problems"],
        )

        # Save report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {output_path}")

    def generate_markdown_report(
        self, results: List[Dict[str, Any]], output_path: str
    ) -> None:
        """
        Generate Markdown report

        Args:
            results: List of evaluation results
            output_path: Path to save Markdown report
        """
        # Prepare data
        report_data = self._prepare_report_data(results)

        # Render template
        template = self.env.get_template("report.md")
        md_content = template.render(
            title="Req2Run Evaluation Report",
            timestamp=datetime.now().isoformat(),
            results=results,
            summary=report_data["summary"],
            problems=report_data["problems"],
        )

        # Save report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Markdown report generated: {output_path}")

    def generate_json_report(
        self, results: List[Dict[str, Any]], output_path: str
    ) -> None:
        """
        Generate JSON report

        Args:
            results: List of evaluation results
            output_path: Path to save JSON report
        """
        # Prepare data
        report_data = self._prepare_report_data(results)

        # Create comprehensive JSON report
        json_report = {
            "metadata": {
                "version": "1.0.0",
                "generated_at": datetime.now().isoformat(),
                "total_problems": len(results),
            },
            "summary": report_data["summary"],
            "problems": report_data["problems"],
            "detailed_results": results,
        }

        # Save report
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(json_report, f, indent=2)

        logger.info(f"JSON report generated: {output_path}")

    def generate_leaderboard(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate leaderboard markdown

        Args:
            results: List of evaluation results

        Returns:
            Leaderboard markdown string
        """
        # Sort results by total score
        sorted_results = sorted(
            results, key=lambda x: x.get("total_score", 0), reverse=True
        )

        leaderboard = "# Req2Run Leaderboard\n\n"
        leaderboard += f"*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        leaderboard += "| Rank | Submission | Problem | Score | Status | Time |\n"
        leaderboard += "|------|------------|---------|-------|--------|------|\n"

        for i, result in enumerate(sorted_results, 1):
            submission_id = result.get("submission_id", "Unknown")
            problem_id = result.get("problem_id", "Unknown")
            score = result.get("total_score", 0) * 100
            status = result.get("status", "Unknown").upper()
            exec_time = result.get("execution_time", 0)

            status_emoji = "✅" if status == "PASSED" else "❌"

            leaderboard += f"| {i} | {submission_id} | {problem_id} | {score:.1f}% | {status_emoji} {status} | {exec_time:.1f}s |\n"

        # Add statistics
        leaderboard += "\n## Statistics\n\n"
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "passed")
        avg_score = (
            sum(r.get("total_score", 0) for r in results) / total if total > 0 else 0
        )

        leaderboard += f"- **Total Submissions**: {total}\n"
        leaderboard += f"- **Pass Rate**: {passed}/{total} ({passed/total*100:.1f}%)\n"
        leaderboard += f"- **Average Score**: {avg_score*100:.1f}%\n"

        return leaderboard

    def _prepare_report_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare data for report generation"""
        if not results:
            return {
                "summary": {
                    "total_problems": 0,
                    "passed": 0,
                    "failed": 0,
                    "average_score": 0,
                    "pass_rate": 0,
                },
                "problems": [],
            }

        # Calculate summary statistics
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = total - passed
        avg_score = sum(r.get("total_score", 0) for r in results) / total

        # Group by problem
        problems = {}
        for result in results:
            problem_id = result.get("problem_id", "Unknown")
            if problem_id not in problems:
                problems[problem_id] = {
                    "id": problem_id,
                    "submissions": [],
                    "best_score": 0,
                    "avg_score": 0,
                    "pass_rate": 0,
                }

            problems[problem_id]["submissions"].append(result)
            problems[problem_id]["best_score"] = max(
                problems[problem_id]["best_score"], result.get("total_score", 0)
            )

        # Calculate problem statistics
        for problem_data in problems.values():
            submissions = problem_data["submissions"]
            problem_data["avg_score"] = sum(
                s.get("total_score", 0) for s in submissions
            ) / len(submissions)
            problem_data["pass_rate"] = sum(
                1 for s in submissions if s.get("status") == "passed"
            ) / len(submissions)

        return {
            "summary": {
                "total_problems": total,
                "passed": passed,
                "failed": failed,
                "average_score": avg_score,
                "pass_rate": passed / total if total > 0 else 0,
            },
            "problems": list(problems.values()),
        }

    def _generate_charts(self, report_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate charts for report"""
        charts = {}

        # Generate pass/fail pie chart
        charts["pass_fail_chart"] = self._create_pie_chart(
            [report_data["summary"]["passed"], report_data["summary"]["failed"]],
            ["Passed", "Failed"],
            ["#28a745", "#dc3545"],
            "Pass/Fail Distribution",
        )

        # Generate score distribution histogram
        if report_data["problems"]:
            scores = []
            for problem in report_data["problems"]:
                scores.extend(
                    [s.get("total_score", 0) * 100 for s in problem["submissions"]]
                )

            if scores:
                charts["score_distribution"] = self._create_histogram(
                    scores, "Score (%)", "Frequency", "Score Distribution"
                )

        # Generate problem comparison bar chart
        if len(report_data["problems"]) > 1:
            problem_ids = [p["id"] for p in report_data["problems"]]
            avg_scores = [p["avg_score"] * 100 for p in report_data["problems"]]

            charts["problem_comparison"] = self._create_bar_chart(
                problem_ids,
                avg_scores,
                "Problem ID",
                "Average Score (%)",
                "Problem Comparison",
            )

        return charts

    def _create_pie_chart(
        self, values: List[float], labels: List[str], colors: List[str], title: str
    ) -> str:
        """Create pie chart and return as base64 encoded image"""
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(values, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
        ax.set_title(title)

        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _create_histogram(
        self, data: List[float], xlabel: str, ylabel: str, title: str
    ) -> str:
        """Create histogram and return as base64 encoded image"""
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(data, bins=20, color="#007bff", edgecolor="black", alpha=0.7)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _create_bar_chart(
        self, x: List[str], y: List[float], xlabel: str, ylabel: str, title: str
    ) -> str:
        """Create bar chart and return as base64 encoded image"""
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(x, y, color="#28a745", edgecolor="black")

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f}",
                ha="center",
                va="bottom",
            )

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3, axis="y")

        # Rotate x labels if needed
        if len(x) > 5:
            plt.xticks(rotation=45, ha="right")

        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f"data:image/png;base64,{image_base64}"

    def _ensure_templates(self):
        """Ensure report templates exist"""
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # Create default HTML template if not exists
        html_template_path = self.template_dir / "report.html"
        if not html_template_path.exists():
            html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 0;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { opacity: 0.9; font-size: 1.1em; }
        .summary-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .card:hover { transform: translateY(-5px); }
        .card-title {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .card-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .card.success .card-value { color: #28a745; }
        .card.danger .card-value { color: #dc3545; }
        .card.info .card-value { color: #007bff; }
        .results-table {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th {
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #666;
            border-bottom: 2px solid #dee2e6;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
        }
        tr:hover { background: #f8f9fa; }
        .status-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .status-passed {
            background: #d4edda;
            color: #155724;
        }
        .status-failed {
            background: #f8d7da;
            color: #721c24;
        }
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .metric-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .metric-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
        }
        .metric-value {
            font-size: 1.2em;
            font-weight: bold;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s;
        }
        footer {
            text-align: center;
            padding: 30px 0;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{{ title }}</h1>
            <div class="subtitle">Generated: {{ timestamp | timestamp }}</div>
        </div>
    </header>
    
    <div class="container">
        <!-- Summary Cards -->
        <div class="summary-cards">
            <div class="card">
                <div class="card-title">Total Problems</div>
                <div class="card-value">{{ summary.total_problems }}</div>
            </div>
            <div class="card success">
                <div class="card-title">Passed</div>
                <div class="card-value">{{ summary.passed }}</div>
            </div>
            <div class="card danger">
                <div class="card-title">Failed</div>
                <div class="card-value">{{ summary.failed }}</div>
            </div>
            <div class="card info">
                <div class="card-title">Average Score</div>
                <div class="card-value">{{ summary.average_score | percentage }}</div>
            </div>
        </div>
        
        <!-- Charts -->
        {% if charts %}
        <div class="chart-container">
            <h2>Evaluation Overview</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 20px;">
                {% if charts.pass_fail_chart %}
                <img src="{{ charts.pass_fail_chart }}" alt="Pass/Fail Distribution">
                {% endif %}
                {% if charts.score_distribution %}
                <img src="{{ charts.score_distribution }}" alt="Score Distribution">
                {% endif %}
            </div>
        </div>
        {% endif %}
        
        <!-- Detailed Results -->
        <div class="results-table">
            <h2 style="padding: 20px 20px 0;">Detailed Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Problem ID</th>
                        <th>Submission ID</th>
                        <th>Status</th>
                        <th>Total Score</th>
                        <th>Execution Time</th>
                        <th>Test Pass Rate</th>
                        <th>Performance</th>
                        <th>Security</th>
                    </tr>
                </thead>
                <tbody>
                    {% for result in results %}
                    <tr>
                        <td><strong>{{ result.problem_id }}</strong></td>
                        <td>{{ result.submission_id }}</td>
                        <td>
                            <span class="status-badge status-{{ result.status }}">
                                {{ result.status | upper }}
                            </span>
                        </td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <strong>{{ result.total_score | percentage }}</strong>
                                <div class="progress-bar" style="flex: 1;">
                                    <div class="progress-bar-fill" style="width: {{ result.total_score * 100 }}%"></div>
                                </div>
                            </div>
                        </td>
                        <td>{{ result.execution_time | round(1) }}s</td>
                        <td>{{ result.metrics.test_pass_rate | percentage if result.metrics else 'N/A' }}</td>
                        <td>{{ result.metrics.performance_score | percentage if result.metrics else 'N/A' }}</td>
                        <td>{{ result.metrics.security_score | percentage if result.metrics else 'N/A' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- Problem Analysis -->
        {% if problems %}
        <div class="results-table">
            <h2 style="padding: 20px 20px 0;">Problem Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Problem ID</th>
                        <th>Submissions</th>
                        <th>Best Score</th>
                        <th>Average Score</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {% for problem in problems %}
                    <tr>
                        <td><strong>{{ problem.id }}</strong></td>
                        <td>{{ problem.submissions | length }}</td>
                        <td>{{ problem.best_score | percentage }}</td>
                        <td>{{ problem.avg_score | percentage }}</td>
                        <td>{{ problem.pass_rate | percentage }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
    
    <footer>
        <div class="container">
            <p>Req2Run Benchmark Framework v1.0.0 | © 2024 IT Dojo Japan</p>
        </div>
    </footer>
</body>
</html>"""
            with open(html_template_path, "w", encoding="utf-8") as f:
                f.write(html_template)

        # Create default Markdown template if not exists
        md_template_path = self.template_dir / "report.md"
        if not md_template_path.exists():
            md_template = """# {{ title }}

*Generated: {{ timestamp | timestamp }}*

## Summary

| Metric | Value |
|--------|-------|
| **Total Problems** | {{ summary.total_problems }} |
| **Passed** | {{ summary.passed }} |
| **Failed** | {{ summary.failed }} |
| **Average Score** | {{ summary.average_score | percentage }} |
| **Pass Rate** | {{ summary.pass_rate | percentage }} |

## Detailed Results

| Problem ID | Submission ID | Status | Score | Time | Test Pass | Performance | Security |
|------------|---------------|--------|-------|------|-----------|-------------|----------|
{% for result in results -%}
| {{ result.problem_id }} | {{ result.submission_id }} | {{ result.status | upper }} | {{ result.total_score | percentage }} | {{ result.execution_time | round(1) }}s | {{ result.metrics.test_pass_rate | percentage if result.metrics else 'N/A' }} | {{ result.metrics.performance_score | percentage if result.metrics else 'N/A' }} | {{ result.metrics.security_score | percentage if result.metrics else 'N/A' }} |
{% endfor %}

## Problem Analysis

{% if problems %}
| Problem ID | Submissions | Best Score | Avg Score | Pass Rate |
|------------|-------------|------------|-----------|-----------|
{% for problem in problems -%}
| {{ problem.id }} | {{ problem.submissions | length }} | {{ problem.best_score | percentage }} | {{ problem.avg_score | percentage }} | {{ problem.pass_rate | percentage }} |
{% endfor %}
{% endif %}

---

*Report generated by Req2Run Benchmark Framework v1.0.0*"""
            with open(md_template_path, "w", encoding="utf-8") as f:
                f.write(md_template)
