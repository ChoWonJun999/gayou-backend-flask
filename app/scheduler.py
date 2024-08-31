import requests
import xmltodict
import pandas as pd
import xml.etree.ElementTree as ET
from apscheduler.schedulers.background import BackgroundScheduler
from .db import save_to_db
from .config import Config
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 스케줄러 인스턴스 생성 (하지만, 즉시 시작하지는 않음)
scheduler = BackgroundScheduler()

def collect_data():
    logging.info("Starting data collection process.")
    all_items = []
    page_no = 1

    # 1. areaBasedList1 API 데이터 수집
    while True:
        logging.info(f"Fetching page {page_no} of areaBasedList1 API.")
        params = {
            'serviceKey': Config.SERVICE_KEY,
            'pageNo': page_no,
            'numOfRows': 1000,
            'MobileOS': 'ETC',
            'MobileApp': 'AppTest',
            'arrange': 'A',
            'areaCode': 3,
            '_type': 'xml'
        }
        response = requests.get(f"{Config.BASE_URL}/areaBasedList1", params=params)

        if response.status_code != 200:
            logging.error(f"Failed to fetch data from areaBasedList1 API: {response.status_code}")
            break

        data_dict = xmltodict.parse(response.text)

        if 'response' in data_dict and 'body' in data_dict['response'] and 'items' in data_dict['response']['body']:
            items = data_dict['response']['body']['items']['item']
            if isinstance(items, list):
                all_items.extend(items)
            else:
                all_items.append(items)

            total_count = int(data_dict['response']['body']['totalCount'])
            logging.info(f"Collected {len(all_items)} of {total_count} items so far.")

            if len(all_items) >= total_count:
                logging.info("Collected all data from areaBasedList1 API.")
                break
            page_no += 1
        else:
            logging.warning("No more data available or response format changed.")
            break

    if not all_items:
        logging.warning("No data collected from areaBasedList1 API.")
        return

    df = pd.DataFrame(all_items)

    # 2. detailCommon1 API를 통해 추가 정보(overview) 수집
    data_list = []
    for content_id in df['contentid'].unique():
        logging.info(f"Fetching overview for content ID {content_id} from detailCommon1 API.")
        params = {
            'serviceKey': Config.SERVICE_KEY,
            'contentId': content_id,
            'MobileOS': 'WIN',
            'MobileApp': 'WebTest',
            'defaultYN': 'Y',
            'firstImageYN': 'Y',
            'areacodeYN': 'Y',
            'catcodeYN': 'Y',
            'overviewYN': 'Y',
            '_type': 'xml'
        }
        response = requests.get(f"{Config.BASE_URL}/detailCommon1", params=params)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.iter('item'):
                data = {
                    'contentid': item.find('contentid').text,
                    'overview': item.find('overview').text if item.find('overview') is not None else None,
                }
                data_list.append(data)
        else:
            logging.error(f"Failed to fetch overview for content ID {content_id}: {response.status_code}")

    overviews = pd.DataFrame(data_list)
    df = pd.merge(df, overviews, on='contentid', how='left')

    # 데이터 저장
    try:
        save_to_db(df)
        logging.info("Data successfully saved to the database.")
    except Exception as e:
        logging.error(f"Failed to save data to the database: {e}")

    logging.info("Data collection process completed.")

# 스케줄러 작업 추가 (하지만, 아직 시작하지 않음)
scheduler.add_job(collect_data, 'interval', weeks=1)
