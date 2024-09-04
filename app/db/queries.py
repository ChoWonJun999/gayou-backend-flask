CREATE_TABLE_PLACES = """
CREATE TABLE IF NOT EXISTS places (
    contentid INT,
    title TEXT,
    addr1 TEXT,
    addr2 TEXT,
    areacode INT,
    booktour DOUBLE,
    cat1 TEXT,
    cat2 TEXT,
    cat3 TEXT,
    contenttypeid TEXT,
    createdtime DATETIME,
    firstimage TEXT,
    firstimage2 TEXT,
    mapx DOUBLE,
    mapy DOUBLE,
    modifiedtime DATETIME,
    tel TEXT,
    overview TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (contentid)
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
