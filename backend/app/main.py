# Import FastAPI so we can create a web application.
from fastapi import FastAPI

# Import BaseModel so we can describe the shape of request body data.
from pydantic import BaseModel

# Create the FastAPI application instance.
app = FastAPI()


# Define the data model for a note sent by the user.
class Note(BaseModel):
    # The note title is required and must be a string.
    title: str

    # The note content is required and must be a string.
    content: str


# Register a GET endpoint for the root URL.
@app.get("/")
# Define the function that runs when someone visits "/".
def read_root():
    # Return a JSON response with a welcome message.
    return {"message": "Welcome from Feature Branch"}


# Register a POST endpoint for creating or saving notes.
@app.post("/notes")
# Define the function that runs when someone sends note data to "/notes".
def save_note(note: Note):
    # Return a simple response that echoes the received note back to the user.
    return {
        "status": "saved",
        "note": {
            "title": note.title,
            "content": note.content,
        },
    }
