"""
FastMCP client for the joke retrieval service.
"""
import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

import typer
from fastmcp.client import Client, SSETransport

app = typer.Typer()


# Create a client to connect to the FastMCP server
def create_client(host: str = "localhost", port: int = 8080) -> Client:
    """Create an MCP client."""
    url = f"http://{host}:{port}"
    print(f"Connecting to FastMCP server at {url}")
    # The SSE endpoint for FastMCP 2.x should be /sse
    transport = SSETransport(f"{url}/sse")
    return Client(transport)


@app.command()
def get(
    query: str = typer.Argument(..., help="The query to search for jokes"),
    context: str = typer.Option(
        None, "--context", "-c", help="Optional context for the query"
    ),
    multiple: bool = typer.Option(False, "--multiple", "-m", help="Get multiple jokes"),
    limit: int = typer.Option(
        5, "--limit", "-l", help="Limit the number of jokes returned"
    ),
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Get jokes matching a query."""

    async def run():
        client = create_client(host, port)
        async with client:
            try:
                if multiple:
                    result = await client.call_tool(
                        "get_jokes", {"query": query, "limit": limit, "context": context}
                    )
                    # Process the results
                    # Handle TextContent objects from FastMCP
                    if isinstance(result, list) and len(result) > 0:
                        import json
                        # In this case, we receive a single TextContent with an array of jokes
                        text_content = result[0]
                        if hasattr(text_content, 'text'):
                            try:
                                # This is an array of jokes in JSON
                                jokes_data = json.loads(text_content.text)
                                if isinstance(jokes_data, list):
                                    for i, joke in enumerate(jokes_data, 1):
                                        typer.echo(f"\n{i}. {joke['text']}")
                                        if joke.get("category"):
                                            typer.echo(f"   Category: {joke['category']}")
                                        if joke.get("similarity_score"):
                                            typer.echo(f"   Similarity: {joke['similarity_score']:.2f}")
                                        typer.echo(f"   ID: {joke['id']}")
                                else:
                                    typer.echo(f"Unexpected response format - not a list: {jokes_data}")
                            except json.JSONDecodeError as e:
                                typer.echo(f"Error parsing jokes: {e}")
                                typer.echo(f"Raw response: {text_content.text}")
                        else:
                            typer.echo(f"Unexpected response format - no text attribute: {result}")
                    else:
                        typer.echo("No jokes found or unexpected response format")
                else:
                    result = await client.call_tool(
                        "get_joke", {"query": query, "context": context}
                    )
                    # Handle TextContent objects from FastMCP
                    if isinstance(result, list) and len(result) > 0:
                        # For TextContent objects, parse the JSON from the text property
                        import json
                        text_content = result[0]
                        if hasattr(text_content, 'text'):
                            # Parse the JSON from the text property
                            try:
                                joke_data = json.loads(text_content.text)
                                typer.echo(f"\n{joke_data['text']}")
                                if joke_data.get("category"):
                                    typer.echo(f"Category: {joke_data['category']}")
                                if joke_data.get("similarity_score"):
                                    typer.echo(f"Similarity: {joke_data['similarity_score']:.2f}")
                                typer.echo(f"ID: {joke_data['id']}")
                            except json.JSONDecodeError as e:
                                typer.echo(f"Error parsing response: {e}")
                                typer.echo(f"Raw response: {text_content.text}")
                        else:
                            typer.echo(f"Unexpected response format: {result}")
                    else:
                        typer.echo("No jokes found or unexpected response format")
            except Exception as e:
                import traceback
                typer.echo(f"Error: {e}", err=True)
                typer.echo(f"Detail: {traceback.format_exc()}", err=True)

    asyncio.run(run())


@app.command()
def rate(
    joke_id: int = typer.Argument(..., help="The ID of the joke to rate"),
    liked: bool = typer.Option(
        True, "--liked/--disliked", help="Whether you liked the joke"
    ),
    user_id: Optional[str] = typer.Option(
        None, "--user", "-u", help="Optional user ID"
    ),
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Rate a joke."""

    async def run():
        client = create_client(host, port)
        async with client:
            try:
                result = await client.call_tool(
                    "record_feedback",
                    {"feedback": {"joke_id": joke_id, "liked": liked, "user_id": user_id}},
                )
                
                # Handle TextContent objects
                if isinstance(result, list) and len(result) > 0:
                    import json
                    text_content = result[0]
                    if hasattr(text_content, 'text'):
                        try:
                            feedback_data = json.loads(text_content.text)
                            typer.echo(feedback_data.get("message", "Feedback recorded"))
                        except json.JSONDecodeError as e:
                            typer.echo(f"Error parsing response: {e}")
                            typer.echo(f"Raw response: {text_content.text}")
                    else:
                        typer.echo(f"Unexpected response format: {result}")
                else:
                    typer.echo("Feedback recorded")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(run())


@app.command()
def add(
    text: str = typer.Argument(..., help="The text of the joke"),
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Category of the joke"
    ),
    source: Optional[str] = typer.Option(
        None, "--source", "-s", help="Source of the joke"
    ),
    tags: List[str] = typer.Option([], "--tag", "-t", help="Tags for the joke"),
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Add a new joke."""

    async def run():
        client = create_client(host, port)
        async with client:
            try:
                result = await client.call_tool(
                    "add_joke",
                    {
                        "joke": {
                            "text": text,
                            "category": category,
                            "source": source,
                            "tags": tags,
                        }
                    },
                )
                
                # Handle TextContent objects
                if isinstance(result, list) and len(result) > 0:
                    import json
                    text_content = result[0]
                    if hasattr(text_content, 'text'):
                        try:
                            joke_data = json.loads(text_content.text)
                            typer.echo(f"Joke added successfully with ID: {joke_data['id']}")
                            typer.echo(f"Text: {joke_data['text']}")
                            if joke_data.get("category"):
                                typer.echo(f"Category: {joke_data['category']}")
                            if joke_data.get("tags"):
                                typer.echo(f"Tags: {', '.join(joke_data['tags'])}")
                        except json.JSONDecodeError as e:
                            typer.echo(f"Error parsing response: {e}")
                            typer.echo(f"Raw response: {text_content.text}")
                    else:
                        typer.echo(f"Unexpected response format: {result}")
                else:
                    typer.echo("Joke added, but couldn't retrieve details")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(run())


@app.command()
def random(
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Get a random joke."""

    async def run():
        client = create_client(host, port)
        async with client:
            try:
                result = await client.read_resource("jokes://random")
                # Handle TextContent objects
                if isinstance(result, list) and len(result) > 0:
                    import json
                    text_content = result[0]
                    if hasattr(text_content, 'text'):
                        try:
                            joke_data = json.loads(text_content.text)
                            typer.echo(f"\n{joke_data['text']}")
                            if joke_data.get("category"):
                                typer.echo(f"Category: {joke_data['category']}")
                            if joke_data.get("tags"):
                                typer.echo(f"Tags: {', '.join(joke_data['tags'])}")
                            typer.echo(f"ID: {joke_data['id']}")
                        except json.JSONDecodeError as e:
                            typer.echo(f"Error parsing response: {e}")
                            typer.echo(f"Raw response: {text_content.text}")
                    else:
                        typer.echo(f"Unexpected response format: {result}")
                else:
                    typer.echo("No jokes found or unexpected response format")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(run())


@app.command()
def get_by_id(
    joke_id: int = typer.Argument(..., help="The ID of the joke to retrieve"),
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Get a joke by ID."""

    async def run():
        client = create_client(host, port)
        async with client:
            try:
                result = await client.read_resource(f"jokes://{joke_id}")
                # Handle TextContent objects
                if isinstance(result, list) and len(result) > 0:
                    import json
                    text_content = result[0]
                    if hasattr(text_content, 'text'):
                        try:
                            joke_data = json.loads(text_content.text)
                            # Check for error
                            if "error" in joke_data:
                                typer.echo(f"Error: {joke_data['error']}", err=True)
                                return
                                
                            typer.echo(f"\n{joke_data['text']}")
                            if joke_data.get("category"):
                                typer.echo(f"Category: {joke_data['category']}")
                            if joke_data.get("tags"):
                                typer.echo(f"Tags: {', '.join(joke_data['tags'])}")
                            typer.echo(f"ID: {joke_data['id']}")
                        except json.JSONDecodeError as e:
                            typer.echo(f"Error parsing response: {e}")
                            typer.echo(f"Raw response: {text_content.text}")
                    else:
                        typer.echo(f"Unexpected response format: {result}")
                else:
                    typer.echo("No jokes found or unexpected response format")
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)

    asyncio.run(run())


if __name__ == "__main__":
    app()