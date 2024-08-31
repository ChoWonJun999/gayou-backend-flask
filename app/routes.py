from flask import Flask, request, jsonify
from flask_cors import CORS
from .db import get_db_connection
from .queries import SELECT_ALL_PLACES, INSERT_OR_UPDATE_PLACE, DELETE_PLACE

def init_routes(app):

    @app.route('/places', methods=['GET'])
    def get_places():
        """
        모든 장소 데이터를 조회하는 엔드포인트.
        """
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(SELECT_ALL_PLACES)
        places = cursor.fetchall()
        conn.close()
        return jsonify(places), 200

    @app.route('/place', methods=['POST'])
    def add_place():
        """
        새로운 장소 데이터를 추가하는 엔드포인트.
        """
        data = request.json
        contentid = data.get('contentid')
        title = data.get('title')
        addr1 = data.get('addr1')
        areacode = data.get('areacode')
        cat1 = data.get('cat1')
        cat2 = data.get('cat2')
        cat3 = data.get('cat3')
        mapx = data.get('mapx')
        mapy = data.get('mapy')
        overview = data.get('overview')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(INSERT_OR_UPDATE_PLACE, (
            contentid, title, addr1, areacode, cat1, cat2, cat3, mapx, mapy, overview, datetime.now()
        ))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Place added successfully'}), 201

    @app.route('/place/<string:contentid>', methods=['PUT'])
    def update_place(contentid):
        """
        기존 장소 데이터를 수정하는 엔드포인트.
        """
        data = request.json
        title = data.get('title')
        addr1 = data.get('addr1')
        areacode = data.get('areacode')
        cat1 = data.get('cat1')
        cat2 = data.get('cat2')
        cat3 = data.get('cat3')
        mapx = data.get('mapx')
        mapy = data.get('mapy')
        overview = data.get('overview')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(INSERT_OR_UPDATE_PLACE, (
            contentid, title, addr1, areacode, cat1, cat2, cat3, mapx, mapy, overview, datetime.now()
        ))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Place updated successfully'}), 200

    @app.route('/place/<string:contentid>', methods=['DELETE'])
    def delete_place(contentid):
        """
        특정 장소 데이터를 삭제하는 엔드포인트.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(DELETE_PLACE, (contentid,))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Place deleted successfully'}), 200
