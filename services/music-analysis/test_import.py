#!/usr/bin/env python3
try:
    import enhanced_flask_api
    print("SUCCESS: Enhanced Flask API imports correctly")
    print("Available routes:")
    for rule in enhanced_flask_api.app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
