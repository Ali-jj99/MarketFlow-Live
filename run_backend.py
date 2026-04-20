import uvicorn

if __name__ == "__main__":
    # This runs the server on port 8000
    print("🚀 Starting Backend Server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)