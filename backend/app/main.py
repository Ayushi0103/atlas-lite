# Import FastAPI so we can create a web application.
from fastapi import FastAPI

# Create the FastAPI application instance.
app = FastAPI()


# Register a GET endpoint for the root URL.
@app.get("/")
# Define the function that runs when someone visits "/".
def read_root():
    # Return a JSON response with a welcome message.
    return {"message": "Welcome to Atlas Lite"}
