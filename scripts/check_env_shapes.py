from dotenv import dotenv_values

v_local = dotenv_values('my-node-app/.env')
v_root = dotenv_values('.env')

print("my-node-app/.env keys & shapes:")
for k, val in v_local.items():
    if "pass" in k.lower() or "secret" in k.lower():
        print(f"  {k}: len={len(val or '')}, hash={hash(val)}")
    else:
        print(f"  {k}: {repr(val)}")

print("\nroot .env keys & shapes:")
for k, val in v_root.items():
    if "pass" in k.lower() or "secret" in k.lower():
        print(f"  {k}: len={len(val or '')}, hash={hash(val)}")
    else:
        print(f"  {k}: {repr(val)}")
