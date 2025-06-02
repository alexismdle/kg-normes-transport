import requests
from bs4 import BeautifulSoup
import sys
import os
import openai
import json

def get_knowledge_graph_from_text(text_content: str, api_key: str):
    """
    Generates a knowledge graph from text content using OpenAI API.

    Args:
        text_content: The text to process.
        api_key: The OpenAI API key.

    Returns:
        A Python dictionary representing the JSON knowledge graph, or None if an error occurred.
    """
    try:
        client = openai.OpenAI(api_key=api_key)
        system_prompt = (
            "You are an AI assistant tasked with converting unstructured text into a structured JSON knowledge graph. "
            "Identify entities and their relationships from the provided text. Output a JSON array where each object "
            "has these exact keys: 'head' (the source entity), 'head_type' (category/type of the source entity), "
            "'relation' (the relationship between entities), 'tail' (the target entity), and 'tail_type' "
            "(category/type of the target entity). Ensure your output is only the JSON array, with no other "
            "explanatory text or markdown."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text_content}
        ]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            response_format={"type": "json_object"},
            messages=messages
        )
        json_output_string = response.choices[0].message.content
        # Basic validation to ensure the string is likely JSON before parsing
        if json_output_string and json_output_string.strip().startswith(('[', '{')):
            return json.loads(json_output_string)
        else:
            print(f"OpenAI response was not valid JSON: {json_output_string}")
            return None
    except openai.APIError as e:
        print(f"OpenAI API error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from OpenAI response: {e}")
        print(f"Received string: {json_output_string}") # Log the problematic string
        return None
    except Exception as e:
        print(f"An unexpected error occurred while processing OpenAI response: {e}")
        return None

def scrape_website(url):
    """
    Scrapes a website and extracts text content from specified HTML tags.

    Args:
        url: The URL of the website to scrape.

    Returns:
        A string containing the extracted text, or None if an error occurred.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.content, 'html.parser')
        texts = []

        # Tags to extract text from
        tags_to_extract = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'a']

        for tag_name in tags_to_extract:
            for tag in soup.find_all(tag_name):
                texts.append(tag.get_text(separator=' ', strip=True))

        return '\n'.join(texts)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"An error occurred during parsing: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        content = scrape_website(sys.argv[1])
        if content is not None:
            try:
                with open('content.txt', 'w', encoding='utf-8') as f:
                    f.write(content)
                print("Content saved to content.txt")

                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    print("OPENAI_API_KEY environment variable not set. Skipping knowledge graph generation.")
                else:
                    print("Attempting to generate knowledge graph with OpenAI...")
                    knowledge_graph_json = get_knowledge_graph_from_text(content, api_key)
                    if knowledge_graph_json is not None:
                        print("Successfully generated knowledge graph:")
                        try:
                            print(json.dumps(knowledge_graph_json, indent=2))
                        except TypeError as te: # Handle cases where knowledge_graph_json might not be serializable as expected
                            print(f"Error pretty-printing JSON: {te}")
                            print("Raw output:", knowledge_graph_json)

                    else:
                        print("Failed to generate knowledge graph from OpenAI.")
            except IOError as e:
                print(f"Error writing to file: {e}")
        else:
            print("Failed to scrape website, content.txt not created.")
    else:
        print("Please provide a URL as a command-line argument.")
