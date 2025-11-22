"""
Centralized Logging Utility Module
Provides structured logging with console and file output, log rotation, and performance tracking
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from functools import wraps
from typing import Optional, Any, Callable
import time


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for other handlers
        record.levelname = levelname
        
        return formatted


class LogContext:
    """Context manager for tracking operation blocks"""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
        msg = f"Starting: {self.operation}"
        if context_str:
            msg += f" | {context_str}"
        self.logger.info(msg)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation} | Duration: {duration:.2f}s")
        else:
            self.logger.error(
                f"Failed: {self.operation} | Duration: {duration:.2f}s | "
                f"Error: {exc_type.__name__}: {exc_val}"
            )
        return False  # Don't suppress exceptions


def setup_logger(
    name: str,
    log_dir: Optional[Path] = None,
    log_level: str = "DEBUG",
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and file handlers
    
    Args:
        name: Logger name (typically module name)
        log_dir: Directory for log files (default: logs/)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Enable console output
        file_output: Enable file output
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler with colors
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console shows INFO and above
        console_formatter = ColoredFormatter(
            fmt='%(levelname)s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        # Create log directory
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create rotating file handler
        log_file = log_dir / f"{name.replace('.', '_')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=30,  # Keep 30 backup files
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File captures everything
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Logger name (use __name__ from calling module)
        
    Returns:
        Configured logger instance
    """
    # Import here to avoid circular dependency
    try:
        from config.settings import settings
        log_level = getattr(settings, 'LOG_LEVEL', 'DEBUG')
        log_dir = getattr(settings, 'LOG_DIR', None)
    except ImportError:
        log_level = 'DEBUG'
        log_dir = None
    
    return setup_logger(name, log_dir=log_dir, log_level=log_level)


def log_execution_time(func: Optional[Callable] = None, *, log_args: bool = False):
    """
    Decorator to log function execution time
    
    Args:
        func: Function to decorate
        log_args: Whether to log function arguments
        
    Usage:
        @log_execution_time
        def my_function():
            pass
            
        @log_execution_time(log_args=True)
        def my_function(arg1, arg2):
            pass
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(f.__module__)
            
            # Build log message
            func_name = f.__name__
            msg_parts = [f"Executing: {func_name}"]
            
            if log_args and (args or kwargs):
                args_str = ", ".join(repr(a) for a in args[:3])  # Limit to first 3 args
                if len(args) > 3:
                    args_str += ", ..."
                if kwargs:
                    kwargs_str = ", ".join(f"{k}={v!r}" for k, v in list(kwargs.items())[:3])
                    if len(kwargs) > 3:
                        kwargs_str += ", ..."
                    args_str = f"{args_str}, {kwargs_str}" if args_str else kwargs_str
                msg_parts.append(f"Args: ({args_str})")
            
            logger.debug(" | ".join(msg_parts))
            
            # Execute function and measure time
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"Completed: {func_name} | Duration: {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Failed: {func_name} | Duration: {duration:.3f}s | "
                    f"Error: {type(e).__name__}: {str(e)}"
                )
                raise
        
        return wrapper
    
    # Handle both @log_execution_time and @log_execution_time()
    if func is None:
        return decorator
    else:
        return decorator(func)


def log_exception(logger: logging.Logger, exc: Exception, context: str = ""):
    """
    Log an exception with full context
    
    Args:
        logger: Logger instance
        exc: Exception to log
        context: Additional context string
    """
    msg = f"Exception occurred"
    if context:
        msg += f" | Context: {context}"
    msg += f" | Type: {type(exc).__name__} | Message: {str(exc)}"
    logger.error(msg, exc_info=True)


# Create a main application logger
app_logger = get_logger("ragg")


# Example usage and testing
if __name__ == "__main__":
    # Test the logging system
    test_logger = get_logger("test_module")
    
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    
    # Test context manager
    with LogContext(test_logger, "Test Operation", param1="value1", param2=123):
        time.sleep(0.1)
        test_logger.info("Doing some work...")
    
    # Test decorator
    @log_execution_time
    def test_function(x, y):
        time.sleep(0.1)
        return x + y
    
    result = test_function(5, 10)
    test_logger.info(f"Result: {result}")
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception as e:
        log_exception(test_logger, e, context="Testing exception logging")
    
    print("\nLogging test completed. Check logs/ directory for log files.")
