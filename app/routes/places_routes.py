from flask import Blueprint, jsonify, request
from ..db import execute_query
from ..logging import setup_logging
from ..db.queries import *

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

# 로그 설정
logger = setup_logging()

# 블루프린트 설정
places_bp = Blueprint('places', __name__)

'''
테스트 용 
curl -X POST http://localhost:5000/places/recommend \
-H "Content-Type: application/json" \
-d '{
     "region": "동구",
     "neighborhoods": ["중앙동", "판암1동"],
     "selectedConcepts": ["전통", "양식"]
}'
'''

# 장소 추천 엔드포인트
@places_bp.route('/recommend', methods=['POST'])
def recommend_places():
    """
    사용자의 선호에 맞는 장소를 추천하는 엔드포인트.
    """
    try:
        # 사용자의 선호 데이터를 받아옴
        data = request.get_json()
        region = data.get('region', '').strip()
        neighborhoods = data.get('neighborhoods', [])
        selected_concepts = data.get('selectedConcepts', [])

        if not selected_concepts:
            return jsonify({"error": "selectedConcepts are required"}), 400

        # DB에서 모든 장소 데이터를 조회
        places_data = execute_query(SELECT_ALL_PLACES)

        # 데이터프레임으로 변환
        df = pd.DataFrame(places_data)

        # combined_text가 비어 있는 데이터 필터링
        df = df[df['combined_text'].str.strip() != '']

        # 필터링 함수
        def filter_data_by_preference(df, region, neighborhoods):
            neighborhoods_pattern = '|'.join(neighborhoods)

            # 1. region과 neighborhoods 모두 비어있는 경우 (전체 데이터 사용)
            if not region and not neighborhoods:
                return df.copy()

            # 2. region이 비어있고 neighborhoods만 있는 경우
            if not region:
                return df[df['addr2'].str.contains(neighborhoods_pattern, case=False, na=False)].copy()

            # 3. neighborhoods가 비어있고 region만 있는 경우
            if not neighborhoods:
                return df[df['addr1'].str.contains(region, case=False, na=False)].copy()

            # 4. region과 neighborhoods 모두 있는 경우
            return df[
                (df['addr1'].str.contains(region, case=False, na=False)) |
                (df['addr2'].str.contains(neighborhoods_pattern, case=False, na=False))
            ].copy()

        # 데이터 필터링
        filtered_df = filter_data_by_preference(df, region, neighborhoods)

        # 필터링된 데이터가 없을 경우
        if filtered_df.empty:
            logger.warning("No places found based on the given region and neighborhoods.")
            return jsonify({"message": "No places found based on the given preferences."}), 404

        # 사용자 입력을 기반으로 코사인 유사도 계산
        user_input = ' '.join(selected_concepts)
        vectorizer = TfidfVectorizer(stop_words=None)
        tfidf_matrix = vectorizer.fit_transform(filtered_df['combined_text'])

        # 사용자 입력을 벡터화하고 코사인 유사도 계산
        user_vector = vectorizer.transform([user_input])
        cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()

        # 유사도가 높은 순으로 정렬
        filtered_df['similarity'] = cosine_similarities
        recommended_df = filtered_df.sort_values(by='similarity', ascending=False)

        # 상위 5개 장소 추천, 모든 정보를 포함하여 반환
        recommended_places = recommended_df.head(5).to_dict(orient='records')

        logger.info("Successfully recommended places based on user preferences.")
        return jsonify(recommended_places), 200

    except Exception as e:
        logger.error(f"Error in POST /places/recommend route: {e}")
        return jsonify({"error": str(e)}), 500

# @app.route('/route/locations', methods=['GET'])
# def get_route_locations():
#     import requests
#     import os
#     from dotenv import load_dotenv

#     load_dotenv()
    
#     url = 'https://apis.data.go.kr/B551011/KorService1/areaBasedList1'
#     params = {
#         'serviceKey': os.environ.get('DATA_API_KEY'),
#         'areaCode': 3,
#         'MobileOS': 'ETC',
#         'MobileApp': 'gayou',
#         "_type": "json",
#     }
#     try:
#         response = requests.get(url, params=params)

#         if response.status_code == 200:
#             data = response.json()
#             return jsonify({'data': data['response']['body']['items']['item'], 'town':'동네 이름', 'courseTite':'계족산에서 힐링 한 바가지 두 바가지'}), 200
#         else:
#             return jsonify({'message': response.text}), response.status_code

#     except requests.exceptions.SSLError as e:
#         return jsonify({'message': f'SSL Error: {e}'}), 500
#     except requests.exceptions.RequestException as e:
#         return jsonify({'message': f'Request Error: {e}'}), 500
    
# 모든 장소 조회
@places_bp.route('/', methods=['GET'])
def get_places():
    """
    모든 장소 데이터를 조회하는 엔드포인트.
    """
    try:
        result = execute_query(SELECT_ALL_PLACES)
        if result is not None:
            logger.info("Successfully fetched all places.")
            return jsonify(result), 200
        else:
            logger.error("Failed to fetch places.")
            return jsonify({"error": "Failed to fetch places"}), 500
    except Exception as e:
        logger.error(f"Error in /places route: {e}")
        return jsonify({"error": str(e)}), 500

# 특정 장소 조회
@places_bp.route('/<contentid>', methods=['GET'])
def get_place(contentid):
    """
    특정 장소 데이터를 조회하는 엔드포인트.
    """
    try:
        query = "SELECT * FROM places WHERE contentid = %s"
        result = execute_query(query, (contentid,))
        if result:
            logger.info(f"Successfully fetched place with contentid: {contentid}.")
            return jsonify(result[0]), 200
        else:
            logger.warning(f"Place with contentid {contentid} not found.")
            return jsonify({"error": "Place not found"}), 404
    except Exception as e:
        logger.error(f"Error in /places/{contentid} route: {e}")
        return jsonify({"error": str(e)}), 500

# 장소 추가
@places_bp.route('/', methods=['POST'])
def add_place():
    """
    새로운 장소 데이터를 추가하는 엔드포인트.
    """
    try:
        data = request.get_json()
        query = """
        INSERT INTO places (contentid, title, addr1, areacode, cat1, cat2, cat3, mapx, mapy, overview, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = (
            data['contentid'], data['title'], data['addr1'], data['areacode'],
            data['cat1'], data['cat2'], data['cat3'], data['mapx'], data['mapy'], data['overview']
        )
        execute_query(query, params)
        logger.info("New place added successfully.")
        return jsonify({"message": "Place added successfully"}), 201
    except Exception as e:
        logger.error(f"Error in POST /places route: {e}")
        return jsonify({"error": str(e)}), 500

# 장소 삭제
@places_bp.route('/<contentid>', methods=['DELETE'])
def delete_place(contentid):
    """
    특정 장소 데이터를 삭제하는 엔드포인트.
    """
    try:
        query = "DELETE FROM places WHERE contentid = %s"
        execute_query(query, (contentid,))
        logger.info(f"Place with contentid {contentid} deleted successfully.")
        return jsonify({"message": "Place deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error in DELETE /places/{contentid} route: {e}")
        return jsonify({"error": str(e)}), 500


## 목록... 
