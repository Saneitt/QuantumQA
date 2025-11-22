#!/usr/bin/env python3
"""
Streamlit Cloud Wrapper for QuantumQA Application

This wrapper ensures the QuantumQA app runs identically on Streamlit Cloud and locally.

Responsibilities:
1. Determine repo root and set working directory correctly
2. Add backend and repo root to sys.path for imports to work
3. Load Streamlit Cloud secrets into os.environ (for GEMINI_API_KEY, etc.)
4. Fall back to local .env loading if available and python-dotenv is installed
5. Execute app.py with proper __main__ semantics using runpy.run_path()
6. Provide diagnostics if import/execution fails

This approach ensures:
- Relative paths in app.py (assets/, db/, backend/, etc.) work correctly
- Environment variables (GEMINI_API_KEY) are available from Streamlit secrets or .env
- The app runs exactly as if you ran: streamlit run app.py
"""

import os
import sys
import runpy
import traceback
from pathlib import Path


def setup_environment_and_run():
    """
    Set up paths, environment, and execute app.py with __main__ semantics.
    """
    
    # ========== STEP 1: DETERMINE REPO ROOT ==========
    # This wrapper is at: ui/streamlit_app.py
    # Repo root is the parent of the ui/ directory
    WRAPPER_DIR = Path(__file__).parent  # ui/
    REPO_ROOT = WRAPPER_DIR.parent       # QuantumQA/
    
    print(f"[INFO] Repo root: {REPO_ROOT}")
    print(f"[INFO] Wrapper dir: {WRAPPER_DIR}")
    
    # ========== STEP 2: CHANGE WORKING DIRECTORY ==========
    # Ensure all relative paths in app.py work (e.g., ./db, ./assets, ./backend)
    try:
        os.chdir(REPO_ROOT)
        print(f"[INFO] Working directory set to: {os.getcwd()}")
    except Exception as e:
        print(f"[ERROR] Failed to change working directory to {REPO_ROOT}: {e}")
        traceback.print_exc()
        raise
    
    # ========== STEP 3: SET UP sys.path ==========
    # Ensure repo root and backend are importable
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    if str(REPO_ROOT / "backend") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "backend"))
    
    print(f"[INFO] sys.path updated. Top entries:")
    for i, p in enumerate(sys.path[:3]):
        print(f"        {i}: {p}")
    
    # ========== STEP 4: LOAD SECRETS & ENVIRONMENT ==========
    # Priority: Streamlit secrets > .env file > os.environ
    
    # Try to load Streamlit secrets (available on Streamlit Cloud)
    secrets_loaded = False
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and st.secrets:
            print("[INFO] Streamlit secrets detected. Loading into os.environ...")
            for key, value in st.secrets.items():
                os.environ[key] = str(value)
            secrets_loaded = True
            print(f"[INFO] Loaded {len(st.secrets)} secret(s) from Streamlit")
    except Exception as e:
        print(f"[DEBUG] Streamlit secrets not available (expected locally): {e}")
    
    # Fall back to .env file if python-dotenv is available
    if not secrets_loaded:
        env_file = REPO_ROOT / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
                print(f"[INFO] Loaded .env from {env_file}")
            except ImportError:
                print(f"[DEBUG] python-dotenv not installed; .env will not be loaded")
            except Exception as e:
                print(f"[WARNING] Failed to load .env: {e}")
        else:
            print(f"[DEBUG] No .env file found at {env_file}")
    
    # ========== STEP 5: VERIFY ENVIRONMENT ==========
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        print(f"[INFO] GEMINI_API_KEY is set (length: {len(gemini_key)})")
    else:
        print("[WARNING] GEMINI_API_KEY not set in environment. Backend may fail if used.")
    
    # ========== STEP 6: EXECUTE app.py ==========
    app_file = REPO_ROOT / "app.py"
    
    if not app_file.exists():
        print(f"[ERROR] app.py not found at {app_file}")
        print(f"[DEBUG] Contents of {REPO_ROOT}:")
        try:
            for item in sorted(REPO_ROOT.iterdir())[:10]:
                print(f"        {item.name}")
        except Exception as e:
            print(f"        (error listing: {e})")
        raise FileNotFoundError(f"app.py not found at {app_file}")
    
    print(f"[INFO] Executing {app_file} with __main__ semantics...")
    
    try:
        # Use runpy.run_path to execute app.py as if run by the Python interpreter
        # This ensures __name__ == "__main__" and all module-level code runs
        runpy.run_path(str(app_file), run_name="__main__")
    except Exception as e:
        print(f"\n[ERROR] Exception occurred while executing app.py:")
        print(f"{type(e).__name__}: {e}")
        traceback.print_exc()
        
        # Print diagnostic info
        print(f"\n[DIAGNOSTICS]")
        print(f"  REPO_ROOT: {REPO_ROOT}")
        print(f"  Working directory: {os.getcwd()}")
        print(f"  app.py exists: {app_file.exists()}")
        print(f"  backend/ exists: {(REPO_ROOT / 'backend').exists()}")
        print(f"  sys.path (first 3):")
        for i, p in enumerate(sys.path[:3]):
            print(f"    {i}: {p}")
        
        raise


if __name__ == "__main__":
    setup_environment_and_run()

