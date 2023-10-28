import requests
from bs4 import BeautifulSoup
import os
import sys

print("Checking for updates...")

# https://raw.githubusercontent.com/CaptainDeathead/Plazma-Engine/main/version.txt

with open("version.txt", "r") as f:
    __version__ = f.read()
    f.close()

r = requests.get("https://raw.githubusercontent.com/CaptainDeathead/Plazma-Engine/main/version.txt")
version = r.text
print("Current version: " + version)
print("This version: " + __version__)

if version == __version__:
    print("No update available")
    exit()

print("Update available!")
print("Getting update...")
r = requests.get("https://raw.githubusercontent.com/CaptainDeathead/Plazma-Engine/main/changelog.txt")
changelog = r.text
print(f"Changelog:\n{changelog}")
print("Updating...")

changelog = changelog.split("\n")

for line in changelog:
    if line == "":
        continue
    else:
        print(f"Getting {line}")
        r = requests.get(f"https://raw.githubusercontent.com/CaptainDeathead/Plazma-Engine/main/{line}")
        print(f"Writing to {line}")
        with open(line, "w") as f:
            f.write(r.text)
            f.close()
        print(f"Done writing to {line}")

print("Done! Restarting...")

os.system("python main.py")
sys.exit()