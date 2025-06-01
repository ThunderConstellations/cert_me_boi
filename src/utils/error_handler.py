from typing import Any, Callable, Optional, Type, TypeVar, cast
import functools
import time
from .logger import logger

class AutomationError(Exception):
    """Base exception for automation errors"""
    pass

class MonitorError(AutomationError):
    """Exception for video monitoring errors"""
    pass

F = TypeVar('F', bound=Callable[..., Any])

def retry_on_error(max_attempts: int = 3, 
                  retry_delay: float = 1.0,
                  allowed_exceptions: Optional[tuple[Type[Exception], ...]] = None) -> Callable[[F], F]:
    """Decorator to retry function on error
    
    Args:
        max_attempts: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        allowed_exceptions: Tuple of exception types to retry on
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            last_error = None
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    # Check if exception is allowed
                    if allowed_exceptions and not isinstance(e, allowed_exceptions):
                        raise
                    
                    # Log retry attempt
                    logger.warning(
                        f"Retry attempt {attempt}/{max_attempts}",
                        module="error_handler",
                        context={
                            "function": getattr(func, "__name__", "unknown"),
                            "error": str(e)
                        }
                    )
                    
                    # Wait before retrying
                    if attempt < max_attempts:
                        time.sleep(retry_delay * attempt)
                    
                    attempt += 1
            
            # Log max attempts reached
            logger.error(
                f"Max retry attempts ({max_attempts}) reached",
                module="error_handler",
                context={
                    "function": getattr(func, "__name__", "unknown"),
                    "error": str(last_error)
                }
            )
            
            raise last_error
            
        return cast(F, wrapper)
    return decorator

def safe_monitor_operation(func: F) -> F:
    """Decorator to handle monitor operation errors
    
    Args:
        func: Function to decorate
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        operation = getattr(func, "__name__", "unknown")
        start_time = time.time()
        
        try:
            # Log operation start
            logger.debug(
                "Starting monitor operation",
                module="error_handler",
                context={
                    "operation": operation,
                    "args": str(args),
                    "kwargs": str(kwargs)
                }
            )
            
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log successful completion
            logger.debug(
                "Monitor operation completed",
                module="error_handler",
                context={
                    "operation": operation,
                    "execution_time": execution_time,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Convert OpenCV errors to MonitorError
            if e.__class__.__module__ == 'cv2':
                error_msg = f"OpenCV error in {operation}: {str(e)}"
                logger.error(
                    "Monitor operation failed",
                    module="error_handler",
                    context={
                        "operation": operation,
                        "execution_time": execution_time,
                        "error": error_msg
                    }
                )
                raise MonitorError(error_msg)
            
            # Log other errors
            logger.error(
                "Monitor operation failed",
                module="error_handler",
                context={
                    "operation": operation,
                    "execution_time": execution_time,
                    "error": str(e)
                }
            )
            raise
            
    return cast(F, wrapper)

def handle_automation_error(func: F) -> F:
    """Decorator to handle automation errors
    
    Args:
        func: Function to decorate
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except AutomationError:
            # Log and re-raise automation errors
            logger.error(
                "Automation error",
                module="error_handler",
                context={
                    "function": getattr(func, "__name__", "unknown"),
                    "error": str(e)
                }
            )
            raise
        except Exception as e:
            # Convert other errors to AutomationError
            error_msg = f"Unexpected error in {getattr(func, '__name__', 'unknown')}: {str(e)}"
            logger.error(
                "Unexpected error",
                module="error_handler",
                context={
                    "function": getattr(func, "__name__", "unknown"),
                    "error": str(e)
                }
            )
            raise AutomationError(error_msg)
            
    return cast(F, wrapper)