"""Copy Flask assets to Vercel's CDN directory, preserving /static URLs."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = ROOT / "website" / "static"
    destination = ROOT / "public" / "static"
    shutil.copytree(source, destination, dirs_exist_ok=True)
    print("Copied website assets to public/static")

if __name__ == "__main__":
    main()
