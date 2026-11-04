import mysql.connector
import inspect

sig = inspect.signature(mysql.connector.connect)
print("connect parameters:")
for p in sig.parameters.values():
    if "ssl" in p.name.lower():
        print(f"  {p.name}: {p.default}")
