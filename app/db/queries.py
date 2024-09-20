# CREATE TABLE 쿼리(api 호출 후 전처리 요약 후 담길 데이터 테이블)
CREATE_TABLE_PLACES = """
CREATE TABLE IF NOT EXISTS places (
    addr1 TEXT ,
    addr2 TEXT ,
    areacode TEXT ,
    booktour TEXT ,
    cat1 TEXT ,
    cat2 TEXT ,
    cat3 TEXT ,
    contentid BIGINT NOT NULL PRIMARY KEY,
    contenttypeid VARCHAR(50) ,
    createdtime VARCHAR(50) ,  -- 또는 DATETIME으로 변환 가능
    firstimage TEXT ,
    firstimage2 TEXT ,
    cpyrhtDivCd TEXT ,
    mapx DOUBLE ,
    mapy DOUBLE ,
    mlevel TEXT ,
    modifiedtime VARCHAR(50) ,  -- 또는 DATETIME으로 변환 가능
    sigungucode TEXT ,
    tel TEXT ,
    title TEXT ,
    zipcode TEXT ,
    overview TEXT ,
    overview_summary TEXT ,     -- 요약된 텍스트를 저장할 컬럼 추가
    combined_text TEXT
);
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
