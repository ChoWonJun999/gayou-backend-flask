CREATE_TABLE_PLACES = """
CREATE TABLE IF NOT EXISTS places (
    contentid INT,                  -- 고유 콘텐츠 ID
    addr1 VARCHAR(255),             -- 주소 1, 최대 255자로 설정
    addr2 VARCHAR(255),             -- 주소 2, 추가 주소
    cat1 VARCHAR(50),               -- 대분류
    cat2 VARCHAR(50),               -- 중분류
    cat3 VARCHAR(50),               -- 소분류
    contenttypeid VARCHAR(10),      -- 콘텐츠 타입 ID
    sigungucode VARCHAR(10),        -- 시군구 코드
    title VARCHAR(255) NOT NULL,    -- 제목, 필수
    overview TEXT,                  -- 개요, 긴 텍스트 필드
    overview_summary TEXT,          -- 요약된 개요, null 허용
    firstimage TEXT,                -- 첫 번째 이미지 URL
    firstimage2 TEXT,               -- 두 번째 이미지 URL
    cpyrhtDivCd VARCHAR(50),        -- 저작권 코드
    mapx DECIMAL(15, 10),           -- 지도 X 좌표
    mapy DECIMAL(15, 10),           -- 지도 Y 좌표
    mlevel INT,                     -- 지도 확대 수준
    tel VARCHAR(50),                -- 전화번호
    zipcode VARCHAR(10),            -- 우편번호
    combined_text TEXT,             -- 전처리된 텍스트 결합 필드
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (contentid)
);
"""

INSERT_OR_UPDATE_PLACE = """
INSERT INTO places (contentid, title, addr1, addr2, cat1, cat2, cat3, contenttypeid, sigungucode,
                    overview, overview_summary, firstimage, firstimage2, cpyrhtDivCd, mapx, mapy, 
                    mlevel, tel, zipcode, combined_text)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
title=VALUES(title),
addr1=VALUES(addr1),
addr2=VALUES(addr2),
cat1=VALUES(cat1),
cat2=VALUES(cat2),
cat3=VALUES(cat3),
contenttypeid=VALUES(contenttypeid),
sigungucode=VALUES(sigungucode),
overview=VALUES(overview),
overview_summary=VALUES(overview_summary),
firstimage=VALUES(firstimage),
firstimage2=VALUES(firstimage2),
cpyrhtDivCd=VALUES(cpyrhtDivCd),
mapx=VALUES(mapx),
mapy=VALUES(mapy),
mlevel=VALUES(mlevel),
tel=VALUES(tel),
zipcode=VALUES(zipcode),
combined_text=VALUES(combined_text),
last_updated=CURRENT_TIMESTAMP;
"""

SELECT_ALL_PLACES = """
SELECT 
    contentid,
    addr1,
    addr2,
    cat1,
    cat2,
    cat3,
    contenttypeid,
    sigungucode,
    title,
    overview,
    overview_summary,
    firstimage,
    firstimage2,
    cpyrhtDivCd,
    mapx,
    mapy,
    mlevel,
    tel,
    zipcode,
    combined_text
FROM places
WHERE 1=1
"""

DELETE_PLACE = """
DELETE FROM places WHERE contentid = %s
"""