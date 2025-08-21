"""
Query Analysis for GraphQL

Implements query depth limiting and complexity analysis.
"""

from typing import Dict, Any, Optional, List
from graphql import DocumentNode, FieldNode, FragmentDefinitionNode, OperationDefinitionNode
from graphql.language import SelectionSetNode
from graphql.validation import ValidationRule, ValidationContext


class QueryDepthAnalyzer:
    """Analyzes query depth to prevent deeply nested queries"""
    
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
    
    def analyze(self, document: DocumentNode) -> int:
        """Analyze the maximum depth of a GraphQL document"""
        max_depth = 0
        
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                depth = self._calculate_depth(definition.selection_set, 0)
                max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calculate_depth(
        self,
        selection_set: Optional[SelectionSetNode],
        current_depth: int,
        fragments: Dict[str, FragmentDefinitionNode] = None
    ) -> int:
        """Recursively calculate query depth"""
        if not selection_set:
            return current_depth
        
        if fragments is None:
            fragments = {}
        
        max_depth = current_depth
        
        for selection in selection_set.selections:
            if hasattr(selection, 'selection_set'):
                # Field with nested selections
                depth = self._calculate_depth(
                    selection.selection_set,
                    current_depth + 1,
                    fragments
                )
                max_depth = max(max_depth, depth)
            elif hasattr(selection, 'name') and selection.name.value in fragments:
                # Fragment spread
                fragment = fragments[selection.name.value]
                depth = self._calculate_depth(
                    fragment.selection_set,
                    current_depth,
                    fragments
                )
                max_depth = max(max_depth, depth)
        
        return max_depth


class QueryComplexityAnalyzer:
    """Analyzes query complexity to prevent expensive queries"""
    
    def __init__(self, max_complexity: int = 1000):
        self.max_complexity = max_complexity
        self.field_complexity = self._default_field_complexity()
    
    def _default_field_complexity(self) -> Dict[str, int]:
        """Default complexity values for fields"""
        return {
            # Simple fields
            'id': 0,
            'title': 0,
            'content': 0,
            'name': 0,
            'email': 0,
            'username': 0,
            'createdAt': 0,
            'updatedAt': 0,
            
            # Single entity lookups
            'user': 1,
            'post': 1,
            'comment': 1,
            'tag': 1,
            
            # List queries (base complexity + multiplier)
            'users': 10,
            'posts': 10,
            'comments': 5,
            'tags': 5,
            
            # Nested relations
            'author': 1,
            'replies': 5,
            
            # Complex queries
            'searchPosts': 20,
            'statistics': 50,
            
            # Mutations
            'createPost': 10,
            'updatePost': 10,
            'deletePost': 5,
            'createComment': 5,
            
            # Subscriptions
            'postAdded': 1,
            'commentAdded': 1
        }
    
    def analyze(
        self,
        document: DocumentNode,
        variables: Dict[str, Any] = None
    ) -> int:
        """Analyze the total complexity of a GraphQL document"""
        if variables is None:
            variables = {}
        
        total_complexity = 0
        fragments = self._extract_fragments(document)
        
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                complexity = self._calculate_complexity(
                    definition.selection_set,
                    variables,
                    fragments
                )
                total_complexity += complexity
        
        return total_complexity
    
    def _extract_fragments(self, document: DocumentNode) -> Dict[str, FragmentDefinitionNode]:
        """Extract fragment definitions from document"""
        fragments = {}
        
        for definition in document.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                fragments[definition.name.value] = definition
        
        return fragments
    
    def _calculate_complexity(
        self,
        selection_set: Optional[SelectionSetNode],
        variables: Dict[str, Any],
        fragments: Dict[str, FragmentDefinitionNode],
        parent_multiplier: int = 1
    ) -> int:
        """Recursively calculate query complexity"""
        if not selection_set:
            return 0
        
        complexity = 0
        
        for selection in selection_set.selections:
            if hasattr(selection, 'name'):
                field_name = selection.name.value
                
                # Get base complexity for field
                base_complexity = self.field_complexity.get(field_name, 1)
                
                # Calculate multiplier from arguments
                multiplier = self._get_multiplier(selection, variables)
                
                # Add field complexity
                field_total = base_complexity * multiplier * parent_multiplier
                complexity += field_total
                
                # Add nested complexity
                if hasattr(selection, 'selection_set'):
                    nested_complexity = self._calculate_complexity(
                        selection.selection_set,
                        variables,
                        fragments,
                        multiplier * parent_multiplier
                    )
                    complexity += nested_complexity
                    
            elif hasattr(selection, 'name') and selection.name.value in fragments:
                # Fragment spread
                fragment = fragments[selection.name.value]
                fragment_complexity = self._calculate_complexity(
                    fragment.selection_set,
                    variables,
                    fragments,
                    parent_multiplier
                )
                complexity += fragment_complexity
        
        return complexity
    
    def _get_multiplier(
        self,
        field: FieldNode,
        variables: Dict[str, Any]
    ) -> int:
        """Get multiplier based on field arguments"""
        if not hasattr(field, 'arguments'):
            return 1
        
        multiplier = 1
        
        for argument in field.arguments:
            arg_name = argument.name.value
            
            # Check for pagination arguments
            if arg_name in ['first', 'last', 'limit']:
                value = self._get_argument_value(argument, variables)
                if value and isinstance(value, int):
                    multiplier = max(multiplier, value)
        
        return min(multiplier, 100)  # Cap multiplier at 100
    
    def _get_argument_value(
        self,
        argument,
        variables: Dict[str, Any]
    ) -> Any:
        """Get the value of an argument"""
        if hasattr(argument.value, 'value'):
            return argument.value.value
        elif hasattr(argument.value, 'name'):
            # Variable reference
            var_name = argument.value.name.value
            return variables.get(var_name)
        
        return None


class DepthLimitValidation(ValidationRule):
    """GraphQL validation rule for depth limiting"""
    
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        super().__init__()
    
    def enter_field(self, node, key, parent, path, ancestors):
        """Check field depth"""
        depth = len([
            ancestor for ancestor in ancestors
            if isinstance(ancestor, FieldNode)
        ])
        
        if depth > self.max_depth:
            self.report_error(
                f"Query depth {depth} exceeds maximum allowed depth of {self.max_depth}"
            )


class ComplexityLimitValidation(ValidationRule):
    """GraphQL validation rule for complexity limiting"""
    
    def __init__(self, max_complexity: int = 1000):
        self.max_complexity = max_complexity
        self.analyzer = QueryComplexityAnalyzer(max_complexity)
        super().__init__()
    
    def enter_document(self, node, key, parent, path, ancestors):
        """Check document complexity"""
        complexity = self.analyzer.analyze(node)
        
        if complexity > self.max_complexity:
            self.report_error(
                f"Query complexity {complexity} exceeds maximum allowed "
                f"complexity of {self.max_complexity}"
            )


class QueryWhitelisting:
    """Whitelist allowed queries for production"""
    
    def __init__(self):
        self.whitelisted_queries: Dict[str, str] = {}
        self.enabled = False
    
    def add_query(self, name: str, query: str):
        """Add query to whitelist"""
        query_hash = self._hash_query(query)
        self.whitelisted_queries[query_hash] = name
    
    def is_allowed(self, query: str) -> bool:
        """Check if query is whitelisted"""
        if not self.enabled:
            return True
        
        query_hash = self._hash_query(query)
        return query_hash in self.whitelisted_queries
    
    def _hash_query(self, query: str) -> str:
        """Hash query for comparison"""
        import hashlib
        # Normalize query by removing whitespace
        normalized = ''.join(query.split())
        return hashlib.sha256(normalized.encode()).hexdigest()


class PersistedQueries:
    """Support for persisted queries to reduce bandwidth"""
    
    def __init__(self):
        self.queries: Dict[str, str] = {}
    
    def register(self, query_id: str, query: str):
        """Register a persisted query"""
        self.queries[query_id] = query
    
    def get(self, query_id: str) -> Optional[str]:
        """Get persisted query by ID"""
        return self.queries.get(query_id)
    
    def generate_id(self, query: str) -> str:
        """Generate ID for query"""
        import hashlib
        return hashlib.sha256(query.encode()).hexdigest()


class RateLimiter:
    """Rate limiting for GraphQL queries"""
    
    def __init__(self, requests_per_minute: int = 100, burst: int = 20):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Get recent requests
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Check burst limit
        recent_requests = [
            req_time for req_time in self.requests[client_id]
            if req_time > now - timedelta(seconds=1)
        ]
        if len(recent_requests) >= self.burst:
            return False
        
        # Record request
        self.requests[client_id].append(now)
        
        return True