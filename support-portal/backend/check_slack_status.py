"""Check Slack integration status"""
import os

print("=" * 60)
print("SLACK INTEGRATION DIAGNOSTIC")
print("=" * 60)

# Check if requests is available
try:
    import requests
    print("✅ requests library is installed")
    print(f"   Version: {requests.__version__}")
    HAS_REQUESTS = True
except ImportError as e:
    print("❌ requests library NOT installed")
    print(f"   Error: {e}")
    print("   Install with: pip install requests")
    HAS_REQUESTS = False

print()

# Check webhook URL
webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
print(f"Webhook URL: {webhook_url}")

print()

if HAS_REQUESTS:
    print("Testing network connectivity to Slack...")
    try:
        response = requests.get("https://slack.com", timeout=5)
        print(f"✅ Can reach Slack (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Cannot reach Slack: {e}")

print()
print("=" * 60)
