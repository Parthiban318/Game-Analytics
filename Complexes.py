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

    # Create Complexes table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Complexes (
            complex_id VARCHAR(50) PRIMARY KEY,
            complex_name VARCHAR(100) NOT NULL
        );
    """)

    # Create Venues table if it doesn't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Venues (
            venue_id VARCHAR(50) PRIMARY KEY,
            venue_name VARCHAR(100) NOT NULL,
            city_name VARCHAR(100) NOT NULL,
            country_name VARCHAR(100) NOT NULL,
            country_code CHAR(3) NOT NULL,
            timezone VARCHAR(100) NOT NULL,
            complex_id VARCHAR(50),
            FOREIGN KEY (complex_id) REFERENCES Complexes(complex_id)
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

# Fetch data from Sportradar API
def fetch_complexes_and_venues(endpoint,format):
    url = URL.format(access_level="trial", version="v3", endpoint=endpoint +format, language_code="en") + f"?api_key={API_KEY}"
    print(f"Fetching data from: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        # Print the response to understand its structure
        #print("API Response:", json.dumps(response.json(), indent=4))
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Insert complexes and venues into the database
def insert_data_into_db(data):
    conn = get_db_connection()
    cur = conn.cursor()

    # Clear existing data in Complexes and Venues tables
    cur.execute("TRUNCATE TABLE Venues RESTART IDENTITY CASCADE;")
    cur.execute("TRUNCATE TABLE Complexes RESTART IDENTITY CASCADE;")

    # Insert complexes
    for complex in data["complexes"]:
        complex_id = complex["id"]
        complex_name = complex["name"]
        cur.execute(
            "INSERT INTO Complexes (complex_id, complex_name) VALUES (%s, %s) ON CONFLICT (complex_id) DO NOTHING",
            (complex_id, complex_name)
        )

        # Check if 'venues' key exists, if it does, insert venue data
        if "venues" in complex:
            for venue in complex["venues"]:
                venue_id = venue["id"]
                venue_name = venue["name"]
                city_name = venue["city_name"]
                country_name = venue["country_name"]
                country_code = venue["country_code"]
                timezone = venue["timezone"]

                cur.execute(
                    """
                    INSERT INTO Venues (venue_id, venue_name, city_name, country_name, country_code, timezone, complex_id) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s) 
                    ON CONFLICT (venue_id) DO NOTHING
                    """,
                    (venue_id, venue_name, city_name, country_name, country_code, timezone, complex_id)
                )
        '''
        else:
            print(f"No venues found for complex {complex_id} - {complex_name}")'''

    conn.commit()
    cur.close()
    conn.close()

# Main function to fetch data and insert it into the database
def main():
    # Check and create tables if they don't exist
    create_tables_if_not_exist()

    # Fetch data from Sportradar API
    data = fetch_complexes_and_venues("complexes",".json")
    if data:
        # Insert data into the database
        insert_data_into_db(data)
        print("Data fetched and inserted successfully!")
    else:
        print("Error fetching data from API")

if __name__ == '__main__':
    main()
