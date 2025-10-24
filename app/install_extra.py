import os
import subprocess

packages = [
    "sentence-transformers",
    "chromadb",
    "google-generativeai",
    "pypdf",
]

for pkg in packages:
    try:
        __import__(pkg.split("-")[0])
    except ImportError:
        subprocess.run(["pip", "install", pkg], check=True)
