#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온누리상품권 가맹점 CSV 파일 처리 스크립트

다운로드한 CSV 파일을 읽어서 JSON 형식으로 변환하고 카카오 API로 좌표를 추가합니다.
"""

import os
import sys
import json
import pandas as pd
import requests
import time
from datetime import datetime
from collections import Counter
import logging
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CSVProcessor:
    """CSV 파일 처리 클래스"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('KAKAO_REST_API_KEY')
        self.geocoding_cache = {}
        self.stats = {
            'total': 0,
            'geocoded': 0,
            'failed': 0,
            'cached': 0
        }

    def load_csv(self, filepath):
        """
        CSV 파일 로드

        Args:
            filepath: CSV 파일 경로

        Returns:
            pd.DataFrame: 데이터프레임
        """
        logger.info(f"CSV 파일 로드: {filepath}")

        df = pd.read_csv(filepath, encoding='utf-8-sig')
        logger.info(f"총 {len(df)}개 레코드 로드")
        logger.info(f"컬럼: {list(df.columns)}")

        return df

    def parse_types(self, row):
        """
        상품권 유형 파싱

        Args:
            row: DataFrame row

        Returns:
            list: 상품권 유형 리스트
        """
        types = []

        # 지류형 (종이 상품권)
        if row.get('지류형 가맹 여부', 'N') == 'Y':
            types.append('paper')

        # 디지털형 (카드/모바일)
        if row.get('디지털형 가맹 여부', 'N') == 'Y':
            types.append('card')
            types.append('mobile')

        # 둘 다 없으면 기본값
        if not types:
            types = ['card', 'paper', 'mobile']

        return types

    def categorize_business(self, item_str):
        """
        취급품목을 기반으로 카테고리 분류

        Args:
            item_str: 취급품목 문자열

        Returns:
            tuple: (category, subCategory)
        """
        if pd.isna(item_str):
            return '기타', '기타'

        item = str(item_str).lower()

        # 음식점
        food_keywords = ['음식', '식당', '한식', '중식', '일식', '양식', '분식', '치킨', '피자',
                        '카페', '커피', '빵', '제과', '떡', '도너츠', '베이커리']
        if any(keyword in item for keyword in food_keywords):
            if '카페' in item or '커피' in item:
                return '음식점', '카페'
            elif '빵' in item or '제과' in item or '베이커리' in item:
                return '음식점', '제과점'
            return '음식점', '일반음식점'

        # 식료품
        grocery_keywords = ['마트', '슈퍼', '정육', '수산', '채소', '과일', '야채']
        if any(keyword in item for keyword in grocery_keywords):
            return '식료품', '슈퍼마켓'

        # 의류/패션
        fashion_keywords = ['의류', '옷', '신발', '가방', '패션', '양복', '한복']
        if any(keyword in item for keyword in fashion_keywords):
            return '의류/패션', '의류'

        # 미용
        beauty_keywords = ['미용', '헤어', '네일', '피부', '화장품']
        if any(keyword in item for keyword in beauty_keywords):
            return '미용', '미용실'

        # 서비스
        service_keywords = ['세탁', '수선', '열쇠', '복사', '인쇄', '사진']
        if any(keyword in item for keyword in service_keywords):
            return '서비스', '생활서비스'

        # 주유소
        if '주유' in item or '충전' in item:
            return '주유소', '주유소'

        return '기타', item[:20] if len(item) > 20 else item

    def geocode_address(self, address):
        """
        주소를 좌표로 변환 (카카오 API)

        Args:
            address: 주소 문자열

        Returns:
            tuple: (lat, lng) 또는 (None, None)
        """
        if not self.api_key:
            logger.warning("카카오 API 키가 없습니다. Geocoding을 건너뜁니다.")
            return None, None

        # 캐시 확인
        if address in self.geocoding_cache:
            self.stats['cached'] += 1
            return self.geocoding_cache[address]

        try:
            url = 'https://dapi.kakao.com/v2/local/search/address.json'
            headers = {'Authorization': f'KakaoAK {self.api_key}'}
            params = {'query': address}

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('documents'):
                    doc = data['documents'][0]
                    lat = float(doc['y'])
                    lng = float(doc['x'])

                    # 캐시 저장
                    self.geocoding_cache[address] = (lat, lng)
                    self.stats['geocoded'] += 1

                    return lat, lng

            # API 제한 대응 (429 에러)
            if response.status_code == 429:
                logger.warning("API 제한 도달. 잠시 대기...")
                time.sleep(1)

        except Exception as e:
            logger.debug(f"Geocoding 실패 ({address}): {e}")

        self.stats['failed'] += 1
        return None, None

    def process_dataframe(self, df, limit=None, enable_geocoding=True):
        """
        DataFrame을 JSON 형식으로 처리

        Args:
            df: pandas DataFrame
            limit: 처리할 최대 행 수 (테스트용)
            enable_geocoding: Geocoding 활성화 여부

        Returns:
            dict: JSON 데이터
        """
        logger.info("데이터 처리 시작...")

        if limit:
            df = df.head(limit)
            logger.info(f"제한: 첫 {limit}개만 처리")

        stores = []
        self.stats['total'] = len(df)

        for idx, row in df.iterrows():
            # 진행상황 출력 (1000개마다)
            if (idx + 1) % 1000 == 0:
                logger.info(f"처리 중: {idx + 1}/{len(df)} ({(idx+1)/len(df)*100:.1f}%)")

            # 기본 정보
            name = str(row.get('가맹점명', '')).strip()
            province = str(row.get('소재지', '')).strip()
            market = str(row.get('소속 시장명(또는 상점가)', '')).strip()

            # 주소 생성: 시장명 + 시/도
            # 예: "권율 골목형상점가 경기" or "일곡동 광주"
            if market and market != 'nan':
                address = f"{market} {province}"
            else:
                address = province

            if not name or not address:
                continue

            # 상품권 유형
            types = self.parse_types(row)

            # 카테고리 분류
            category, sub_category = self.categorize_business(row.get('취급품목'))

            # 좌표 변환
            lat, lng = None, None
            if enable_geocoding:
                lat, lng = self.geocode_address(address)

                # API 제한 방지 (10 requests/sec)
                if self.api_key and (idx + 1) % 10 == 0:
                    time.sleep(0.1)

            store = {
                'id': idx + 1,
                'name': name,
                'address': address,
                'types': types
            }

            # 좌표가 있으면 추가
            if lat and lng:
                store['lat'] = lat
                store['lng'] = lng

            # 선택적 필드
            if market and market != 'nan':
                store['market'] = market

            # province 정보 추가
            if province and province != 'nan':
                store['province'] = province

            store['category'] = category
            store['subCategory'] = sub_category

            # 네이버 URL 생성
            store['naverUrl'] = f"https://map.naver.com/v5/search/{name.replace(' ', '%20')}%20{address.replace(' ', '%20')}"

            stores.append(store)

        # 최종 JSON 구조
        json_data = {
            'version': '2.0.0',
            'lastUpdated': datetime.now().isoformat() + 'Z',
            'dataSource': '공공데이터포털 - 온누리상품권 가맹점 (2025-07-31)',
            'totalStores': len(stores),
            'stores': stores
        }

        return json_data

    def save_json(self, data, output_path):
        """
        JSON 파일 저장

        Args:
            data: JSON 데이터
            output_path: 출력 파일 경로
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON 저장 완료: {output_path}")

        # 파일 크기 확인
        file_size = os.path.getsize(output_path)
        logger.info(f"파일 크기: {file_size / (1024*1024):.2f} MB")

    def print_stats(self):
        """통계 출력"""
        logger.info("=" * 60)
        logger.info("처리 통계:")
        logger.info(f"  총 레코드: {self.stats['total']:,}개")
        logger.info(f"  Geocoding 성공: {self.stats['geocoded']:,}개")
        logger.info(f"  캐시 사용: {self.stats['cached']:,}개")
        logger.info(f"  실패: {self.stats['failed']:,}개")
        if self.stats['total'] > 0:
            success_rate = (self.stats['geocoded'] + self.stats['cached']) / self.stats['total'] * 100
            logger.info(f"  성공률: {success_rate:.1f}%")
        logger.info("=" * 60)


def main():
    """메인 함수"""

    # CSV 파일 경로
    csv_file = '소상공인시장진흥공단_전국 온누리상품권 가맹점 현황_20250731.csv'

    if not os.path.exists(csv_file):
        logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_file}")
        sys.exit(1)

    # 처리기 생성
    processor = CSVProcessor()

    # CSV 로드
    df = processor.load_csv(csv_file)

    # 테스트 모드 확인
    test_mode = '--test' in sys.argv
    limit = 100 if test_mode else None

    if test_mode:
        logger.info("테스트 모드: 처음 100개만 처리합니다.")

    # Geocoding 활성화 여부
    enable_geocoding = '--no-geocoding' not in sys.argv

    if not enable_geocoding:
        logger.info("Geocoding 비활성화 모드")

    # 데이터 처리
    json_data = processor.process_dataframe(df, limit=limit, enable_geocoding=enable_geocoding)

    # JSON 저장
    processor.save_json(json_data, 'data/stores.json')

    # docs 폴더에도 복사 (프론트엔드용)
    processor.save_json(json_data, 'docs/data/stores.json')

    # 통계 출력
    processor.print_stats()

    logger.info("")
    logger.info("완료! 생성된 파일:")
    logger.info("  - data/stores.json")
    logger.info("  - docs/data/stores.json")
    logger.info("")
    logger.info("사용법:")
    logger.info("  python scripts/process_csv.py              # 전체 처리")
    logger.info("  python scripts/process_csv.py --test       # 테스트 (100개만)")
    logger.info("  python scripts/process_csv.py --no-geocoding  # Geocoding 없이")


if __name__ == '__main__':
    main()
