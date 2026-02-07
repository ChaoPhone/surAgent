import time
import requests
import httpx

url = 'https://www.google.com'

# Benchmark function

def benchmark_requests():
    start_time = time.time()
    for _ in range(10):
        requests.get(url)
    return (time.time() - start_time) / 10


def benchmark_httpx():
    start_time = time.time()
    for _ in range(10):
        httpx.get(url)
    return (time.time() - start_time) / 10

if __name__ == '__main__':
    requests_time = benchmark_requests()
    print(f'Average time for requests: {requests_time:.4f} seconds')
    httpx_time = benchmark_httpx()
    print(f'Average time for httpx: {httpx_time:.4f} seconds')