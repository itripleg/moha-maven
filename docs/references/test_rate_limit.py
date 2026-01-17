#!/usr/bin/env python3
"""
Quick rate limit test for Hyperliquid public API.

Tests how many requests/second we can make before hitting rate limits.
"""
import sys
import os
import time
from datetime import datetime

# Add services/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

from hl_client import get_public_client


def test_rate_limit(duration_seconds=30, requests_per_second=10):
    """
    Test Hyperliquid public API rate limits.

    Args:
        duration_seconds: How long to run the test
        requests_per_second: Target requests per second
    """
    client = get_public_client()
    if not client:
        print("❌ Failed to initialize public client")
        return

    print(f"[TEST] Hyperliquid Public API Rate Limits")
    print(f"Network: {client.network_name}")
    print(f"Duration: {duration_seconds}s")
    print(f"Target RPS: {requests_per_second}")
    print(f"Base URL: {client.base_url}")
    print("-" * 60)

    results = {
        'successful': 0,
        'failed': 0,
        'rate_limited': 0,
        'errors': [],
        'latencies': []
    }

    start_time = time.time()
    request_interval = 1.0 / requests_per_second
    next_request_time = start_time

    try:
        while time.time() - start_time < duration_seconds:
            # Wait until next request time
            now = time.time()
            if now < next_request_time:
                time.sleep(next_request_time - now)

            # Make request and time it
            request_start = time.time()
            try:
                # Use a lightweight endpoint - all_mids() returns current prices
                prices = client.info.all_mids()
                request_end = time.time()
                latency = (request_end - request_start) * 1000  # ms

                if prices:
                    results['successful'] += 1
                    results['latencies'].append(latency)
                else:
                    results['failed'] += 1

            except Exception as e:
                request_end = time.time()
                error_msg = str(e).lower()

                if 'rate' in error_msg or 'limit' in error_msg or '429' in error_msg:
                    results['rate_limited'] += 1
                    results['errors'].append(f"Rate limited: {e}")
                    print(f"[!] Rate limit hit at {time.time() - start_time:.1f}s")
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Error: {e}")

            # Schedule next request
            next_request_time += request_interval

            # Print progress every 5 seconds
            elapsed = time.time() - start_time
            if int(elapsed) % 5 == 0 and elapsed > 0:
                total = results['successful'] + results['failed'] + results['rate_limited']
                avg_latency = sum(results['latencies']) / len(results['latencies']) if results['latencies'] else 0
                current_rps = total / elapsed
                print(f"[PROGRESS] {elapsed:.0f}s - {total} requests ({current_rps:.1f} RPS) - Avg latency: {avg_latency:.0f}ms")
                time.sleep(0.1)  # Prevent duplicate prints

    except KeyboardInterrupt:
        print("\n[!] Test interrupted by user")

    # Calculate stats
    total_time = time.time() - start_time
    total_requests = results['successful'] + results['failed'] + results['rate_limited']
    actual_rps = total_requests / total_time if total_time > 0 else 0

    avg_latency = sum(results['latencies']) / len(results['latencies']) if results['latencies'] else 0
    min_latency = min(results['latencies']) if results['latencies'] else 0
    max_latency = max(results['latencies']) if results['latencies'] else 0

    # Print results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total Requests:    {total_requests}")
    print(f"[OK] Successful:   {results['successful']}")
    print(f"[X] Failed:        {results['failed']}")
    print(f"[!] Rate Limited:  {results['rate_limited']}")
    print(f"\nActual RPS:        {actual_rps:.2f}")
    print(f"Test Duration:     {total_time:.2f}s")
    print(f"\nLatency Stats:")
    print(f"  Average:         {avg_latency:.1f}ms")
    print(f"  Min:             {min_latency:.1f}ms")
    print(f"  Max:             {max_latency:.1f}ms")

    if results['rate_limited'] > 0:
        print(f"\n[!] RATE LIMIT DETECTED")
        print(f"First hit at:      ~{total_time / (total_requests / (results['rate_limited'] + results['successful'])):.1f}s")
        print(f"Rate limit count:  {results['rate_limited']}")
    else:
        print(f"\n[OK] NO RATE LIMITS - Safe to use {actual_rps:.1f} RPS")

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    if results['rate_limited'] > 0:
        safe_rps = actual_rps * (results['successful'] / total_requests) * 0.8  # 80% safety margin
        print(f"Recommended max RPS: {safe_rps:.2f}")
        print(f"Recommended tick interval: {1000/safe_rps:.0f}ms")
    else:
        print(f"No rate limits detected at {actual_rps:.1f} RPS")
        print(f"Consider testing higher rates or")
        print(f"Use {1000/actual_rps:.0f}ms tick interval for safety")

    # Show sample errors
    if results['errors']:
        print(f"\nSample Errors (first 3):")
        for error in results['errors'][:3]:
            print(f"  - {error}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test Hyperliquid API rate limits')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds (default: 30)')
    parser.add_argument('--rps', type=int, default=10, help='Target requests per second (default: 10)')

    args = parser.parse_args()

    test_rate_limit(duration_seconds=args.duration, requests_per_second=args.rps)
