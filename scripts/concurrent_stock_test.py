"""
Fires many stock-out requests at the same time and checks the final stock.

Usage:
    python scripts/concurrent_stock_test.py <admin_token> <product_id>

Before running, put exactly 20 units of stock on the product.
It sends 30 requests of 1 unit each at once.
Expected: 20 succeed, 10 fail with 400, and the final stock is 0.
"""
import json
import sys
import threading
import urllib.error
import urllib.request

BASE_URL = "http://localhost:8003"
token, product_id = sys.argv[1], sys.argv[2]
results = []


def stock_out():
    request = urllib.request.Request(
        f"{BASE_URL}/api/inventory/{product_id}/stock-out",
        data=json.dumps({"quantity": 1, "remarks": "concurrency test"}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            results.append(response.status)
    except urllib.error.HTTPError as error:
        results.append(error.code)


threads = [threading.Thread(target=stock_out) for _ in range(30)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print("Successful (201):", results.count(201))
print("Rejected   (400):", results.count(400))

request = urllib.request.Request(
    f"{BASE_URL}/api/inventory/{product_id}",
    headers={"Authorization": f"Bearer {token}"},
)
with urllib.request.urlopen(request) as response:
    print("Final stock:", json.load(response)["stock_quantity"])
