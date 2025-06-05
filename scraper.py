import requests
from bs4 import BeautifulSoup
import sys
import os
import openai
import json
from transformers import T5Tokenizer, T5ForConditionalGeneration


def generate_knowledge_graph_hf(text_content: str) -> list | None:
    """
    Generates a knowledge graph from text content using a Hugging Face T5 model.

    Args:
        text_content: The text to process.

    Returns:
        A list representing the JSON knowledge graph, or None if an error occurred.
    """
    model_name = "google/flan-t5-base"
    try:
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
    except Exception as e:
        print(f"Error loading Hugging Face model or tokenizer: {e}")
        # This error will likely occur due to the previous installation failure.
        return None

    prompt = f"""
Extract entities and their relationships from the following text.
Format the output as a JSON array, where each object has EXACTLY these keys: "head", "head_type", "relation", "tail", "tail_type".
The "head" is the source entity.
The "head_type" is the category or type of the source entity (e.g., Person, Organization, Location, Concept, Product, Event).
The "relation" is the relationship between the head and the tail entity (e.g., works_at, located_in, part_of, is_a, produces, owns).
The "tail" is the target entity.
The "tail_type" is the category or type of the target entity.

If no relationships are found, output an empty JSON array: [].
Do not include any explanations or introductory text outside the JSON array itself.

Text:
{text_content}

JSON Output:
"""
    try:
        input_ids = tokenizer(prompt, return_tensors="pt", max_length=2048, truncation=True).input_ids
        outputs = model.generate(input_ids, max_length=1024, num_beams=4, early_stopping=True)
        raw_output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as e:
        print(f"Error during Hugging Face model inference: {e}")
        # This error will also likely occur.
        return None

    try:
        json_start_index = raw_output_text.find('[')
        json_end_index = raw_output_text.rfind(']')

        if json_start_index != -1 and json_end_index != -1 and json_start_index < json_end_index:
            json_string = raw_output_text[json_start_index : json_end_index + 1]
            parsed_json = json.loads(json_string)
            if isinstance(parsed_json, list):
                return parsed_json
            else:
                print(f"Parsed JSON is not a list: {parsed_json}")
                return None
        else:
            print(f"Could not find valid JSON array in model output: {raw_output_text}")
            return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from model output: {e}")
        print(f"Raw output was: {raw_output_text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while parsing Hugging Face model output: {e}")
        return None

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
