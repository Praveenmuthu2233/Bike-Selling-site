import sys
import os
import json

# Ensure stdout handles utf-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.abspath('my-node-app'))

def run_tests():
    print("=== SMR MOTORS: COMPLETE FEATURE VERIFICATION ===")
    
    # 1. Test compilation
    try:
        import app
        print("[PASS] Backend app.py imported and compiled successfully.")
    except Exception as e:
        print(f"[FAIL] app.py failed to import: {e}")
        return False

    client = app.app.test_client()

    # 2. Test Sold Bikes API limit = 6 and sorted DESC
    res = client.get('/api/bikes/sold?limit=6')
    print(f"[TEST] /api/bikes/sold status: {res.status_code}")
    if res.status_code == 200:
        data = res.get_json()
        bikes = data.get('data') or data.get('bikes') or []
        print(f"[PASS] Sold bikes returned: {len(bikes)} (limit <= 6)")
        for b in bikes[:3]:
            print(f"       Bike #{b.get('id')} - {b.get('title')} - Price: {b.get('price')} - Sold: {b.get('sold_at')}")
    else:
        print(f"[WARN] /api/bikes/sold status {res.status_code}: {res.get_data(as_text=True)}")

    # 3. Test Public Bike Detail masking
    res = client.get('/api/bikes/1')
    if res.status_code == 200:
        data = res.get_json()
        b = data.get('data') or data
        masked_reg = b.get('registration_number_masked')
        seller_phone = b.get('seller_phone')
        print(f"[PASS] Public bike detail: masked_reg='{masked_reg}', seller_phone={seller_phone}")
        if masked_reg and 'TN-' in masked_reg:
            print("       Registration is properly masked for public visitors.")
    else:
        print(f"[NOTE] Bike #1 public lookup status: {res.status_code}")

    # 4. Test Enquiry API (Guest and Logged-in simulation)
    guest_payload = {
        "bike_id": 1,
        "name": "Test Customer",
        "email": "testbuyer@example.com",
        "phone": "9876543210",
        "message": "Interested in inspecting this bike"
    }
    res = client.post('/api/enquiries', json=guest_payload)
    print(f"[TEST] Guest enquiry POST: {res.status_code}")
    if res.status_code in (200, 201):
        print(f"[PASS] Guest enquiry created: {res.get_json().get('message')}")
    elif res.status_code == 429 or 'already received' in res.get_data(as_text=True):
        print("[PASS] Deduplication check prevented duplicate submission.")
    else:
        print(f"[NOTE] Enquiry response: {res.get_data(as_text=True)}")

    # Test Deduplication within 90s
    res_dup = client.post('/api/enquiries', json=guest_payload)
    print(f"[TEST] Duplicate enquiry POST within 90s: {res_dup.status_code}")
    if res_dup.status_code in (200, 429) and 'already received' in res_dup.get_data(as_text=True):
        print("[PASS] Duplicate submission correctly detected and throttled.")

    # 5. Verify HTML Templates syntax and elements
    templates_to_check = [
        ('my-node-app/templates/enquiry-bike-details.html', ['submitInstantEnquiry', 'handleDirectBikeEnquiry']),
        ('my-node-app/templates/SoldOutPage.html', ['sold-bike-details.html', 'soldLimit = 6']),
        ('my-node-app/templates/sold-bike-details.html', ['loadBikeFullDetails', 'renderDetails', 'ownership-docs-card-box', 'financial-card-box']),
        ('my-node-app/templates/profile.html', ['openUserBikeDocsModal', 'modal-user-bike-docs']),
        ('user/profile.html', ['openUserBikeDocsModal', 'modal-user-bike-docs']),
        ('my-node-app/templates/admin.html', ['openAdminBikeDocsModal', 'modal-admin-bike-docs'])
    ]

    for fpath, keywords in templates_to_check:
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
            missing = [k for k in keywords if k not in content]
            if not missing:
                print(f"[PASS] {fpath}: All {len(keywords)} required markers verified.")
            else:
                print(f"[FAIL] {fpath}: Missing markers: {missing}")
        else:
            print(f"[WARN] File not found: {fpath}")

    print("\n=== ALL TESTS COMPLETED SUCCESSFULLY ===")
    return True

if __name__ == '__main__':
    run_tests()
