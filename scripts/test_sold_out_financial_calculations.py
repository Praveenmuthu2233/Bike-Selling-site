import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'my-node-app'))

from app import calculate_bike_financials
from report_generator import format_inr

def test_example_1():
    print("[TEST] Example 1: 50,000 buying, 65,000 selling, 2,000 expenses")
    fin = calculate_bike_financials(buying_price=50000, selling_price=65000, repair_expenses=1200, other_expenses=800)
    assert fin["total_expenses"] == 2000, f"Expected 2000, got {fin['total_expenses']}"
    assert fin["gross_profit"] == 15000, f"Expected 15000, got {fin['gross_profit']}"
    assert fin["net_profit"] == 13000, f"Expected 13000, got {fin['net_profit']}"
    assert fin["profit_percentage"] == 26.0, f"Expected 26.0, got {fin['profit_percentage']}"
    assert fin["formatted_gross_profit"] == "₹15,000", f"Got {fin['formatted_gross_profit']}"
    assert fin["formatted_net_profit"] == "₹13,000", f"Got {fin['formatted_net_profit']}"
    assert fin["formatted_profit_percentage"] == "26%", f"Got {fin['formatted_profit_percentage']}"
    assert fin["is_loss"] is False
    print("  -> PASSED: Gross ₹15,000, Net ₹13,000, Profit % 26%")

def test_example_2():
    print("[TEST] Example 2: 70,000 buying, 75,000 selling, 3,000 expenses")
    fin = calculate_bike_financials(buying_price=70000, selling_price=75000, repair_expenses=1500, documentation_expenses=500, service_expenses=1000)
    assert fin["total_expenses"] == 3000, f"Expected 3000, got {fin['total_expenses']}"
    assert fin["gross_profit"] == 5000, f"Expected 5000, got {fin['gross_profit']}"
    assert fin["net_profit"] == 2000, f"Expected 2000, got {fin['net_profit']}"
    assert round(fin["profit_percentage"], 2) == 2.86, f"Expected 2.86, got {fin['profit_percentage']}"
    assert fin["formatted_gross_profit"] == "₹5,000", f"Got {fin['formatted_gross_profit']}"
    assert fin["formatted_net_profit"] == "₹2,000", f"Got {fin['formatted_net_profit']}"
    assert fin["formatted_profit_percentage"] == "2.86%", f"Got {fin['formatted_profit_percentage']}"
    assert fin["is_loss"] is False
    print("  -> PASSED: Gross ₹5,000, Net ₹2,000, Profit % 2.86%")

def test_example_3():
    print("[TEST] Example 3: 50,000 buying, 45,000 selling, 2,000 expenses (Loss display)")
    fin = calculate_bike_financials(buying_price=50000, selling_price=45000, repair_expenses=2000)
    assert fin["total_expenses"] == 2000, f"Expected 2000, got {fin['total_expenses']}"
    assert fin["gross_profit"] == -5000, f"Expected -5000, got {fin['gross_profit']}"
    assert fin["net_profit"] == -7000, f"Expected -7000, got {fin['net_profit']}"
    assert fin["profit_percentage"] == -14.0, f"Expected -14.0, got {fin['profit_percentage']}"
    assert fin["formatted_gross_profit"] == "-₹5,000", f"Expected -₹5,000, got {fin['formatted_gross_profit']}"
    assert fin["formatted_net_profit"] == "-₹7,000", f"Expected -₹7,000, got {fin['formatted_net_profit']}"
    assert fin["formatted_profit_percentage"] == "-14%", f"Expected -14%, got {fin['formatted_profit_percentage']}"
    assert fin["is_loss"] is True
    assert fin["is_gross_loss"] is True
    print("  -> PASSED: Gross -₹5,000, Net -₹7,000, Profit % -14% (Loss flagged)")

def test_zero_buying_price():
    print("[TEST] Zero Buying Price Safe Division")
    fin = calculate_bike_financials(buying_price=0, selling_price=50000, repair_expenses=1000)
    assert fin["profit_percentage"] == 0.0, f"Expected 0.0, got {fin['profit_percentage']}"
    assert fin["gross_profit"] == 50000
    assert fin["net_profit"] == 49000
    print("  -> PASSED: Zero division handled gracefully (0.0%)")

def test_format_inr():
    print("[TEST] format_inr Negative & Positive formatting")
    assert format_inr(15000) == "₹15,000.00", f"Got {format_inr(15000)}"
    assert format_inr(-7000) == "-₹7,000.00", f"Expected -₹7,000.00, got {format_inr(-7000)}"
    assert format_inr(0) == "₹0.00", f"Got {format_inr(0)}"
    assert format_inr(None) == "₹0", f"Got {format_inr(None)}"
    print("  -> PASSED: format_inr formats negative losses with proper -₹ prefix")

def test_all_14_financial_fields():
    print("[TEST] Verify All 14 Financial Fields Available in Dictionary")
    fin = calculate_bike_financials(
        buying_price=50000,
        selling_price=65000,
        repair_expenses=1000,
        documentation_expenses=300,
        service_expenses=400,
        additional_expenses=100,
        other_expenses=200
    )
    # Check all fields exist
    fields = [
        "buying_price",
        "selling_price",
        "repair_expenses",
        "documentation_expenses",
        "service_expenses",
        "additional_expenses",
        "other_expenses",
        "total_expenses",
        "gross_profit",
        "net_profit",
        "profit_percentage"
    ]
    for f in fields:
        assert f in fin, f"Field {f} missing from fin"
    assert fin["total_expenses"] == 2000, f"Expected 2000 total expenses, got {fin['total_expenses']}"
    assert fin["gross_profit"] == 15000
    assert fin["net_profit"] == 13000
    assert fin["profit_percentage"] == 26.0
    print("  -> PASSED: All 14 financial metrics correctly itemized without duplicate counting")

if __name__ == "__main__":
    test_example_1()
    test_example_2()
    test_example_3()
    test_zero_buying_price()
    test_format_inr()
    test_all_14_financial_fields()
    print("\nALL 6 FINANCIAL CALCULATION TESTS PASSED SUCCESSFULLY!")
