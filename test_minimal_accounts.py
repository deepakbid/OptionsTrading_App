#!/usr/bin/env python3
"""
Minimal test for accounts router
"""
from fastapi import APIRouter

# Create a minimal router
router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/")
async def get_accounts():
    return {"message": "test"}

@router.post("/connect")
async def connect():
    return {"message": "connect"}

@router.post("/disconnect")
async def disconnect():
    return {"message": "disconnect"}

print("Router created successfully")
print(f"Prefix: {router.prefix}")
print(f"Tags: {router.tags}")
print(f"Routes: {len(router.routes)}")

for route in router.routes:
    print(f"  {route.methods} {route.path}")
