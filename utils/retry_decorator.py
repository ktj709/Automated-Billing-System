"""
Retry decorator and error handling utilities
"""
import time
import functools
import logging
from typing import Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
    
    Example:
        @retry(max_attempts=3, delay=1, backoff=2)
        def api_call():
            return requests.get('https://api.example.com')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {str(e)}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {str(e)}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(f"on_retry callback failed: {callback_error}")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def safe_execute(func: Callable, default=None, log_errors: bool = True):
    """
    Execute a function safely, returning default value on error
    
    Args:
        func: Function to execute
        default: Value to return on error
        log_errors: Whether to log errors
    
    Returns:
        Function result or default value on error
    
    Example:
        result = safe_execute(lambda: risky_operation(), default={})
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__ if hasattr(func, '__name__') else 'function'}: {str(e)}")
        return default


class CircuitBreaker:
    """
    Circuit breaker pattern implementation
    
    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Too many failures, requests fail immediately
        - HALF_OPEN: Testing if service recovered
    
    Example:
        breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        
        @breaker
        def api_call():
            return requests.get('https://api.example.com')
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (HALF_OPEN)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'CLOSED'
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time >= self.timeout:
                    self.state = 'HALF_OPEN'
                    logger.info(f"Circuit breaker for {func.__name__} entering HALF_OPEN state")
                else:
                    raise Exception(
                        f"Circuit breaker OPEN for {func.__name__}. "
                        f"Service unavailable. Try again in {self.timeout - (time.time() - self.last_failure_time):.0f}s"
                    )
            
            try:
                result = func(*args, **kwargs)
                
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failures = 0
                    logger.info(f"Circuit breaker for {func.__name__} recovered to CLOSED state")
                
                return result
                
            except Exception as e:
                self.failures += 1
                self.last_failure_time = time.time()
                
                if self.failures >= self.failure_threshold:
                    self.state = 'OPEN'
                    logger.error(
                        f"Circuit breaker OPEN for {func.__name__} after {self.failures} failures"
                    )
                
                raise
        
        return wrapper
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.failures = 0
        self.state = 'CLOSED'
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")


class ErrorContext:
    """
    Context manager for safe error handling
    
    Example:
        with ErrorContext("Database operation", default_return=None) as ctx:
            result = db.query()
            ctx.set_result(result)
        
        if ctx.success:
            print(f"Result: {ctx.result}")
        else:
            print(f"Error: {ctx.error}")
    """
    
    def __init__(self, operation_name: str, default_return=None, raise_on_error: bool = False):
        self.operation_name = operation_name
        self.default_return = default_return
        self.raise_on_error = raise_on_error
        self.result = None
        self.error = None
        self.success = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            self.success = False
            logger.error(f"Error in {self.operation_name}: {exc_val}")
            
            if self.raise_on_error:
                return False  # Re-raise exception
            
            self.result = self.default_return
            return True  # Suppress exception
        
        self.success = True
        return True
    
    def set_result(self, value):
        """Set the result value"""
        self.result = value


def handle_api_errors(func: Callable) -> Callable:
    """
    Decorator for Flask API endpoints to handle errors gracefully
    
    Returns JSON error responses with appropriate HTTP status codes
    
    Example:
        @app.route('/api/data')
        @handle_api_errors
        def get_data():
            return jsonify(data)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            from flask import jsonify
            return jsonify({"error": "Invalid input", "message": str(e)}), 400
        except PermissionError as e:
            logger.warning(f"Permission error in {func.__name__}: {e}")
            from flask import jsonify
            return jsonify({"error": "Forbidden", "message": str(e)}), 403
        except FileNotFoundError as e:
            logger.warning(f"Not found in {func.__name__}: {e}")
            from flask import jsonify
            return jsonify({"error": "Not found", "message": str(e)}), 404
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            from flask import jsonify
            return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500
    
    return wrapper
