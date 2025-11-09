"""
Unit tests for the token-bucket rate limiter.

Tests cover basic functionality, burst capacity, token refill rate,
and thread safety.
"""

import time
import threading
import unittest
from rate_limiter import TokenBucketRateLimiter


class TestTokenBucketRateLimiter(unittest.TestCase):
    """Test cases for TokenBucketRateLimiter."""
    
    def test_initialization(self):
        """Test that the rate limiter initializes correctly."""
        limiter = TokenBucketRateLimiter(rate=10)
        self.assertEqual(limiter.rate, 10)
        self.assertEqual(limiter.capacity, 10)
        self.assertEqual(limiter.tokens, 10.0)
    
    def test_initialization_with_custom_capacity(self):
        """Test initialization with custom capacity."""
        limiter = TokenBucketRateLimiter(rate=10, capacity=20)
        self.assertEqual(limiter.rate, 10)
        self.assertEqual(limiter.capacity, 20)
        self.assertEqual(limiter.tokens, 20.0)
    
    def test_invalid_rate(self):
        """Test that invalid rate raises ValueError."""
        with self.assertRaises(ValueError):
            TokenBucketRateLimiter(rate=0)
        with self.assertRaises(ValueError):
            TokenBucketRateLimiter(rate=-5)
    
    def test_invalid_capacity(self):
        """Test that invalid capacity raises ValueError."""
        with self.assertRaises(ValueError):
            TokenBucketRateLimiter(rate=10, capacity=0)
        with self.assertRaises(ValueError):
            TokenBucketRateLimiter(rate=10, capacity=-5)
        with self.assertRaises(ValueError):
            TokenBucketRateLimiter(rate=10, capacity=0.5)
        with self.assertRaises(ValueError):
            TokenBucketRateLimiter(rate=0.5, capacity=0.9)
    
    def test_allow_request_basic(self):
        """Test basic allow_request functionality."""
        limiter = TokenBucketRateLimiter(rate=10)
        # Should allow the first request
        self.assertTrue(limiter.allow_request())
    
    def test_burst_capacity(self):
        """Test that burst capacity works correctly."""
        limiter = TokenBucketRateLimiter(rate=5, capacity=5)
        
        # Should allow up to 5 requests immediately (burst)
        for i in range(5):
            self.assertTrue(limiter.allow_request(), 
                          f"Request {i+1} should be allowed")
        
        # 6th request should be denied (no tokens left)
        self.assertFalse(limiter.allow_request(), 
                        "6th request should be denied")
    
    def test_token_refill(self):
        """Test that tokens refill at the correct rate."""
        limiter = TokenBucketRateLimiter(rate=10)  # 10 tokens per second
        
        # Consume all tokens
        for _ in range(10):
            self.assertTrue(limiter.allow_request())
        
        # Should be denied now
        self.assertFalse(limiter.allow_request())
        
        # Wait for 0.5 seconds (should refill ~5 tokens)
        time.sleep(0.5)
        
        # Should now allow ~5 requests
        allowed_count = 0
        for _ in range(10):
            if limiter.allow_request():
                allowed_count += 1
        
        # Allow some margin due to timing precision
        self.assertGreaterEqual(allowed_count, 4, 
                              "Should allow at least 4 requests after 0.5s")
        self.assertLessEqual(allowed_count, 6, 
                           "Should allow at most 6 requests after 0.5s")
    
    def test_token_refill_does_not_exceed_capacity(self):
        """Test that refilling does not exceed bucket capacity."""
        limiter = TokenBucketRateLimiter(rate=10, capacity=5)
        
        # Consume 2 tokens
        self.assertTrue(limiter.allow_request())
        self.assertTrue(limiter.allow_request())
        
        # Wait for 2 seconds (would refill 20 tokens without cap)
        time.sleep(2.0)
        
        # Should only allow 5 requests (capacity limit)
        allowed_count = 0
        for _ in range(10):
            if limiter.allow_request():
                allowed_count += 1
        
        self.assertEqual(allowed_count, 5, 
                        "Should only allow capacity number of requests")
    
    def test_thread_safety(self):
        """Test that the rate limiter is thread-safe."""
        limiter = TokenBucketRateLimiter(rate=100, capacity=100)
        
        allowed_requests = []
        denied_requests = []
        lock = threading.Lock()
        
        def make_requests():
            """Function to be run in threads."""
            for _ in range(50):
                if limiter.allow_request():
                    with lock:
                        allowed_requests.append(1)
                else:
                    with lock:
                        denied_requests.append(1)
        
        # Create multiple threads
        threads = []
        for _ in range(4):  # 4 threads, each making 50 requests = 200 total
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Total requests = 200, capacity = 100
        # So we should have ~100 allowed and ~100 denied
        total_allowed = len(allowed_requests)
        total_denied = len(denied_requests)
        
        self.assertEqual(total_allowed + total_denied, 200, 
                        "Should process all 200 requests")
        
        # Allow some margin for timing
        self.assertGreaterEqual(total_allowed, 95, 
                              "Should allow at least 95 requests")
        self.assertLessEqual(total_allowed, 105, 
                           "Should allow at most 105 requests")
    
    def test_concurrent_bursts(self):
        """Test handling concurrent burst requests from multiple threads."""
        limiter = TokenBucketRateLimiter(rate=50, capacity=50)
        
        results = {'allowed': 0, 'denied': 0}
        results_lock = threading.Lock()
        
        def burst_requests(count):
            """Make a burst of requests."""
            local_allowed = 0
            local_denied = 0
            for _ in range(count):
                if limiter.allow_request():
                    local_allowed += 1
                else:
                    local_denied += 1
            
            with results_lock:
                results['allowed'] += local_allowed
                results['denied'] += local_denied
        
        # 5 threads each making 20 requests = 100 total requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=burst_requests, args=(20,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should allow approximately 50 (capacity) and deny approximately 50
        self.assertEqual(results['allowed'] + results['denied'], 100)
        self.assertGreaterEqual(results['allowed'], 45)
        self.assertLessEqual(results['allowed'], 55)
    
    def test_get_available_tokens(self):
        """Test the get_available_tokens method."""
        limiter = TokenBucketRateLimiter(rate=10, capacity=10)
        
        # Initially should have full capacity
        self.assertAlmostEqual(limiter.get_available_tokens(), 10.0, delta=0.1)
        
        # Consume 3 tokens
        for _ in range(3):
            limiter.allow_request()
        
        # Should have 7 tokens
        self.assertAlmostEqual(limiter.get_available_tokens(), 7.0, delta=0.1)
        
        # Wait 0.5 seconds (should refill ~5 tokens)
        time.sleep(0.5)
        
        # Should have ~10 tokens (capped at capacity)
        tokens = limiter.get_available_tokens()
        self.assertGreaterEqual(tokens, 9.5)
        self.assertLessEqual(tokens, 10.0)
    
    def test_sustained_rate(self):
        """Test that the limiter maintains the correct sustained rate."""
        limiter = TokenBucketRateLimiter(rate=20)  # 20 requests per second
        
        # Consume initial burst
        for _ in range(20):
            limiter.allow_request()
        
        # Now test sustained rate over 1 second
        start_time = time.time()
        allowed_count = 0
        
        # Try to make requests for approximately 1 second
        while time.time() - start_time < 1.0:
            if limiter.allow_request():
                allowed_count += 1
            time.sleep(0.01)  # Small delay between attempts
        
        # Should allow approximately 20 requests in 1 second (±10% margin)
        self.assertGreaterEqual(allowed_count, 18, 
                              f"Expected ~20 requests, got {allowed_count}")
        self.assertLessEqual(allowed_count, 22, 
                           f"Expected ~20 requests, got {allowed_count}")
    
    def test_rate_limiter_size_one(self):
        """Test edge case: rate limiter with rate=1, capacity=1."""
        limiter = TokenBucketRateLimiter(rate=1, capacity=1)
        
        # First request should be allowed
        self.assertTrue(limiter.allow_request())
        
        # Second immediate request should be denied
        self.assertFalse(limiter.allow_request())
        
        # Wait for 1 second to refill
        time.sleep(1.0)
        
        # Should allow one more request
        self.assertTrue(limiter.allow_request())
        
        # Immediate request should be denied again
        self.assertFalse(limiter.allow_request())
    
    def test_fractional_rate(self):
        """Test edge case: fractional rate (e.g., 0.5 requests per second)."""
        limiter = TokenBucketRateLimiter(rate=0.5, capacity=1)
        
        # First request should be allowed
        self.assertTrue(limiter.allow_request())
        
        # Second immediate request should be denied
        self.assertFalse(limiter.allow_request())
        
        # Wait 2 seconds to refill 1 token
        time.sleep(2.0)
        
        # Should allow one more request
        self.assertTrue(limiter.allow_request())
    
    def test_capacity_less_than_rate(self):
        """Test edge case: capacity < rate (slow burst, fast refill)."""
        limiter = TokenBucketRateLimiter(rate=10, capacity=2)
        
        # Should allow 2 requests immediately (capacity limit)
        self.assertTrue(limiter.allow_request())
        self.assertTrue(limiter.allow_request())
        
        # Third request should be denied
        self.assertFalse(limiter.allow_request())
        
        # Wait 0.5 seconds (refills 5 tokens, capped at 2)
        time.sleep(0.5)
        
        # Should allow up to 2 more requests
        allowed = sum(1 for _ in range(5) if limiter.allow_request())
        self.assertEqual(allowed, 2)
    
    def test_capacity_greater_than_rate(self):
        """Test edge case: capacity > rate (large burst, slow refill)."""
        limiter = TokenBucketRateLimiter(rate=2, capacity=10)
        
        # Should allow 10 requests immediately (capacity limit)
        for i in range(10):
            self.assertTrue(limiter.allow_request(), 
                          f"Request {i+1} should be allowed")
        
        # 11th request should be denied
        self.assertFalse(limiter.allow_request())
        
        # Wait 1 second (refills 2 tokens)
        time.sleep(1.0)
        
        # Should allow 2 more requests
        allowed = sum(1 for _ in range(5) if limiter.allow_request())
        self.assertEqual(allowed, 2)
    
    def test_very_large_rate(self):
        """Test edge case: very large rate."""
        limiter = TokenBucketRateLimiter(rate=1000, capacity=1000)
        
        # Should handle 1000 immediate requests
        allowed = sum(1 for _ in range(1000) if limiter.allow_request())
        self.assertEqual(allowed, 1000)
        
        # 1001st request should be denied
        self.assertFalse(limiter.allow_request())
    
    def test_minimum_valid_capacity(self):
        """Test edge case: minimum valid capacity of 1.0."""
        limiter = TokenBucketRateLimiter(rate=1, capacity=1.0)
        
        # Should allow exactly 1 request
        self.assertTrue(limiter.allow_request())
        self.assertFalse(limiter.allow_request())
        
        # Test with fractional rate but valid capacity
        limiter2 = TokenBucketRateLimiter(rate=0.1, capacity=1.0)
        self.assertTrue(limiter2.allow_request())
        self.assertFalse(limiter2.allow_request())


if __name__ == '__main__':
    unittest.main()
