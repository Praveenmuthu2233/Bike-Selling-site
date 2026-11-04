with open("my-node-app/.env", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            k = line.split("=")[0]
            print("my-node-app/.env key:", k)

with open(".env", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            k = line.split("=")[0]
            print("root .env key:", k)
