from flask import Blueprint, jsonify, request
from ..db import execute_query
from ..logging import setup_logging

# 로그 설정
logger = setup_logging()

# 블루프린트 설정
places_bp = Blueprint('places', __name__)

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
        query = "SELECT * FROM places"
        result = execute_query(query)
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
