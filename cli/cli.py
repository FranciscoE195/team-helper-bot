"""CLI tool for RAG system."""

import click
import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group()
def cli():
    """BPI RAG System CLI"""
    pass


@cli.command()
@click.argument('question')
@click.option('--max-sources', default=5, help='Maximum number of sources')
@click.option('--api-url', default='http://localhost:8000', help='API base URL')
def query(question: str, max_sources: int, api_url: str):
    """Query the documentation."""
    console.print(f"\n[bold blue]Question:[/bold blue] {question}\n")
    
    with console.status("[bold green]Searching documentation..."):
        try:
            response = httpx.post(
                f"{api_url}/api/query",
                json={"question": question, "max_sources": max_sources},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
        
        except httpx.HTTPError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            return
    
    # Display answer
    console.print(Panel(
        Markdown(data['answer']),
        title="[bold green]Answer",
        border_style="green",
    ))
    
    # Display sources
    console.print("\n[bold blue]Sources:[/bold blue]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Document")
    table.add_column("Section")
    table.add_column("Score", justify="right")
    
    for evidence in data['evidence']:
        table.add_row(
            str(evidence['citation_number']),
            evidence['doc_title'],
            evidence.get('section_title', ''),
            f"{evidence['relevance_score']:.2f}",
        )
    
    console.print(table)
    
    # Display metadata
    console.print(f"\n[dim]Confidence: {data['confidence']}")
    console.print(f"Generation time: {data['generation_time_ms']}ms")
    console.print(f"Trace ID: {data['trace_id']}[/dim]")


@cli.command()
@click.argument('trace_id')
@click.option('--api-url', default='http://localhost:8000', help='API base URL')
def trace(trace_id: str, api_url: str):
    """Get trace details by ID."""
    try:
        response = httpx.get(f"{api_url}/api/trace/{trace_id}")
        response.raise_for_status()
        data = response.json()
    
    except httpx.HTTPError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        return
    
    # Display trace info
    console.print(Panel(
        f"[bold]Query:[/bold] {data['query_text']}\n"
        f"[bold]User:[/bold] {data.get('user_id', 'N/A')}\n"
        f"[bold]Timestamp:[/bold] {data['timestamp']}\n"
        f"[bold]Confidence:[/bold] {data['confidence']}",
        title="[bold blue]Trace Details",
        border_style="blue",
    ))
    
    # Display answer
    console.print(Panel(
        Markdown(data['answer_text']),
        title="[bold green]Answer",
        border_style="green",
    ))
    
    # Display citations
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Document")
    table.add_column("Section")
    table.add_column("Score", justify="right")
    
    for cit in data['citations']:
        table.add_row(
            str(cit['citation_number']),
            cit['doc_title'],
            cit.get('section_title', ''),
            f"{cit['relevance_score']:.2f}",
        )
    
    console.print(table)


if __name__ == '__main__':
    cli()
