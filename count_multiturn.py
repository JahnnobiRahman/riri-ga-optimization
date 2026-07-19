import json
from collections import Counter

path = "all_data.jsonl"

n_users = 0
n_sessions = 0
n_multiturn_sessions = 0
turn_counts = []
exchange_counts = []
empty_first_turn = 0

with open(path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        user = json.loads(line)
        n_users += 1

        for session in user.get("sessions", []):
            n_sessions += 1
            turns = session.get("turns", [])
            n_turns = len(turns)
            turn_counts.append(n_turns)

            user_msgs = [t for t in turns if t.get("is_bot") == 0 and t.get("message", "").strip() != ""]
            n_exchanges = len(user_msgs)
            exchange_counts.append(n_exchanges)

            if turns and turns[0].get("message", "") == "":
                empty_first_turn += 1

            if n_exchanges > 1:
                n_multiturn_sessions += 1

print(f"Total users:                 {n_users}")
print(f"Total sessions (conversations): {n_sessions}")
print(f"Sessions with empty first turn: {empty_first_turn}")
print(f"Multi-turn sessions (>1 user msg): {n_multiturn_sessions}")
print(f"Single-turn sessions:            {n_sessions - n_multiturn_sessions}")
if exchange_counts:
    print(f"Avg user exchanges per session:  {sum(exchange_counts)/len(exchange_counts):.2f}")
    print(f"Min/Max exchanges per session:   {min(exchange_counts)} / {max(exchange_counts)}")
if turn_counts:
    print(f"Avg total turns (user+bot) per session: {sum(turn_counts)/len(turn_counts):.2f}")

dist = Counter(exchange_counts)
print("\nDistribution of exchange counts (top 10):")
for k, v in sorted(dist.items())[:10]:
    print(f"  {k} exchange(s): {v} sessions")
