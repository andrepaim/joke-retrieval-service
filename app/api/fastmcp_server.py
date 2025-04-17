"""FastMCP server implementation for joke retrieval service."""
from typing import List, Optional, Dict, Any, Annotated

from fastmcp import FastMCP
from pydantic import BaseModel

from app.core.embeddings import EmbeddingService
from app.db.database import get_db
from app.models.joke import Joke, JokeFeedback, QueryLog
from sqlalchemy import desc
from sqlalchemy.orm import Session


class JokeResponse(BaseModel):
    """Response model for a joke."""
    id: int
    text: str
    category: Optional[str] = None
    source: Optional[str] = None
    similarity_score: Optional[float] = None
    tags: List[str] = []


class FeedbackRequest(BaseModel):
    """Request model for joke feedback."""
    joke_id: int
    liked: bool
    user_id: Optional[str] = None


class AddJokeRequest(BaseModel):
    """Request model for adding a joke."""
    text: str
    category: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = []


# Initialize FastMCP
mcp = FastMCP("JokeRetrievalService")


@mcp.tool()
def get_joke(query: str, context: Optional[str] = None) -> JokeResponse:
    """
    Get a single joke based on the query.
    
    Args:
        query: The text to search for related jokes
        context: Optional context to help with joke selection
        
    Returns:
        A joke that matches the query
    """
    db = next(get_db())
    embedding_service = EmbeddingService()
    
    # Create query embedding
    query_with_context = f"{query} {context}" if context else query
    query_embedding = embedding_service.create_embedding(query_with_context)
    
    # Log the query
    query_log = QueryLog(
        query_text=query,
        context=context,
        embedding=query_embedding
    )
    db.add(query_log)
    db.commit()
    
    # Search for similar jokes
    jokes = db.query(Joke).order_by(
        Joke.embedding.cosine_distance(query_embedding)
    ).limit(1).all()
    
    if not jokes:
        db.close()
        return JokeResponse(
            id=-1,
            text="Sorry, I couldn't find a joke matching your query.",
            similarity_score=0
        )
    
    joke = jokes[0]
    similarity = 1 - Joke.embedding.cosine_distance(query_embedding).scalar_value(joke)
    
    # Update query log with selected joke
    query_log.selected_joke_id = joke.id
    db.commit()
    
    # Convert to response model
    response = JokeResponse(
        id=joke.id,
        text=joke.text,
        category=joke.category,
        source=joke.source,
        similarity_score=float(similarity),
        tags=[tag.name for tag in joke.tags]
    )
    
    db.close()
    return response


@mcp.tool()
def get_jokes(query: str, limit: int = 5, context: Optional[str] = None) -> List[JokeResponse]:
    """
    Get multiple jokes based on the query.
    
    Args:
        query: The text to search for related jokes
        limit: Maximum number of jokes to return (default: 5)
        context: Optional context to help with joke selection
        
    Returns:
        A list of jokes that match the query
    """
    db = next(get_db())
    embedding_service = EmbeddingService()
    
    # Create query embedding
    query_with_context = f"{query} {context}" if context else query
    query_embedding = embedding_service.create_embedding(query_with_context)
    
    # Log the query
    query_log = QueryLog(
        query_text=query,
        context=context,
        embedding=query_embedding
    )
    db.add(query_log)
    db.commit()
    
    # Search for similar jokes
    jokes = db.query(Joke).order_by(
        Joke.embedding.cosine_distance(query_embedding)
    ).limit(limit).all()
    
    if not jokes:
        db.close()
        return [JokeResponse(
            id=-1,
            text="Sorry, I couldn't find any jokes matching your query.",
            similarity_score=0
        )]
    
    # Calculate similarity scores and convert to response models
    responses = []
    for joke in jokes:
        similarity = 1 - Joke.embedding.cosine_distance(query_embedding).scalar_value(joke)
        responses.append(JokeResponse(
            id=joke.id,
            text=joke.text,
            category=joke.category,
            source=joke.source,
            similarity_score=float(similarity),
            tags=[tag.name for tag in joke.tags]
        ))
    
    # Update query log with first selected joke
    query_log.selected_joke_id = jokes[0].id
    db.commit()
    
    db.close()
    return responses


@mcp.tool()
def record_feedback(feedback: FeedbackRequest) -> Dict[str, Any]:
    """
    Record user feedback for a joke.
    
    Args:
        feedback: The feedback data containing joke_id, liked status, and optional user_id
        
    Returns:
        A confirmation message
    """
    db = next(get_db())
    
    # Check if joke exists
    joke = db.query(Joke).filter(Joke.id == feedback.joke_id).first()
    if not joke:
        db.close()
        return {"success": False, "message": f"Joke with ID {feedback.joke_id} not found"}
    
    # Record feedback
    joke_feedback = JokeFeedback(
        joke_id=feedback.joke_id,
        user_id=feedback.user_id or "anonymous",
        liked=feedback.liked
    )
    db.add(joke_feedback)
    db.commit()
    db.close()
    
    return {
        "success": True,
        "message": f"Feedback recorded for joke ID {feedback.joke_id}"
    }


@mcp.tool()
def add_joke(joke: AddJokeRequest) -> Dict[str, Any]:
    """
    Add a new joke to the database.
    
    Args:
        joke: The joke data containing text, category, source, and tags
        
    Returns:
        The created joke data including its ID
    """
    db = next(get_db())
    embedding_service = EmbeddingService()
    
    # Create embedding for joke
    embedding = embedding_service.create_embedding(joke.text)
    
    # Create new joke
    new_joke = Joke(
        text=joke.text,
        category=joke.category,
        source=joke.source,
        embedding=embedding
    )
    
    db.add(new_joke)
    db.flush()  # To get the ID
    
    # Add tags if provided
    if joke.tags:
        from app.models.joke import Tag
        for tag_name in joke.tags:
            # Check if tag exists, create if not
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                db.flush()
            
            new_joke.tags.append(tag)
    
    db.commit()
    
    # Create response
    response = {
        "id": new_joke.id,
        "text": new_joke.text,
        "category": new_joke.category,
        "source": new_joke.source,
        "tags": [tag.name for tag in new_joke.tags]
    }
    
    db.close()
    return response


@mcp.resource("jokes://{joke_id}")
def get_joke_by_id(joke_id: int) -> Dict[str, Any]:
    """
    Get a specific joke by ID.
    
    Args:
        joke_id: The ID of the joke to retrieve
        
    Returns:
        The joke data or an error message
    """
    db = next(get_db())
    
    joke = db.query(Joke).filter(Joke.id == joke_id).first()
    if not joke:
        db.close()
        return {"error": f"Joke with ID {joke_id} not found"}
    
    response = {
        "id": joke.id,
        "text": joke.text,
        "category": joke.category,
        "source": joke.source,
        "tags": [tag.name for tag in joke.tags]
    }
    
    db.close()
    return response


@mcp.resource("jokes://random")
def get_random_joke() -> Dict[str, Any]:
    """
    Get a random joke.
    
    Returns:
        A random joke from the database
    """
    db = next(get_db())
    
    # Get random joke by ordering by ID in random order
    joke = db.query(Joke).order_by(desc("random()")).first()
    
    if not joke:
        db.close()
        return {"error": "No jokes found in database"}
    
    response = {
        "id": joke.id,
        "text": joke.text,
        "category": joke.category,
        "source": joke.source,
        "tags": [tag.name for tag in joke.tags]
    }
    
    db.close()
    return response


# Function to start the server
def start_mcp_server(host: str = "0.0.0.0", port: int = 8080):
    """Start the FastMCP server."""
    from uvicorn import run
    app = mcp.create_app()
    run(app, host=host, port=port)