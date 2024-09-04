import requests
import xmltodict
import pandas as pd
import xml.etree.ElementTree as ET
from ..db import save_to_db
from ..config.config import Config
from ..logging import setup_logging

# 로그 설정
logger = setup_logging()

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
            '_type': 'xml'
        }

        try:
            response = requests.get(f"{base_url}/areaBasedList1", params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from areaBasedList1 API: {e}")
            break

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
            'defaultYN': 'Y',
            'firstImageYN': 'Y',
            'areacodeYN': 'Y',
            'catcodeYN': 'Y',
            'overviewYN': 'Y',
            '_type': 'xml'
        }

        try:
            response = requests.get(f"{base_url}/detailCommon1", params=params)
            logger.error(response)
        except requests.RequestException as e:
            logger.error(f"Failed to fetch overview for content ID {content_id}: {e}")
            continue

        root = ET.fromstring(response.content)
        for item in root.iter('item'):
            data = {
                'contentid': item.find('contentid').text,
                'overview': item.find('overview').text if item.find('overview') is not None else None,
            }
            data_list.append(data)
    
    return pd.DataFrame(data_list)


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
        # 주소
        df['addr1'] = df['addr1'].fillna('정보 없음')
        df['addr2'] = df['addr2'].fillna('정보 없음')

        # 이미지
        df['firstimage'] = df['firstimage'].fillna('이미지 미제공')
        df['firstimage2'] = df['firstimage2'].fillna('이미지 미제공')

        df['overview'] = df['overview'].fillna('정보 미제공')

    # 3. 데이터 저장
    try:
        save_to_db(df)
        logger.info("Data successfully saved to the database.")
    except Exception as e:
        logger.error(f"Failed to save data to the database: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info("Data collection process completed.")
