"""Quick check: what does the venues payload look like end-to-end?"""
import json
import uuid

from dotenv import load_dotenv
load_dotenv()

import agent

sid = f"check-{uuid.uuid4().hex[:8]}"
result = agent.run_turn(sid, "demo_user_99", "find me a restaurant in westwood tonight")
agent.reset_session(sid)

print("=" * 60)
print("VENUES PAYLOAD (what the frontend receives):")
print("=" * 60)
for i, v in enumerate(result.get("venues", []), 1):
    print(f"\n#{i} {v.get('venue_name')}")
    print(f"  cuisine: {v.get('cuisine')!r}")
    print(f"  address: {v.get('address')!r}")
    print(f"  description: {v.get('description')!r}")
    print(f"  popular_items: {v.get('popular_items')!r}")
