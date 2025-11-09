#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
서울 샘플용 JSON 파일 생성 스크립트
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


def parse_types(row):
    """상품권 유형 파싱"""
    types = []

    # 지류형
    if pd.notna(row.get('지류형 가맹 여부')) and str(row['지류형 가맹 여부']).upper() == 'Y':
        types.append('paper')

    # 디지털형 (충전식카드 + 모바일)
    if pd.notna(row.get('디지털형 가맹 여부')) and str(row['디지털형 가맹 여부']).upper() == 'Y':
        types.append('card')
        types.append('mobile')

    # 기본값
    if not types:
        types = ['card', 'paper', 'mobile']

    return types


def categorize_business(category_str):
    """업종 분류"""
    if pd.isna(category_str):
        return '기타', None

    category_str = str(category_str).lower()

    # 음식점
    if any(word in category_str for word in ['음식', '식당', '카페', '커피', '베이커리', '한식', '중식', '일식', '양식', '치킨', '피자']):
        if '카페' in category_str or '커피' in category_str:
            return '음식점', '카페'
        elif '한식' in category_str:
            return '음식점', '한식'
        elif '중식' in category_str:
            return '음식점', '중식'
        elif '일식' in category_str:
            return '음식점', '일식'
        elif '양식' in category_str:
            return '음식점', '양식'
        return '음식점', None

    # 식료품
    if any(word in category_str for word in ['마트', '슈퍼', '편의점', '정육', '청과', '야채', '과일', '식료품']):
        if '편의점' in category_str:
            return '식료품', '편의점'
        elif '마트' in category_str or '슈퍼' in category_str:
            return '식료품', '슈퍼마켓'
        return '식료품', None

    # 주유소
    if any(word in category_str for word in ['주유소', 'gs', 's-oil', 'sk']):
        return '주유소', None

    return '기타', None


def main():
    """메인 함수"""

    # Geocoding된 데이터 로드
    input_file = 'data/raw/seoul_geocoded_100.csv'
    if not os.path.exists(input_file):
        logger.error(f"{input_file}이 없습니다.")
        sys.exit(1)

    logger.info(f"데이터 로드: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    # 좌표가 있는 데이터만 선택
    df_valid = df[df['lat'].notna() & df['lng'].notna()].copy()
    logger.info(f"유효한 데이터: {len(df_valid)}/{len(df)}개")

    # stores 배열 생성
    stores = []
    category_counts = Counter()

    for idx, row in df_valid.iterrows():
        # 업종 분류
        category, subCategory = categorize_business(row.get('category'))
        category_counts[category] += 1

        # 상품권 유형
        types = parse_types(row)

        store = {
            'id': len(stores) + 1,
            'name': str(row['가맹점명']),
            'address': str(row['address']) if pd.notna(row.get('address')) else '',
            'lat': float(row['lat']),
            'lng': float(row['lng']),
            'category': category,
            'types': types
        }

        # 선택적 필드
        if pd.notna(row.get('roadAddress')) and str(row['roadAddress']):
            store['roadAddress'] = str(row['roadAddress'])

        if pd.notna(row.get('소속 시장명(또는 상점가)')) and str(row['소속 시장명(또는 상점가)']):
            store['market'] = str(row['소속 시장명(또는 상점가)'])

        if subCategory:
            store['subCategory'] = subCategory

        if pd.notna(row.get('취급품목')) and str(row['취급품목']):
            store['products'] = str(row['취급품목'])

        # 네이버 URL 생성
        search_query = f"{row['가맹점명']} {row['address']}"
        store['naverUrl'] = f"https://map.naver.com/v5/search/{search_query.replace(' ', '%20')}"

        stores.append(store)

    # 최종 JSON 구조
    json_data = {
        'version': '1.0.0',
        'lastUpdated': datetime.now().isoformat() + 'Z',
        'totalStores': len(stores),
        'region': '서울 샘플',
        'stores': stores
    }

    # 저장
    output_file = 'data/stores.json'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    logger.info(f"JSON 저장 완료: {output_file}")

    # 파일 크기 확인
    file_size = os.path.getsize(output_file)
    logger.info(f"파일 크기: {file_size / 1024:.1f} KB")

    # 메타데이터
    metadata = {
        'lastUpdated': datetime.now().isoformat() + 'Z',
        'dataSource': '공공데이터포털 - 온누리상품권 가맹점 (서울 샘플 100개)',
        'totalStores': len(stores),
        'geocodingSuccess': len(df_valid),
        'geocodingRate': len(df_valid) / len(df) * 100,
        'categories': dict(category_counts),
        'region': '서울'
    }

    metadata_file = 'data/metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    logger.info(f"메타데이터 저장 완료: {metadata_file}")

    # 통계 출력
    logger.info("=" * 60)
    logger.info("JSON 생성 완료!")
    logger.info(f"총 가맹점: {len(stores)}개")
    logger.info(f"업종별 분포: {dict(category_counts)}")
    logger.info(f"업데이트: {json_data['lastUpdated']}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("파일 경로:")
    logger.info(f"  - {output_file} (프론트엔드용)")
    logger.info(f"  - {metadata_file} (통계 정보)")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
