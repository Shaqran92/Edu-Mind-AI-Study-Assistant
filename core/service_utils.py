"""
Enhanced Utilities for Core Services
Additional utility functions for response caching, analytics, and performance.
"""

from typing import Dict, Any, Callable, TypeVar, Optional, List
from functools import wraps
from datetime import datetime
import time

from utils.logger import get_logger

logger = get_logger("service_utils")

T = TypeVar('T')


class ServiceIntegration:
    """Helper class for integrating services into operations."""
    
    @staticmethod
    def with_cache(func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator to automatically cache function results.
        
        Usage:
            @ServiceIntegration.with_cache
            def expensive_operation(input_data):
                return result
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            from core.services.response_cache import get_cache
            
            cache = get_cache()
            
            # Generate cache key from function and arguments
            cache_key_parts = [func.__name__]
            for arg in args:
                cache_key_parts.append(str(arg)[:100])  # Limit size
            for key, value in sorted(kwargs.items()):
                cache_key_parts.append(f"{key}={str(value)[:50]}")
            
            cache_key = "|".join(cache_key_parts)
            
            # Check cache
            cached = cache.get("internal", func.__name__, cache_key)
            if cached:
                logger.debug(f"Cache hit: {func.__name__}")
                return cached
            
            # Execute and cache
            result = func(*args, **kwargs)
            cache.set("internal", func.__name__, cache_key, result)
            return result
        
        return wrapper
    
    @staticmethod
    def with_analytics(operation_type: str) -> Callable:
        """
        Decorator to track operations in analytics.
        
        Usage:
            @ServiceIntegration.with_analytics("content_processing")
            def process_content(data):
                return processed
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                from core.services.advanced_analytics import get_analytics
                
                analytics = get_analytics()
                
                # Execute operation
                result = func(*args, **kwargs)
                
                # Record based on type
                if operation_type == "content_processing":
                    content_size = len(str(result)) if result else 0
                    analytics.record_content_processed(content_size)
                elif operation_type == "summary":
                    analytics.record_summary_created()
                elif operation_type == "flashcard":
                    count = len(result) if isinstance(result, list) else 1
                    analytics.record_flashcards_created(count)
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def with_performance_tracking(operation_name: str) -> Callable:
        """
        Decorator to track operation performance.
        
        Usage:
            @ServiceIntegration.with_performance_tracking("ai_summarization")
            def summarize(text):
                return summary
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                from core.services.performance import get_performance_monitor
                
                monitor = get_performance_monitor()
                
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    monitor.record_operation(operation_name, duration_ms)
            
            return wrapper
        return decorator


class AnalyticsHelper:
    """Helper functions for analytics."""
    
    @staticmethod
    def get_current_stats() -> Dict[str, Any]:
        """Get current session statistics."""
        from core.services.advanced_analytics import get_analytics
        
        analytics = get_analytics()
        
        if not analytics.current_session:
            return {}
        
        session = analytics.current_session
        return {
            "duration_minutes": session.duration_minutes,
            "content_processed": session.content_processed,
            "summaries_created": session.summaries_created,
            "flashcards_created": session.flashcards_created,
            "quizzes_taken": session.quizzes_taken,
            "average_score": sum(session.quiz_scores) / len(session.quiz_scores) if session.quiz_scores else 0,
        }
    
    @staticmethod
    def get_improvement_metrics() -> Dict[str, Any]:
        """Get learning improvement metrics."""
        from core.services.advanced_analytics import get_analytics
        
        analytics = get_analytics()
        
        current_stats = analytics.get_session_stats(days=7)
        prev_stats = analytics.get_session_stats(days=14)
        
        # Calculate improvements
        improvements = {}
        
        if current_stats.get("total_sessions", 0) > 0 and prev_stats.get("total_sessions", 0) > 0:
            current_avg = current_stats.get("average_quiz_score", 0)
            prev_avg = prev_stats.get("average_quiz_score", 0)
            
            if prev_avg > 0:
                improvement_pct = ((current_avg - prev_avg) / prev_avg) * 100
                improvements["score_improvement_pct"] = improvement_pct
        
        return improvements
    
    @staticmethod
    def get_recommendations() -> List[str]:
        """Get personalized learning recommendations."""
        from core.services.advanced_analytics import get_analytics
        
        analytics = get_analytics()
        return analytics.get_recommendations()


class CacheHelper:
    """Helper functions for response caching."""
    
    @staticmethod
    def get_cache_status() -> Dict[str, Any]:
        """Get current cache status."""
        from core.services.response_cache import get_cache
        
        cache = get_cache()
        return cache.get_stats()
    
    @staticmethod
    def clear_cache() -> bool:
        """Clear all cached responses."""
        try:
            from core.services.response_cache import get_cache
            
            cache = get_cache()
            cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    @staticmethod
    def optimize_cache() -> Dict[str, Any]:
        """Optimize cache by removing expired entries."""
        from core.services.response_cache import get_cache
        
        cache = get_cache()
        before = len(cache.index)
        
        # Remove expired entries
        expired_keys = []
        for key, entry in cache.index.items():
            created_time = datetime.fromisoformat(entry.get("created", ""))
            from datetime import timedelta
            if datetime.now() - created_time > timedelta(seconds=cache.ttl_seconds):
                expired_keys.append(key)
        
        for key in expired_keys:
            cache._delete_cache_file(key)
            if key in cache.index:
                del cache.index[key]
        
        cache._save_index()
        
        return {
            "entries_before": before,
            "entries_after": len(cache.index),
            "entries_removed": len(expired_keys),
        }


class PerformanceHelper:
    """Helper functions for performance optimization."""
    
    @staticmethod
    def get_performance_report() -> Dict[str, Any]:
        """Get detailed performance report."""
        from core.services.performance import get_performance_monitor
        
        monitor = get_performance_monitor()
        
        return {
            "total_operations": sum(len(times) for times in monitor.operation_times.values()),
            "operations_tracked": list(monitor.operation_times.keys()),
            "slow_operations": monitor.get_slow_operations(threshold_ms=1000),
        }
    
    @staticmethod
    def get_operation_stats(operation_name: str) -> Dict[str, float]:
        """Get statistics for a specific operation."""
        from core.services.performance import get_performance_monitor
        
        monitor = get_performance_monitor()
        return monitor.get_stats(operation_name)
    
    @staticmethod
    def submit_async_task(func: Callable, *args, **kwargs):
        """Submit a task for async execution."""
        from core.services.performance import get_task_pool
        
        pool = get_task_pool()
        return pool.submit_task(func, *args, **kwargs)


class SessionHelper:
    """Helper functions for session management."""
    
    @staticmethod
    def start_new_session(subject: str, ai_provider: str = "offline") -> str:
        """Start a new study session."""
        from core.services.session_manager import get_session_manager
        from core.services.advanced_analytics import get_analytics
        
        manager = get_session_manager()
        analytics = get_analytics()
        
        # Create session in manager
        session = manager.create_session()
        session.current_subject = subject
        session.ai_provider = ai_provider
        manager.save_session()
        
        # Start analytics session
        analytics.start_session(subject, ai_provider)
        
        return session.session_id
    
    @staticmethod
    def end_current_session() -> Dict[str, Any]:
        """End the current study session."""
        from core.services.session_manager import get_session_manager
        from core.services.advanced_analytics import get_analytics
        
        manager = get_session_manager()
        analytics = get_analytics()
        
        # End analytics session
        analytics_summary = analytics.end_session()
        
        # Save session in manager
        manager.save_session()
        
        return analytics_summary
    
    @staticmethod
    def get_available_sessions() -> List[Dict[str, Any]]:
        """Get list of available sessions."""
        from core.services.session_manager import get_session_manager
        
        manager = get_session_manager()
        return manager.list_sessions()


# Convenience functions for common operations

def track_analytics(operation_type: str):
    """Convenient decorator for analytics tracking."""
    return ServiceIntegration.with_analytics(operation_type)


def track_performance(operation_name: str):
    """Convenient decorator for performance tracking."""
    return ServiceIntegration.with_performance_tracking(operation_name)


def cache_result(func: Callable[..., T]) -> Callable[..., T]:
    """Convenient decorator for caching results."""
    return ServiceIntegration.with_cache(func)
