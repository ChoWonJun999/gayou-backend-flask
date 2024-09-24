from flask import Blueprint, jsonify, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from ..db import execute_query
from ..db.queries import SELECT_ALL_PLACES
from ..logging import setup_logging

# 로그 설정
logger = setup_logging()

# 블루프린트 설정
places_bp = Blueprint('places', __name__)
recommend_bp = Blueprint('recommend', __name__)


# 모든 장소 조회
@places_bp.route('/', methods=['GET'])
def get_places():
    """
    DB에서 모든 장소 데이터를 조회하고 DataFrame으로 변환하는 함수.
    
    Returns:
        DataFrame: DB에서 조회한 장소 데이터를 반환.
    """
    try:
        # 데이터 조회
        places_data = execute_query(SELECT_ALL_PLACES, [])
        df = pd.DataFrame(places_data)

        # 데이터프레임이 비어 있으면 오류 반환
        if df.empty:
            logger.error("No data available in the places table.")
            return pd.DataFrame()  # 빈 데이터프레임 반환

        return df

    except Exception as e:
        logger.error(f"Error fetching places data: {e}")
        return pd.DataFrame()  # 예외 발생 시 빈 데이터프레임 반환


# 1. 필터링 조건 설정
def filter_data_by_preference(df, preference):
    """
    사용자 선호 데이터를 기반으로 장소 데이터를 필터링하는 함수.
    
    Args:
        df (DataFrame): DB에서 불러온 장소 데이터프레임.
        preference (dict): 사용자 선호 데이터를 담고 있는 JSON 객체.
    
    Returns:
        DataFrame: 필터링된 장소 데이터프레임.
    """
    region = preference.get("region", "").strip()
    neighborhoods = preference.get("neighborhoods", [])

    # 1. region과 neighborhoods 모두 비어있는 경우 (전체 데이터 사용)
    if not region and not neighborhoods:
        return df.copy()

    # 2. region이 비어있고 neighborhoods만 있는 경우
    if not region:
        neighborhoods_pattern = '|'.join(neighborhoods)
        return df[df['addr2'].str.contains(neighborhoods_pattern, case=False, na=False)].copy()

    # 3. neighborhoods가 비어있고 region만 있는 경우
    if not neighborhoods:
        return df[df['addr1'].str.contains(region, case=False, na=False)].copy()

    # 4. region과 neighborhoods 모두 있는 경우
    neighborhoods_pattern = '|'.join(neighborhoods)
    return df[
        (df['addr1'].str.contains(region, case=False, na=False)) |
        (df['addr2'].str.contains(neighborhoods_pattern, case=False, na=False))
    ].copy()


# 2. 코사인 유사도 계산 (기존 코드 재사용)
def calculate_cosine_similarity(filtered_df, preference):
    """
    사용자 선호 데이터를 기반으로 장소 데이터를 TF-IDF와 코사인 유사도로 계산.
    
    Args:
        filtered_df (DataFrame): 필터링된 장소 데이터.
        preference (dict): 사용자 선호 데이터를 담은 JSON 객체.
    
    Returns:
        DataFrame: 코사인 유사도에 따라 정렬된 장소 데이터프레임.
    """
    # combined_text가 비어있는 데이터 제거
    filtered_df = filtered_df[filtered_df['combined_text'].str.strip() != '']

    # 필터링된 데이터가 없는 경우 예외 처리
    if filtered_df.empty:
        print("유효한 combined_text가 없습니다. 전체 데이터를 사용하여 추천을 진행합니다.")
        return pd.DataFrame()

    # 사용자 입력에 기반한 텍스트 (selectedConcepts 사용)
    user_input = ' '.join(preference["selectedConcepts"])

    # TF-IDF 벡터화 및 코사인 유사도 계산
    vectorizer = TfidfVectorizer(stop_words=None)
    tfidf_matrix = vectorizer.fit_transform(filtered_df['combined_text'])

    # 사용자 입력을 벡터화하고 코사인 유사도 계산
    user_vector = vectorizer.transform([user_input])
    cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()

    # 유사도가 높은 순으로 정렬
    filtered_df.loc[:, 'similarity'] = cosine_similarities
    return filtered_df.sort_values(by='similarity', ascending=False)


# 3. 추천 코스 생성
def create_course(filtered_df):
    """
    사용자 선호도에 맞춰 장소를 추천하여 코스를 생성하는 함수.
    식당을 포함한 장소를 5개 추천합니다.
    
    Args:
        filtered_df (DataFrame): 유사도에 따라 정렬된 장소 데이터프레임.
    
    Returns:
        list: 추천된 장소들의 리스트.
    """
    course = []

    # 식당 필터링
    restaurant_df = filtered_df[filtered_df['cat1'] == '음식']
    other_df = filtered_df[filtered_df['cat1'] != '음식']

    # 1번째 장소는 일반 장소 추천
    if not other_df.empty:
        course.append(other_df.iloc[0].to_dict())
        other_df = other_df.iloc[1:]

    # 2번째 장소는 무조건 식당 추천
    if not restaurant_df.empty:
        course.append(restaurant_df.iloc[0].to_dict())
        restaurant_df = restaurant_df.iloc[1:]
    else:
        if not other_df.empty:
            course.append(other_df.iloc[0].to_dict())
            other_df = other_df.iloc[1:]

    # 3~5번째 장소 추천 로직
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


# 4. 추천 API 엔드포인트
@recommend_bp.route('/recommend', methods=['POST'])
def recommend():
    """
    사용자의 선호 데이터를 기반으로 장소를 추천하는 엔드포인트.
    
    Returns:
        JSON: 추천된 장소 목록.
    """
    try:
        preference = request.json  # 사용자 선호 데이터를 가져옴
        df = get_places()  # DB에서 모든 장소 데이터 불러오기

        if df.empty:
            return jsonify({"error": "No data available"}), 500

        # 1. 필터링 단계
        filtered_df = filter_data_by_preference(df, preference)

        if filtered_df.empty:
            return jsonify({"error": "No matching places found based on preference"}), 404

        # 2. 코사인 유사도 계산
        recommended_df = calculate_cosine_similarity(filtered_df, preference)

        if recommended_df.empty:
            return jsonify({"error": "No recommendations available"}), 404

        # 3. 추천 코스 생성
        recommended_course = create_course(recommended_df)

        # 4. 결과를 JSON 형태로 반환
        return jsonify(recommended_course)

    except Exception as e:
        logger.error(f"Error during recommendation: {str(e)}")
        return jsonify({"error": str(e)}), 500


# 5. 전체 유사도 정렬된 장소 조회 엔드포인트
@places_bp.route('/places/similarity', methods=['POST'])
def get_places_by_similarity():
    """
    사용자의 선호 데이터를 기반으로 유사도 정렬된 장소 목록을 조회하는 엔드포인트.
    
    Returns:
        JSON: 유사도에 따라 정렬된 장소 목록.
    """
    try:
        preference = request.json  # 사용자 선호 데이터를 가져옴
        df = get_places()  # DB에서 모든 장소 데이터 불러오기

        if df.empty:
            return jsonify({"error": "No data available"}), 500

        # 1. 필터링 단계
        filtered_df = filter_data_by_preference(df, preference)

        if filtered_df.empty:
            return jsonify({"error": "No matching places found based on preference"}), 404

        # 2. 코사인 유사도 계산
        recommended_df = calculate_cosine_similarity(filtered_df, preference)

        if recommended_df.empty:
            return jsonify({"error": "No places found based on similarity"}), 404

        # 3. 결과를 JSON 형태로 반환
        return jsonify(recommended_df.to_dict(orient='records'))

    except Exception as e:
        logger.error(f"Error during similarity query: {str(e)}")
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