import logging
import time
from concurrent import futures
from typing import List, Optional

import grpc

# Import the generated protobuf code (will be generated later)
# from proto import joke_service_pb2 as pb2
# from proto import joke_service_pb2_grpc as pb2_grpc

# This is a placeholder import that we'll uncomment after generating the protobuf code
# For now, we'll implement the service using the expected interface

from app.core.config import settings
from app.core.embeddings import EmbeddingService
from app.db.database import SessionLocal
from app.models.joke import Joke, Tag, JokeFeedback, QueryLog

logger = logging.getLogger(__name__)


class JokeServicer:
    """Implementation of the JokeService gRPC service."""
    
    def __init__(self):
        """Initialize the JokeServicer with necessary services."""
        self.embedding_service = EmbeddingService()
        logger.info("JokeServicer initialized with pgvector for vector search")
    
    async def GetJoke(self, request, context):
        """
        Get a single joke based on query and context.
        
        Args:
            request: JokeRequest with query, context, etc.
            context: gRPC context
            
        Returns:
            JokeResponse with matching joke
        """
        db = SessionLocal()
        try:
            query = request.query
            user_context = request.context if hasattr(request, 'context') and request.context else None
            
            # Generate query embedding
            query_text = f"{query} {user_context}" if user_context else query
            query_embedding = self.embedding_service.create_embedding(query_text)
            
            # Search for similar jokes
            joke_matches = self.embedding_service.search(query_embedding, k=1)
            
            if not joke_matches:
                # No matches found
                return self._create_joke_response(
                    id="0",
                    text="I couldn't find a joke matching your query. Could you try a different topic?",
                    category="unknown",
                    tags=[],
                    relevance_score=0.0,
                    is_clarification_needed=True,
                    clarification_prompt="Can you tell me more about what kind of joke you're looking for?"
                )
            
            joke_id, score = joke_matches[0]
            joke = db.query(Joke).filter(Joke.id == joke_id).first()
            
            # Log the query
            log_entry = QueryLog(
                query=query,
                context=user_context,
                embedding=query_embedding.tolist(),
                clarification_needed=score < settings.VECTOR_SIMILARITY_THRESHOLD,
                selected_joke_id=joke_id,
                relevance_score=score
            )
            db.add(log_entry)
            db.commit()
            
            # Determine if clarification is needed
            is_clarification_needed = score < settings.VECTOR_SIMILARITY_THRESHOLD
            clarification_prompt = None
            if is_clarification_needed:
                clarification_prompt = "Your request was a bit ambiguous. Could you be more specific about the kind of joke you want?"
            
            # Convert tags to string list
            tag_names = [tag.name for tag in joke.tags]
            
            return self._create_joke_response(
                id=str(joke.id),
                text=joke.text,
                category=joke.category,
                tags=tag_names,
                relevance_score=score,
                is_clarification_needed=is_clarification_needed,
                clarification_prompt=clarification_prompt
            )
        except Exception as e:
            logger.error(f"Error in GetJoke: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return self._create_joke_response(
                id="0",
                text="An error occurred while retrieving the joke.",
                category="error",
                tags=[],
                relevance_score=0.0,
                is_clarification_needed=False
            )
        finally:
            db.close()
    
    async def GetJokes(self, request, context):
        """
        Get multiple jokes based on query and context.
        
        Args:
            request: JokeRequest with query, context, max_results
            context: gRPC context
            
        Returns:
            JokesResponse with list of matching jokes
        """
        db = SessionLocal()
        try:
            query = request.query
            user_context = request.context if hasattr(request, 'context') and request.context else None
            max_results = request.max_results if hasattr(request, 'max_results') and request.max_results else 5
            
            # Generate query embedding
            query_text = f"{query} {user_context}" if user_context else query
            query_embedding = self.embedding_service.create_embedding(query_text)
            
            # Search for similar jokes
            joke_matches = self.embedding_service.search(query_embedding, k=max_results)
            
            if not joke_matches:
                # Return empty response with clarification needed
                return self._create_jokes_response([
                    self._create_joke_response(
                        id="0",
                        text="I couldn't find any jokes matching your query. Could you try a different topic?",
                        category="unknown",
                        tags=[],
                        relevance_score=0.0,
                        is_clarification_needed=True,
                        clarification_prompt="Can you tell me more about what kind of jokes you're looking for?"
                    )
                ])
            
            joke_ids = [joke_id for joke_id, _ in joke_matches]
            jokes = db.query(Joke).filter(Joke.id.in_(joke_ids)).all()
            
            # Map scores to jokes
            id_to_score = {joke_id: score for joke_id, score in joke_matches}
            
            # Create response objects
            joke_responses = []
            for joke in jokes:
                score = id_to_score.get(joke.id, 0.0)
                is_clarification_needed = score < settings.VECTOR_SIMILARITY_THRESHOLD
                
                tag_names = [tag.name for tag in joke.tags]
                
                joke_response = self._create_joke_response(
                    id=str(joke.id),
                    text=joke.text,
                    category=joke.category,
                    tags=tag_names,
                    relevance_score=score,
                    is_clarification_needed=is_clarification_needed,
                    clarification_prompt="Could you be more specific about the type of joke you want?" if is_clarification_needed else None
                )
                joke_responses.append(joke_response)
            
            # Log the query
            log_entry = QueryLog(
                query=query,
                context=user_context,
                embedding=query_embedding.tolist(),
                clarification_needed=any(j.is_clarification_needed for j in joke_responses),
                selected_joke_id=jokes[0].id if jokes else None,
                relevance_score=id_to_score.get(jokes[0].id, 0.0) if jokes else 0.0
            )
            db.add(log_entry)
            db.commit()
            
            return self._create_jokes_response(joke_responses)
        except Exception as e:
            logger.error(f"Error in GetJokes: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return self._create_jokes_response([
                self._create_joke_response(
                    id="0",
                    text="An error occurred while retrieving jokes.",
                    category="error",
                    tags=[],
                    relevance_score=0.0,
                    is_clarification_needed=False
                )
            ])
        finally:
            db.close()
    
    async def RecordFeedback(self, request, context):
        """
        Record user feedback for a joke.
        
        Args:
            request: FeedbackRequest with joke_id, liked, feedback_text
            context: gRPC context
            
        Returns:
            FeedbackResponse indicating success
        """
        db = SessionLocal()
        try:
            joke_id = int(request.joke_id)
            liked = request.liked
            feedback_text = request.feedback_text if hasattr(request, 'feedback_text') and request.feedback_text else None
            
            # Check if joke exists
            joke = db.query(Joke).filter(Joke.id == joke_id).first()
            if not joke:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Joke with id {joke_id} not found")
                return self._create_feedback_response(False, "Joke not found")
            
            # Record feedback
            feedback = JokeFeedback(
                joke_id=joke_id,
                liked=liked,
                feedback_text=feedback_text
            )
            db.add(feedback)
            db.commit()
            
            return self._create_feedback_response(True, "Feedback recorded successfully")
        except Exception as e:
            logger.error(f"Error in RecordFeedback: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return self._create_feedback_response(False, f"Error recording feedback: {str(e)}")
        finally:
            db.close()
    
    async def AddJoke(self, request, context):
        """
        Add a new joke to the database.
        
        Args:
            request: AddJokeRequest with joke text, category, tags
            context: gRPC context
            
        Returns:
            JokeResponse with the newly added joke
        """
        db = SessionLocal()
        try:
            # Extract fields from request
            text = request.text
            category = request.category
            tag_names = request.tags
            source = request.source if hasattr(request, 'source') and request.source else None
            
            # Generate embedding for the joke
            embedding = self.embedding_service.create_embedding(text)
            
            # Create and add the joke
            joke = Joke(
                text=text,
                category=category,
                source=source,
                embedding=embedding.tolist()
            )
            
            # Handle tags
            for tag_name in tag_names:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                joke.tags.append(tag)
            
            db.add(joke)
            db.commit()
            db.refresh(joke)
            
            
            # Convert tags to string list for response
            response_tag_names = [tag.name for tag in joke.tags]
            
            return self._create_joke_response(
                id=str(joke.id),
                text=joke.text,
                category=joke.category,
                tags=response_tag_names,
                relevance_score=1.0,  # Perfect match for itself
                is_clarification_needed=False
            )
        except Exception as e:
            logger.error(f"Error in AddJoke: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal error: {str(e)}")
            return self._create_joke_response(
                id="0",
                text="An error occurred while adding the joke.",
                category="error",
                tags=[],
                relevance_score=0.0,
                is_clarification_needed=False
            )
        finally:
            db.close()
    
    # Helper methods to create response objects
    # These will be replaced with actual protobuf objects after generating the code
    
    def _create_joke_response(self, id, text, category, tags, relevance_score, is_clarification_needed, clarification_prompt=None):
        """Create a placeholder for JokeResponse."""
        # This is a placeholder that will be replaced with actual protobuf objects
        return {
            "id": id,
            "text": text,
            "category": category,
            "tags": tags,
            "relevance_score": relevance_score,
            "is_clarification_needed": is_clarification_needed,
            "clarification_prompt": clarification_prompt
        }
    
    def _create_jokes_response(self, jokes):
        """Create a placeholder for JokesResponse."""
        # This is a placeholder that will be replaced with actual protobuf objects
        return {
            "jokes": jokes
        }
    
    def _create_feedback_response(self, success, message=None):
        """Create a placeholder for FeedbackResponse."""
        # This is a placeholder that will be replaced with actual protobuf objects
        return {
            "success": success,
            "message": message
        }


def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # This will be uncommented after generating the protobuf code
    # pb2_grpc.add_JokeServiceServicer_to_server(JokeServicer(), server)
    
    server.add_insecure_port(f"{settings.GRPC_HOST}:{settings.GRPC_PORT}")
    server.start()
    logger.info(f"Server started on {settings.GRPC_HOST}:{settings.GRPC_PORT}")
    
    try:
        # Keep thread alive
        while True:
            time.sleep(86400)  # Sleep for a day
    except KeyboardInterrupt:
        server.stop(0)
        logger.info("Server stopped")