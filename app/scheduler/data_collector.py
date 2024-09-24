import requests
import pandas as pd
import openai
import re
from ..db import save_to_db
from ..config.config import Config
from ..logging import setup_logging

# 로그 설정
logger = setup_logging()

# OpenAI API 키 설정
openai.api_key = Config.OPENAI_API_KEY

# 정규 표현식 컴파일 (한 번만 컴파일)
# 특수 문자를 제거하는 패턴과 다중 공백을 단일 공백으로 바꾸는 패턴을 미리 컴파일하여 성능을 향상
re_special_chars = re.compile(r'[^a-z0-9가-힣\s]')
re_multiple_spaces = re.compile(r'\s+')


def fetch_area_based_data(service_key, base_url):
    """
    지역 기반 데이터를 공공 API로부터 수집하는 함수.
    
    Args:
        service_key (str): 공공데이터 API 서비스 키.
        base_url (str): API의 기본 URL.
    
    Returns:
        DataFrame: 수집된 데이터를 포함하는 판다스 데이터프레임.
    """
    logger.info("Starting area-based data collection process.")
    all_items = []  # 모든 데이터를 저장할 리스트
    page_no = 1  # 첫 페이지부터 시작

    while True:
        # 현재 페이지 데이터를 가져옴
        logger.info(f"Fetching page {page_no} of areaBasedList1 API.")
        params = {
            'serviceKey': service_key,
            'pageNo': page_no,
            'numOfRows': 1000,  # 한 페이지에 1000개 항목 요청
            'MobileOS': 'WIN',
            'MobileApp': 'gayou',
            'arrange': 'A',
            'areaCode': 3,
            '_type': 'json'
        }

        try:
            # API 요청
            response = requests.get(f"{base_url}/areaBasedList1", params=params)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from areaBasedList1 API: {e}")
            break

        logger.info(f"Response status code: {response.status_code}")
        logger.debug(f"Response text: {response.text}")

        # 응답이 비어있는지 확인
        if not response.text.strip():
            logger.error("Empty response from areaBasedList1 API.")
            break

        try:
            # JSON 형식으로 응답을 파싱
            data_dict = response.json()
        except ValueError as e:
            logger.error(f"Error decoding JSON: {e}")
            break

        # 필요한 데이터 추출
        items = data_dict.get('response', {}).get('body', {}).get('items', {}).get('item')

        if items:
            # 리스트 형식으로 데이터를 저장
            if isinstance(items, list):
                all_items.extend(items)
            else:
                all_items.append(items)

            total_count = int(data_dict['response']['body']['totalCount'])
            logger.info(f"Collected {len(all_items)} of {total_count} items so far.")

            # 수집된 데이터가 전체 개수에 도달하면 종료
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
    추가적으로 overview 데이터를 공공 API로부터 수집하는 함수.
    
    Args:
        service_key (str): 공공데이터 API 서비스 키.
        base_url (str): API의 기본 URL.
        df (DataFrame): 수집된 데이터가 포함된 데이터프레임.
    
    Returns:
        DataFrame: 추가된 overview 데이터를 포함한 데이터프레임.
    """
    logger.info("Starting additional overview data collection process.")
    data_list = []

    # 수집된 데이터프레임에서 contentid를 순차적으로 처리
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
            # API 요청
            response = requests.get(f"{base_url}/detailCommon1", params=params)
            response.raise_for_status()  # HTTP 에러 발생 시 예외 처리

            if response.status_code != 200:
                logger.error(f"Failed to fetch overview for content ID {content_id}. Status code: {response.status_code}")
                continue

            try:
                # JSON 응답 파싱
                data_dict = response.json()
            except ValueError:
                logger.error(f"Failed to parse JSON for content ID {content_id}. Response: {response.text}")
                continue

            # overview 데이터를 추출
            items = data_dict.get('response', {}).get('body', {}).get('items', {}).get('item')

            if items:
                if isinstance(items, dict):
                    items = [items]
                for item in items:
                    data = {
                        'contentid': item['contentid'],
                        'overview': item.get('overview', None)
                    }
                    data_list.append(data)

        except requests.RequestException as e:
            logger.error(f"HTTP request failed for content ID {content_id}: {e}")
            continue

    if not data_list:
        logger.warning("No overview data collected from detailCommon1 API.")
        return pd.DataFrame()

    return pd.DataFrame(data_list)


def preprocess_data(df):
    """
    데이터를 전처리하는 함수. 데이터를 가공하여 사용할 수 있게 만듦.
    
    Args:
        df (DataFrame): 원본 데이터가 포함된 데이터프레임.
    
    Returns:
        DataFrame: 전처리된 데이터를 포함한 데이터프레임.
    """
    try:
        logger.info("Starting data preprocessing...")

        # 매핑 테이블 설정
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

        # 서비스 분류 엑셀 파일을 읽어와서 병합
        classification_df = pd.read_excel('./한국관광공사_국문_서비스분류코드_v4.2.xlsx', header=4).iloc[:, 1:]
        classification_df.columns = ['cat1', 'cat2', 'cat3', '대분류', '중분류', '소분류']

        df = df.merge(classification_df, on=['cat1', 'cat2', 'cat3'], how='left')
        df = df.drop(columns=['cat1', 'cat2', 'cat3'])
        df = df.rename(columns={'대분류': 'cat1', '중분류': 'cat2', '소분류': 'cat3'})

        # 텍스트 결합
        columns_to_combine = ['addr1', 'cat1', 'cat2', 'cat3', 'contenttypeid', 'sigungucode', 'title', 'overview']
        df['combined_text'] = df[columns_to_combine].fillna('').agg(' '.join, axis=1)

        # 텍스트 정규화
        def normalize_text(text):
            text = text.lower()
            text = re_special_chars.sub('', text)
            text = re_multiple_spaces.sub(' ', text).strip()
            return text

        df['combined_text'] = df['combined_text'].apply(normalize_text)

        # GPT API를 사용하여 overview 요약 생성
        def summarize_overview(overview):
            if pd.isna(overview) or not overview.strip():
                return None
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "당신은 텍스트를 요약하는 유용한 어시스턴트입니다."},
                        {"role": "user", "content": f"다음 텍스트를 한글로 요약해줘: {overview}"}
                    ]
                )
                if 'choices' in response:
                    summary = response['choices'][0]['message']['content'].strip()
                    return summary
                else:
                    logger.error("No choices found in the response.")
                    return None
            except Exception as e:
                logger.error(f"Error summarizing text: {e}")
                return None

        df['overview_summary'] = df['overview'].apply(summarize_overview)

        logger.info("Data preprocessing completed.")
        return df

    except Exception as e:
        logger.error(f"Error during data preprocessing: {e}")
        return pd.DataFrame()


def collect_data():
    """
    데이터를 수집하고 전처리한 후, 데이터베이스에 저장하는 메인 함수.
    """
    logger.info("Starting data collection and update process.")

    try:
        # 1. 데이터 수집
        df = fetch_area_based_data(Config.SERVICE_KEY, Config.BASE_URL)
        if df.empty:
            logger.warning("No data to process. Exiting data collection.")
            return
    except Exception as e:
        logger.error(f"Error during data collection: {e}")
        df = pd.DataFrame()

    # 2. 추가 정보 수집
    if not df.empty:
        try:
            overviews = fetch_additional_overview(Config.SERVICE_KEY, Config.BASE_URL, df)
            if not overviews.empty:
                df = pd.merge(df, overviews, on='contentid', how='left')
                df['overview'] = df['overview'].fillna('정보 없음')
        except Exception as e:
            logger.error(f"Error fetching additional overviews: {e}")

    # 3. 데이터 전처리
    try:
        df_processed = preprocess_data(df)
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        df_processed = df

    # 4. 데이터 저장
    if not df_processed.empty:
        try:
            save_to_db(df_processed)
            logger.info("Processed data successfully saved to 'places' table.")
        except Exception as e:
            logger.error(f"Failed to save processed data to 'places' table: {e}")
    else:
        logger.warning("No processed data to save.")
