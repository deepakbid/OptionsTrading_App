#!/usr/bin/env python3
"""
Minimal test app to isolate accounts router issue
"""
from fastapi import FastAPI
import uvicorn

# Create minimal app
app = FastAPI(title="Minimal Test")

# Test basic endpoint
@app.get("/")
async def root():
    return {"message": "Hello World"}

# Test accounts endpoint directly
@app.get("/test-accounts")
async def test_accounts():
    return {"message": "Accounts test endpoint"}

if __name__ == "__main__":
    print("Starting minimal test app...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
