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

    # Create Competitors table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Competitors (
            competitor_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            country VARCHAR(100) NOT NULL,
            country_code CHAR(3) NOT NULL,
            abbreviation VARCHAR(10) NOT NULL
        );
    """)

    # Create Competitor_Rankings table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Competitor_Rankings (
            rank_id SERIAL PRIMARY KEY,
            rank INT NOT NULL,
            movement INT NOT NULL,
            points INT NOT NULL,
            competitions_played INT NOT NULL,
            competitor_id VARCHAR(50),
            FOREIGN KEY (competitor_id) REFERENCES Competitors(competitor_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# Fetch data from Sportradar API
def fetch_competitor_rankings(endpoint, format):
    url = URL.format(access_level="trial", version="v3", endpoint=endpoint + format, language_code="en") + f"?api_key={API_KEY}"
    print(f"Fetching data from: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Insert competitors and rankings data into the database
def insert_data_into_db(data):
    conn = get_db_connection()
    cur = conn.cursor()

    # Clear existing data in Competitors and Competitor_Rankings tables
    cur.execute("TRUNCATE TABLE Competitor_Rankings RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE TABLE Competitors RESTART IDENTITY CASCADE;")

    # Insert competitors and rankings data
    for ranking in data["rankings"]:
        for competitor_ranking in ranking["competitor_rankings"]:
            competitor = competitor_ranking["competitor"]
            competitor_id = competitor.get("id", None)
            name = competitor.get("name", "Unknown")
            country = competitor.get("country", "Unknown")
            country_code = competitor.get("country_code", "UNK")  # Default value if country_code is missing
            abbreviation = competitor.get("abbreviation", "N/A")
            
            # Insert competitor data if not already in the database
            cur.execute("""
                INSERT INTO Competitors (competitor_id, name, country, country_code, abbreviation) 
                VALUES (%s, %s, %s, %s, %s) 
                ON CONFLICT (competitor_id) DO NOTHING
            """, (competitor_id, name, country, country_code, abbreviation))

            # Insert competitor ranking data
            rank = competitor_ranking.get("rank", None)
            movement = competitor_ranking.get("movement", 0)
            points = competitor_ranking.get("points", 0)
            competitions_played = competitor_ranking.get("competitions_played", 0)
            
            cur.execute("""
                INSERT INTO Competitor_Rankings (rank, movement, points, competitions_played, competitor_id) 
                VALUES (%s, %s, %s, %s, %s)
            """, (rank, movement, points, competitions_played, competitor_id))

    conn.commit()
    cur.close()
    conn.close()

# Main function to fetch data and insert it into the database
def main():
    # Check and create tables if they don't exist
    create_tables_if_not_exist()

    # Fetch data from Sportradar API
    data = fetch_competitor_rankings("double_competitors_rankings", ".json")
    if data:
        # Insert data into the database
        insert_data_into_db(data)
        print("Data fetched and inserted successfully!")
    else:
        print("Error fetching data from API")

if __name__ == '__main__':
    main()
