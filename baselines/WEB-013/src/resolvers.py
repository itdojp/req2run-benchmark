"""
GraphQL Resolvers with DataLoader integration

Implements query, mutation, and subscription resolvers.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json
from graphql import GraphQLError

from dataloader import DataLoaderRegistry


class QueryResolvers:
    """Query resolvers"""
    
    def __init__(self, loaders: DataLoaderRegistry, db_session):
        self.loaders = loaders
        self.db = db_session
    
    async def user(self, parent, info, id: str) -> Optional[Dict]:
        """Resolve single user"""
        return await self.loaders.get('user').load(int(id))
    
    async def users(
        self,
        parent,
        info,
        limit: int = 10,
        offset: int = 0,
        orderBy: str = 'CREATED_AT_DESC'
    ) -> List[Dict]:
        """Resolve multiple users"""
        order_map = {
            'CREATED_AT_ASC': 'created_at ASC',
            'CREATED_AT_DESC': 'created_at DESC',
            'USERNAME_ASC': 'username ASC',
            'USERNAME_DESC': 'username DESC'
        }
        
        query = f"""
            SELECT * FROM users
            ORDER BY {order_map.get(orderBy, 'created_at DESC')}
            LIMIT %s OFFSET %s
        """
        
        users = await self.db.fetch_all(query, limit, offset)
        
        # Prime the cache
        for user in users:
            await self.loaders.get('user').prime(user['id'], user)
        
        return users
    
    async def post(self, parent, info, id: str) -> Optional[Dict]:
        """Resolve single post"""
        return await self.loaders.get('post').load(int(id))
    
    async def posts(
        self,
        parent,
        info,
        first: Optional[int] = None,
        after: Optional[str] = None,
        last: Optional[int] = None,
        before: Optional[str] = None,
        published: Optional[bool] = None,
        authorId: Optional[str] = None,
        tagName: Optional[str] = None,
        orderBy: str = 'CREATED_AT_DESC'
    ) -> Dict:
        """Resolve posts with cursor-based pagination"""
        # Build query conditions
        conditions = []
        params = []
        
        if published is not None:
            conditions.append("published = %s")
            params.append(published)
        
        if authorId:
            conditions.append("author_id = %s")
            params.append(int(authorId))
        
        if tagName:
            conditions.append("""
                EXISTS (
                    SELECT 1 FROM post_tags pt
                    JOIN tags t ON pt.tag_id = t.id
                    WHERE pt.post_id = posts.id AND t.name = %s
                )
            """)
            params.append(tagName)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Handle pagination
        limit = first or last or 10
        
        # Count total
        count_query = f"SELECT COUNT(*) as total FROM posts WHERE {where_clause}"
        total_result = await self.db.fetch_one(count_query, *params)
        total_count = total_result['total']
        
        # Fetch posts
        order_map = {
            'CREATED_AT_ASC': 'created_at ASC',
            'CREATED_AT_DESC': 'created_at DESC',
            'UPDATED_AT_ASC': 'updated_at ASC',
            'UPDATED_AT_DESC': 'updated_at DESC',
            'VIEW_COUNT_DESC': 'view_count DESC',
            'TITLE_ASC': 'title ASC'
        }
        
        query = f"""
            SELECT * FROM posts
            WHERE {where_clause}
            ORDER BY {order_map.get(orderBy, 'created_at DESC')}
            LIMIT %s
        """
        
        posts = await self.db.fetch_all(query, *params, limit)
        
        # Prime the cache
        for post in posts:
            await self.loaders.get('post').prime(post['id'], post)
        
        # Build connection response
        edges = [
            {
                'node': post,
                'cursor': self._encode_cursor(post['id'])
            }
            for post in posts
        ]
        
        return {
            'edges': edges,
            'pageInfo': {
                'hasNextPage': len(posts) == limit,
                'hasPreviousPage': offset > 0 if after else False,
                'startCursor': edges[0]['cursor'] if edges else None,
                'endCursor': edges[-1]['cursor'] if edges else None
            },
            'totalCount': total_count
        }
    
    async def searchPosts(
        self,
        parent,
        info,
        query: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search posts"""
        search_query = """
            SELECT * FROM posts
            WHERE (title ILIKE %s OR content ILIKE %s)
            AND published = true
            ORDER BY view_count DESC
            LIMIT %s
        """
        
        search_term = f"%{query}%"
        posts = await self.db.fetch_all(search_query, search_term, search_term, limit)
        
        return posts
    
    async def tags(self, parent, info, limit: int = 20) -> List[Dict]:
        """Resolve tags"""
        query = """
            SELECT t.*, COUNT(pt.post_id) as post_count
            FROM tags t
            LEFT JOIN post_tags pt ON t.id = pt.tag_id
            GROUP BY t.id
            ORDER BY t.name
            LIMIT %s
        """
        
        return await self.db.fetch_all(query, limit)
    
    async def popularTags(self, parent, info, limit: int = 10) -> List[Dict]:
        """Resolve popular tags"""
        query = """
            SELECT t.*, COUNT(pt.post_id) as post_count
            FROM tags t
            LEFT JOIN post_tags pt ON t.id = pt.tag_id
            GROUP BY t.id
            ORDER BY post_count DESC
            LIMIT %s
        """
        
        return await self.db.fetch_all(query, limit)
    
    async def statistics(self, parent, info) -> Dict:
        """Resolve statistics"""
        stats_query = """
            SELECT
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM posts) as total_posts,
                (SELECT COUNT(*) FROM comments) as total_comments,
                (SELECT COUNT(*) FROM tags) as total_tags,
                (SELECT COUNT(*) FROM users WHERE last_active > NOW() - INTERVAL '1 day') as active_users,
                (SELECT COUNT(*) FROM posts WHERE created_at > NOW() - INTERVAL '1 day') as posts_today,
                (SELECT COUNT(*) FROM comments WHERE created_at > NOW() - INTERVAL '1 day') as comments_today
        """
        
        result = await self.db.fetch_one(stats_query)
        
        return {
            'totalUsers': result['total_users'],
            'totalPosts': result['total_posts'],
            'totalComments': result['total_comments'],
            'totalTags': result['total_tags'],
            'activeUsers': result['active_users'],
            'postsToday': result['posts_today'],
            'commentsToday': result['comments_today']
        }
    
    def _encode_cursor(self, id: int) -> str:
        """Encode cursor for pagination"""
        import base64
        return base64.b64encode(str(id).encode()).decode()
    
    def _decode_cursor(self, cursor: str) -> int:
        """Decode cursor for pagination"""
        import base64
        return int(base64.b64decode(cursor.encode()).decode())


class MutationResolvers:
    """Mutation resolvers"""
    
    def __init__(self, loaders: DataLoaderRegistry, db_session):
        self.loaders = loaders
        self.db = db_session
    
    async def createPost(self, parent, info, input: Dict) -> Dict:
        """Create a new post"""
        user = info.context.get('user')
        if not user:
            raise GraphQLError("Authentication required")
        
        query = """
            INSERT INTO posts (title, content, published, author_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        now = datetime.utcnow()
        post = await self.db.fetch_one(
            query,
            input['title'],
            input['content'],
            input.get('published', False),
            user['id'],
            now,
            now
        )
        
        # Handle tags
        if 'tagIds' in input:
            for tag_id in input['tagIds']:
                await self.db.execute(
                    "INSERT INTO post_tags (post_id, tag_id) VALUES (%s, %s)",
                    post['id'],
                    int(tag_id)
                )
        
        # Clear relevant caches
        self.loaders.get('posts_by_user').clear(user['id'])
        
        return post
    
    async def updatePost(self, parent, info, id: str, input: Dict) -> Dict:
        """Update a post"""
        user = info.context.get('user')
        if not user:
            raise GraphQLError("Authentication required")
        
        # Check ownership
        post = await self.loaders.get('post').load(int(id))
        if not post or post['author_id'] != user['id']:
            raise GraphQLError("Post not found or unauthorized")
        
        # Build update query
        updates = []
        params = []
        
        if 'title' in input:
            updates.append("title = %s")
            params.append(input['title'])
        
        if 'content' in input:
            updates.append("content = %s")
            params.append(input['content'])
        
        if 'published' in input:
            updates.append("published = %s")
            params.append(input['published'])
        
        updates.append("updated_at = %s")
        params.append(datetime.utcnow())
        
        params.append(int(id))
        
        query = f"""
            UPDATE posts
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING *
        """
        
        updated_post = await self.db.fetch_one(query, *params)
        
        # Clear cache
        self.loaders.get('post').clear(int(id))
        self.loaders.get('posts_by_user').clear(user['id'])
        
        return updated_post
    
    async def deletePost(self, parent, info, id: str) -> bool:
        """Delete a post"""
        user = info.context.get('user')
        if not user:
            raise GraphQLError("Authentication required")
        
        # Check ownership
        post = await self.loaders.get('post').load(int(id))
        if not post or post['author_id'] != user['id']:
            raise GraphQLError("Post not found or unauthorized")
        
        # Delete post (cascades to comments and tags)
        await self.db.execute("DELETE FROM posts WHERE id = %s", int(id))
        
        # Clear caches
        self.loaders.get('post').clear(int(id))
        self.loaders.get('posts_by_user').clear(user['id'])
        self.loaders.get('comments_by_post').clear(int(id))
        
        return True
    
    async def createComment(self, parent, info, input: Dict) -> Dict:
        """Create a comment"""
        user = info.context.get('user')
        if not user:
            raise GraphQLError("Authentication required")
        
        # Verify post exists
        post = await self.loaders.get('post').load(int(input['postId']))
        if not post:
            raise GraphQLError("Post not found")
        
        # Verify parent comment if provided
        if input.get('parentId'):
            parent_comment = await self.loaders.get('comment').load(int(input['parentId']))
            if not parent_comment or parent_comment['post_id'] != int(input['postId']):
                raise GraphQLError("Invalid parent comment")
        
        query = """
            INSERT INTO comments (content, post_id, author_id, parent_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        
        now = datetime.utcnow()
        comment = await self.db.fetch_one(
            query,
            input['content'],
            int(input['postId']),
            user['id'],
            int(input['parentId']) if input.get('parentId') else None,
            now,
            now
        )
        
        # Clear cache
        self.loaders.get('comments_by_post').clear(int(input['postId']))
        
        return comment


class SubscriptionResolvers:
    """Subscription resolvers"""
    
    def __init__(self, pubsub):
        self.pubsub = pubsub
    
    async def postAdded(self, parent, info, authorId: Optional[str] = None):
        """Subscribe to new posts"""
        channel = f"post:added:{authorId}" if authorId else "post:added:*"
        
        async for post in self.pubsub.subscribe(channel):
            yield post
    
    async def commentAdded(self, parent, info, postId: str):
        """Subscribe to new comments on a post"""
        async for comment in self.pubsub.subscribe(f"comment:added:{postId}"):
            yield comment
    
    async def statisticsUpdated(self, parent, info):
        """Subscribe to statistics updates"""
        async for stats in self.pubsub.subscribe("statistics:updated"):
            yield stats


class FieldResolvers:
    """Field-level resolvers for nested data"""
    
    def __init__(self, loaders: DataLoaderRegistry):
        self.loaders = loaders
    
    async def user_posts(self, parent: Dict, info) -> List[Dict]:
        """Resolve posts for a user"""
        return await self.loaders.get('posts_by_user').load(parent['id'])
    
    async def user_comments(self, parent: Dict, info) -> List[Dict]:
        """Resolve comments for a user"""
        # This would use a comments_by_user loader
        return []
    
    async def post_author(self, parent: Dict, info) -> Optional[Dict]:
        """Resolve author for a post"""
        return await self.loaders.get('user').load(parent['author_id'])
    
    async def post_comments(self, parent: Dict, info) -> List[Dict]:
        """Resolve comments for a post"""
        return await self.loaders.get('comments_by_post').load(parent['id'])
    
    async def post_tags(self, parent: Dict, info) -> List[Dict]:
        """Resolve tags for a post"""
        return await self.loaders.get('tags_by_post').load(parent['id'])
    
    async def comment_author(self, parent: Dict, info) -> Optional[Dict]:
        """Resolve author for a comment"""
        return await self.loaders.get('user').load(parent['author_id'])
    
    async def comment_post(self, parent: Dict, info) -> Optional[Dict]:
        """Resolve post for a comment"""
        return await self.loaders.get('post').load(parent['post_id'])
    
    async def comment_parent(self, parent: Dict, info) -> Optional[Dict]:
        """Resolve parent comment"""
        if parent.get('parent_id'):
            return await self.loaders.get('comment').load(parent['parent_id'])
        return None