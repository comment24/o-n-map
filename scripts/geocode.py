#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
주소를 좌표로 변환하는 Geocoding 스크립트

카카오 Geocoding API를 사용하여 주소를 위도/경도로 변환합니다.
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


class KakaoGeocoder:
    """카카오 Geocoding API 클래스"""

    API_URL = "https://dapi.kakao.com/v2/local/search/address.json"

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

        # 캐시 (이미 변환한 주소 저장)
        self.cache = {}
        self.load_cache()

    def load_cache(self, cache_file='data/raw/geocode_cache.json'):
        """
        캐시 파일 로드

        Args:
            cache_file: 캐시 파일 경로
        """
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"캐시 로드 완료: {len(self.cache)}개")
            except Exception as e:
                logger.warning(f"캐시 로드 실패: {e}")
                self.cache = {}

    def save_cache(self, cache_file='data/raw/geocode_cache.json'):
        """
        캐시 파일 저장

        Args:
            cache_file: 캐시 파일 경로
        """
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
        logger.info(f"캐시 저장 완료: {len(self.cache)}개")

    def geocode(self, address):
        """
        주소를 좌표로 변환

        Args:
            address: 주소 문자열

        Returns:
            dict: {'lat': 위도, 'lng': 경도, 'address': 정제된 주소} 또는 None
        """
        self.stats['total'] += 1

        # 캐시 확인
        if address in self.cache:
            self.stats['cached'] += 1
            return self.cache[address]

        # API 호출
        try:
            params = {'query': address}
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

                if 'road_address' in result and result['road_address']:
                    # 도로명 주소 우선
                    coord = {
                        'lat': float(result['road_address']['y']),
                        'lng': float(result['road_address']['x']),
                        'roadAddress': result['road_address']['address_name']
                    }
                elif 'address' in result and result['address']:
                    # 지번 주소
                    coord = {
                        'lat': float(result['address']['y']),
                        'lng': float(result['address']['x']),
                        'address': result['address']['address_name']
                    }
                else:
                    coord = None

                if coord:
                    # 캐시에 저장
                    self.cache[address] = coord
                    self.stats['success'] += 1
                    return coord

            self.stats['failed'] += 1
            return None

        except Exception as e:
            logger.error(f"Geocoding 에러 ({address}): {e}")
            self.stats['failed'] += 1
            return None

        finally:
            # Rate limiting (카카오 API 제한 준수)
            time.sleep(0.1)  # 초당 10건

    def geocode_dataframe(self, df, address_column='address'):
        """
        DataFrame의 모든 주소를 변환

        Args:
            df: pandas DataFrame
            address_column: 주소 컬럼명

        Returns:
            pd.DataFrame: 좌표가 추가된 DataFrame
        """
        logger.info(f"{len(df)}개 주소 Geocoding 시작...")

        # 좌표 컬럼 추가
        df['lat'] = None
        df['lng'] = None
        df['roadAddress'] = None

        # 진행률 표시
        total = len(df)
        for idx, row in df.iterrows():
            address = row[address_column]

            if pd.isna(address):
                continue

            # Geocoding
            coord = self.geocode(address)

            if coord:
                df.at[idx, 'lat'] = coord['lat']
                df.at[idx, 'lng'] = coord['lng']
                if 'roadAddress' in coord:
                    df.at[idx, 'roadAddress'] = coord['roadAddress']

            # 진행률 출력
            if (idx + 1) % 100 == 0 or (idx + 1) == total:
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
        logger.info(f"전체: {self.stats['total']}개")
        logger.info(f"성공: {self.stats['success']}개")
        logger.info(f"실패: {self.stats['failed']}개")
        logger.info(f"캐시: {self.stats['cached']}개")
        success_rate = (self.stats['success'] / self.stats['total'] * 100) if self.stats['total'] > 0 else 0
        logger.info(f"성공률: {success_rate:.1f}%")
        logger.info("=" * 60)

        return df


def main():
    """메인 함수"""

    # 정제된 데이터 로드
    input_file = 'data/raw/cleaned_stores.csv'
    if not os.path.exists(input_file):
        logger.error(f"{input_file}이 없습니다.")
        logger.info("먼저 python scripts/fetch_data.py를 실행해주세요.")
        sys.exit(1)

    logger.info(f"데이터 로드: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    # Geocoder 초기화
    try:
        geocoder = KakaoGeocoder()
    except ValueError as e:
        logger.error(str(e))
        logger.info("환경 변수를 설정해주세요:")
        logger.info("  export KAKAO_REST_API_KEY=your_rest_api_key")
        logger.info("또는 .env 파일을 생성해주세요.")
        sys.exit(1)

    # Geocoding 실행
    df = geocoder.geocode_dataframe(df, address_column='address')

    # 결과 저장
    output_file = 'data/raw/geocoded_stores.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"결과 저장: {output_file}")

    # 실패한 항목 확인
    failed_df = df[df['lat'].isna()]
    if len(failed_df) > 0:
        logger.warning(f"Geocoding 실패: {len(failed_df)}개")
        failed_file = 'data/raw/geocode_failed.csv'
        failed_df.to_csv(failed_file, index=False, encoding='utf-8-sig')
        logger.info(f"실패 목록 저장: {failed_file}")

    logger.info("=" * 60)
    logger.info("다음 단계: python scripts/generate_json.py")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
