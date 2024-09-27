from flask import Blueprint, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from ..db import execute_query
from ..db.queries import SELECT_ALL_PLACES
from ..logging import setup_logging

logger = setup_logging()
places_bp = Blueprint('route/locations', __name__)


def fetch_places(limit=None):
    """Fetches places from the database with an optional limit."""
    try:
        query = SELECT_ALL_PLACES
        if limit:
            query += f" LIMIT {limit}"
        places = execute_query(query)
        if places is None:
            raise ValueError("Failed to fetch places from the database.")
        return places
    except Exception as e:
        logger.error(f"Error fetching places: {e}")
        raise


def filter_data_by_preference(df: pd.DataFrame, preference: dict) -> pd.DataFrame:
    """Filters the dataframe based on user preferences."""
    region = preference.get("region")
    neighborhoods = preference.get("neighborhoods", [])

    if not region and not neighborhoods:
        return df.copy()

    neighborhoods_pattern = '|'.join(neighborhoods)
    
    if not region:
        return df[df['addr2'].str.contains(neighborhoods_pattern, case=False, na=False)].copy()
    
    if not neighborhoods:
        return df[df['addr1'].str.contains(region, case=False, na=False)].copy()

    return df[
        (df['addr1'].str.contains(region, case=False, na=False)) |
        (df['addr2'].str.contains(neighborhoods_pattern, case=False, na=False))
    ].copy()


def calculate_cosine_similarity(filtered_df: pd.DataFrame, preference: dict) -> pd.DataFrame:
    """Calculates cosine similarity based on user-selected concepts."""
    filtered_df = filtered_df[filtered_df['combined_text'].str.strip() != '']

    if filtered_df.empty:
        logger.info("No valid combined_text. Recommending based on full data.")
        return pd.DataFrame()

    user_input = ' '.join(preference.get("selectedConcepts", []))
    vectorizer = TfidfVectorizer(stop_words=None)
    tfidf_matrix = vectorizer.fit_transform(filtered_df['combined_text'])

    user_vector = vectorizer.transform([user_input])
    cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()

    filtered_df['similarity'] = cosine_similarities
    return filtered_df.sort_values(by='similarity', ascending=False)


def create_course(filtered_df: pd.DataFrame) -> list:
    """Creates a travel course based on the highest similarity scores."""
    course = []

    restaurant_df = filtered_df[filtered_df['cat1'] == '음식']
    other_df = filtered_df[filtered_df['cat1'] != '음식']

    if not other_df.empty:
        course.append(other_df.iloc[0].to_dict())
        other_df = other_df.iloc[1:]

    if not restaurant_df.empty:
        course.append(restaurant_df.iloc[0].to_dict())
        restaurant_df = restaurant_df.iloc[1:]
    else:
        if not other_df.empty:
            course.append(other_df.iloc[0].to_dict())
            other_df = other_df.iloc[1:]

    while len(course) < 5:
        if not restaurant_df.empty:
            course.append(restaurant_df.iloc[0].to_dict())
            restaurant_df = restaurant_df.iloc[1:]
        elif not other_df.empty:
            course.append(other_df.iloc[0].to_dict())
            other_df = other_df.iloc[1:]
        else:
            break

    return course


@places_bp.route('/', methods=['GET'])
def recommend():
    """Endpoint to recommend a course based on user preferences."""
    try:
        region = request.args.get('region')
        neighborhoods = request.args.getlist('neighborhoods[]')
        selected_concepts = request.args.getlist('selectedConcepts[]')

        preference = {
            'region': region,
            'neighborhoods': neighborhoods,
            'selectedConcepts': selected_concepts
        }

        places_data = fetch_places()
        df = pd.DataFrame(places_data)

        if df.empty:
            return jsonify({"error": "No data available"}), 500

        filtered_df = filter_data_by_preference(df, preference)

        if filtered_df.empty:
            return jsonify({"error": "No matching places found based on preference"}), 404

        recommended_df = calculate_cosine_similarity(filtered_df, preference)

        if recommended_df.empty:
            return jsonify({"error": "No recommendations available"}), 404

        recommended_course = create_course(recommended_df)
        content = {
            'town': region,
            'data': recommended_course,
        }
        return jsonify(content), 200

    except Exception as e:
        logger.error(f"Error during recommendation: {e}")
        return jsonify({"error": str(e)}), 500


@places_bp.route('/sort/', methods=['GET'])
def get_places_by_similarity():
    """Endpoint to sort places by similarity based on preferences."""
    try:
        region = request.args.get('region')
        neighborhoods = request.args.getlist('neighborhoods[]')
        selected_concepts = request.args.getlist('selectedConcepts[]')

        preference = {
            'region': region,
            'neighborhoods': neighborhoods,
            'selectedConcepts': selected_concepts
        }
        
        places_data = fetch_places()
        df = pd.DataFrame(places_data)

        if df.empty:
            return jsonify({"error": "No data available"}), 500

        filtered_df = filter_data_by_preference(df, preference)

        if filtered_df.empty:
            return jsonify({"error": "No matching places found based on preference"}), 404

        recommended_df = calculate_cosine_similarity(filtered_df, preference)

        if recommended_df.empty:
            return jsonify({"error": "No places found based on similarity"}), 404

        return jsonify(recommended_df.to_dict(orient='records')), 200

    except Exception as e:
        logger.error(f"Error during similarity query: {e}")
        return jsonify({"error": str(e)}), 500
