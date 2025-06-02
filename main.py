import argparse
import os
import json # For pretty printing the final JSON
from scraper import scrape_website, get_knowledge_graph_from_text

def main():
    parser = argparse.ArgumentParser(description="Scrape a website and generate a knowledge graph using OpenAI.")
    parser.add_argument("url", help="The URL of the website to scrape.")
    args = parser.parse_args()

    print(f"Starting to scrape website: {args.url}...")
    scraped_content = scrape_website(args.url)

    if scraped_content is None:
        print("Failed to scrape the website. Exiting.")
        return 

    print("Website scraped successfully. Raw text content extracted.")

    try:
        with open("content.txt", "w", encoding="utf-8") as f:
            f.write(scraped_content)
        print("Scraped content saved to content.txt")
    except IOError as e:
        print(f"Error saving content to content.txt: {e}")
        return 

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY environment variable not set. Cannot generate knowledge graph.")
        print("Scraped text is available in content.txt")
        return 

    print("Attempting to generate knowledge graph with OpenAI...")
    knowledge_graph = get_knowledge_graph_from_text(scraped_content, api_key)

    if knowledge_graph is None:
        print("Failed to generate knowledge graph from OpenAI. Raw scraped text is in content.txt.")
        return 

    print("Knowledge graph generated successfully:")
    print(json.dumps(knowledge_graph, indent=2)) # Pretty print the JSON

    try:
        with open("knowledge_graph.json", "w", encoding="utf-8") as f:
            json.dump(knowledge_graph, f, indent=2)
        print("Knowledge graph saved to knowledge_graph.json")
    except IOError as e:
        print(f"Error saving knowledge graph to knowledge_graph.json: {e}")

if __name__ == "__main__":
    main()
