# 테이블 생성 쿼리
CREATE_PLACES_TABLE = '''
CREATE TABLE IF NOT EXISTS places (
    contentid VARCHAR(50) PRIMARY KEY,
    title TEXT,
    addr1 TEXT,
    areacode TEXT,
    cat1 TEXT,
    cat2 TEXT,
    cat3 TEXT,
    mapx DOUBLE,
    mapy DOUBLE,
    overview TEXT,
    last_updated TIMESTAMP
)
'''

# 데이터 삽입 및 업데이트 쿼리
INSERT_OR_UPDATE_PLACE = '''
INSERT INTO places (contentid, title, addr1, areacode, cat1, cat2, cat3, mapx, mapy, overview, last_updated)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    title=VALUES(title),
    addr1=VALUES(addr1),
    areacode=VALUES(areacode),
    cat1=VALUES(cat1),
    cat2=VALUES(cat2),
    cat3=VALUES(cat3),
    mapx=VALUES(mapx),
    mapy=VALUES(mapy),
    overview=VALUES(overview),
    last_updated=VALUES(last_updated)
'''

# 모든 데이터 조회 쿼리
SELECT_ALL_PLACES = 'SELECT * FROM places'

# 데이터 삽입 및 업데이트 쿼리
INSERT_OR_UPDATE_PLACE = '''
INSERT INTO places (contentid, title, addr1, areacode, cat1, cat2, cat3, mapx, mapy, overview, last_updated)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    title=VALUES(title),
    addr1=VALUES(addr1),
    areacode=VALUES(areacode),
    cat1=VALUES(cat1),
    cat2=VALUES(cat2),
    cat3=VALUES(cat3),
    mapx=VALUES(mapx),
    mapy=VALUES(mapy),
    overview=VALUES(overview),
    last_updated=VALUES(last_updated)
'''

# 데이터 삭제 쿼리
DELETE_PLACE = 'DELETE FROM places WHERE contentid = %s'

