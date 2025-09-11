# test_main.py - TEST FILE
print("DEBUG: Using test_main.py - UNIQUE ID: TEST_MAIN_004")
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Test main.py file", "status": "working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
