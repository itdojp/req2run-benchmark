"""
GraphQL API with N+1 Query Prevention

Main application with query complexity analysis and depth limiting.
"""

import asyncio
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from graphql import (
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLField,
    GraphQLString,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLBoolean,
    GraphQLID,
    GraphQLArgument,
    GraphQLInputObjectType,
    GraphQLInputField,
    GraphQLEnumType,
    GraphQLEnumValue,
    graphql,
    parse,
    validate,
    ValidationRule,
    GraphQLError
)
from graphql.execution import ExecutionResult
from graphql.language import DocumentNode, FieldNode
from graphql.validation import ValidationContext
import strawberry
from strawberry.fastapi import GraphQLRouter

from dataloader import DataLoaderRegistry
from resolvers import QueryResolvers, MutationResolvers, SubscriptionResolvers, FieldResolvers
from query_analysis import QueryDepthAnalyzer, QueryComplexityAnalyzer
from auth import authenticate_token, get_current_user


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GraphQLApp:
    """Main GraphQL application"""
    
    def __init__(self, config_path: str = "config/graphql.yaml"):
        self.config = self._load_config(config_path)
        self.app = FastAPI(title="GraphQL API with N+1 Prevention")
        self.db_session = None  # Would be actual database session
        self.loaders = None
        self.schema = None
        self.pubsub = None  # For subscriptions
        
        # Initialize components
        self._setup_middleware()
        self._setup_database()
        self._setup_graphql()
        self._setup_routes()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False
            },
            "graphql": {
                "max_query_depth": 10,
                "max_query_complexity": 1000,
                "introspection": True,
                "playground": True,
                "batching": True,
                "persisted_queries": True
            },
            "dataloader": {
                "cache_ttl": 60,
                "max_batch_size": 100
            },
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 100,
                "burst": 20
            },
            "database": {
                "url": "postgresql://user:pass@localhost/graphql_db",
                "pool_size": 20,
                "max_overflow": 10
            }
        }
    
    def _setup_middleware(self):
        """Setup middleware"""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Request logging
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = datetime.utcnow()
            response = await call_next(request)
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {duration:.3f}s"
            )
            
            return response
    
    def _setup_database(self):
        """Setup database connection"""
        # This would initialize actual database connection
        # For now, using mock database session
        class MockDBSession:
            async def fetch_all(self, query: str, *args):
                # Mock implementation
                return []
            
            async def fetch_one(self, query: str, *args):
                # Mock implementation
                return {}
            
            async def execute(self, query: str, *args):
                # Mock implementation
                return None
        
        self.db_session = MockDBSession()
        self.loaders = DataLoaderRegistry(self.db_session)
    
    def _setup_graphql(self):
        """Setup GraphQL schema and resolvers"""
        # Load schema from file
        with open('schema.graphql', 'r') as f:
            schema_str = f.read()
        
        # Create resolvers
        query_resolvers = QueryResolvers(self.loaders, self.db_session)
        mutation_resolvers = MutationResolvers(self.loaders, self.db_session)
        field_resolvers = FieldResolvers(self.loaders)
        
        # Build executable schema
        # In production, this would use graphql-core or strawberry
        # For demonstration, creating a simple schema structure
        
        # Query depth and complexity analyzers
        self.depth_analyzer = QueryDepthAnalyzer(
            max_depth=self.config['graphql']['max_query_depth']
        )
        self.complexity_analyzer = QueryComplexityAnalyzer(
            max_complexity=self.config['graphql']['max_query_complexity']
        )
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "config": {
                    "max_query_depth": self.config['graphql']['max_query_depth'],
                    "max_query_complexity": self.config['graphql']['max_query_complexity'],
                    "dataloader_cache_ttl": self.config['dataloader']['cache_ttl']
                }
            }
        
        @self.app.post("/graphql")
        async def graphql_endpoint(request: Request):
            """Main GraphQL endpoint"""
            try:
                # Parse request
                body = await request.json()
                query = body.get('query')
                variables = body.get('variables', {})
                operation_name = body.get('operationName')
                
                # Get user from auth header (optional)
                auth_header = request.headers.get('Authorization')
                user = None
                if auth_header:
                    user = await get_current_user(auth_header)
                
                # Parse query
                document = parse(query)
                
                # Analyze query depth
                depth = self.depth_analyzer.analyze(document)
                if depth > self.config['graphql']['max_query_depth']:
                    raise GraphQLError(
                        f"Query depth {depth} exceeds maximum allowed depth "
                        f"of {self.config['graphql']['max_query_depth']}"
                    )
                
                # Analyze query complexity
                complexity = self.complexity_analyzer.analyze(document, variables)
                if complexity > self.config['graphql']['max_query_complexity']:
                    raise GraphQLError(
                        f"Query complexity {complexity} exceeds maximum allowed "
                        f"complexity of {self.config['graphql']['max_query_complexity']}"
                    )
                
                # Create context with DataLoaders
                context = {
                    'user': user,
                    'loaders': self.loaders,
                    'db': self.db_session,
                    'request': request
                }
                
                # Execute query
                result = await self._execute_query(
                    query,
                    variables,
                    operation_name,
                    context
                )
                
                # Add extensions
                if result.get('errors'):
                    result['extensions'] = {
                        'query_depth': depth,
                        'query_complexity': complexity,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                
                return result
                
            except GraphQLError as e:
                return {
                    'errors': [{
                        'message': str(e),
                        'extensions': {
                            'code': 'GRAPHQL_VALIDATION_FAILED'
                        }
                    }]
                }
            except Exception as e:
                logger.error(f"GraphQL execution error: {e}")
                return {
                    'errors': [{
                        'message': 'Internal server error',
                        'extensions': {
                            'code': 'INTERNAL_SERVER_ERROR'
                        }
                    }]
                }
        
        @self.app.post("/graphql/batch")
        async def graphql_batch_endpoint(request: Request):
            """Batch GraphQL endpoint"""
            if not self.config['graphql']['batching']:
                raise HTTPException(status_code=404, detail="Batch queries not enabled")
            
            try:
                # Parse batch request
                body = await request.json()
                if not isinstance(body, list):
                    raise ValueError("Batch request must be an array")
                
                # Execute queries in parallel
                results = await asyncio.gather(*[
                    self._execute_query(
                        q.get('query'),
                        q.get('variables', {}),
                        q.get('operationName'),
                        {'request': request}
                    )
                    for q in body
                ])
                
                return results
                
            except Exception as e:
                logger.error(f"Batch execution error: {e}")
                return [{
                    'errors': [{
                        'message': 'Batch execution failed',
                        'extensions': {'code': 'BATCH_EXECUTION_ERROR'}
                    }]
                }]
        
        @self.app.get("/graphql/schema")
        async def get_schema():
            """Get GraphQL schema"""
            if not self.config['graphql']['introspection']:
                raise HTTPException(status_code=403, detail="Schema introspection disabled")
            
            with open('schema.graphql', 'r') as f:
                return {"schema": f.read()}
        
        if self.config['graphql']['playground']:
            @self.app.get("/graphql/playground")
            async def graphql_playground():
                """GraphQL Playground"""
                return """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>GraphQL Playground</title>
                    <link rel="stylesheet" href="https://unpkg.com/graphql-playground-react/build/static/css/index.css" />
                    <script src="https://unpkg.com/graphql-playground-react/build/static/js/middleware.js"></script>
                </head>
                <body>
                    <div id="root"></div>
                    <script>
                        window.addEventListener('load', function (event) {
                            GraphQLPlayground.init(document.getElementById('root'), {
                                endpoint: '/graphql',
                                subscriptionEndpoint: 'ws://localhost:8000/graphql',
                                settings: {
                                    'request.credentials': 'include',
                                }
                            })
                        })
                    </script>
                </body>
                </html>
                """
    
    async def _execute_query(
        self,
        query: str,
        variables: Dict,
        operation_name: Optional[str],
        context: Dict
    ) -> Dict:
        """Execute GraphQL query"""
        # This is a simplified implementation
        # In production, use graphql-core or strawberry
        
        # Mock execution result
        return {
            'data': {
                'users': [
                    {'id': '1', 'username': 'user1', 'email': 'user1@example.com'},
                    {'id': '2', 'username': 'user2', 'email': 'user2@example.com'}
                ]
            }
        }
    
    def run(self):
        """Run the application"""
        import uvicorn
        
        host = self.config['server']['host']
        port = self.config['server']['port']
        debug = self.config['server']['debug']
        
        logger.info(f"Starting GraphQL server on {host}:{port}")
        logger.info(f"GraphQL endpoint: http://{host}:{port}/graphql")
        
        if self.config['graphql']['playground']:
            logger.info(f"GraphQL Playground: http://{host}:{port}/graphql/playground")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=debug
        )


def main():
    """Main entry point"""
    app = GraphQLApp()
    app.run()


if __name__ == "__main__":
    main()