import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import warnings  

# Suppress pandas warnings about DBAPI2 connections  suruss the warnings
warnings.filterwarnings("ignore", category=UserWarning, message="pandas only supports SQLAlchemy connectable.*")
# Database connection
def get_db_connection():
    conn = psycopg2.connect("dbname=Game_Analytics user=postgres password=pvasudwvan")
    return conn

# Function to execute a selected query
def execute_query(query):
    conn = get_db_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Function to get all competitors from the database
def get_competitors():
    conn = get_db_connection()
    query = """
        SELECT 
            competitors.competitor_id, 
            competitors.name, 
            competitors.country, 
            competitors.country_code, 
            competitors.abbreviation, 
            competitor_rankings.rank, 
            competitor_rankings.movement, 
            competitor_rankings.points, 
            competitor_rankings.competitions_played
        FROM competitors
        JOIN competitor_rankings ON competitors.competitor_id = competitor_rankings.competitor_id;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Function to get summary statistics for the homepage dashboard
def get_summary_statistics():
    conn = get_db_connection()
    query = """
        SELECT 
            COUNT(DISTINCT competitors.competitor_id) AS total_competitors, 
            COUNT(DISTINCT competitors.country) AS total_countries, 
            MAX(competitor_rankings.points) AS highest_points
        FROM competitors
        JOIN competitor_rankings ON competitors.competitor_id = competitor_rankings.competitor_id;
    """
    summary = pd.read_sql(query, conn)
    conn.close()
    return summary

# Function to get country-wise analysis
def get_country_analysis():
    conn = get_db_connection()
    query = """
        SELECT 
            competitors.country, 
            COUNT(competitors.competitor_id) AS total_competitors, 
            AVG(competitor_rankings.points) AS avg_points
        FROM competitors
        JOIN competitor_rankings ON competitors.competitor_id = competitor_rankings.competitor_id
        GROUP BY competitors.country
        ORDER BY total_competitors DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Streamlit Application 
def main():
    # Set up the layout 
    st.set_page_config(page_title="Tennis Competitor Rankings Dashboard", layout="wide")
    st.title("🎾 Tennis Competitor Rankings Dashboard")
    st.sidebar.title("Filters & Navigation")

    # Load data # data from above function
    df = get_competitors()
    summary = get_summary_statistics()
    country_analysis = get_country_analysis()

    # Sidebar filters 
    st.sidebar.header("Filter Competitors")
    competitor_name = st.sidebar.text_input("Search Competitor by Name")
    rank_range = st.sidebar.slider("Filter by Rank", min_value=int(df['rank'].min()), max_value=int(df['rank'].max()), value=(int(df['rank'].min()), int(df['rank'].max())))
    points_range = st.sidebar.slider("Filter by Points", min_value=int(df['points'].min()), max_value=int(df['points'].max()), value=(int(df['points'].min()), int(df['points'].max())))
    selected_country = st.sidebar.selectbox("Filter by Country", ["All"] + list(df['country'].unique()))

    # Apply filters 
    if competitor_name:
        df = df[df['name'].str.contains(competitor_name, case=False, na=False)]
    df = df[(df['rank'] >= rank_range[0]) & (df['rank'] <= rank_range[1])]
    df = df[(df['points'] >= points_range[0]) & (df['points'] <= points_range[1])]
    if selected_country != "All":
        df = df[df['country'] == selected_country]

    # Homepage Dashboard #used dashboard details
    st.header("📊 Homepage Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Competitors", summary['total_competitors'][0])
    with col2:
        st.metric("Countries Represented", summary['total_countries'][0])
    with col3:
        st.metric("Highest Points", summary['highest_points'][0])

    # Competitor Data Table
    st.header("🎾 Competitor Data")
    st.dataframe(df, use_container_width=True)

    # Competitor Details Viewer
    st.header("👤 Competitor Details")
    selected_competitor = st.selectbox("Select a Competitor", df['name'].unique())
    competitor_details = df[df['name'] == selected_competitor].iloc[0]
    st.write(f"**Name:** {competitor_details['name']}")
    st.write(f"**Rank:** {competitor_details['rank']}")
    st.write(f"**Movement:** {competitor_details['movement']}")
    st.write(f"**Points:** {competitor_details['points']}")
    st.write(f"**Competitions Played:** {competitor_details['competitions_played']}")
    st.write(f"**Country:** {competitor_details['country']}")

    # Country-wise Analysis
    st.header("🌍 Country-Wise Analysis")
    st.dataframe(country_analysis, use_container_width=True)

    # Leaderboards
    st.header("🏆 Leaderboards")
    top_ranked = df.sort_values(by='rank').head(10)
    top_points = df.sort_values(by='points', ascending=False).head(10)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top-Ranked Competitors")
        st.dataframe(top_ranked[['name', 'rank', 'country']], use_container_width=True)
    with col2:
        st.subheader("Competitors with Highest Points")
        st.dataframe(top_points[['name', 'points', 'country']], use_container_width=True)

    # Charts
    st.header("📈 Visualizations")
    fig1 = px.bar(top_points, x='name', y='points', title="Top 10 Competitors by Points", color='points')
    st.plotly_chart(fig1, use_container_width=True)

# Query Selection
    st.sidebar.header("Task1 Custom Queries")
    query_options = {
        "1.List all competitions along with their category name": """
                SELECT c.competition_name, cat.category_name
                FROM Competitions c
                JOIN Categories cat ON c.category_id = cat.category_id;
            """,
        "2.Count the number of competitions in each category": """
                SELECT cat.category_name, COUNT(c.competition_id) AS competition_count
                FROM Competitions c
                JOIN Categories cat ON c.category_id = cat.category_id
                GROUP BY cat.category_name;
            """,
        "3.Find all competitions of type 'doubles'": """
                SELECT competition_name
                FROM Competitions
                WHERE type = 'doubles';
            """,
        "4.Get competitions that belong to a specific category (e.g., ITF Men)": """
                SELECT competition_name
                FROM Competitions c
                JOIN Categories cat ON c.category_id = cat.category_id
                WHERE cat.category_name = 'ITF Men';
            """,
        "5.Identify parent competitions and their sub-competitions": """
                SELECT parent.competition_name AS parent_competition, sub.competition_name AS sub_competition
                FROM Competitions sub
                JOIN Competitions parent ON sub.parent_id = parent.competition_id;
            """,
        "6.Analyze the distribution of competition types by category": """
                SELECT cat.category_name, c.type, COUNT(*) AS competition_count
                FROM Competitions c
                JOIN Categories cat ON c.category_id = cat.category_id
                GROUP BY cat.category_name, c.type
                ORDER BY cat.category_name, c.type;
            """,
        "7.List all competitions with no parent (top-level competitions)": """
                SELECT competition_name
                FROM Competitions
                WHERE parent_id IS NULL;
            """

    }
    selected_query = st.sidebar.selectbox("Select a Query", list(query_options.keys()))

    if selected_query:
        query = query_options[selected_query]
        result_df = execute_query(query)
        st.header(f"Task1 Query: {selected_query}")
        st.dataframe(result_df, use_container_width=True)

    st.sidebar.header("Task2 Custom Queries")
    query_options = {
        "1.List all venues along with their associated complex name": """
                SELECT v.venue_name, v.city_name, v.country_name, c.complex_name
                FROM Venues v
                JOIN Complexes c ON v.complex_id = c.complex_id;
            """,
        "2.Count the number of venues in each complex": """
                SELECT v.complex_id, c.complex_name, COUNT(v.venue_id) AS venue_count
                FROM Venues v
                JOIN Complexes c ON v.complex_id = c.complex_id
                GROUP BY v.complex_id, c.complex_name;
            """,
        "3.Get details of venues in a specific country (e.g., Chile)": """
                SELECT * FROM Venues
                WHERE country_name = 'Chile';
            """,
        "4.Identify all venues and their timezones": """
                SELECT venue_name, timezone FROM Venues;
            """,
        "5.Find complexes that have more than one venue": """
                SELECT v.complex_id, c.complex_name, COUNT(v.venue_id) AS venue_count
                FROM Venues v
                JOIN Complexes c ON v.complex_id = c.complex_id
                GROUP BY v.complex_id, c.complex_name
                HAVING COUNT(v.venue_id) > 1;
            """,
        "6.List venues grouped by country": """
                SELECT country_name, ARRAY_AGG(venue_name) AS venues
                FROM Venues
                GROUP BY country_name;
            """,
        "7.Find all venues for a specific complex (e.g., Nacional)": """
                SELECT v.venue_name, v.city_name, v.country_name
                FROM Venues v
                JOIN Complexes c ON v.complex_id = c.complex_id
                WHERE c.complex_name = 'Nacional';
            """
    }
    selected_query = st.sidebar.selectbox("Select a Query", list(query_options.keys()))

    if selected_query:
        query = query_options[selected_query]
        result_df = execute_query(query)
        st.header(f"Task2 Query: {selected_query}")
        st.dataframe(result_df, use_container_width=True)

    st.sidebar.header("Task3 Custom Queries")
    query_options = {
        "1.Get all competitors with their rank and points": """
                SELECT c.name, r.rank, r.points 
                FROM Competitors c
                JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id;
            """,
        "2.Find competitors ranked in the top 5": """
                SELECT c.name, r.rank, r.points
                FROM Competitors c
                JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
                WHERE r.rank <= 5;
            """,
        "3.List competitors with no rank movement (stable rank)": """
                SELECT c.name, r.rank, r.points
                FROM Competitors c
                JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
                WHERE r.movement = 0;
            """,
        "4.Get the total points of competitors from a specific country (e.g., Croatia)": """
                SELECT SUM(r.points) AS total_points
                FROM Competitors c
                JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
                WHERE c.country = 'Croatia';
            """,
        "5.Count the number of competitors per country": """
                SELECT c.country, COUNT(*) AS competitor_count
                FROM Competitors c
                JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
                GROUP BY c.country;
            """,
        "6.Find competitors with the highest points in the current week": """
                SELECT c.name, r.rank, r.points
                FROM Competitors c
                JOIN Competitor_Rankings r ON c.competitor_id = r.competitor_id
                WHERE r.points = (SELECT MAX(points) FROM Competitor_Rankings);
            """
    }
    selected_query = st.sidebar.selectbox("Select a Query", list(query_options.keys()))

    if selected_query:
        query = query_options[selected_query]
        result_df = execute_query(query)
        st.header(f"Task3 Query: {selected_query}")
        st.dataframe(result_df, use_container_width=True)

    

if __name__ == "__main__":
    main()
