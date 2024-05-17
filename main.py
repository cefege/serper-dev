import streamlit as st
import requests
import json
import sqlite3


# Initialize the database and create the cache table if it doesn't exist
def init_db():
    conn = sqlite3.connect("cache.db")
    cursor = conn.cursor()
    # Create table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            query TEXT PRIMARY KEY,
            json_data TEXT
        )
    """
    )
    conn.commit()
    conn.close()


# Function to fetch search results from the serper.dev API
def fetch_search_results(query):
    # Check if the query exists in the cache
    conn = sqlite3.connect("cache.db")
    cursor = conn.cursor()
    cursor.execute("SELECT json_data FROM cache WHERE query=?", (query,))
    result = cursor.fetchone()
    if result:
        # Return the cached JSON data
        return json.loads(result[0])

    # If query not found in cache, fetch from API
    url = "https://google.serper.dev/search"
    payload = json.dumps(
        {
            "q": query,
            "gl": "us",
            "hl": "en",
            "num": 20,
        }
    )
    headers = {
        "X-API-KEY": st.secrets["serper_key"],
        "Content-Type": "application/json",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    json_data = response.json()

    # Cache the query and JSON data
    cursor.execute(
        "INSERT OR REPLACE INTO cache (query, json_data) VALUES (?, ?)",
        (query, json.dumps(json_data)),
    )
    conn.commit()
    conn.close()

    return json_data


# Streamlit app UI
def main():
    # Initialize the database
    init_db()

    st.title("Search Results using serper.dev API")

    # Input field for the search query
    query = st.text_input("Enter your search query:", "")

    # Button to trigger the search
    if st.button("Search"):
        if query:
            st.info("Fetching search results...")
            # Fetch search results
            data = fetch_search_results(query)

            # Extract snippets from the JSON data
            snippets = []

            # Extract snippet from "answerBox" (assuming only one answer box)
            if "answerBox" in data:
                answer_box = data["answerBox"]
                if "snippet" in answer_box:
                    snippets.append(answer_box["snippet"])

            # Extract snippets from "organic" (assuming it's a list of elements)
            if "organic" in data:
                organic_results = data["organic"]
                for result in organic_results:
                    if "snippet" in result:
                        snippets.append(result["snippet"])

            # Display snippets in an editable text area
            st.title("Snippets")
            combined_snippets = "\n".join(snippets)
            edited_snippets = st.text_area(
                "Edit snippets", combined_snippets, height=500
            )


if __name__ == "__main__":
    main()
