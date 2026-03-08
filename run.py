import uvicorn
from api.main import app

if __name__ == "__main__":
    print("🚀 OSINT System running locally!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
