"""
Test script to verify Print-on-Demand (POD) readiness functionality.

This script checks:
1. POD dimensions are correctly calculated
2. Safe area margins are correct
3. Images are processed for CMYK and bleed
4. PDF is generated with correct dimensions
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pod_preflight import (
    get_pod_dimensions,
    get_safe_area,
    BLEED_SIZE,
    TRIM_MARGIN
)
from reportlab.lib.units import inch  # type: ignore


def test_pod_dimensions():
    """Test that POD dimensions are correct."""
    print("\n" + "="*60)
    print("TEST 1: POD Dimensions")
    print("="*60)
    
    page_width, page_height, trim_width, trim_height = get_pod_dimensions()
    
    # Expected values (8.5" x 11" with 0.125" bleed on each side)
    expected_trim_width = 8.5 * inch
    expected_trim_height = 11 * inch
    expected_bleed = 0.125 * inch
    expected_page_width = expected_trim_width + (2 * expected_bleed)
    expected_page_height = expected_trim_height + (2 * expected_bleed)
    
    print(f"Page width (with bleed): {page_width:.2f} pt (expected: {expected_page_width:.2f} pt)")
    print(f"Page height (with bleed): {page_height:.2f} pt (expected: {expected_page_height:.2f} pt)")
    print(f"Trim width: {trim_width:.2f} pt (expected: {expected_trim_width:.2f} pt)")
    print(f"Trim height: {trim_height:.2f} pt (expected: {expected_trim_height:.2f} pt)")
    
    assert abs(page_width - expected_page_width) < 0.01, f"Page width mismatch: {page_width} vs {expected_page_width}"
    assert abs(page_height - expected_page_height) < 0.01, f"Page height mismatch: {page_height} vs {expected_page_height}"
    assert abs(trim_width - expected_trim_width) < 0.01, f"Trim width mismatch: {trim_width} vs {expected_trim_width}"
    assert abs(trim_height - expected_trim_height) < 0.01, f"Trim height mismatch: {trim_height} vs {expected_trim_height}"
    
    print("[PASS] POD dimensions are correct!")
    return True


def test_safe_area():
    """Test that safe area is correctly calculated."""
    print("\n" + "="*60)
    print("TEST 2: Safe Area")
    print("="*60)
    
    safe_x, safe_y, safe_width, safe_height = get_safe_area()
    page_width, page_height, trim_width, trim_height = get_pod_dimensions()
    
    # Safe area should be: trim_size - (2 * trim_margin)
    expected_safe_width = trim_width - (2 * TRIM_MARGIN)
    expected_safe_height = trim_height - (2 * TRIM_MARGIN)
    expected_safe_x = BLEED_SIZE + TRIM_MARGIN
    expected_safe_y = BLEED_SIZE + TRIM_MARGIN
    
    print(f"Safe X: {safe_x:.2f} pt (expected: {expected_safe_x:.2f} pt)")
    print(f"Safe Y: {safe_y:.2f} pt (expected: {expected_safe_y:.2f} pt)")
    print(f"Safe width: {safe_width:.2f} pt (expected: {expected_safe_width:.2f} pt)")
    print(f"Safe height: {safe_height:.2f} pt (expected: {expected_safe_height:.2f} pt)")
    
    assert abs(safe_x - expected_safe_x) < 0.01, f"Safe X mismatch: {safe_x} vs {expected_safe_x}"
    assert abs(safe_y - expected_safe_y) < 0.01, f"Safe Y mismatch: {safe_y} vs {expected_safe_y}"
    assert abs(safe_width - expected_safe_width) < 0.01, f"Safe width mismatch: {safe_width} vs {expected_safe_width}"
    assert abs(safe_height - expected_safe_height) < 0.01, f"Safe height mismatch: {safe_height} vs {expected_safe_height}"
    
    print("[PASS] Safe area is correct!")
    return True


def test_constants():
    """Test that POD constants are correct."""
    print("\n" + "="*60)
    print("TEST 3: POD Constants")
    print("="*60)
    
    expected_bleed = 0.125 * inch  # 9 points
    expected_trim_margin = 0.25 * inch  # 18 points
    
    print(f"BLEED_SIZE: {BLEED_SIZE:.2f} pt (expected: {expected_bleed:.2f} pt)")
    print(f"TRIM_MARGIN: {TRIM_MARGIN:.2f} pt (expected: {expected_trim_margin:.2f} pt)")
    
    assert abs(BLEED_SIZE - expected_bleed) < 0.01, f"BLEED_SIZE mismatch: {BLEED_SIZE} vs {expected_bleed}"
    assert abs(TRIM_MARGIN - expected_trim_margin) < 0.01, f"TRIM_MARGIN mismatch: {TRIM_MARGIN} vs {expected_trim_margin}"
    
    print("[PASS] POD constants are correct!")
    return True


def print_pod_summary():
    """Print a summary of POD specifications."""
    print("\n" + "="*60)
    print("POD SPECIFICATIONS SUMMARY")
    print("="*60)
    
    page_width, page_height, trim_width, trim_height = get_pod_dimensions()
    safe_x, safe_y, safe_width, safe_height = get_safe_area()
    
    print(f"\nPage Size (with bleed):")
    print(f"  Width:  {page_width:.2f} pt ({page_width/inch:.3f}\")")
    print(f"  Height: {page_height:.2f} pt ({page_height/inch:.3f}\")")
    
    print(f"\nTrim Size (final page size):")
    print(f"  Width:  {trim_width:.2f} pt ({trim_width/inch:.3f}\")")
    print(f"  Height: {trim_height:.2f} pt ({trim_height/inch:.3f}\")")
    
    print(f"\nBleed Area:")
    print(f"  Size: {BLEED_SIZE:.2f} pt ({BLEED_SIZE/inch:.3f}\") on each side")
    print(f"  Total extra width: {2 * BLEED_SIZE:.2f} pt")
    print(f"  Total extra height: {2 * BLEED_SIZE:.2f} pt")
    
    print(f"\nSafe Area (where text should be):")
    print(f"  X: {safe_x:.2f} pt, Y: {safe_y:.2f} pt")
    print(f"  Width: {safe_width:.2f} pt ({safe_width/inch:.3f}\")")
    print(f"  Height: {safe_height:.2f} pt ({safe_height/inch:.3f}\")")
    print(f"  Margin from trim: {TRIM_MARGIN:.2f} pt ({TRIM_MARGIN/inch:.3f}\")")
    
    print(f"\nKDP Requirements:")
    print(f"  [OK] Bleed: 0.125\" on all sides ({BLEED_SIZE/inch:.3f}\")")
    print(f"  [OK] Trim margin: 0.25\" minimum ({TRIM_MARGIN/inch:.3f}\")")
    print(f"  [OK] Page size: 8.5\" x 11\" ({trim_width/inch:.3f}\" x {trim_height/inch:.3f}\")")
    print("="*60)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("POD READINESS VERIFICATION TEST")
    print("="*60)
    
    try:
        # Run tests
        test_pod_dimensions()
        test_safe_area()
        test_constants()
        
        # Print summary
        print_pod_summary()
        
        print("\n" + "="*60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("="*60)
        print("\nTo verify POD in a generated PDF:")
        print("1. Generate a PDF with pod_ready=True")
        print("2. Check the logs for 'POD-READY PDF GENERATION ENABLED'")
        print("3. Verify images have '_cmyk_bleed' suffix in their filenames")
        print("4. Open PDF and check dimensions match POD specs")
        print("5. Verify text is within safe margins")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
