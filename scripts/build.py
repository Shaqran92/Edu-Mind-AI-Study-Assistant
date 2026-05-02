# scripts/build.py
"""
Build script for creating EduMind distributables.
Supports Windows, macOS, and Linux via PyInstaller.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

# Project root
ROOT = Path(__file__).parent.parent
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"


def get_version() -> str:
    """Get version from pyproject.toml."""
    try:
        with open(ROOT / "pyproject.toml") as f:
            for line in f:
                if line.startswith("version"):
                    return line.split("=")[1].strip().strip('"')
    except:
        pass
    return "1.0.0"


def clean():
    """Clean build artifacts."""
    print("🧹 Cleaning build directories...")
    
    for dir_path in [DIST_DIR, BUILD_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   Removed: {dir_path}")
    
    # Remove .spec files
    for spec in ROOT.glob("*.spec"):
        spec.unlink()
        print(f"   Removed: {spec}")


def build_windows():
    """Build Windows executable."""
    print("\n📦 Building Windows executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "EduMind",
        "--windowed",  # No console window
        "--onefile",   # Single executable
        "--icon", str(ROOT / "assets" / "icon.ico") if (ROOT / "assets" / "icon.ico").exists() else "",
        "--add-data", f"{ROOT / 'assets'};assets",
        "--add-data", f"{ROOT / 'prompts.py'};.",
        "--hidden-import", "pyttsx3.drivers.sapi5",
        "--hidden-import", "openai",
        "--hidden-import", "google.generativeai",
        str(ROOT / "app.py")
    ]
    
    # Remove empty icon argument if no icon
    cmd = [c for c in cmd if c]
    
    subprocess.run(cmd, check=True)
    
    print("✅ Windows build complete!")
    print(f"   Output: {DIST_DIR / 'EduMind.exe'}")


def build_macos():
    """Build macOS application bundle."""
    print("\n📦 Building macOS application...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "EduMind",
        "--windowed",
        "--onedir",    # App bundle
        "--icon", str(ROOT / "assets" / "icon.icns") if (ROOT / "assets" / "icon.icns").exists() else "",
        "--add-data", f"{ROOT / 'assets'}:assets",
        "--add-data", f"{ROOT / 'prompts.py'}:.",
        "--hidden-import", "pyttsx3.drivers.nsss",
        "--osx-bundle-identifier", "com.edumind.app",
        str(ROOT / "app.py")
    ]
    
    cmd = [c for c in cmd if c]
    
    subprocess.run(cmd, check=True)
    
    print("✅ macOS build complete!")
    print(f"   Output: {DIST_DIR / 'EduMind.app'}")


def build_linux():
    """Build Linux executable."""
    print("\n📦 Building Linux executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "edumind",
        "--onefile",
        "--add-data", f"{ROOT / 'assets'}:assets",
        "--add-data", f"{ROOT / 'prompts.py'}:.",
        "--hidden-import", "pyttsx3.drivers.espeak",
        str(ROOT / "app.py")
    ]
    
    subprocess.run(cmd, check=True)
    
    print("✅ Linux build complete!")
    print(f"   Output: {DIST_DIR / 'edumind'}")


def create_installer_windows():
    """Create Windows installer using NSIS (if available)."""
    print("\n📦 Creating Windows installer...")
    
    nsis_script = ROOT / "scripts" / "installer.nsi"
    
    if not shutil.which("makensis"):
        print("⚠️  NSIS not found. Skipping installer creation.")
        return
    
    if not nsis_script.exists():
        print("⚠️  NSIS script not found. Skipping installer creation.")
        return
    
    subprocess.run(["makensis", str(nsis_script)], check=True)
    print("✅ Windows installer created!")


def main():
    """Main build script."""
    print("=" * 60)
    print(f"🎓 EduMind Build Script - v{get_version()}")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Parse arguments
    args = sys.argv[1:]
    
    if not args or "clean" in args:
        clean()
    
    if not args or "all" in args:
        if sys.platform == "win32":
            build_windows()
        elif sys.platform == "darwin":
            build_macos()
        else:
            build_linux()
    elif "windows" in args:
        build_windows()
    elif "macos" in args:
        build_macos()
    elif "linux" in args:
        build_linux()
    
    if "installer" in args and sys.platform == "win32":
        create_installer_windows()
    
    print("\n" + "=" * 60)
    print("🎉 Build complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
