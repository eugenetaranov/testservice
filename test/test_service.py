#!/usr/bin/env python3
import argparse
import requests
import time
import os
import shutil
import urllib3
from collections import defaultdict
from datetime import datetime

YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

sorted_names = []
last_sort_time = 0


def print_table(counts, total, last_seen, status_counts, headers=None, is_error=False):
    global sorted_names, last_sort_time
    now = time.time()
    if now - last_sort_time >= 5:
        sorted_names = sorted(last_seen, key=lambda n: last_seen[n], reverse=True)
        last_sort_time = now
    # Include any new names not yet in the sorted list
    known = set(sorted_names)
    for name in last_seen:
        if name not in known:
            sorted_names.insert(0, name)
    os.system("clear")
    timestamp = datetime.now().strftime("%H:%M:%S")
    cols = shutil.get_terminal_size().columns
    header_left = f"Total: {total}  2xx: {status_counts['2xx']}  4xx: {status_counts['4xx']}  5xx: {status_counts['5xx']}  err: {status_counts['err']}"
    status_line = f"{header_left}{timestamp:>{cols - len(header_left)}}"
    if is_error:
        print(f"{RED}{status_line}{RESET}\n")
    else:
        print(f"{status_line}\n")
    print(f"{'Instance Name':<40} | {'Requests':>8} | {'%':>6} | {'Last Seen':>10}")
    print(f"{'-'*40}-|{'-'*10}|{'-'*8}|{'-'*11}")
    for name in sorted_names:
        count = counts[name]
        pct = count / total * 100 if total else 0
        ago = int(now - last_seen[name])
        ago_str = f"{ago}s ago"
        row = f"{name:<40} | {count:>8} | {pct:>5.1f}% | {ago_str:>10}"
        if is_error:
            print(f"{RED}{row}{RESET}")
        elif ago > 300:
            print(f"{RED}{row}{RESET}")
        elif ago > 60:
            print(f"{YELLOW}{row}{RESET}")
        else:
            print(row)
    if headers:
        print(f"\n\n{'Response Headers':}")
        print("-" * 40)
        for key, value in headers:
            print(f"  {key}: {value}")


def main():
    parser = argparse.ArgumentParser(
        description="Load test a service and track response distribution by hostname"
    )
    parser.add_argument("-u", "--url", required=True, help="URL to poll")
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds (default: 1)",
    )
    parser.add_argument(
        "-k", "--insecure", action="store_true", help="Ignore SSL certificate errors"
    )
    args = parser.parse_args()

    verify = not args.insecure
    if args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    session = requests.Session()
    session.verify = verify
    counts = defaultdict(int)
    last_seen = {}
    total = 0
    status_counts = defaultdict(int)
    saved_set_cookies = {}  # name -> (raw_value, expires_at)

    try:
        while True:
            try:
                resp = session.get(args.url, timeout=5, stream=True)
            except Exception:
                total += 1
                status_counts["err"] += 1
                print_table(counts, total, last_seen, status_counts, is_error=True)
                time.sleep(args.interval)
                continue
            total += 1
            try:
                code = resp.status_code
                if 200 <= code < 300:
                    status_counts["2xx"] += 1
                elif 400 <= code < 500:
                    status_counts["4xx"] += 1
                elif 500 <= code < 600:
                    status_counts["5xx"] += 1
                raw_headers = list(resp.raw.headers.items())
                # Capture any new Set-Cookie headers with their expiry
                now = time.time()
                has_set_cookie = False
                for key, value in raw_headers:
                    if key.lower() == "set-cookie":
                        has_set_cookie = True
                        cookie_name = value.split("=", 1)[0]
                        max_age = None
                        for part in value.split(";"):
                            part = part.strip()
                            if part.lower().startswith("max-age="):
                                max_age = int(part.split("=", 1)[1])
                        expires_at = now + max_age if max_age else None
                        saved_set_cookies[cookie_name] = (value, expires_at)
                # If no Set-Cookie in response, inject saved ones that haven't expired
                if not has_set_cookie:
                    expired = []
                    for cookie_name, (
                        raw_value,
                        expires_at,
                    ) in saved_set_cookies.items():
                        if expires_at and now > expires_at:
                            expired.append(cookie_name)
                        else:
                            raw_headers.append(("Set-Cookie", raw_value))
                    for name in expired:
                        del saved_set_cookies[name]
                data = resp.json()
                hostname = data["hostname"]
                counts[hostname] += 1
                last_seen[hostname] = time.time()
                print_table(counts, total, last_seen, status_counts, raw_headers)
            except Exception:
                status_counts["err"] += 1
                print_table(counts, total, last_seen, status_counts, is_error=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n")
        print_table(counts, total, last_seen, status_counts)
        print()


if __name__ == "__main__":
    main()
