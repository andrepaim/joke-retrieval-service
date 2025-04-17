"""
FastMCP client for the joke retrieval service.
"""
import asyncio
import json
import sys
from typing import List, Dict, Any, Optional

import typer
from mcp import MCPClient, FormattedError

app = typer.Typer()

# Create a client to connect to the FastMCP server
async def create_client(host: str = "localhost", port: int = 8080) -> MCPClient:
    """Create an MCP client."""
    return await MCPClient.connect(f"http://{host}:{port}")


@app.command()
def get(
    query: str = typer.Argument(..., help="The query to search for jokes"),
    context: str = typer.Option(None, "--context", "-c", help="Optional context for the query"),
    multiple: bool = typer.Option(False, "--multiple", "-m", help="Get multiple jokes"),
    limit: int = typer.Option(5, "--limit", "-l", help="Limit the number of jokes returned"),
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Get jokes matching a query."""
    async def run():
        client = await create_client(host, port)
        try:
            if multiple:
                result = await client.invoke_tool(
                    "get_jokes", 
                    {"query": query, "limit": limit, "context": context}
                )
                for i, joke in enumerate(result, 1):
                    typer.echo(f"\n{i}. {joke['text']}")
                    if joke.get("category"):
                        typer.echo(f"   Category: {joke['category']}")
                    if joke.get("similarity_score"):
                        typer.echo(f"   Similarity: {joke['similarity_score']:.2f}")
                    typer.echo(f"   ID: {joke['id']}")
            else:
                result = await client.invoke_tool(
                    "get_joke", 
                    {"query": query, "context": context}
                )
                typer.echo(f"\n{result['text']}")
                if result.get("category"):
                    typer.echo(f"Category: {result['category']}")
                if result.get("similarity_score"):
                    typer.echo(f"Similarity: {result['similarity_score']:.2f}")
                typer.echo(f"ID: {result['id']}")
        except FormattedError as e:
            typer.echo(f"Error: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(run())


@app.command()
def rate(
    joke_id: int = typer.Argument(..., help="The ID of the joke to rate"),
    liked: bool = typer.Option(True, "--liked/--disliked", help="Whether you liked the joke"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="Optional user ID"),
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Rate a joke."""
    async def run():
        client = await create_client(host, port)
        try:
            result = await client.invoke_tool(
                "record_feedback", 
                {"feedback": {"joke_id": joke_id, "liked": liked, "user_id": user_id}}
            )
            typer.echo(result["message"])
        except FormattedError as e:
            typer.echo(f"Error: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(run())


@app.command()
def add(
    text: str = typer.Argument(..., help="The text of the joke"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Category of the joke"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Source of the joke"),
    tags: List[str] = typer.Option([], "--tag", "-t", help="Tags for the joke"),
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Add a new joke."""
    async def run():
        client = await create_client(host, port)
        try:
            result = await client.invoke_tool(
                "add_joke", 
                {"joke": {"text": text, "category": category, "source": source, "tags": tags}}
            )
            typer.echo(f"Joke added successfully with ID: {result['id']}")
            typer.echo(f"Text: {result['text']}")
            if result.get("category"):
                typer.echo(f"Category: {result['category']}")
            if result.get("tags"):
                typer.echo(f"Tags: {', '.join(result['tags'])}")
        except FormattedError as e:
            typer.echo(f"Error: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(run())


@app.command()
def random(
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Get a random joke."""
    async def run():
        client = await create_client(host, port)
        try:
            result = await client.resource("jokes://random")
            typer.echo(f"\n{result['text']}")
            if result.get("category"):
                typer.echo(f"Category: {result['category']}")
            if result.get("tags"):
                typer.echo(f"Tags: {', '.join(result['tags'])}")
            typer.echo(f"ID: {result['id']}")
        except FormattedError as e:
            typer.echo(f"Error: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(run())


@app.command()
def get_by_id(
    joke_id: int = typer.Argument(..., help="The ID of the joke to retrieve"),
    host: str = typer.Option("localhost", "--host", help="Host of the MCP server"),
    port: int = typer.Option(8080, "--port", "-p", help="Port of the MCP server"),
) -> None:
    """Get a joke by ID."""
    async def run():
        client = await create_client(host, port)
        try:
            result = await client.resource(f"jokes://{joke_id}")
            if "error" in result:
                typer.echo(f"Error: {result['error']}", err=True)
                return
                
            typer.echo(f"\n{result['text']}")
            if result.get("category"):
                typer.echo(f"Category: {result['category']}")
            if result.get("tags"):
                typer.echo(f"Tags: {', '.join(result['tags'])}")
            typer.echo(f"ID: {result['id']}")
        except FormattedError as e:
            typer.echo(f"Error: {e}", err=True)
        finally:
            await client.close()

    asyncio.run(run())


if __name__ == "__main__":
    app()