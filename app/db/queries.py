# CREATE TABLE 쿼리
CREATE_TABLE_PLACES = """
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
"""

# SELECT 쿼리
SELECT_ALL_PLACES = """
SELECT * FROM places
"""

# INSERT OR UPDATE 쿼리
INSERT_OR_UPDATE_PLACE = """
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
"""

# DELETE 쿼리
DELETE_PLACE = """
DELETE FROM places WHERE contentid = %s
"""

# 추가로 필요한 쿼리문이 있으면 여기에 정의
