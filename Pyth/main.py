from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from bson import ObjectId
import motor.motor_asyncio

app = FastAPI()

# Connect to Mongo Atlas
def get_db():
    client = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://lydoncamilleri05:username@lydoncluster.an0c0vd.mongodb.net/?retryWrites=true&w=majority&appName=LydonCluster")
    return client["multimedia_db"]


class PlayerScore(BaseModel):
    player_name: str
    score: int

# Root route 
@app.get("/")
async def read_root():
    return {"message": "Welcome to the API!"}

# POST route to upload sprites
@app.post("/sprites")
async def upload_sprite(file: UploadFile = File(...)):
    if file.content_type not in ["image/png", "image/jpeg"]: # File Extennsion validation
        raise HTTPException(status_code=400, detail="Only PNG and JPG images are allowed.")
    
    content = await file.read() # Reads binary content
    if len(content) > 2 * 1024 * 1024: # Limit to 2MB
        raise HTTPException(status_code=400, detail="Image file too large (max 2MB).")

    db = get_db()
    sprite_doc = {"filename": file.filename, "content": content} # Formats data into entry
    result = await db.sprites.insert_one(sprite_doc) # Inserts entry into table
    return {"message": "Sprite uploaded", "id": str(result.inserted_id)} # Confirms POST request

# POST route to upload audio files
@app.post("/audio")
async def upload_audio(file: UploadFile = File(...)):
    if file.content_type not in ["audio/mpeg", "audio/wav"]:
        raise HTTPException(status_code=400, detail="Only MP3 or WAV files are allowed.")
    
    content = await file.read()
    if len(content) > 5 * 1024 * 1024: # Limit to 5MB
        raise HTTPException(status_code=400, detail="Audio file too large (max 5MB).")

    db = get_db()
    audio_doc = {"filename": file.filename, "content": content}
    result = await db.audio.insert_one(audio_doc)
    return {"message": "Audio file uploaded", "id": str(result.inserted_id)}

# POST route to add player scores
@app.post("/scores")
async def add_score(score: PlayerScore):
    db = get_db()
    score_doc = score.dict() 
    result = await db.scores.insert_one(score_doc)
    return {"message": "Score recorded", "id": str(result.inserted_id)}


# GET route to retrieve sprites
@app.get("/sprites")
async def get_sprites():
    db = get_db()
    sprites = [] # Contains entries to be printed
    async for sprite in db.sprites.find({}, {"content": 0}): # Finds all entries, Exclude binary field
        sprite["_id"] = str(sprite["_id"]) # Convert _id to string
        sprites.append(sprite) # Appends entry to be printed
    return {"sprites": sprites}

# GET route to retrieve audios
@app.get("/audio")
async def get_audio():
    db = get_db()
    audio_files = []
    async for audio in db.audio.find({}, {"content": 0}):
        audio["_id"] = str(audio["_id"])
        audio_files.append(audio)
    return {"audio_files": audio_files}

# GET route to retrieve player scores
@app.get("/scores")
async def get_scores():
    db = get_db()
    scores = []
    async for score in db.scores.find():
        score["_id"] = str(score["_id"])  
        scores.append(score)
    return {"scores": scores}


# PUT route to replace/update sprites
@app.put("/sprites/{sprite_id}")
async def update_sprite(sprite_id: str, file: UploadFile = File(...)):
    if file.content_type not in ["image/png", "image/jpeg"]: # File Extension validation
        raise HTTPException(status_code=400, detail="Only PNG and JPG images are allowed.")
    
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image file too large (max 2MB).") # Limit to 2MB

    db = get_db()
    result = await db.sprites.update_one(
        {"_id": ObjectId(sprite_id)}, # Updates entry with given ID
        {"$set": {"filename": file.filename, "content": content}} # using uploaded file
    )
    if result.matched_count == 0: # Validates if entry has been found to be changed
        raise HTTPException(status_code=404, detail="Sprite not found")
    return {"message": "Sprite updated"}

# PUT route to replace/update audio
@app.put("/audio/{audio_id}")
async def update_audio(audio_id: str, file: UploadFile = File(...)):
    if file.content_type not in ["audio/mpeg", "audio/wav"]:
        raise HTTPException(status_code=400, detail="Only MP3 or WAV files are allowed.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file too large (max 5MB).")

    db = get_db()
    result = await db.audio.update_one(
        {"_id": ObjectId(audio_id)},
        {"$set": {"filename": file.filename, "content": content}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return {"message": "Audio file updated"}

# PUT route to replace/update score
@app.put("/scores/{score_id}")
async def update_score(score_id: str, score: PlayerScore):
    db = get_db()
    result = await db.scores.update_one(
        {"_id": ObjectId(score_id)},
        {"$set": score.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Score not found")
    return {"message": "Score updated"}


# DELETE route to remove sprites
@app.delete("/sprites/{sprite_id}")
async def delete_sprite(sprite_id: str):
    db = get_db()
    result = await db.sprites.delete_one({"_id": ObjectId(sprite_id)}) # Delete entry with a given ID
    if result.deleted_count == 0: # Validate a score has been removed
        raise HTTPException(status_code=404, detail="Sprite not found") 
    return {"message": "Sprite deleted"}

# DELETE route to remove audio
@app.delete("/audio/{audio_id}")
async def delete_audio(audio_id: str):
    db = get_db()
    result = await db.audio.delete_one({"_id": ObjectId(audio_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Audio file not found")
    return {"message": "Audio file deleted"}

# DELETE route to remove score
@app.delete("/scores/{score_id}")
async def delete_score(score_id: str):
    db = get_db()
    result = await db.scores.delete_one({"_id": ObjectId(score_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Score not found")
    return {"message": "Score deleted"}