from fastapi import FastAPI

from api.v1 import api_endpoints

app = FastAPI()
app.include_router(api_endpoints)

if __name__ == "__main__":
    import uvicorn
    # for running on localhost
    # uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
    # for running docker container-->use host 0.0.0.0 so that it can be accessed via all the IP addresses
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
