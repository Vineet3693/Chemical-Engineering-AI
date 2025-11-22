"""
Setup Helper Script for Chemical Engineering RAG System
Run this script to verify your setup and get started
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_directories():
    """Check if required directories exist"""
    base_dir = Path(__file__).parent
    
    required_dirs = [
        base_dir / "data" / "books",
        base_dir / "data" / "chroma_db",
        base_dir / "config",
        base_dir / "src",
        base_dir / "utils"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✅ Directory exists: {dir_path.relative_to(base_dir)}")
        else:
            print(f"❌ Directory missing: {dir_path.relative_to(base_dir)}")
            all_exist = False
    
    return all_exist

def check_env_file():
    """Check if .env file exists and has API key"""
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Please copy .env.example to .env and add your API key")
        return False
    
    print("✅ .env file exists")
    
    # Check if API key is set
    with open(env_path, 'r') as f:
        content = f.read()
        if "your_gemini_api_key_here" in content or "GOOGLE_API_KEY=" not in content:
            print("⚠️  Warning: API key may not be configured")
            print("   Please edit .env and add your Google Gemini API key")
            return False
    
    print("✅ API key appears to be configured")
    return True

def check_books():
    """Check if PDF books are present"""
    books_dir = Path(__file__).parent / "data" / "books"
    
    if not books_dir.exists():
        print("❌ Books directory not found")
        return False
    
    pdf_files = list(books_dir.glob("*.pdf"))
    
    if len(pdf_files) == 0:
        print("⚠️  No PDF books found in data/books/")
        print("   Please add 4-5 Chemical Engineering PDF textbooks")
        return False
    
    print(f"✅ Found {len(pdf_files)} PDF book(s):")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'chromadb',
        'google.generativeai',
        'sentence_transformers',
        'fitz',  # PyMuPDF
        'reportlab',
        'docx'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('.', '_'))
            print(f"✅ Package installed: {package}")
        except ImportError:
            print(f"❌ Package missing: {package}")
            missing.append(package)
    
    if missing:
        print("\n⚠️  Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Run all checks"""
    print("=" * 60)
    print("Chemical Engineering RAG System - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Directory Structure", check_directories),
        ("Environment File", check_env_file),
        ("PDF Books", check_books),
        ("Dependencies", check_dependencies)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n📋 Checking: {name}")
        print("-" * 60)
        results.append(check_func())
    
    print("\n" + "=" * 60)
    print("Setup Verification Summary")
    print("=" * 60)
    
    if all(results):
        print("✅ All checks passed! You're ready to run the application.")
        print("\nNext steps:")
        print("1. Run: streamlit run app.py")
        print("2. Open browser to: http://localhost:8501")
        print("3. Click 'Initialize System' in the sidebar")
        print("4. Click 'Process Books' to index your PDFs")
        print("5. Start asking questions!")
    else:
        print("⚠️  Some checks failed. Please review the issues above.")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Create .env file: cp .env.example .env")
        print("3. Add API key to .env file")
        print("4. Add PDF books to data/books/ directory")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
