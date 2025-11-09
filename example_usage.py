"""
Example usage of the TokenBucketRateLimiter.

This script demonstrates how to use the rate limiter in a real-world scenario.
"""

import time
import threading
from rate_limiter import TokenBucketRateLimiter


def example_1_basic_usage():
    """Example 1: Basic usage of the rate limiter."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Create a rate limiter that allows 5 requests per second
    limiter = TokenBucketRateLimiter(rate=5)
    
    print(f"Rate limiter: {limiter.rate} requests/second")
    print(f"Capacity: {limiter.capacity} tokens\n")
    
    # Try to make 10 requests immediately
    print("Attempting 10 requests immediately:")
    for i in range(10):
        allowed = limiter.allow_request()
        status = "ALLOWED" if allowed else "DENIED"
        print(f"  Request {i+1}: {status}")
    
    print()


def example_2_burst_and_refill():
    """Example 2: Demonstrate burst capacity and token refill."""
    print("=" * 60)
    print("Example 2: Burst Capacity and Token Refill")
    print("=" * 60)
    
    # Create a rate limiter: 10 requests/second
    limiter = TokenBucketRateLimiter(rate=10)
    
    print("Making 10 requests (burst)...")
    for i in range(10):
        limiter.allow_request()
    print("All 10 tokens consumed.\n")
    
    # Wait and refill
    print("Waiting 0.5 seconds for refill...")
    time.sleep(0.5)
    
    print(f"Available tokens: {limiter.get_available_tokens():.2f}\n")
    
    print("Attempting 10 more requests:")
    allowed_count = 0
    for i in range(10):
        if limiter.allow_request():
            allowed_count += 1
            print(f"  Request {i+1}: ALLOWED")
        else:
            print(f"  Request {i+1}: DENIED")
    
    print(f"\nTotal allowed: {allowed_count} requests")
    print()


def example_3_multi_threaded():
    """Example 3: Multi-threaded usage."""
    print("=" * 60)
    print("Example 3: Multi-threaded Usage")
    print("=" * 60)
    
    # Create a rate limiter: 20 requests/second, capacity 20
    limiter = TokenBucketRateLimiter(rate=20, capacity=20)
    
    results = {'allowed': 0, 'denied': 0}
    lock = threading.Lock()
    
    def worker(worker_id, num_requests):
        """Worker function that makes requests."""
        local_allowed = 0
        local_denied = 0
        
        for _ in range(num_requests):
            if limiter.allow_request():
                local_allowed += 1
            else:
                local_denied += 1
            time.sleep(0.01)  # Small delay between requests
        
        with lock:
            results['allowed'] += local_allowed
            results['denied'] += local_denied
        
        print(f"  Worker {worker_id}: {local_allowed} allowed, "
              f"{local_denied} denied")
    
    print(f"Starting 4 worker threads, each making 15 requests...")
    print(f"Total requests: 60\n")
    
    threads = []
    for i in range(4):
        thread = threading.Thread(target=worker, args=(i+1, 15))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    print(f"\nTotal results:")
    print(f"  Allowed: {results['allowed']}")
    print(f"  Denied: {results['denied']}")
    print()


def example_4_expensive_operation():
    """Example 4: Protecting an expensive operation."""
    print("=" * 60)
    print("Example 4: Protecting an Expensive Operation")
    print("=" * 60)
    
    # Simulating an expensive API endpoint with rate limiting
    limiter = TokenBucketRateLimiter(rate=3)  # Only 3 calls per second
    
    def expensive_operation(request_id):
        """Simulate an expensive operation."""
        print(f"  Processing request {request_id}... (expensive operation)")
        time.sleep(0.1)  # Simulate work
        return f"Result for request {request_id}"
    
    print("Simulating API endpoint with 3 requests/second limit:\n")
    
    for i in range(8):
        if limiter.allow_request():
            result = expensive_operation(i+1)
            print(f"  ✓ Request {i+1}: SUCCESS")
        else:
            print(f"  ✗ Request {i+1}: RATE LIMITED (429 Too Many Requests)")
        
        time.sleep(0.2)  # Simulate time between requests
    
    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("Token Bucket Rate Limiter - Usage Examples")
    print("=" * 60 + "\n")
    
    example_1_basic_usage()
    time.sleep(1)  # Reset between examples
    
    example_2_burst_and_refill()
    time.sleep(1)
    
    example_3_multi_threaded()
    time.sleep(1)
    
    example_4_expensive_operation()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
