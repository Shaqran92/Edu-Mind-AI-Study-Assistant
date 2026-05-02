"""
Performance Optimization Module
Provides utilities for improving application performance and responsiveness.
"""

import time
from typing import Callable, Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock, Event
from utils.logger import get_logger

logger = get_logger("performance")


class PerformanceMonitor:
    """
    Monitors and optimizes application performance.
    
    Features:
    - Operation timing
    - Performance profiling
    - Bottleneck identification
    - Performance alerts
    """
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = {}
        self.lock = Lock()
    
    def record_operation(self, operation_name: str, duration_ms: float) -> None:
        """
        Record an operation's execution time.
        
        Args:
            operation_name: Name of the operation
            duration_ms: Duration in milliseconds
        """
        with self.lock:
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
            
            self.operation_times[operation_name].append(duration_ms)
            
            # Keep only last 100 measurements
            if len(self.operation_times[operation_name]) > 100:
                self.operation_times[operation_name].pop(0)
            
            # Alert if slow
            if duration_ms > 5000:  # > 5 seconds
                logger.warning(f"Slow operation detected: {operation_name} took {duration_ms:.2f}ms")
    
    def get_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        with self.lock:
            if operation_name not in self.operation_times:
                return {}
            
            times = self.operation_times[operation_name]
            if not times:
                return {}
            
            return {
                "count": len(times),
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / len(times),
                "last": times[-1],
            }
    
    def get_slow_operations(self, threshold_ms: float = 1000) -> List[tuple]:
        """
        Get operations that regularly exceed a performance threshold.
        
        Args:
            threshold_ms: Performance threshold in milliseconds
        
        Returns:
            List of (operation_name, avg_time) tuples
        """
        slow_ops = []
        with self.lock:
            for op_name, times in self.operation_times.items():
                if times:
                    avg_time = sum(times) / len(times)
                    if avg_time > threshold_ms:
                        slow_ops.append((op_name, avg_time))
        
        return sorted(slow_ops, key=lambda x: x[1], reverse=True)


class BatchProcessor:
    """
    Processes items in batches for better performance.
    
    Useful for:
    - Batch processing AI requests
    - Database operations
    - File I/O
    """
    
    def __init__(self, batch_size: int = 10, max_wait_ms: int = 1000):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Number of items per batch
            max_wait_ms: Maximum wait time before processing partial batch
        """
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.batch: List[Any] = []
        self.lock = Lock()
        self.ready_event = Event()
    
    def add_item(self, item: Any) -> bool:
        """
        Add an item to the batch.
        
        Args:
            item: Item to add
        
        Returns:
            True if batch is ready for processing
        """
        with self.lock:
            self.batch.append(item)
            is_ready = len(self.batch) >= self.batch_size
            if is_ready:
                self.ready_event.set()
            return is_ready
    
    def get_batch(self, timeout_ms: Optional[float] = None) -> List[Any]:
        """Get the current batch."""
        with self.lock:
            batch = self.batch.copy()
            self.batch = []
            self.ready_event.clear()
            return batch
    
    def is_ready(self) -> bool:
        """Check if batch is ready for processing."""
        with self.lock:
            return len(self.batch) >= self.batch_size


class AsyncTaskPool:
    """
    Thread pool for async processing.
    
    Manages background tasks without blocking the UI.
    """
    
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks: List[Future] = []
        self.lock = Lock()
    
    def submit_task(self, func: Callable, *args, **kwargs) -> Future:
        """
        Submit a task for async execution.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Future object
        """
        future = self.executor.submit(func, *args, **kwargs)
        
        with self.lock:
            self.active_tasks.append(future)
            # Clean up completed tasks
            self.active_tasks = [t for t in self.active_tasks if not t.done()]
        
        return future
    
    def wait_all(self, timeout_seconds: float = 30) -> bool:
        """
        Wait for all active tasks to complete.
        
        Args:
            timeout_seconds: Maximum wait time
        
        Returns:
            True if all completed, False if timeout
        """
        try:
            with self.lock:
                tasks_to_wait = self.active_tasks.copy()
            
            for task in tasks_to_wait:
                task.result(timeout=timeout_seconds)
            
            return True
        except Exception:
            return False
    
    def shutdown(self) -> None:
        """Shutdown the task pool."""
        self.executor.shutdown(wait=True)


def timed_operation(operation_name: str, monitor: Optional[PerformanceMonitor] = None) -> Callable:
    """
    Decorator for timing operations.
    
    Args:
        operation_name: Name of the operation
        monitor: Performance monitor instance
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                if monitor:
                    monitor.record_operation(operation_name, duration_ms)
                logger.debug(f"{operation_name} took {duration_ms:.2f}ms")
        return wrapper
    return decorator


# Global instances
_monitor_instance = None
_task_pool_instance = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PerformanceMonitor()
    return _monitor_instance


def get_task_pool() -> AsyncTaskPool:
    """Get the global task pool."""
    global _task_pool_instance
    if _task_pool_instance is None:
        _task_pool_instance = AsyncTaskPool()
    return _task_pool_instance
