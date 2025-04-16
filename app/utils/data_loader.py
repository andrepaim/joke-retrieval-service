import json
import logging
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from app.core.embeddings import EmbeddingService
from app.db.database import SessionLocal
from app.models.joke import Joke, Tag

logger = logging.getLogger(__name__)


def load_jokes_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load jokes from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of joke dictionaries
    """
    try:
        with open(file_path, "r") as f:
            jokes = json.load(f)
        return jokes
    except Exception as e:
        logger.error(f"Error loading jokes from {file_path}: {e}")
        return []


def import_jokes(json_file: str, regenerate_embeddings: bool = True) -> None:
    """
    Import jokes from a JSON file into the database.
    
    Args:
        json_file: Path to JSON file containing jokes
        regenerate_embeddings: Whether to regenerate embeddings for existing jokes
    """
    jokes_data = load_jokes_from_json(json_file)
    if not jokes_data:
        logger.error("No jokes loaded from file")
        return
    
    db = SessionLocal()
    embedding_service = EmbeddingService()
    
    try:
        # Process each joke
        for joke_data in jokes_data:
            # Check if joke already exists
            existing_joke = db.query(Joke).filter(Joke.text == joke_data["text"]).first()
            
            if existing_joke:
                logger.info(f"Joke already exists: {joke_data['text'][:50]}...")
                # Update existing joke if needed
                existing_joke.category = joke_data.get("category", "general")
                existing_joke.source = joke_data.get("source")
                
                # Regenerate embedding if requested
                if regenerate_embeddings:
                    embedding = embedding_service.create_embedding(existing_joke.text)
                    existing_joke.embedding = embedding.tolist()
                
                # Update tags
                if "tags" in joke_data:
                    # Clear existing tags
                    existing_joke.tags = []
                    
                    # Add new tags
                    for tag_name in joke_data["tags"]:
                        tag = db.query(Tag).filter(Tag.name == tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            db.add(tag)
                        existing_joke.tags.append(tag)
                
                joke = existing_joke
            else:
                # Create new joke
                logger.info(f"Adding new joke: {joke_data['text'][:50]}...")
                embedding = embedding_service.create_embedding(joke_data["text"])
                
                joke = Joke(
                    text=joke_data["text"],
                    category=joke_data.get("category", "general"),
                    source=joke_data.get("source"),
                    embedding=embedding.tolist()
                )
                
                # Add tags
                if "tags" in joke_data:
                    for tag_name in joke_data["tags"]:
                        tag = db.query(Tag).filter(Tag.name == tag_name).first()
                        if not tag:
                            tag = Tag(name=tag_name)
                            db.add(tag)
                        joke.tags.append(tag)
                
                db.add(joke)
            
        # Commit changes
        db.commit()
        logger.info(f"Successfully processed {len(jokes_data)} jokes")
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing jokes: {e}")
    finally:
        db.close()


def create_sample_json() -> None:
    """Create a sample jokes JSON file."""
    sample_jokes = [
        {
            "text": "Why did the chicken cross the road? To get to the other side!",
            "category": "classic",
            "tags": ["animals", "classic", "short"]
        },
        {
            "text": "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "category": "pun",
            "tags": ["pun", "one-liner", "appearance"]
        },
        {
            "text": "What do you call a fake noodle? An impasta!",
            "category": "pun",
            "tags": ["pun", "food", "short"]
        },
        {
            "text": "How many software engineers does it take to change a light bulb? None, that's a hardware problem.",
            "category": "professional",
            "tags": ["tech", "programming", "profession"]
        },
        {
            "text": "Why don't scientists trust atoms? Because they make up everything!",
            "category": "science",
            "tags": ["science", "pun", "short"]
        }
    ]
    
    with open("data/sample_jokes.json", "w") as f:
        json.dump(sample_jokes, f, indent=2)
    
    logger.info("Created sample jokes JSON file at data/sample_jokes.json")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python data_loader.py <json_file> [--regenerate-embeddings]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    regenerate_embeddings = "--regenerate-embeddings" in sys.argv
    
    import_jokes(json_file, regenerate_embeddings)