#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
체크포인트 기능이 있는 Geocoding 스크립트

중간에 중단되어도 이어서 작업할 수 있도록 진행상태를 저장합니다.
"""

import os
import sys
import json
import pandas as pd
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import logging

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GeocodeCheckpoint:
    """체크포인트 기능이 있는 Geocoding 클래스"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('KAKAO_REST_API_KEY')
        if not self.api_key:
            raise ValueError("KAKAO_REST_API_KEY가 필요합니다. .env 파일을 확인하세요.")

        self.checkpoint_file = 'data/.checkpoint.json'
        self.output_file = 'data/.geocoded_partial.json'
        self.batch_size = 1000  # 1000개마다 저장

        self.stats = {
            'total': 0,
            'processed': 0,
            'geocoded': 0,
            'failed': 0,
            'cached': 0,
            'skipped': 0
        }

        self.geocoding_cache = {}
        self.results = []
        self.start_index = 0

    def load_checkpoint(self):
        """체크포인트 로드"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                    self.start_index = checkpoint.get('last_index', 0) + 1
                    self.stats = checkpoint.get('stats', self.stats)
                    logger.info(f"체크포인트 로드: {self.start_index}번부터 시작")
                    return True
            except Exception as e:
                logger.warning(f"체크포인트 로드 실패: {e}")
        return False

    def save_checkpoint(self, current_index):
        """체크포인트 저장"""
        os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)

        checkpoint = {
            'last_index': current_index,
            'stats': self.stats,
            'timestamp': datetime.now().isoformat()
        }

        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

    def load_partial_results(self):
        """중간 결과 로드"""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.results = data.get('stores', [])
                    logger.info(f"중간 결과 로드: {len(self.results)}개")
                    return True
            except Exception as e:
                logger.warning(f"중간 결과 로드 실패: {e}")
        return False

    def save_partial_results(self):
        """중간 결과 저장"""
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        data = {
            'version': '2.0.0',
            'lastUpdated': datetime.now().isoformat() + 'Z',
            'totalStores': len(self.results),
            'stores': self.results
        }

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def geocode_address(self, address):
        """
        주소를 좌표로 변환 (카카오 API)

        Args:
            address: 주소 문자열

        Returns:
            tuple: (lat, lng) 또는 (None, None)
        """
        # 캐시 확인
        if address in self.geocoding_cache:
            self.stats['cached'] += 1
            return self.geocoding_cache[address]

        max_retries = 3
        retry_delay = 2  # 초

        for attempt in range(max_retries):
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
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"API 제한 도달. {wait_time}초 대기...")
                    time.sleep(wait_time)
                    continue

                # 기타 에러
                if response.status_code >= 400:
                    logger.debug(f"Geocoding 실패 ({address}): HTTP {response.status_code}")
                    break

            except Exception as e:
                logger.debug(f"Geocoding 오류 ({address}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue

        self.stats['failed'] += 1
        self.geocoding_cache[address] = (None, None)
        return None, None

    def parse_types(self, row):
        """상품권 유형 파싱"""
        types = []
        if row.get('지류형 가맹 여부', 'N') == 'Y':
            types.append('paper')
        if row.get('디지털형 가맹 여부', 'N') == 'Y':
            types.append('card')
            types.append('mobile')
        if not types:
            types = ['card', 'paper', 'mobile']
        return types

    def categorize_business(self, item_str):
        """취급품목 기반 카테고리 분류"""
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

    def process_csv(self, csv_file):
        """
        CSV 파일 처리

        Args:
            csv_file: CSV 파일 경로
        """
        logger.info("="*60)
        logger.info("체크포인트 기반 Geocoding 시작")
        logger.info("="*60)

        # 체크포인트 로드
        has_checkpoint = self.load_checkpoint()
        if has_checkpoint:
            self.load_partial_results()

        # CSV 로드
        logger.info(f"CSV 파일 로드: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig')

        self.stats['total'] = len(df)
        logger.info(f"총 {self.stats['total']:,}개 레코드")

        if self.start_index > 0:
            logger.info(f"진행 중인 작업 계속: {self.start_index:,}번부터")
            logger.info(f"이미 처리됨: {len(self.results):,}개")

        # 처리
        start_time = time.time()
        last_save_time = time.time()

        for idx in range(self.start_index, len(df)):
            row = df.iloc[idx]

            # 진행상황 출력
            if (idx + 1) % 100 == 0:
                elapsed = time.time() - start_time
                processed = idx + 1 - self.start_index
                if processed > 0:
                    rate = processed / elapsed
                    remaining = (len(df) - idx - 1) / rate if rate > 0 else 0
                    logger.info(
                        f"처리 중: {idx + 1:,}/{len(df):,} ({(idx+1)/len(df)*100:.1f}%) | "
                        f"속도: {rate:.1f}개/s | 남은시간: {remaining/60:.1f}분 | "
                        f"성공: {self.stats['geocoded']:,} | 실패: {self.stats['failed']:,}"
                    )

            # 데이터 추출
            name = str(row.get('가맹점명', '')).strip()
            province = str(row.get('소재지', '')).strip()
            market = str(row.get('소속 시장명(또는 상점가)', '')).strip()

            # 주소 생성
            if market and market != 'nan':
                address = f"{market} {province}"
            else:
                address = province

            if not name or not address:
                self.stats['skipped'] += 1
                continue

            # Geocoding
            lat, lng = self.geocode_address(address)

            # API 제한 방지 (10 requests/sec)
            if (idx + 1) % 10 == 0:
                time.sleep(0.1)

            # 상품권 유형 및 카테고리
            types = self.parse_types(row)
            category, sub_category = self.categorize_business(row.get('취급품목'))

            # Store 객체 생성
            store = {
                'id': len(self.results) + 1,
                'name': name,
                'address': address,
                'types': types
            }

            # 좌표 추가
            if lat and lng:
                store['lat'] = lat
                store['lng'] = lng

            # 선택적 필드
            if market and market != 'nan':
                store['market'] = market
            if province and province != 'nan':
                store['province'] = province

            store['category'] = category
            store['subCategory'] = sub_category
            store['naverUrl'] = f"https://map.naver.com/v5/search/{name.replace(' ', '%20')}%20{address.replace(' ', '%20')}"

            self.results.append(store)
            self.stats['processed'] += 1

            # 배치 저장 (1000개마다 또는 5분마다)
            current_time = time.time()
            if (idx + 1) % self.batch_size == 0 or (current_time - last_save_time) > 300:
                logger.info(f"체크포인트 저장 중... ({len(self.results):,}개)")
                self.save_checkpoint(idx)
                self.save_partial_results()
                last_save_time = current_time

        # 최종 저장
        logger.info("최종 결과 저장 중...")
        self.save_checkpoint(len(df) - 1)
        self.save_partial_results()

        # 통계 출력
        elapsed = time.time() - start_time
        logger.info("="*60)
        logger.info("Geocoding 완료!")
        logger.info(f"소요 시간: {elapsed/60:.1f}분")
        logger.info(f"총 레코드: {self.stats['total']:,}개")
        logger.info(f"처리됨: {self.stats['processed']:,}개")
        logger.info(f"Geocoding 성공: {self.stats['geocoded']:,}개")
        logger.info(f"캐시 사용: {self.stats['cached']:,}개")
        logger.info(f"실패: {self.stats['failed']:,}개")
        logger.info(f"건너뜀: {self.stats['skipped']:,}개")
        if self.stats['processed'] > 0:
            success_rate = (self.stats['geocoded'] + self.stats['cached']) / self.stats['processed'] * 100
            logger.info(f"성공률: {success_rate:.1f}%")
        logger.info("="*60)


def main():
    """메인 함수"""

    csv_file = '소상공인시장진흥공단_전국 온누리상품권 가맹점 현황_20250731.csv'

    if not os.path.exists(csv_file):
        logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_file}")
        sys.exit(1)

    try:
        processor = GeocodeCheckpoint()
        processor.process_csv(csv_file)

        logger.info("")
        logger.info("중간 결과 파일:")
        logger.info("  - data/.geocoded_partial.json")
        logger.info("  - data/.checkpoint.json")
        logger.info("")
        logger.info("다음 단계:")
        logger.info("  python scripts/split_to_grid.py  # Geohash 그리드로 분할")

    except KeyboardInterrupt:
        logger.info("")
        logger.info("="*60)
        logger.info("작업 중단됨!")
        logger.info("다음 실행 시 체크포인트부터 이어서 진행됩니다.")
        logger.info("="*60)
        sys.exit(0)
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
