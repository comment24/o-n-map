#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
최종 JSON 파일 생성 스크립트

Geocoding된 데이터를 프론트엔드에서 사용할 JSON 형식으로 변환합니다.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from collections import Counter
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JSONGenerator:
    """JSON 파일 생성 클래스"""

    def __init__(self):
        self.metadata = {
            'lastUpdated': datetime.now().isoformat() + 'Z',
            'dataSource': '공공데이터포털 - 온누리상품권 가맹점',
            'totalStores': 0,
            'geocodingSuccess': 0,
            'geocodingRate': 0,
            'naverMatched': 0,
            'categories': {},
            'regions': {},
            'types': {'card': 0, 'paper': 0, 'mobile': 0}
        }

    def load_data(self, filepath='data/raw/geocoded_stores.csv'):
        """
        Geocoding된 데이터 로드

        Args:
            filepath: 파일 경로

        Returns:
            pd.DataFrame: 데이터
        """
        logger.info(f"데이터 로드: {filepath}")
        df = pd.read_csv(filepath, encoding='utf-8-sig')

        # types 컬럼 파싱 (문자열 → 리스트)
        if 'types' in df.columns:
            df['types'] = df['types'].apply(self._parse_types)

        return df

    def _parse_types(self, types_str):
        """
        상품권 유형 문자열을 리스트로 변환

        Args:
            types_str: 문자열 (예: "['card', 'paper']")

        Returns:
            list: 유형 리스트
        """
        if pd.isna(types_str):
            return ['card', 'paper', 'mobile']

        # 문자열이 이미 리스트 형태인 경우
        if isinstance(types_str, str):
            try:
                # eval 대신 안전한 파싱
                types_str = types_str.strip('[]').replace("'", "").replace('"', '')
                return [t.strip() for t in types_str.split(',') if t.strip()]
            except:
                return ['card', 'paper', 'mobile']

        return types_str

    def generate_naver_url(self, row):
        """
        네이버 지도 검색 URL 생성

        Args:
            row: DataFrame row

        Returns:
            str: 네이버 URL
        """
        name = row.get('name', '')
        address = row.get('address', '')
        query = f"{name} {address}"
        return f"https://map.naver.com/v5/search/{query.replace(' ', '%20')}"

    def convert_to_json_format(self, df):
        """
        DataFrame을 JSON 형식으로 변환

        Args:
            df: pandas DataFrame

        Returns:
            dict: JSON 데이터
        """
        logger.info("JSON 형식으로 변환 중...")

        # 좌표가 있는 데이터만 선택
        df_valid = df[df['lat'].notna() & df['lng'].notna()].copy()

        logger.info(f"유효한 데이터: {len(df_valid)}/{len(df)}개")

        # ID 추가
        df_valid['id'] = range(1, len(df_valid) + 1)

        # stores 배열 생성
        stores = []
        for _, row in df_valid.iterrows():
            store = {
                'id': int(row['id']),
                'name': str(row['name']),
                'address': str(row['address']),
                'lat': float(row['lat']),
                'lng': float(row['lng']),
                'types': row.get('types', ['card', 'paper', 'mobile'])
            }

            # 선택적 필드
            if pd.notna(row.get('roadAddress')):
                store['roadAddress'] = str(row['roadAddress'])
            if pd.notna(row.get('market')):
                store['market'] = str(row['market'])
            if pd.notna(row.get('category')):
                store['category'] = str(row['category'])
            if pd.notna(row.get('subCategory')):
                store['subCategory'] = str(row['subCategory'])
            if pd.notna(row.get('phone')):
                phone = str(row['phone']).strip()
                if phone and phone != 'nan':
                    store['phone'] = phone

            # 네이버 URL 생성
            store['naverUrl'] = self.generate_naver_url(row)

            stores.append(store)

        # 메타데이터 업데이트
        self._update_metadata(df_valid)

        # 최종 JSON 구조
        json_data = {
            'version': '1.0.0',
            'lastUpdated': self.metadata['lastUpdated'],
            'totalStores': len(stores),
            'stores': stores
        }

        return json_data

    def _update_metadata(self, df):
        """
        메타데이터 업데이트

        Args:
            df: pandas DataFrame
        """
        self.metadata['totalStores'] = len(df)
        self.metadata['geocodingSuccess'] = len(df)

        # 카테고리 통계
        if 'category' in df.columns:
            categories = df['category'].value_counts().to_dict()
            self.metadata['categories'] = {str(k): int(v) for k, v in categories.items()}

        # 지역 통계 (주소에서 시/도 추출)
        if 'address' in df.columns:
            regions = df['address'].apply(lambda x: str(x).split()[0] if pd.notna(x) else '기타')
            region_counts = regions.value_counts().to_dict()
            self.metadata['regions'] = {str(k): int(v) for k, v in region_counts.items()}

        # 상품권 유형 통계
        type_counter = Counter()
        for types in df['types']:
            if isinstance(types, list):
                type_counter.update(types)
        self.metadata['types'] = {
            'card': type_counter.get('card', 0),
            'paper': type_counter.get('paper', 0),
            'mobile': type_counter.get('mobile', 0)
        }

    def save_json(self, data, output_path='data/stores.json'):
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
        logger.info(f"파일 크기: {file_size / 1024:.1f} KB")

    def save_metadata(self, output_path='data/metadata.json'):
        """
        메타데이터 저장

        Args:
            output_path: 출력 파일 경로
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"메타데이터 저장 완료: {output_path}")


def main():
    """메인 함수"""

    # Geocoding된 데이터 로드
    input_file = 'data/raw/geocoded_stores.csv'
    if not os.path.exists(input_file):
        logger.error(f"{input_file}이 없습니다.")
        logger.info("먼저 python scripts/geocode.py를 실행해주세요.")
        sys.exit(1)

    generator = JSONGenerator()

    # 데이터 로드
    df = generator.load_data(input_file)

    # JSON 변환
    json_data = generator.convert_to_json_format(df)

    # 저장
    generator.save_json(json_data, 'data/stores.json')
    generator.save_metadata('data/metadata.json')

    # 통계 출력
    logger.info("=" * 60)
    logger.info("JSON 생성 완료!")
    logger.info(f"총 가맹점: {json_data['totalStores']}개")
    logger.info(f"업데이트: {json_data['lastUpdated']}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("파일 경로:")
    logger.info("  - data/stores.json (프론트엔드용)")
    logger.info("  - data/metadata.json (통계 정보)")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
