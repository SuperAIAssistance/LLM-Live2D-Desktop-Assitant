from typing import Optional, Dict, Any
from fastapi import WebSocket
import json
import os
import yaml
from loguru import logger
from bson.objectid import ObjectId

from ..db.mongo_client import mongo_client
from ..service_context import ServiceContext

class SaaSHandler:
    """Handler for SaaS-related operations"""
    
    def __init__(self):
        """Initialize SaaS handler"""
        pass

    @staticmethod
    async def handle_character_load(
        websocket: WebSocket, 
        client_uid: str, 
        character_id: str,
        client_context: ServiceContext
    ) -> None:
        """
        Handle loading character from MongoDB and creating/updating YAML config
        
        Args:
            websocket: WebSocket connection
            client_uid: Client's unique identifier
            character_id: Character ID to load
            client_context: Client's service context
        """
        try:
            logger.debug(f"Received load-character request for ID: {character_id}")
            
            if not character_id:
                raise ValueError("No character ID provided")
            
            # Get character data from MongoDB
            character = await mongo_client.get_character(character_id)
            logger.debug(f"Retrieved character data from MongoDB: {character}")
            
            if not character:
                raise ValueError(f"Character {character_id} not found")
            
            # Process Live2D model information
            model_dict = await SaaSHandler._process_model_info(character)
            
            # Create and save YAML config
            await SaaSHandler._create_character_config(
                character_id=character_id,
                character=character,
                model_dict=model_dict
            )
            
            # Switch to the new config
            logger.debug(f"Switching config to {character_id}.yaml")
            await client_context.handle_config_switch(
                websocket, 
                f"{character_id}.yaml"
            )
            
            # Send set-model message to client
            await websocket.send_text(
                json.dumps({
                    "type": "set-model-and-conf",
                    "model_info": model_dict if model_dict else None,
                    "conf_name": character["name"],
                    "conf_uid": str(character["_id"]),
                })
            )
            
            logger.info(f"Successfully loaded character {character_id} for client {client_uid}")
            
        except Exception as e:
            error_msg = f"Error loading character: {str(e)}"
            logger.error(error_msg)
            logger.exception("Full traceback:")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": error_msg
            }))

    @staticmethod
    async def _process_model_info(character: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process Live2D model information from character data"""
        model_dict = None
        if character.get("modelDict") and character.get("live2d", {}).get("modelUrl"):
            try:
                # Parse the model dictionary
                model_dict = json.loads(character["modelDict"])
                # Replace the URL in model dictionary with the one from live2d.modelUrl
                model_url = character["live2d"]["modelUrl"]
                if isinstance(model_dict, dict) and "url" in model_dict:
                    model_dict["url"] = model_url
                    logger.debug(f"Updated model URL to: {model_url}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse modelDict: {e}")
                model_dict = None
        return model_dict

    @staticmethod
    async def _create_character_config(
        character_id: str,
        character: Dict[str, Any],
        model_dict: Optional[Dict[str, Any]]
    ) -> None:
        """Create or update character YAML configuration file"""
        yaml_config = {
            "character_config": {
                "conf_name": character["name"],
                "conf_uid": str(character["_id"]),
                "live2d_model_name": character["name"],
                "character_name": character["name"],
                "avatar": character["avatar"],
                "persona_prompt": character.get("prompt", "")
            }
        }
        
        # Save/Update YAML file
        characters_dir = "characters"
        os.makedirs(characters_dir, exist_ok=True)
        yaml_path = os.path.join(characters_dir, f"{character_id}.yaml")
        
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(yaml_config, f, allow_unicode=True)

# Create singleton instance
saas_handler = SaaSHandler()
