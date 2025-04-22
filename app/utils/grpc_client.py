import argparse
import logging
import os
import sys

import grpc

# Import the generated protobuf code
import joke_service_pb2 as pb2
import joke_service_pb2_grpc as pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JokeClient:
    """Sample gRPC client for the Joke Service."""

    def __init__(self, host: str = "localhost", port: int = 50051):
        """
        Initialize the client.

        Args:
            host: Server hostname
            port: Server port
        """
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = pb2_grpc.JokeServiceStub(self.channel)

    def get_joke(self, query: str, context: str = None) -> None:
        """
        Get a joke based on a query.

        Args:
            query: The search query
            context: Optional context information
        """
        try:
            logger.info(f"Requesting joke with query: {query}")
            request = pb2.JokeRequest(query=query, context=context)
            response = self.stub.GetJoke(request)
            print(f"Joke: {response.text}")
            print(f"Category: {response.category}")
            print(f"Tags: {', '.join(response.tags)}")
            print(f"Relevance: {response.relevance_score:.2f}")

            if response.is_clarification_needed:
                print(f"Clarification needed: {response.clarification_prompt}")
        except Exception as e:
            logger.error(f"Error getting joke: {e}")

    def get_jokes(self, query: str, context: str = None, max_results: int = 3) -> None:
        """
        Get multiple jokes based on a query.

        Args:
            query: The search query
            context: Optional context information
            max_results: Maximum number of jokes to return
        """
        try:
            logger.info(f"Requesting {max_results} jokes with query: {query}")
            request = pb2.JokeRequest(
                query=query, context=context, max_results=max_results
            )
            response = self.stub.GetJokes(request)

            print(f"Found {len(response.jokes)} jokes:")
            for i, joke in enumerate(response.jokes, 1):
                print(f"\n{i}. {joke.text}")
                print(f"   Category: {joke.category}")
                print(f"   Tags: {', '.join(joke.tags)}")
                print(f"   Relevance: {joke.relevance_score:.2f}")
        except Exception as e:
            logger.error(f"Error getting jokes: {e}")

    def record_feedback(
        self, joke_id: str, liked: bool, feedback_text: str = None
    ) -> None:
        """
        Record feedback for a joke.

        Args:
            joke_id: The ID of the joke
            liked: Whether the user liked the joke
            feedback_text: Optional text feedback
        """
        try:
            logger.info(
                f"Recording feedback for joke {joke_id}: {'liked' if liked else 'disliked'}"
            )
            request = pb2.FeedbackRequest(
                joke_id=joke_id, liked=liked, feedback_text=feedback_text
            )
            response = self.stub.RecordFeedback(request)
            print(f"Feedback recorded: {response.success}")
            if response.message:
                print(f"Message: {response.message}")
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")

    def add_joke(
        self, text: str, category: str, tags: list, source: str = None
    ) -> None:
        """
        Add a new joke to the database.

        Args:
            text: The joke text
            category: The joke category
            tags: List of tags
            source: Optional source information
        """
        try:
            logger.info(f"Adding new joke: {text[:50]}...")
            request = pb2.AddJokeRequest(
                text=text, category=category, tags=tags, source=source
            )
            response = self.stub.AddJoke(request)
            print(f"Joke added with ID: {response.id}")
        except Exception as e:
            logger.error(f"Error adding joke: {e}")


def main():
    """Run the client with command line arguments."""
    parser = argparse.ArgumentParser(description="Joke Service Client")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=50051, help="Server port")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Get joke command
    get_parser = subparsers.add_parser("get", help="Get a joke")
    get_parser.add_argument("query", help="Search query")
    get_parser.add_argument("--context", help="Additional context")

    # Get multiple jokes command
    multi_parser = subparsers.add_parser("multi", help="Get multiple jokes")
    multi_parser.add_argument("query", help="Search query")
    multi_parser.add_argument("--context", help="Additional context")
    multi_parser.add_argument(
        "--max", type=int, default=3, help="Maximum number of jokes to return"
    )

    # Record feedback command
    feedback_parser = subparsers.add_parser(
        "feedback", help="Record feedback for a joke"
    )
    feedback_parser.add_argument("joke_id", help="Joke ID")
    feedback_parser.add_argument(
        "--liked", action="store_true", help="Whether the joke was liked"
    )
    feedback_parser.add_argument("--text", help="Feedback text")

    # Add joke command
    add_parser = subparsers.add_parser("add", help="Add a new joke")
    add_parser.add_argument("text", help="Joke text")
    add_parser.add_argument("--category", default="general", help="Joke category")
    add_parser.add_argument("--tags", nargs="+", default=[], help="Joke tags")
    add_parser.add_argument("--source", help="Joke source")

    args = parser.parse_args()

    client = JokeClient(args.host, args.port)

    if args.command == "get":
        client.get_joke(args.query, args.context)
    elif args.command == "multi":
        client.get_jokes(args.query, args.context, args.max)
    elif args.command == "feedback":
        client.record_feedback(args.joke_id, args.liked, args.text)
    elif args.command == "add":
        client.add_joke(args.text, args.category, args.tags, args.source)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
