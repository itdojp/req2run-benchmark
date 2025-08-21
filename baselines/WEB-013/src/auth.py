"""
Authentication and Authorization for GraphQL API

Implements field-level authorization and JWT authentication.
"""

import jwt
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import secrets


class AuthService:
    """Authentication service"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)
        self.refresh_token_expiry = timedelta(days=30)
    
    def generate_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT token"""
        payload = {
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(self, user: Dict[str, Any]) -> str:
        """Generate refresh token"""
        payload = {
            "user_id": user["id"],
            "exp": datetime.utcnow() + self.refresh_token_expiry,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload.get("type") != "access":
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify refresh token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload.get("type") != "refresh":
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


class FieldAuthorization:
    """Field-level authorization for GraphQL"""
    
    def __init__(self):
        self.field_permissions: Dict[str, Dict[str, Any]] = {}
        self._setup_default_permissions()
    
    def _setup_default_permissions(self):
        """Setup default field permissions"""
        # Public fields (no auth required)
        self.field_permissions['public'] = {
            'Query': ['posts', 'post', 'tags', 'popularTags', 'searchPosts'],
            'Post': ['id', 'title', 'content', 'published', 'createdAt', 'author'],
            'User': ['id', 'username', 'name'],
            'Tag': ['id', 'name', 'postCount']
        }
        
        # Authenticated fields
        self.field_permissions['authenticated'] = {
            'Query': ['me', 'user', 'users'],
            'Mutation': ['createPost', 'updatePost', 'deletePost', 'createComment'],
            'User': ['email', 'posts', 'comments']
        }
        
        # Admin only fields
        self.field_permissions['admin'] = {
            'Query': ['statistics'],
            'Mutation': ['deleteComment'],
            'User': ['createdAt', 'updatedAt']
        }
    
    def is_field_allowed(
        self,
        field_name: str,
        parent_type: str,
        user: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if field access is allowed"""
        # Check public fields
        public_fields = self.field_permissions['public'].get(parent_type, [])
        if field_name in public_fields:
            return True
        
        # Check authenticated fields
        if user:
            auth_fields = self.field_permissions['authenticated'].get(parent_type, [])
            if field_name in auth_fields:
                return True
            
            # Check admin fields
            if user.get('role') == 'admin':
                admin_fields = self.field_permissions['admin'].get(parent_type, [])
                if field_name in admin_fields:
                    return True
        
        return False
    
    def check_object_permission(
        self,
        obj: Dict[str, Any],
        user: Optional[Dict[str, Any]],
        permission: str
    ) -> bool:
        """Check object-level permission"""
        if not user:
            return False
        
        # Owner permission
        if permission == 'owner':
            return obj.get('author_id') == user.get('id') or \
                   obj.get('user_id') == user.get('id')
        
        # Admin permission
        if permission == 'admin':
            return user.get('role') == 'admin'
        
        return False


def auth_directive(field_resolver):
    """Decorator for authentication directive"""
    @wraps(field_resolver)
    async def wrapper(parent, info, **kwargs):
        user = info.context.get('user')
        
        if not user:
            raise GraphQLError("Authentication required")
        
        return await field_resolver(parent, info, **kwargs)
    
    return wrapper


def has_role_directive(role: str):
    """Decorator for role-based authorization"""
    def decorator(field_resolver):
        @wraps(field_resolver)
        async def wrapper(parent, info, **kwargs):
            user = info.context.get('user')
            
            if not user:
                raise GraphQLError("Authentication required")
            
            if user.get('role') != role:
                raise GraphQLError(f"Requires {role} role")
            
            return await field_resolver(parent, info, **kwargs)
        
        return wrapper
    
    return decorator


def rate_limit_directive(limit: int, duration: int):
    """Decorator for rate limiting"""
    request_counts = {}
    
    def decorator(field_resolver):
        @wraps(field_resolver)
        async def wrapper(parent, info, **kwargs):
            # Get client identifier
            request = info.context.get('request')
            client_ip = request.client.host if request else 'unknown'
            
            # Check rate limit
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(seconds=duration)
            
            if client_ip not in request_counts:
                request_counts[client_ip] = []
            
            # Remove old requests
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip]
                if req_time > window_start
            ]
            
            # Check limit
            if len(request_counts[client_ip]) >= limit:
                raise GraphQLError(
                    f"Rate limit exceeded: {limit} requests per {duration} seconds"
                )
            
            # Record request
            request_counts[client_ip].append(current_time)
            
            return await field_resolver(parent, info, **kwargs)
        
        return wrapper
    
    return decorator


async def authenticate_token(auth_header: str) -> Optional[Dict[str, Any]]:
    """Authenticate token from Authorization header"""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.replace('Bearer ', '')
    auth_service = AuthService()
    
    return auth_service.verify_token(token)


async def get_current_user(auth_header: str) -> Optional[Dict[str, Any]]:
    """Get current user from token"""
    token_data = await authenticate_token(auth_header)
    
    if not token_data:
        return None
    
    # In production, fetch user from database
    # For now, return token data as user
    return {
        'id': token_data['user_id'],
        'username': token_data['username'],
        'email': token_data['email'],
        'role': 'user'  # Default role
    }


# Import GraphQLError for type checking
try:
    from graphql import GraphQLError
except ImportError:
    class GraphQLError(Exception):
        pass