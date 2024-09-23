from flask import Blueprint, jsonify, request
from ..db import execute_query
from ..db.queries import SELECT_ALL_PLACES
from ..logging import setup_logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import json

# 로그 설정
logger = setup_logging()

# 블루프린트 설정
places_bp = Blueprint('route/locations', __name__)

def filter_combined_text(df):
    """combined_text가 비어있거나, stop words만 포함한 데이터를 필터링하는 함수"""
    # combined_text가 None이 아니고, 비어 있지 않은 데이터만 필터링
    filtered_df = df[df['combined_text'].notna() & df['combined_text'].str.strip().ne('')]
    
    # 너무 짧거나, 의미 있는 단어가 없는 경우도 제거
    return filtered_df[filtered_df['combined_text'].apply(lambda x: len(x.split()) > 1)]


def calculate_cosine_similarity(filtered_df, preference, default_df):
    """코사인 유사도를 계산하는 함수"""
    if filtered_df.empty:
        filtered_df = default_df

    # 사용자 입력에 기반한 텍스트 (selectedConcepts 사용)
    user_input = ' '.join(preference.get("selectedConcepts", []))

    if not user_input.strip():
        logger.error("User input for TF-IDF vectorization is empty.")
        return default_df

    # TF-IDF 벡터화 및 코사인 유사도 계산
    try:
        vectorizer = TfidfVectorizer(stop_words=None)
        
        # 벡터화할 텍스트가 없으면 바로 반환
        if filtered_df.empty or filtered_df['combined_text'].str.strip().eq('').all():
            raise ValueError("No valid text data for TF-IDF vectorization.")

        tfidf_matrix = vectorizer.fit_transform(filtered_df['combined_text'])

        # 빈 벡터인 경우 예외 발생
        if tfidf_matrix.shape[1] == 0:
            raise ValueError("Empty vocabulary after TF-IDF vectorization.")

        # 사용자 입력을 벡터화하고 코사인 유사도 계산
        user_vector = vectorizer.transform([user_input])
        cosine_similarities = cosine_similarity(user_vector, tfidf_matrix).flatten()

        # 유사도가 높은 순으로 정렬
        filtered_df['similarity'] = cosine_similarities
        return filtered_df.sort_values(by='similarity', ascending=False)

    except ValueError as ve:
        logger.error(f"TF-IDF Vectorizer Error: {ve}")
        return default_df  # 오류 발생 시 기본 데이터를 반환



def create_course(filtered_df):
    """추천 코스를 생성하는 함수"""
    course = []
    restaurant_df = filtered_df[filtered_df['cat1'] == '음식']
    other_df = filtered_df[filtered_df['cat1'] != '음식']

    # 장소 추천 로직 (음식점과 다른 장소 추천)
    def append_course(df):
        if not df.empty:
            course.append(df.iloc[0].to_dict())
            return df.iloc[1:]
        return df

    other_df = append_course(other_df)
    restaurant_df = append_course(restaurant_df)
    other_df = append_course(other_df)
    other_df = append_course(other_df)

    # 음식점 또는 다른 장소로 5개의 장소를 채움
    while len(course) < 5:
        if not restaurant_df.empty:
            restaurant_df = append_course(restaurant_df)
        elif not other_df.empty:
            other_df = append_course(other_df)
        else:
            break

    return course

@places_bp.route('/', methods=['POST'])
def get_places():
    """
    추천 코스 데이터를 조회하는 엔드포인트.
    """
    try:
        preference = request.get_json()
        region = preference.get("region", "")
        neighborhoods = preference.get("neighborhoods", "")

        logger.info(f"Region: {region}, Neighborhoods: {neighborhoods}")

        # DB에서 모든 장소 데이터를 조회
        my_query = SELECT_ALL_PLACES
        query_params = []
        
        if region:
            my_query += " AND (addr1 LIKE %s OR addr2 LIKE %s)"
            query_params += [f"%{region}%", f"%{region}%"]

        if neighborhoods and "전체" not in neighborhoods:
            neighborhood_conditions = " OR ".join(["(addr1 LIKE %s OR addr2 LIKE %s)" for neigh in neighborhoods])
            my_query += f" AND ({neighborhood_conditions})"
            for neigh in neighborhoods:
                query_params += [f"%{neigh}%", f"%{neigh}%"]

        # SQL Injection 방지 위해 파라미터화된 쿼리 사용
        places_data = execute_query(my_query, query_params)

        # 데이터프레임으로 변환
        df = pd.DataFrame(places_data)

        # cat1 필드 확인
        if 'cat1' not in df.columns:
            logger.error("Missing 'cat1' field in the retrieved data.")
            return jsonify({"error": "Invalid data format: 'cat1' field missing"}), 500

        logger.info(f"Dataframe shape: {df.shape}")
        
        # combined_text가 비어 있는 데이터 필터링
        df = filter_combined_text(df)

        # 유효한 텍스트 데이터가 없을 경우 예외 처리
        if df.empty:
            logger.error("No valid text data after filtering.")
            return jsonify({"error": "No valid text data for recommendation."}), 500

        # 2. 코사인 유사도 계산
        recommended_df = calculate_cosine_similarity(df, preference, df)

        # 3. 코스 생성
        recommended_course = create_course(recommended_df)

        # JSON 응답 생성
        return jsonify(recommended_course), 200
    except Exception as e:
        logger.error(f"Error in /places route: {e}")
        return jsonify({"error": str(e)}), 500
