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

INSERT_OR_UPDATE_PLACE = """
INSERT INTO places (contentid, title, addr1, addr2, areacode, booktour, cat1, cat2, cat3, contenttypeid, createdtime, 
                    firstimage, firstimage2, mapx, mapy, modifiedtime, tel, overview)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
title=VALUES(title),
addr1=VALUES(addr1),
addr2=VALUES(addr2),
areacode=VALUES(areacode),
booktour=VALUES(booktour),
cat1=VALUES(cat1),
cat2=VALUES(cat2),
cat3=VALUES(cat3),
contenttypeid=VALUES(contenttypeid),
createdtime=VALUES(createdtime),
firstimage=VALUES(firstimage),
firstimage2=VALUES(firstimage2),
mapx=VALUES(mapx),
mapy=VALUES(mapy),
modifiedtime=VALUES(modifiedtime),
tel=VALUES(tel),
overview=VALUES(overview);
"""

SELECT_ALL_PLACES = """
SELECT * FROM places Order by rand() LIMIT 5;
"""

DELETE_PLACE = """
DELETE FROM places WHERE contentid = %s
"""

# 추가로 필요한 쿼리문이 있으면 여기에 정의
