import re
import requests
import xmltodict
import pandas as pd
import xml.etree.ElementTree as ET
from ..db import save_to_db
from ..config.config import Config
from ..logging import setup_logging

# 로그 설정
logger = setup_logging()

re_special_chars = re.compile(r'[^a-z0-9가-힣\s]')
re_multiple_spaces = re.compile(r'\s+')


def fetch_area_based_data(service_key, base_url):
    """
    areaBasedList1 API로부터 데이터를 수집하는 함수.
    
    Args:
        service_key (str): 공공데이터 API 서비스 키.
        base_url (str): API 요청의 기본 URL.
    
    Returns:
        DataFrame: 수집된 데이터가 포함된 데이터프레임.
    """
    logger.info("Starting area-based data collection process.")
    all_items = []
    page_no = 1

    while True:
        logger.info(f"Fetching page {page_no} of areaBasedList1 API.")
        params = {
            'serviceKey': service_key,
            'pageNo': page_no,
            'numOfRows': 1000,
            'MobileOS': 'WIN',
            'MobileApp': 'gayou',
            'arrange': 'A',
            'areaCode': 3,
            # '_type': 'json'
            '_type': 'xml'
        }

        try:
            response = requests.get(f"{base_url}/areaBasedList1", params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from areaBasedList1 API: {e}")
            break

        # data_dict = response.json()
        data_dict = xmltodict.parse(response.text)
        items = data_dict.get('response', {}).get('body', {}).get('items', {}).get('item')

        if items:
            if isinstance(items, list):
                all_items.extend(items)
            else:
                all_items.append(items)

            total_count = int(data_dict['response']['body']['totalCount'])
            logger.info(f"Collected {len(all_items)} of {total_count} items so far.")

            if len(all_items) >= total_count:
                logger.info("Collected all data from areaBasedList1 API.")
                break
            page_no += 1
        else:
            logger.warning("No more data available or response format changed.")
            break
        
    if not all_items:
        logger.warning("No data collected from areaBasedList1 API.")
        return pd.DataFrame()  # 빈 데이터프레임 반환

    return pd.DataFrame(all_items)


def fetch_additional_overview(service_key, base_url, df):
    """
    detailCommon1 API를 사용하여 추가 정보를 수집하는 함수.
    
    Args:
        service_key (str): 공공데이터 API 서비스 키.
        base_url (str): API 요청의 기본 URL.
        df (DataFrame): 기존 수집된 데이터가 포함된 데이터프레임.
    
    Returns:
        DataFrame: 추가 정보가 포함된 데이터프레임.
    """
    logger.info("Starting additional overview data collection process.")
    data_list = []

    for content_id in df['contentid'].unique():
        logger.info(f"Fetching overview for content ID {content_id} from detailCommon1 API.")
        params = {
            'serviceKey': service_key,
            'contentId': content_id,
            'MobileOS': 'WIN',
            'MobileApp': 'gayou',
            'overviewYN': 'Y',
            '_type': 'json'
        }

        try:
            response = requests.get(f"{base_url}/detailCommon1", params=params)
            response.raise_for_status()  # HTTP 에러 처리

            # 상태 코드가 200이 아니면 오류 기록
            if response.status_code != 200:
                logger.error(f"Failed to fetch overview for content ID {content_id}. Status code: {response.status_code}")
                continue

            # 응답 내용이 비어있을 경우 예외 처리
            try:
                data_dict = response.json()
            except ValueError:
                logger.error(f"Failed to parse JSON for content ID {content_id}. Response: {response.text}")
                continue

            items = data_dict.get('response', {}).get('body', {}).get('items', {}).get('item')

            if items:
                if isinstance(items, dict):  # 단일 항목일 경우
                    items = [items]
                for item in items:
                    data = {
                        'contentid': item['contentid'],
                        'overview': item.get('overview', None)
                    }
                    data_list.append(data)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch overview for content ID {content_id}: {e}")
            continue
    
    return pd.DataFrame(data_list)


def process_data(df):
    """
    데이터를 전처리하는 함수. 데이터베이스에서 places_info 테이블을 불러와 전처리한 후, places 테이블에 저장.
    
    Returns:
        DataFrame: 전처리된 데이터프레임.
    """
    try:
        # 매핑
        sigunguCode_mapping = {1: '대덕구', 2: '동구', 3: '서구', 4: '유성구', 5: '중구'}
        contenttypeid_mapping = {
            12: '관광지',
            14: '문화시설',
            15: '축제공연행사',
            25: '여행코스',
            28: '레포츠',
            32: '숙박',
            38: '쇼핑',
            39: '음식점'
        }
        cpyrhtDivCd_mapping = {
            'Type1': '제1유형, 출처표시-권장',
            'Type3': '제1유형 + 변경금지',
        }

        # 매핑 적용
        df['cpyrhtDivCd'] = df['cpyrhtDivCd'].map(cpyrhtDivCd_mapping)
        df['sigungucode'] = df['sigungucode'].map(sigunguCode_mapping)
        df['contenttypeid'] = df['contenttypeid'].map(contenttypeid_mapping)

        # 엑셀 파일 병합
        classification_df = pd.read_excel('./한국관광공사_국문_서비스분류코드_v4.2.xlsx', header=4).iloc[:, 1:]
        classification_df.columns = ['cat1', 'cat2', 'cat3', '대분류', '중분류', '소분류']

        df = df.merge(classification_df, on=['cat1', 'cat2', 'cat3'], how='left')
        df = df.drop(columns=['cat1', 'cat2', 'cat3'])

        df = df.rename(columns={
            '대분류': 'cat1',
            '중분류': 'cat2',
            '소분류': 'cat3'
        })

        # 텍스트 결합
        columns_to_combine = ['addr1', 'cat1', 'cat2', 'cat3', 'contenttypeid', 'sigungucode', 'title', 'overview']
        df['combined_text'] = df[columns_to_combine].fillna('').agg(' '.join, axis=1)

        # 텍스트 정규화 함수
        def normalize_text(text):
            text = text.lower()
            text = re_special_chars.sub('', text)  # 특수 문자 제거
            text = re_multiple_spaces.sub(' ', text).strip()  # 불필요한 공백 제거
            return text

        # 정규화 적용
        df['combined_text'] = df['combined_text'].apply(normalize_text)

        # GPT API를 사용하여 overview 요약 생성 (비활성화)
        # def summarize_overview(overview):
        #     if pd.isna(overview) or not overview.strip():
        #         return None  # 내용이 없을 경우 None 반환
        #     try:
        #         response = openai.ChatCompletion.create(
        #             model="gpt-4o-mini",  # 저렴한 요약용 모델
        #             messages=[{"role": "system", "content": "You are a helpful assistant that summarizes text."},
        #                       {"role": "user", "content": f"Summarize this text: {overview}"}]
        #         )
        #         summary = response['choices'][0]['message']['content'].strip()
        #         return summary
        #     except Exception as e:
        #         logger.error(f"Error summarizing overview: {e}")
        #         return None

        # overview 요약 컬럼 추가 (비활성화 상태)
        # df['overview_summary'] = df['overview'].apply(summarize_overview)

        print("Data preprocessing completed.")
        
        return df

    except Exception as e:
        print(f"Error fetching data from places_info: {e}")
        return pd.DataFrame()
    

def collect_data():
    """
    공공데이터 API로부터 데이터를 수집하고 데이터베이스에 저장하는 메인 함수.
    """
    logger.info("Starting data collection process.")
    
    # 1. 기본 데이터 수집
    df = fetch_area_based_data(Config.SERVICE_KEY, Config.BASE_URL)
    
    if df.empty:
        logger.warning("No data to process. Exiting data collection.")
        return

    # 2. 추가 정보 수집
    overviews = fetch_additional_overview(Config.SERVICE_KEY, Config.BASE_URL, df)
    if not overviews.empty:
        df = pd.merge(df, overviews, on='contentid', how='left')
        df = process_data(df)
        
    # 3. 데이터 저장
    try:
        save_to_db(df)
        logger.info("Data successfully saved to the database.")
    except Exception as e:
        logger.error(f"Failed to save data to the database: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info("Data collection process completed.")
