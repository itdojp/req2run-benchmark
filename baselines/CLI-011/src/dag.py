"""DAG (Directed Acyclic Graph) operations and analysis"""
import networkx as nx
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from models import JobDefinition, DAGMetadata


class DAGAnalyzer:
    """Analyzes DAG structure and provides execution planning"""
    
    def __init__(self, jobs: List[JobDefinition]):
        self.jobs = {job.id: job for job in jobs}
        self.graph = self._build_graph()
    
    def _build_graph(self) -> nx.DiGraph:
        """Build NetworkX directed graph from job dependencies"""
        graph = nx.DiGraph()
        
        # Add all jobs as nodes
        for job_id in self.jobs:
            graph.add_node(job_id)
        
        # Add dependency edges
        for job_id, job in self.jobs.items():
            for dep_id in job.dependencies:
                if dep_id in self.jobs:
                    # Edge from dependency to dependent job
                    graph.add_edge(dep_id, job_id)
        
        return graph
    
    def validate_dag(self) -> Tuple[bool, List[str]]:
        """Validate that the graph is a valid DAG"""
        errors = []
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            try:
                cycle = nx.find_cycle(self.graph)
                cycle_str = " -> ".join([f"{edge[0]}" for edge in cycle] + [cycle[0][0]])
                errors.append(f"Circular dependency detected: {cycle_str}")
            except nx.NetworkXNoCycle:
                errors.append("Graph contains cycles")
        
        # Check for missing dependencies
        for job_id, job in self.jobs.items():
            for dep_id in job.dependencies:
                if dep_id not in self.jobs:
                    errors.append(f"Job '{job_id}' depends on non-existent job '{dep_id}'")
        
        # Check for self-dependencies
        for job_id, job in self.jobs.items():
            if job_id in job.dependencies:
                errors.append(f"Job '{job_id}' cannot depend on itself")
        
        return len(errors) == 0, errors
    
    def get_metadata(self) -> DAGMetadata:
        """Get metadata about the DAG structure"""
        is_valid, _ = self.validate_dag()
        
        if not is_valid:
            return DAGMetadata(
                total_jobs=len(self.jobs),
                levels=0,
                critical_path_length=0,
                has_cycles=True,
                max_parallelism=0
            )
        
        # Calculate levels using topological sorting
        levels = self._calculate_levels()
        
        # Calculate critical path length
        critical_path_length = self._calculate_critical_path()
        
        # Calculate maximum parallelism (max jobs at any level)
        max_parallelism = max(len(jobs) for jobs in levels.values()) if levels else 0
        
        return DAGMetadata(
            total_jobs=len(self.jobs),
            levels=len(levels),
            critical_path_length=critical_path_length,
            has_cycles=False,
            max_parallelism=max_parallelism
        )
    
    def _calculate_levels(self) -> Dict[int, List[str]]:
        """Calculate execution levels using topological sorting"""
        levels = defaultdict(list)
        
        if not self.jobs:
            return levels
        
        # Calculate longest path to each node (level)
        try:
            # Use topological sort to process nodes in dependency order
            for node in nx.topological_sort(self.graph):
                # Find maximum level of all predecessors
                max_pred_level = -1
                for pred in self.graph.predecessors(node):
                    pred_level = next(
                        level for level, jobs in levels.items() 
                        if pred in jobs
                    )
                    max_pred_level = max(max_pred_level, pred_level)
                
                # This node's level is one more than its highest predecessor
                node_level = max_pred_level + 1
                levels[node_level].append(node)
        
        except nx.NetworkXError:
            # If there are cycles, we can't calculate levels
            pass
        
        return levels
    
    def _calculate_critical_path(self) -> int:
        """Calculate the length of the critical path"""
        if not nx.is_directed_acyclic_graph(self.graph):
            return 0
        
        try:
            # Use longest path algorithm on DAG
            return nx.dag_longest_path_length(self.graph)
        except nx.NetworkXError:
            return 0
    
    def get_execution_order(self) -> List[List[str]]:
        """Get jobs grouped by execution level (can run in parallel within level)"""
        levels = self._calculate_levels()
        
        # Return jobs ordered by level
        execution_order = []
        for level in sorted(levels.keys()):
            execution_order.append(levels[level])
        
        return execution_order
    
    def get_ready_jobs(self, completed_jobs: Set[str], failed_jobs: Set[str]) -> List[str]:
        """Get jobs that are ready to execute based on completed dependencies"""
        ready_jobs = []
        
        for job_id, job in self.jobs.items():
            # Skip if already processed
            if job_id in completed_jobs or job_id in failed_jobs:
                continue
            
            # Check if all dependencies are completed
            all_deps_completed = True
            for dep_id in job.dependencies:
                if dep_id not in completed_jobs:
                    # Check if dependency failed and if we should skip
                    if dep_id in failed_jobs:
                        # For now, skip jobs with failed dependencies
                        all_deps_completed = False
                        break
                    all_deps_completed = False
                    break
            
            if all_deps_completed:
                ready_jobs.append(job_id)
        
        return ready_jobs
    
    def get_dependents(self, job_id: str) -> List[str]:
        """Get all jobs that depend on the given job"""
        return list(self.graph.successors(job_id))
    
    def get_dependencies(self, job_id: str) -> List[str]:
        """Get all jobs that the given job depends on"""
        return list(self.graph.predecessors(job_id))
    
    def get_transitive_dependencies(self, job_id: str) -> Set[str]:
        """Get all transitive dependencies of a job"""
        if job_id not in self.graph:
            return set()
        
        # Use networkx to find all ancestors (transitive dependencies)
        return set(nx.ancestors(self.graph, job_id))
    
    def get_transitive_dependents(self, job_id: str) -> Set[str]:
        """Get all transitive dependents of a job"""
        if job_id not in self.graph:
            return set()
        
        # Use networkx to find all descendants (transitive dependents)
        return set(nx.descendants(self.graph, job_id))
    
    def simulate_execution(self, max_parallel: int = 4) -> List[Tuple[float, List[str]]]:
        """Simulate execution timeline with given parallelism"""
        timeline = []
        completed = set()
        running = {}  # job_id -> end_time
        current_time = 0.0
        
        while len(completed) < len(self.jobs):
            # Remove completed jobs from running
            newly_completed = []
            for job_id, end_time in list(running.items()):
                if current_time >= end_time:
                    newly_completed.append(job_id)
                    completed.add(job_id)
                    del running[job_id]
            
            if newly_completed:
                timeline.append((current_time, f"Completed: {newly_completed}"))
            
            # Start new jobs if we have capacity
            ready_jobs = self.get_ready_jobs(completed, set())
            available_slots = max_parallel - len(running)
            
            jobs_to_start = ready_jobs[:available_slots]
            for job_id in jobs_to_start:
                # Assume each job takes 1 time unit for simulation
                running[job_id] = current_time + 1.0
                timeline.append((current_time, f"Started: {job_id}"))
            
            # Advance time to next event
            if running:
                next_completion = min(running.values())
                current_time = max(current_time + 0.1, next_completion)
            else:
                current_time += 0.1
        
        return timeline