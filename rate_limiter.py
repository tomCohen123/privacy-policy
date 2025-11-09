"""
Token-bucket rate limiter implementation for high-traffic web services.

This module provides a thread-safe token-bucket rate limiter that prevents
abuse of expensive operations by limiting the rate of requests.
"""

import threading
import time


class TokenBucketRateLimiter:
    """
    A thread-safe token-bucket rate limiter.
    
    The rate limiter allows up to N requests per second, with burst capacity
    up to N requests at once. Tokens refill at a rate of N tokens per second.
    
    Args:
        rate: Maximum number of requests per second (tokens per second)
        capacity: Maximum burst capacity (defaults to rate if not specified)
    
    Example:
        >>> limiter = TokenBucketRateLimiter(rate=10)  # 10 requests/second
        >>> if limiter.allow_request():
        ...     # Process the request
        ...     pass
        ... else:
        ...     # Throttle the request
        ...     pass
    """
    
    def __init__(self, rate, capacity=None):
        """
        Initialize the token bucket rate limiter.
        
        Args:
            rate: Number of tokens to refill per second (requests per second)
            capacity: Maximum number of tokens in the bucket (burst size).
                     If None, defaults to rate.
        """
        if rate <= 0:
            raise ValueError("Rate must be positive")
        
        self.rate = rate
        self.capacity = capacity if capacity is not None else rate
        
        if self.capacity <= 0:
            raise ValueError("Capacity must be positive")
        
        # Start with a full bucket
        self.tokens = float(self.capacity)
        self.last_refill_time = time.time()
        
        # Thread safety lock
        self.lock = threading.Lock()
    
    def allow_request(self):
        """
        Check if a request should be allowed.
        
        This method attempts to consume one token from the bucket. If a token
        is available, it returns True and consumes the token. Otherwise, it
        returns False.
        
        The method is thread-safe and can be called from multiple threads
        simultaneously.
        
        Returns:
            bool: True if the request is allowed (token available), 
                  False if the caller must be throttled.
        """
        with self.lock:
            # Refill tokens based on elapsed time
            current_time = time.time()
            elapsed_time = current_time - self.last_refill_time
            
            # Calculate tokens to add based on elapsed time and refill rate
            tokens_to_add = elapsed_time * self.rate
            
            # Add tokens but don't exceed capacity
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill_time = current_time
            
            # Try to consume a token
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            else:
                return False
    
    def get_available_tokens(self):
        """
        Get the current number of available tokens (for debugging/monitoring).
        
        Returns:
            float: Current number of tokens in the bucket.
        """
        with self.lock:
            # Update tokens based on elapsed time
            current_time = time.time()
            elapsed_time = current_time - self.last_refill_time
            tokens_to_add = elapsed_time * self.rate
            tokens = min(self.capacity, self.tokens + tokens_to_add)
            return tokens
