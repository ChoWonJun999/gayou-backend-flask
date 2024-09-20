# app/scheduler/data_collector.py
import requests
import xmltodict
import pandas as pd
import xml.etree.ElementTree as ET
import openai
import re
from datetime import datetime
from ..db import save_to_db
from ..config.config import Config
from ..logging import setup_logging

# 로그 설정
logger = setup_logging()

# OpenAI API 키 설정
openai.api_key = Config.OPENAI_API_KEY


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
    all_items = []  # 모든 데이터를 저장할 리스트
    page_no = 1  # 초기 페이지 번호 설정

    # 반복적으로 API를 호출하여 데이터를 수집
    while True:
        logger.info(f"Fetching page {page_no} of areaBasedList1 API.")
        params = {
            'serviceKey': service_key,
            'pageNo': page_no,
            'numOfRows': 1000,  # 한 번에 가져올 데이터 수
            'MobileOS': 'WIN',
            'MobileApp': 'WebTest',
            'arrange': 'A',  # 데이터 정렬 기준
            'areaCode': 3,
            '_type': 'xml'  # 응답 형식
        }

        try:
            # API 호출
            response = requests.get(f"{base_url}/areaBasedList1", params=params)
            response.raise_for_status()  # 요청이 실패할 경우 예외 발생
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from areaBasedList1 API: {e}")
            break

        # 응답 데이터를 XML에서 딕셔너리로 파싱
        data_dict = xmltodict.parse(response.text)
        items = data_dict.get('response', {}).get('body', {}).get('items', {}).get('item')

        if items:
            # 수집된 데이터를 리스트에 추가
            if isinstance(items, list):
                all_items.extend(items)
            else:
                all_items.append(items)

            # 총 데이터 개수를 확인하여 수집 완료 여부 판단
            total_count = int(data_dict['response']['body']['totalCount'])
            logger.info(f"Collected {len(all_items)} of {total_count} items so far.")

            if len(all_items) >= total_count:
                logger.info("Collected all data from areaBasedList1 API.")
                break
            page_no += 1  # 다음 페이지로 이동
        else:
            logger.warning("No more data available or response format changed.")
            break

    # 수집된 데이터가 없을 경우 빈 데이터프레임 반환
    if not all_items:
        logger.warning("No data collected from areaBasedList1 API.")
        return pd.DataFrame()

    # 수집된 데이터를 데이터프레임으로 변환하여 반환
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
    data_list = []  # 추가 데이터를 저장할 리스트

    # 각 contentid에 대해 추가 데이터를 수집
    for content_id in df['contentid'].unique():
        logger.info(f"Fetching overview for content ID {content_id} from detailCommon1 API.")
        params = {
            'serviceKey': service_key,
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

        try:
            # API 호출
            response = requests.get(f"{base_url}/detailCommon1", params=params)
            response.raise_for_status()  # 요청이 실패할 경우 예외 발생
        except requests.RequestException as e:
            logger.error(f"Failed to fetch overview for content ID {content_id}: {e}")
            continue

        # XML 응답을 파싱하여 추가 데이터를 리스트에 추가
        root = ET.fromstring(response.content)
        for item in root.iter('item'):
            contentid = item.find('contentid').text if item.find('contentid') is not None else None
            overview = item.find('overview').text if item.find('overview') is not None else '정보 없음'
            
            # 확인 로깅 추가
            logger.info(f"Fetched contentid: {contentid}")
            logger.info(f"Fetched overview: {overview}")

            if contentid:
                data = {
                    'contentid': contentid,
                    'overview': overview,
                }
                data_list.append(data)

    # 추가된 데이터를 데이터프레임으로 변환하여 반환
    overview_df = pd.DataFrame(data_list)

    # contentid 필드가 없는 경우 에러 로깅
    if overview_df.empty:
        logger.warning("No overview data collected.")
        return pd.DataFrame()  # 빈 데이터프레임 반환
    
    # contentid의 타입을 일치시킴
    logger.info(f"Overview DataFrame columns: {overview_df.columns}")
    if 'contentid' in overview_df.columns:
        overview_df['contentid'] = overview_df['contentid'].astype(str)
    else:
        logger.error("contentid column is missing from overview_df")
    
    return overview_df


def preprocess_data(df, classification_path):
    """
    전처리 파이프라인을 적용하는 함수.

    Args:
        df (DataFrame): 수집된 데이터프레임.
        classification_path (str): 분류 코드 엑셀 파일 경로.

    Returns:
        DataFrame: 전처리된 데이터프레임.
    """
    # contenttypeid를 매핑하여 읽기 쉽게 변경
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
    df['contenttypeid'] = df['contenttypeid'].map(contenttypeid_mapping)

    # 분류 코드 데이터를 로드하고 병합
    classification_df = pd.read_excel(classification_path, header=4).iloc[:, 1:]
    classification_df.columns = ['cat1', 'cat2', 'cat3', '대분류', '중분류', '소분류']
    df = df.merge(classification_df, on=['cat1', 'cat2', 'cat3'], how='left')
    df = df.drop(columns=['cat1', 'cat2', 'cat3'])
    df = df.rename(columns={'대분류': 'cat1', '중분류': 'cat2', '소분류': 'cat3'})

    # 열의 순서를 재정렬
    cols = df.columns.tolist()
    cols.insert(4, cols.pop(cols.index('cat1')))
    cols.insert(5, cols.pop(cols.index('cat2')))
    cols.insert(6, cols.pop(cols.index('cat3')))
    df = df[cols]

    # 열 확인 로깅 추가
    logger.info(f"Columns in the dataframe: {df.columns}")

    # 'overview' 열이 있는지 확인
    if 'overview' not in df.columns:
        logger.error("'overview' 열이 데이터프레임에 없습니다.")
        raise KeyError("'overview' column is missing from the dataframe.")
    
    # 여러 텍스트 컬럼을 결합하여 새로운 컬럼 생성
    columns_to_combine = ['addr1', 'cat1', 'cat2', 'cat3', 'contenttypeid', 'sigungucode', 'title', 'overview']
    df['combined_text'] = df[columns_to_combine].fillna('').agg(' '.join, axis=1)

    # 텍스트 정규화 함수 정의 및 적용
    def normalize_text(text):
        text = text.lower()  # 소문자 변환
        text = re.sub(r'[^a-z0-9가-힣\s]', '', text)  # 특수 문자 제거
        text = re.sub(r'\s+', ' ', text).strip()  # 불필요한 공백 제거
        return text

    df['combined_text'] = df['combined_text'].apply(normalize_text)

    return df



def summarize_overview(text):
    """
    GPT-4 API를 사용하여 텍스트를 요약하는 함수.

    Args:
        text (str): 요약할 텍스트.

    Returns:
        str: 요약된 텍스트.
    """
    try:
        if not text or len(text.strip()) == 0:
            return "정보 없음"  # 빈 텍스트 처리

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": f"Summarize the following text: {text}"}
            ]
        )
        summary = response['choices'][0]['message']['content']
        return summary.strip()
    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        return "요약 실패"


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

    # 2. 추가 정보 수집 및 전처리
    overviews = fetch_additional_overview(Config.SERVICE_KEY, Config.BASE_URL, df)
    
    if overviews.empty:
        logger.warning("No overviews collected, skipping the merge.")
    else:
        # 병합 전에 로깅을 통해 두 데이터프레임 확인
        logger.info(f"Original dataframe: {df[['contentid', 'title']].head()}")
        logger.info(f"Overview dataframe: {overviews[['contentid', 'overview']].head()}")

        # contentid 타입이 일치하는지 확인 후 병합
        df['contentid'] = df['contentid'].astype(str)
        df = pd.merge(df, overviews, on='contentid', how='left')
        logger.info(f"Overview merged data: {df[['contentid', 'overview']].head()}")

        # 병합 후에도 overview에 결측값이 있을 경우 기본값으로 대체
        df['overview'] = df['overview'].fillna('정보 없음')

    # 전처리 수행 (여기서 overview 요약이 적용됨)
    processed_df = preprocess_data(df, 'app/scheduler/한국관광공사_국문_서비스분류코드_v4.2.xlsx')

    # 3. GPT-4 API를 사용하여 'overview' 컬럼 요약
    processed_df['overview_summary'] = processed_df['overview'].apply(lambda x: summarize_overview(x) if pd.notnull(x) else x)
    logger.info(f"Summarized overviews: {processed_df[['contentid', 'overview_summary']].head()}")

    # 4. DB에 저장하기 위해 save_to_db 함수 호출
    try:
        save_to_db(processed_df)  # DB에 저장
        logger.info("Data collection process completed.")
    except Exception as e:
        logger.error(f"Failed to save data to the database: {e}")


# 실행
if __name__ == "__main__":
    collect_data()
