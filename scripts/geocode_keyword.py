#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 검색을 통한 Geocoding 스크립트

가맹점명 + 시장명을 조합하여 카카오 로컬 검색 API로 좌표를 찾습니다.
"""

import os
import sys
import time
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()


class KakaoKeywordGeocoder:
    """카카오 로컬 검색 API 클래스"""

    API_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

    def __init__(self, api_key=None):
        """
        Args:
            api_key: 카카오 REST API 키
        """
        self.api_key = api_key or os.getenv('KAKAO_REST_API_KEY')
        if not self.api_key:
            raise ValueError("KAKAO_REST_API_KEY가 설정되지 않았습니다.")

        self.headers = {
            'Authorization': f'KakaoAK {self.api_key}'
        }

        # API 호출 통계
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'cached': 0
        }

        # 캐시 (이미 검색한 키워드 저장)
        self.cache = {}
        self.load_cache()

    def load_cache(self, cache_file='data/raw/geocode_keyword_cache.json'):
        """캐시 파일 로드"""
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"캐시 로드 완료: {len(self.cache)}개")
            except Exception as e:
                logger.warning(f"캐시 로드 실패: {e}")
                self.cache = {}

    def save_cache(self, cache_file='data/raw/geocode_keyword_cache.json'):
        """캐시 파일 저장"""
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
        logger.info(f"캐시 저장 완료: {len(self.cache)}개")

    def search_place(self, query, region=None):
        """
        키워드로 장소 검색

        Args:
            query: 검색 키워드 (가맹점명 + 시장명)
            region: 지역 필터 (예: "서울")

        Returns:
            dict: {'lat': 위도, 'lng': 경도, 'address': 주소, 'place_name': 장소명} 또는 None
        """
        self.stats['total'] += 1

        # 캐시 확인
        cache_key = f"{query}_{region}" if region else query
        if cache_key in self.cache:
            self.stats['cached'] += 1
            return self.cache[cache_key]

        # API 호출
        try:
            params = {'query': query}
            if region:
                params['region'] = region

            response = requests.get(
                self.API_URL,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if data['meta']['total_count'] > 0:
                # 첫 번째 결과 사용
                result = data['documents'][0]

                coord = {
                    'lat': float(result['y']),
                    'lng': float(result['x']),
                    'address': result['address_name'],
                    'roadAddress': result.get('road_address_name', ''),
                    'place_name': result['place_name'],
                    'category': result['category_name']
                }

                # 캐시에 저장
                self.cache[cache_key] = coord
                self.stats['success'] += 1
                return coord

            self.stats['failed'] += 1
            return None

        except Exception as e:
            logger.debug(f"검색 실패 ({query}): {e}")
            self.stats['failed'] += 1
            return None

        finally:
            # Rate limiting (카카오 API 제한 준수)
            time.sleep(0.1)  # 초당 10건

    def geocode_dataframe(self, df):
        """
        DataFrame의 모든 가맹점 검색

        Args:
            df: pandas DataFrame (가맹점명, 소속 시장명, 소재지 필요)

        Returns:
            pd.DataFrame: 좌표가 추가된 DataFrame
        """
        logger.info(f"{len(df)}개 가맹점 검색 시작...")

        # 좌표 컬럼 추가
        df['lat'] = None
        df['lng'] = None
        df['address'] = None
        df['roadAddress'] = None
        df['place_name'] = None
        df['category'] = None

        # 진행률 표시
        total = len(df)
        for idx, row in df.iterrows():
            # 검색 쿼리 생성
            name = str(row['가맹점명']) if pd.notna(row['가맹점명']) else ''
            market = str(row['소속 시장명(또는 상점가)']) if pd.notna(row['소속 시장명(또는 상점가)']) else ''
            region = str(row['소재지']) if pd.notna(row['소재지']) else ''

            if not name:
                continue

            # 여러 검색 전략 시도
            queries = [
                f"{name} {market} {region}",  # 전체 조합
                f"{name} {market}",            # 가맹점 + 시장명
                f"{name} {region}",            # 가맹점 + 지역
            ]

            coord = None
            for query in queries:
                if not query.strip():
                    continue

                coord = self.search_place(query.strip(), region)
                if coord:
                    break

            if coord:
                df.at[idx, 'lat'] = coord['lat']
                df.at[idx, 'lng'] = coord['lng']
                df.at[idx, 'address'] = coord['address']
                df.at[idx, 'roadAddress'] = coord['roadAddress']
                df.at[idx, 'place_name'] = coord['place_name']
                df.at[idx, 'category'] = coord['category']

            # 진행률 출력
            if (idx + 1) % 10 == 0 or (idx + 1) == total:
                success_rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
                logger.info(
                    f"진행: {idx + 1}/{total} "
                    f"(성공: {self.stats['success']}, "
                    f"실패: {self.stats['failed']}, "
                    f"캐시: {self.stats['cached']}, "
                    f"성공률: {success_rate:.1f}%)"
                )

        # 캐시 저장
        self.save_cache()

        # 통계 출력
        logger.info("=" * 60)
        logger.info("Geocoding 완료!")
        logger.info(f"전체: {self.stats['total']}개 검색 시도")
        logger.info(f"성공: {self.stats['success']}개")
        logger.info(f"실패: {self.stats['failed']}개")
        logger.info(f"캐시: {self.stats['cached']}개")
        success_rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        logger.info(f"성공률: {success_rate:.1f}%")
        logger.info("=" * 60)

        return df


def main():
    """메인 함수"""

    # 서울 샘플 데이터 로드
    input_file = 'data/raw/seoul_sample_100.csv'
    if not os.path.exists(input_file):
        logger.error(f"{input_file}이 없습니다.")
        sys.exit(1)

    logger.info(f"데이터 로드: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    # Geocoder 초기화
    try:
        geocoder = KakaoKeywordGeocoder()
    except ValueError as e:
        logger.error(str(e))
        logger.info("환경 변수를 설정해주세요:")
        logger.info("  export KAKAO_REST_API_KEY=your_rest_api_key")
        logger.info("또는 .env 파일을 생성해주세요.")
        sys.exit(1)

    # Geocoding 실행
    df = geocoder.geocode_dataframe(df)

    # 결과 저장
    output_file = 'data/raw/seoul_geocoded_100.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"결과 저장: {output_file}")

    # 성공/실패 통계
    success_df = df[df['lat'].notna()]
    failed_df = df[df['lat'].isna()]

    logger.info(f"\n최종 결과:")
    logger.info(f"  성공: {len(success_df)}개 ({len(success_df)/len(df)*100:.1f}%)")
    logger.info(f"  실패: {len(failed_df)}개 ({len(failed_df)/len(df)*100:.1f}%)")

    if len(failed_df) > 0:
        logger.warning(f"\nGeocoding 실패: {len(failed_df)}개")
        failed_file = 'data/raw/seoul_geocode_failed.csv'
        failed_df[['가맹점명', '소속 시장명(또는 상점가)', '소재지', '취급품목']].to_csv(
            failed_file, index=False, encoding='utf-8-sig'
        )
        logger.info(f"실패 목록 저장: {failed_file}")

    logger.info("\n" + "=" * 60)
    logger.info("다음 단계: python scripts/generate_json.py")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
