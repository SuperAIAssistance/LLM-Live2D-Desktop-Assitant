from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from loguru import logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBClient:
    """MongoDB client for character database operations"""
    
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB using connection string from environment variables"""
        try:
            # Get MongoDB URI from environment variables
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                raise ValueError("MONGODB_URI environment variable not set")
                
            self.client = AsyncIOMotorClient(mongodb_uri)
            self.db = self.client["character-db"]
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def get_character(self, character_id: str) -> Optional[dict]:
        """
        Retrieve character data by ID
        
        Args:
            character_id: The ID of the character to retrieve
            
        Returns:
            Character data dictionary or None if not found
        """
        try:
            # Convert string ID to ObjectId
            obj_id = ObjectId(character_id)
            logger.debug(f"Querying MongoDB with ObjectId: {obj_id}")
            
            character = await self.db.characters.find_one({"_id": obj_id})
            if character:
                # Convert ObjectId to string for JSON serialization
                character["_id"] = str(character["_id"])
                logger.debug(f"Found character: {character['name']}")
            else:
                logger.warning(f"No character found with ID: {character_id}")
            
            return character
            
        except Exception as e:
            logger.error(f"Error retrieving character {character_id}: {e}")
            return None

# Create singleton instance
mongo_client = MongoDBClient() 