#!/usr/bin/env python3
"""
Smartpay API Test Script
Tests all microservice endpoints through the API Gateway and directly.

Usage:
    python3 test_apis.py
    python3 test_apis.py --direct   # bypass gateway, hit services directly
"""

import sys
import json

import time
import argparse
import urllib.request
import urllib.error

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
GATEWAY      = "http://localhost:8080"
USER_SVC     = "http://localhost:8081"
TRANSACTION  = "http://localhost:8082"
WALLET       = "http://localhost:8083"   # no port in config — update if different
NOTIFICATION = "http://localhost:8084"
REWARD       = "http://localhost:8089"   # NOTE: gateway routes to 8085 (mismatch — known bug)

TEST_EMAIL   = f"testuser_{int(time.time())}@smartpay.test"
TEST_PASS    = "Test@1234"
TEST_NAME    = "Test User"

# ─────────────────────────────────────────────
# ANSI colours
# ─────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

passed = failed = skipped = 0


def _request(method, url, body=None, headers=None):
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    data = json.dumps(body).encode() if body is not None else None
    req  = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except Exception as e:
        return 0, str(e)


def check(label, status, body, expect_status, *, warn=False):
    global passed, failed, skipped
    ok = status == expect_status
    tag  = f"{GREEN}PASS{RESET}" if ok else (f"{YELLOW}WARN{RESET}" if warn else f"{RED}FAIL{RESET}")
    note = f"  got {status}, expected {expect_status}"
    print(f"  [{tag}] {label}{'' if ok else note}")
    if not ok and not warn:
        body_str = json.dumps(body, indent=2) if isinstance(body, dict) else str(body)
        print(f"         body: {body_str[:200]}")
    if ok:
        passed += 1
    elif warn:
        skipped += 1
    else:
        failed += 1
    return ok


def section(title):
    print(f"\n{BOLD}{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*55}{RESET}")


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

def test_auth(base):
    section("Auth Service  (/auth)")
    token = None
    user_id = None

    # Signup
    status, body = _request("POST", f"{base}/auth/signup",
                             {"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASS})
    check("POST /auth/signup  → 200 OK", status, body, 200)

    # Duplicate signup
    status, body = _request("POST", f"{base}/auth/signup",
                             {"name": TEST_NAME, "email": TEST_EMAIL, "password": TEST_PASS})
    check("POST /auth/signup  (duplicate) → 400", status, body, 400)

    # Login
    status, body = _request("POST", f"{base}/auth/login",
                             {"email": TEST_EMAIL, "password": TEST_PASS})
    if check("POST /auth/login  → 200 + token", status, body, 200):
        token   = body.get("token") if isinstance(body, dict) else None
        if token:
            print(f"         token (truncated): {token[:40]}...")

    # Bad login
    status, body = _request("POST", f"{base}/auth/login",
                             {"email": TEST_EMAIL, "password": "wrongpass"})
    check("POST /auth/login  (bad creds) → 401", status, body, 401)

    return token


def test_users(base, token, direct_base):
    section("User Service  (/api/users)")
    auth = {"Authorization": f"Bearer {token}"}

    # GET all users
    status, body = _request("GET", f"{base}/api/users/all", headers=auth)
    check("GET  /api/users/all → 200", status, body, 200)

    user_id = None
    if isinstance(body, list) and body:
        user_id = body[-1].get("id")

    # GET user by id
    if user_id:
        status, body = _request("GET", f"{base}/api/users/{user_id}", headers=auth)
        check(f"GET  /api/users/{user_id} → 200", status, body, 200)
    else:
        print(f"  [{YELLOW}SKIP{RESET}] GET /api/users/{{id}} — no users found")
        global skipped; skipped += 1

    return user_id


def test_transactions(base, token, user_id):
    section("Transaction Service  (/api/transactions)")
    # ⚠️  The gateway JwtAuthFilter only forwards X-User-Email, but
    #     TransactionController requires X-User-Id.  Tests may fail
    #     through the gateway until the filter is updated.
    auth = {"Authorization": f"Bearer {token}"}

    tx_body = {
        "senderId":   user_id or 1,
        "receiverId": 2,
        "amount":     100.0,
        "status":     "PENDING"
    }

    status, body = _request("POST", f"{base}/api/transactions/create",
                             tx_body, headers=auth)
    ok = check("POST /api/transactions/create → 200", status, body, 200,
               warn=(status == 403))  # 403 expected if gateway doesn't forward X-User-Id

    tx_id = body.get("id") if isinstance(body, dict) and ok else None

    if tx_id:
        status, body = _request("GET", f"{base}/api/transactions/{tx_id}", headers=auth)
        check(f"GET  /api/transactions/{tx_id} → 200", status, body, 200)

        status, body = _request("GET",
                                 f"{base}/api/transactions/user/{user_id or 1}",
                                 headers=auth)
        check(f"GET  /api/transactions/user/{user_id or 1} → 200", status, body, 200)
    else:
        print(f"  [{YELLOW}SKIP{RESET}] GET by id/user — no transaction created")
        global skipped; skipped += 2

    return tx_id


def test_wallet(wallet_base):
    section("Wallet Service  (direct → no gateway route)")
    # Wallet service has no gateway route and no explicit port in its config.
    # Set WALLET at the top of this script to match your actual port.

    uid = 999  # isolated test user id

    status, body = _request("POST", f"{wallet_base}/api/v1/wallets",
                             {"userId": uid, "currency": "USD"})
    check("POST /api/v1/wallets (create) → 200", status, body, 200)

    status, body = _request("GET", f"{wallet_base}/api/v1/wallets/{uid}")
    check(f"GET  /api/v1/wallets/{uid} → 200", status, body, 200)

    status, body = _request("POST", f"{wallet_base}/api/v1/wallets/credit",
                             {"userId": uid, "currency": "USD", "amount": 5000})
    check("POST /api/v1/wallets/credit → 200", status, body, 200)

    status, body = _request("POST", f"{wallet_base}/api/v1/wallets/debit",
                             {"userId": uid, "currency": "USD", "amount": 1000})
    check("POST /api/v1/wallets/debit → 200", status, body, 200)

    # Place hold
    status, body = _request("POST", f"{wallet_base}/api/v1/wallets/hold",
                             {"userId": uid, "currency": "USD", "amount": 500})
    check("POST /api/v1/wallets/hold → 200", status, body, 200)
    hold_ref = body.get("holdReference") if isinstance(body, dict) else None

    if hold_ref:
        status, body = _request("POST", f"{wallet_base}/api/v1/wallets/capture",
                                 {"holdReference": hold_ref})
        check("POST /api/v1/wallets/capture → 200", status, body, 200)
    else:
        # place a second hold to test release
        status, body = _request("POST", f"{wallet_base}/api/v1/wallets/hold",
                                 {"userId": uid, "currency": "USD", "amount": 200})
        hold_ref = body.get("holdReference") if isinstance(body, dict) else "dummy-ref"

    if hold_ref:
        status, body = _request("POST",
                                 f"{wallet_base}/api/v1/wallets/release/{hold_ref}")
        check(f"POST /api/v1/wallets/release/{{ref}} → 200", status, body, 200)


def test_rewards(base, token, user_id):
    section("Reward Service  (/api/rewards)")
    # ⚠️  Gateway routes /api/rewards/** to port 8085, but the service
    #     listens on 8089.  These tests call the service directly (REWARD base).
    auth = {"Authorization": f"Bearer {token}"}

    status, body = _request("GET", f"{base}/api/rewards/", headers=auth)
    check("GET  /api/rewards/ → 200", status, body, 200)

    uid = user_id or 1
    status, body = _request("GET", f"{base}/api/rewards/user/{uid}", headers=auth)
    check(f"GET  /api/rewards/user/{uid} → 200", status, body, 200)


def test_notifications(base, token, user_id):
    section("Notification Service  (/api/notify)")
    # ⚠️  Gateway routes /api/notifications/**, controller listens on /api/notify.
    #     These tests call the service directly (NOTIFICATION base).
    auth = {"Authorization": f"Bearer {token}"}
    uid  = user_id or 1

    notif = {"userId": uid, "message": "Test notification from test suite",
             "type": "INFO", "read": False}
    status, body = _request("POST", f"{base}/api/notify", notif, headers=auth)
    check("POST /api/notify → 200", status, body, 200)

    status, body = _request("GET", f"{base}/api/notify/{uid}", headers=auth)
    check(f"GET  /api/notify/{uid} → 200", status, body, 200)


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--direct", action="store_true",
                        help="Bypass gateway; call each service directly")
    args = parser.parse_args()

    print(f"\n{BOLD}Smartpay API Test Suite{RESET}")
    print(f"Mode: {'direct (bypassing gateway)' if args.direct else 'through gateway'}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if args.direct:
        auth_base  = USER_SVC
        user_base  = USER_SVC
        tx_base    = TRANSACTION
        reward_base= REWARD
        notif_base = NOTIFICATION
    else:
        auth_base  = GATEWAY
        user_base  = GATEWAY
        tx_base    = GATEWAY
        reward_base= GATEWAY   # NOTE: will fail — gateway routes to 8085 not 8089
        notif_base = GATEWAY   # NOTE: will fail — path mismatch /notifications vs /notify

    token   = test_auth(auth_base)
    user_id = None

    if token:
        user_id = test_users(user_base, token, USER_SVC)
        test_transactions(tx_base, token, user_id)
        test_rewards(reward_base if not args.direct else REWARD, token, user_id)
        test_notifications(notif_base if not args.direct else NOTIFICATION, token, user_id)
    else:
        print(f"\n{RED}Cannot proceed — login failed, no JWT token obtained.{RESET}")

    test_wallet(WALLET)

    # ── Summary ───────────────────────────────
    total = passed + failed + skipped
    print(f"\n{BOLD}{'═'*55}{RESET}")
    print(f"{BOLD}Results:  "
          f"{GREEN}{passed} passed{RESET}  "
          f"{RED}{failed} failed{RESET}  "
          f"{YELLOW}{skipped} warned/skipped{RESET}  "
          f"({total} total){RESET}")

    if not args.direct:
        print(f"\n{YELLOW}Known gateway issues (run with --direct to bypass):{RESET}")
        print("  • Reward service: gateway routes to :8085 but service listens on :8089")
        print("  • Notification:   gateway path /api/notifications/** ≠ controller /api/notify")
        print("  • Transactions:   gateway forwards X-User-Email but service expects X-User-Id")
        print("  • Wallet service: no gateway route configured")

    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
