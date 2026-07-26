# Import FastAPI so we can create a web application.
from fastapi import FastAPI, HTTPException

# Import BaseModel so we can describe the shape of request body data.
from pydantic import BaseModel

# Create the FastAPI application instance.
app = FastAPI()

# Store notes in memory for now.
notes = []

# Keep track of the next available note ID.
next_note_id = 1


# Define the data model for a note sent by the user.
class NoteCreate(BaseModel):
    # The note title is required and must be a string.
    title: str

    # The note content is required and must be a string.
    content: str


class Note(BaseModel):
    id: int
    title: str
    content: str    


# Register a GET endpoint for the root URL.
@app.get("/")
# Define the function that runs when someone visits "/".
def read_root():
    # Return a JSON response with a welcome message.
       return {"message": "Welcome to Atlas Lite"}

# Register a POST endpoint for creating or saving notes.
@app.post("/notes")
# Define the function that runs when someone sends note data to "/notes".
def save_note(note: NoteCreate):
    global next_note_id

    # Save the received note in memory.

    new_note = Note(
         id = next_note_id,
         title = note.title,
         content = note.content,
    )
    notes.append(new_note)

    next_note_id += 1 

    # Return a simple response that echoes the received note back to the user.
    return {

        "status": "saved",
        "note": new_note,
    }


# Register a GET endpoint for returning all saved notes.
@app.get("/notes")
# Define the function that runs when someone asks for saved notes.
def get_notes():
    # Return the complete in-memory list of notes.
    return notes


# Register a GET endpoint for returning notes by their id.
@app.get("/notes/{note_id}")
# Define the function that runs when someone requests a note by its ID.
def get_note(note_id: int):
     
     for note in notes:
        if note.id == note_id:
            return note
        
    # Loop finished
    # Nothing matched
     raise HTTPException(
       status_code=404,
       detail="Note not found"
)


# Register a PUT endpoint for updating notes by their id.
@app.put("/notes/{note_id}")
# Define the function that runs when user wants to update an existing note.
def update_note(note_id: int, updated_note: NoteCreate):
    for note in notes:
      if note.id == note_id:
        note.title = updated_note.title
        note.content = updated_note.content

        return {
            "status": "updated",
            "note": note,
        }

    # Loop finished
    # Nothing matched
    raise HTTPException(
      status_code=404,
      detail="Note not found"
)


# Register a DELETE endpoint for deleting notes by their id.
@app.delete("/notes/{note_id}")
# Define the function that runs when the user wants to delete an existing note.
def delete_note(note_id: int):
    for note in notes:
      if note.id == note_id:
        notes.remove(note)

        return {
            "status": "deleted",
            "message": "Note deleted successfully"
        }

    # Loop finished
    # Nothing matched
    raise HTTPException(
      status_code=404,
      detail="Note not found"
)