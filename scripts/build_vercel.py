"""Copy Flask assets to Vercel's CDN directory, preserving /static URLs."""
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]

def main():
    source = ROOT / "website" / "static"
    destination = ROOT / "public" / "static"
    shutil.copytree(source, destination, dirs_exist_ok=True)
    print("Copied website assets to public/static")
    # Fail the build if runtime dependencies or bundled data are missing.
    sys.path.insert(0, str(ROOT))
    from website.server import app
    with app.test_client() as client:
        response = client.get("/")
        if response.status_code != 200:
            raise RuntimeError("Flask startup check failed")
    print("Flask runtime import and homepage check passed")

if __name__ == "__main__":
    main()
