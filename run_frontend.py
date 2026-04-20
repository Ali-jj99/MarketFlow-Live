import sys
from streamlit.web import cli as stcli

if __name__ == "__main__":
    print("🚀 Starting Frontend Dashboard...")
    sys.argv = ["streamlit", "run", "frontend/dashboard.py"]
    sys.exit(stcli.main())