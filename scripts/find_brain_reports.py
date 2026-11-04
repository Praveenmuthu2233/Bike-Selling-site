import os
import glob

app_data = r"C:\Users\COREI5 8THGEN\.gemini\antigravity\brain"
conv_id = "a0275452-396f-403c-b255-8d8aa229d41f"

for p in glob.glob(os.path.join(app_data, conv_id, "*.md")):
    print("Found report:", p)
