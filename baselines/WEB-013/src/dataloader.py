"""
DataLoader implementation to prevent N+1 queries

Implements batching and caching for efficient data fetching.
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from collections import defaultdict
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta


T = TypeVar('T')
K = TypeVar('K')


class DataLoader(Generic[K, T]):
    """Generic DataLoader for batching and caching database queries"""
    
    def __init__(
        self,
        batch_fn: Callable[[List[K]], List[Optional[T]]],
        cache: bool = True,
        cache_ttl: int = 60,
        max_batch_size: int = 100
    ):
        self.batch_fn = batch_fn
        self.cache_enabled = cache
        self.cache_ttl = cache_ttl
        self.max_batch_size = max_batch_size
        
        self._cache: Dict[K, T] = {}
        self._cache_timestamps: Dict[K, datetime] = {}
        self._queue: List[tuple[K, asyncio.Future]] = []
        self._batch_scheduled = False
    
    async def load(self, key: K) -> Optional[T]:
        """Load a single item by key"""
        # Check cache first
        if self.cache_enabled and key in self._cache:
            if self._is_cache_valid(key):
                return self._cache[key]
            else:
                del self._cache[key]
                del self._cache_timestamps[key]
        
        # Create future for this request
        future = asyncio.get_event_loop().create_future()
        self._queue.append((key, future))
        
        # Schedule batch if not already scheduled
        if not self._batch_scheduled:
            self._batch_scheduled = True
            asyncio.create_task(self._dispatch_batch())
        
        return await future
    
    async def load_many(self, keys: List[K]) -> List[Optional[T]]:
        """Load multiple items by keys"""
        results = await asyncio.gather(*[self.load(key) for key in keys])
        return results
    
    async def prime(self, key: K, value: T):
        """Prime the cache with a known value"""
        if self.cache_enabled:
            self._cache[key] = value
            self._cache_timestamps[key] = datetime.utcnow()
    
    def clear(self, key: Optional[K] = None):
        """Clear cache for specific key or all keys"""
        if key is not None:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
    
    async def _dispatch_batch(self):
        """Dispatch a batch of queries"""
        await asyncio.sleep(0)  # Yield to allow more requests to queue
        
        if not self._queue:
            self._batch_scheduled = False
            return
        
        # Process queue in batches
        while self._queue:
            # Take up to max_batch_size items
            batch = self._queue[:self.max_batch_size]
            self._queue = self._queue[self.max_batch_size:]
            
            keys = [key for key, _ in batch]
            futures = [future for _, future in batch]
            
            try:
                # Call batch function
                results = await self.batch_fn(keys)
                
                # Ensure results match keys length
                if len(results) != len(keys):
                    raise ValueError(f"Batch function returned {len(results)} results for {len(keys)} keys")
                
                # Cache and resolve futures
                for key, result, future in zip(keys, results, futures):
                    if self.cache_enabled and result is not None:
                        self._cache[key] = result
                        self._cache_timestamps[key] = datetime.utcnow()
                    
                    future.set_result(result)
                    
            except Exception as e:
                # Reject all futures on error
                for future in futures:
                    future.set_exception(e)
        
        self._batch_scheduled = False
    
    def _is_cache_valid(self, key: K) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache_timestamps:
            return False
        
        age = (datetime.utcnow() - self._cache_timestamps[key]).total_seconds()
        return age < self.cache_ttl


class UserLoader(DataLoader):
    """DataLoader for User entities"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        super().__init__(
            batch_fn=self._batch_load_users,
            cache=True,
            cache_ttl=60
        )
    
    async def _batch_load_users(self, user_ids: List[int]) -> List[Optional[Dict]]:
        """Batch load users from database"""
        # Simulate database query
        query = """
            SELECT * FROM users
            WHERE id = ANY(%s)
        """
        
        # This would be actual database query
        users = await self.db_session.fetch_all(query, user_ids)
        
        # Create mapping
        user_map = {user['id']: user for user in users}
        
        # Return in same order as requested
        return [user_map.get(user_id) for user_id in user_ids]


class PostLoader(DataLoader):
    """DataLoader for Post entities"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        super().__init__(
            batch_fn=self._batch_load_posts,
            cache=True,
            cache_ttl=30
        )
    
    async def _batch_load_posts(self, post_ids: List[int]) -> List[Optional[Dict]]:
        """Batch load posts from database"""
        query = """
            SELECT * FROM posts
            WHERE id = ANY(%s)
        """
        
        posts = await self.db_session.fetch_all(query, post_ids)
        post_map = {post['id']: post for post in posts}
        
        return [post_map.get(post_id) for post_id in post_ids]


class CommentLoader(DataLoader):
    """DataLoader for Comment entities"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        super().__init__(
            batch_fn=self._batch_load_comments,
            cache=True,
            cache_ttl=30
        )
    
    async def _batch_load_comments(self, comment_ids: List[int]) -> List[Optional[Dict]]:
        """Batch load comments from database"""
        query = """
            SELECT * FROM comments
            WHERE id = ANY(%s)
        """
        
        comments = await self.db_session.fetch_all(query, comment_ids)
        comment_map = {comment['id']: comment for comment in comments}
        
        return [comment_map.get(comment_id) for comment_id in comment_ids]


class PostsByUserLoader(DataLoader):
    """DataLoader for loading posts by user ID"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        super().__init__(
            batch_fn=self._batch_load_posts_by_user,
            cache=True,
            cache_ttl=30
        )
    
    async def _batch_load_posts_by_user(self, user_ids: List[int]) -> List[List[Dict]]:
        """Batch load posts grouped by user"""
        query = """
            SELECT * FROM posts
            WHERE author_id = ANY(%s)
            ORDER BY created_at DESC
        """
        
        posts = await self.db_session.fetch_all(query, user_ids)
        
        # Group by user_id
        posts_by_user = defaultdict(list)
        for post in posts:
            posts_by_user[post['author_id']].append(post)
        
        # Return in same order as requested
        return [posts_by_user.get(user_id, []) for user_id in user_ids]


class CommentsByPostLoader(DataLoader):
    """DataLoader for loading comments by post ID"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        super().__init__(
            batch_fn=self._batch_load_comments_by_post,
            cache=True,
            cache_ttl=30
        )
    
    async def _batch_load_comments_by_post(self, post_ids: List[int]) -> List[List[Dict]]:
        """Batch load comments grouped by post"""
        query = """
            SELECT * FROM comments
            WHERE post_id = ANY(%s)
            ORDER BY created_at ASC
        """
        
        comments = await self.db_session.fetch_all(query, post_ids)
        
        # Group by post_id
        comments_by_post = defaultdict(list)
        for comment in comments:
            comments_by_post[comment['post_id']].append(comment)
        
        return [comments_by_post.get(post_id, []) for post_id in post_ids]


class TagsByPostLoader(DataLoader):
    """DataLoader for loading tags by post ID"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        super().__init__(
            batch_fn=self._batch_load_tags_by_post,
            cache=True,
            cache_ttl=60
        )
    
    async def _batch_load_tags_by_post(self, post_ids: List[int]) -> List[List[Dict]]:
        """Batch load tags for posts"""
        query = """
            SELECT pt.post_id, t.*
            FROM post_tags pt
            JOIN tags t ON pt.tag_id = t.id
            WHERE pt.post_id = ANY(%s)
        """
        
        results = await self.db_session.fetch_all(query, post_ids)
        
        # Group by post_id
        tags_by_post = defaultdict(list)
        for row in results:
            post_id = row['post_id']
            tag = {k: v for k, v in row.items() if k != 'post_id'}
            tags_by_post[post_id].append(tag)
        
        return [tags_by_post.get(post_id, []) for post_id in post_ids]


class DataLoaderRegistry:
    """Registry for all DataLoader instances"""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self._loaders = {}
        self._initialize_loaders()
    
    def _initialize_loaders(self):
        """Initialize all DataLoader instances"""
        self._loaders['user'] = UserLoader(self.db_session)
        self._loaders['post'] = PostLoader(self.db_session)
        self._loaders['comment'] = CommentLoader(self.db_session)
        self._loaders['posts_by_user'] = PostsByUserLoader(self.db_session)
        self._loaders['comments_by_post'] = CommentsByPostLoader(self.db_session)
        self._loaders['tags_by_post'] = TagsByPostLoader(self.db_session)
    
    def get(self, name: str) -> DataLoader:
        """Get a DataLoader by name"""
        if name not in self._loaders:
            raise ValueError(f"DataLoader '{name}' not found")
        return self._loaders[name]
    
    def clear_all(self):
        """Clear all DataLoader caches"""
        for loader in self._loaders.values():
            loader.clear()
    
    def clear(self, name: str, key: Optional[Any] = None):
        """Clear specific DataLoader cache"""
        if name in self._loaders:
            self._loaders[name].clear(key)