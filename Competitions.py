import requests
import psycopg2
import json

# API Key and URL for Sportradar API
API_KEY = "nP8nXPFAznxPPtYj22bPDmZQctwhodWOLUVLeHNR"
URL = "https://api.sportradar.com/tennis/{access_level}/{version}/{language_code}/{endpoint}"

# Database connection setup
def get_db_connection():
    conn = psycopg2.connect("dbname=Game_Analytics user=postgres password=pvasudwvan")
    return conn

# Check if the tables exist, if not create them
def create_tables_if_not_exist():
    conn = get_db_connection()
    cur = conn.cursor()

    # Create Categories table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Categories (
            category_id VARCHAR(50) PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL
        );
    """)

    # Create Competitions table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Competitions (
            competition_id VARCHAR(50) PRIMARY KEY,
            competition_name VARCHAR(100) NOT NULL,
            parent_id VARCHAR(50) NULL,
            type VARCHAR(20) NOT NULL,
            gender VARCHAR(10) NOT NULL,
            category_id VARCHAR(50),
            FOREIGN KEY (category_id) REFERENCES Categories(category_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# Fetch data from Sportradar API
def fetch_competitions(endpoint,format):
    url = URL.format(access_level="trial", version="v3", endpoint=endpoint +format, language_code="en") + f"?api_key={API_KEY}"
    print(f"Fetching data from: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Insert categories and competitions into the database
def insert_data_into_db(data):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("TRUNCATE TABLE Competitions RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE TABLE Categories RESTART IDENTITY CASCADE;")

    # Insert categories
    categories = {}
    for comp in data["competitions"]:
        category = comp["category"]
        if category["id"] not in categories:
            categories[category["id"]] = category["name"]
    
    for category_id, category_name in categories.items():
        cur.execute(
            "INSERT INTO Categories (category_id, category_name) VALUES (%s, %s) ON CONFLICT (category_id) DO NOTHING",
            (category_id, category_name)
        )

    # Insert competitions
    competitions = []
    for comp in data["competitions"]:
        category = comp["category"]
        competitions.append((
            comp["id"], comp["name"], comp.get("parent_id"), 
            comp["type"], comp["gender"], category["id"]
        ))

    for comp in competitions:
        cur.execute(
            """
            INSERT INTO Competitions (competition_id, competition_name, parent_id, type, gender, category_id) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            ON CONFLICT (competition_id) DO NOTHING
            """,
            comp
        )

    conn.commit()
    cur.close()
    conn.close()

# Main function to fetch data and insert it into the database
def main():
    # Check and create tables if they don't exist
    create_tables_if_not_exist()

    # Fetch data from Sportradar API
    data = fetch_competitions("competitions",".json")
    if data:
        # Insert data into the database
        insert_data_into_db(data)
        print("Data fetched and inserted successfully!")
    else:
        print("Error fetching data from API")

if __name__ == '__main__':
    main()
