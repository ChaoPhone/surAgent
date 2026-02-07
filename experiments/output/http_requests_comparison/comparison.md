# Comparison of Python `requests` and `httpx`

| Feature               | `requests`                     | `httpx`                        |
|-----------------------|--------------------------------|--------------------------------|
| Asynchronous Support   | No                             | Yes                            |
| HTTP/2 Support        | No                             | Yes                            |
| Connection Pooling    | Yes                            | Yes                            |
| Timeout Handling       | Yes                            | Yes                            |
| Streaming Uploads      | No                             | Yes                            |
| Simplicity            | Very simple API               | Slightly more complex          |
| Community Support      | Large and mature               | Growing rapidly                 |
| Performance           | Good                           | Generally better with async    |
| Compatibility         | Python 2 and 3                | Python 3.6+                    |

## Summary
- `requests` is great for simple, synchronous HTTP requests.
- `httpx` is better for modern applications requiring async support and HTTP/2.