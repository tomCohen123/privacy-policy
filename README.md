# Token Bucket Rate Limiter

A thread-safe token-bucket rate limiter implementation in Python, designed for high-traffic web services to prevent abuse of expensive operations.

## Features

- **Thread-Safe**: Uses locks to ensure safe concurrent access from multiple threads
- **Configurable Rate**: Set the number of requests per second
- **Burst Support**: Allows burst traffic up to the bucket capacity
- **Automatic Refill**: Tokens refill continuously at the configured rate
- **Simple API**: Easy-to-use `allow_request()` method returns True/False

## Installation

No external dependencies required. The implementation uses only Python standard library modules:
- `threading` for thread safety
- `time` for timing operations

## Usage

### Basic Example

```python
from rate_limiter import TokenBucketRateLimiter

# Create a rate limiter that allows 10 requests per second
limiter = TokenBucketRateLimiter(rate=10)

# Check if a request should be allowed
if limiter.allow_request():
    # Process the request
    handle_request()
else:
    # Throttle the request (return 429 Too Many Requests)
    return "Rate limit exceeded"
```

### Custom Capacity

```python
# Allow 10 requests/second, but support bursts up to 20 requests
limiter = TokenBucketRateLimiter(rate=10, capacity=20)
```

### Multi-threaded Server Example

```python
from rate_limiter import TokenBucketRateLimiter
import threading

# Shared rate limiter for all threads
limiter = TokenBucketRateLimiter(rate=100)

def handle_api_request(request_id):
    """Handler for API requests with rate limiting."""
    if not limiter.allow_request():
        return {"error": "Rate limit exceeded"}, 429
    
    # Process the expensive operation
    result = expensive_operation(request_id)
    return {"result": result}, 200

# Use in your multi-threaded server
# (Flask, Django, FastAPI, etc.)
```

### Monitoring

```python
# Check available tokens (for debugging/monitoring)
available = limiter.get_available_tokens()
print(f"Available tokens: {available:.2f}")
```

## How It Works

The token bucket algorithm works as follows:

1. **Initialization**: The bucket starts full with `capacity` tokens
2. **Token Consumption**: Each request consumes 1 token
3. **Refill**: Tokens are added at a rate of `rate` tokens per second
4. **Capacity Limit**: The bucket never exceeds its `capacity`
5. **Request Decision**: If ≥1 token is available, the request is allowed and a token is consumed

### Key Parameters

- **rate**: Number of tokens added per second (requests per second)
- **capacity**: Maximum number of tokens in the bucket (burst size)

### Thread Safety

The implementation uses `threading.Lock` to ensure that:
- Token refill calculations are atomic
- Token consumption is atomic
- Multiple threads can safely call `allow_request()` concurrently

## Testing

Run the comprehensive test suite:

```bash
python3 -m unittest test_rate_limiter.py -v
```

The tests cover:
- Basic functionality
- Burst capacity
- Token refill rate
- Thread safety with concurrent requests
- Edge cases and error handling

## Examples

Run the example usage script to see the rate limiter in action:

```bash
python3 example_usage.py
```

This demonstrates:
1. Basic usage
2. Burst capacity and token refill
3. Multi-threaded usage
4. Protecting an expensive operation

## Implementation Details

### Time-based Refill

The rate limiter uses a time-based refill strategy:
- Tracks the last refill time
- On each `allow_request()` call, calculates elapsed time
- Adds `elapsed_time * rate` tokens (capped at capacity)
- Updates the last refill time

This approach ensures smooth token refill without requiring a background thread.

### Precision

The implementation uses floating-point arithmetic for tokens, allowing fractional tokens to be tracked for more precise rate limiting over time.

## Performance Considerations

- **Lock Contention**: The implementation uses a single lock. For extremely high-throughput scenarios (>100k requests/second), consider per-user or per-resource rate limiters to reduce lock contention.
- **Memory**: Each rate limiter instance uses minimal memory (~100 bytes).
- **CPU**: Token calculation is O(1) with minimal CPU overhead.

## Use Cases

- **API Rate Limiting**: Protect REST APIs from abuse
- **Resource-Intensive Operations**: Limit expensive database queries, external API calls, or compute operations
- **Fair Usage**: Ensure fair resource allocation among users
- **DDoS Protection**: Basic protection against denial-of-service attacks
- **Cost Control**: Limit operations that incur costs (e.g., third-party API calls)

## License

This implementation is provided as-is for educational and commercial use.
