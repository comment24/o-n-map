#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Geohash 기반 그리드로 데이터 분할

좌표가 있는 데이터를 Geohash로 그룹화하여 작은 파일로 분할합니다.
"""

import os
import sys
import json
import logging
from collections import defaultdict
from datetime import datetime

try:
    import pygeohash as geohash
except ImportError:
    try:
        import geohash
    except ImportError:
        print("geohash 패키지가 필요합니다: pip install pygeohash")
        sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GeohashGridSplitter:
    """Geohash 기반 그리드 분할 클래스"""

    def __init__(self, precision=5):
        """
        Args:
            precision: Geohash 정밀도
                5: ~4.9km × 4.9km (추천)
                6: ~1.2km × 609m (더 세밀)
        """
        self.precision = precision
        self.grid_data = defaultdict(list)
        self.stats = {
            'total': 0,
            'with_coords': 0,
            'without_coords': 0,
            'grids': 0
        }

    def load_data(self, filepath):
        """
        JSON 데이터 로드

        Args:
            filepath: JSON 파일 경로

        Returns:
            dict: JSON 데이터
        """
        logger.info(f"데이터 로드: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"총 {data.get('totalStores', 0):,}개 가맹점")
        return data

    def split_to_grid(self, stores):
        """
        가맹점을 Geohash 그리드로 분할

        Args:
            stores: 가맹점 리스트
        """
        logger.info(f"Geohash 그리드 분할 시작 (정밀도: {self.precision})")

        self.stats['total'] = len(stores)

        for store in stores:
            lat = store.get('lat')
            lng = store.get('lng')

            if lat and lng:
                # Geohash 계산
                gh = geohash.encode(lat, lng, precision=self.precision)
                self.grid_data[gh].append(store)
                self.stats['with_coords'] += 1
            else:
                # 좌표 없는 데이터는 'unknown' 그리드에
                self.grid_data['unknown'].append(store)
                self.stats['without_coords'] += 1

        self.stats['grids'] = len(self.grid_data)

        logger.info(f"그리드 분할 완료:")
        logger.info(f"  - 좌표 있음: {self.stats['with_coords']:,}개")
        logger.info(f"  - 좌표 없음: {self.stats['without_coords']:,}개")
        logger.info(f"  - 총 그리드: {self.stats['grids']:,}개")

    def create_index(self):
        """
        인덱스 파일 생성

        Returns:
            dict: 인덱스 데이터
        """
        logger.info("인덱스 생성 중...")

        grids = []
        for gh, stores in self.grid_data.items():
            if gh == 'unknown':
                grids.append({
                    'geohash': gh,
                    'count': len(stores),
                    'bounds': None
                })
            else:
                # Geohash 경계 계산
                lat, lng = geohash.decode(gh)
                lat_err, lng_err = geohash.decode_exactly(gh)[2:4]

                grids.append({
                    'geohash': gh,
                    'count': len(stores),
                    'center': {'lat': lat, 'lng': lng},
                    'bounds': {
                        'north': lat + lat_err,
                        'south': lat - lat_err,
                        'east': lng + lng_err,
                        'west': lng - lng_err
                    }
                })

        # 카운트 순으로 정렬 (큰 그리드가 먼저)
        grids.sort(key=lambda x: x['count'], reverse=True)

        index_data = {
            'version': '2.0.0',
            'lastUpdated': datetime.now().isoformat() + 'Z',
            'precision': self.precision,
            'totalStores': self.stats['total'],
            'totalGrids': self.stats['grids'],
            'grids': grids,
            'stats': {
                'withCoords': self.stats['with_coords'],
                'withoutCoords': self.stats['without_coords']
            }
        }

        logger.info(f"인덱스 생성 완료: {len(grids)}개 그리드")
        return index_data

    def save_grid_files(self, output_dir='docs/data/grid'):
        """
        그리드 파일 저장

        Args:
            output_dir: 출력 디렉토리
        """
        logger.info(f"그리드 파일 저장 중: {output_dir}")

        os.makedirs(output_dir, exist_ok=True)

        total_size = 0

        for gh, stores in self.grid_data.items():
            grid_data = {
                'geohash': gh,
                'count': len(stores),
                'stores': stores
            }

            output_path = os.path.join(output_dir, f'{gh}.json')

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(grid_data, f, ensure_ascii=False, indent=2)

            file_size = os.path.getsize(output_path)
            total_size += file_size

            if len(stores) > 100:  # 큰 파일만 로그
                logger.info(f"  - {gh}.json: {len(stores):,}개, {file_size/1024:.1f} KB")

        logger.info(f"총 파일 크기: {total_size/(1024*1024):.2f} MB")

    def save_index(self, index_data, output_path='docs/data/grid_index.json'):
        """
        인덱스 파일 저장

        Args:
            index_data: 인덱스 데이터
            output_path: 출력 파일 경로
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        file_size = os.path.getsize(output_path)
        logger.info(f"인덱스 저장 완료: {output_path} ({file_size/1024:.1f} KB)")


def main():
    """메인 함수"""

    # 입력 파일
    input_file = 'data/.geocoded_partial.json'

    if not os.path.exists(input_file):
        logger.error(f"Geocoding 결과 파일을 찾을 수 없습니다: {input_file}")
        logger.info("먼저 python scripts/geocode_with_checkpoint.py를 실행해주세요.")
        sys.exit(1)

    # Geohash 정밀도 설정
    precision = 5  # ~4.9km × 4.9km

    if '--precision' in sys.argv:
        idx = sys.argv.index('--precision')
        if idx + 1 < len(sys.argv):
            try:
                precision = int(sys.argv[idx + 1])
                if precision < 1 or precision > 12:
                    logger.warning("정밀도는 1-12 사이여야 합니다. 기본값 5 사용")
                    precision = 5
            except ValueError:
                logger.warning("정밀도는 정수여야 합니다. 기본값 5 사용")

    logger.info("="*60)
    logger.info(f"Geohash 그리드 분할 (정밀도: {precision})")
    logger.info("="*60)

    splitter = GeohashGridSplitter(precision=precision)

    # 데이터 로드
    data = splitter.load_data(input_file)
    stores = data.get('stores', [])

    # 그리드 분할
    splitter.split_to_grid(stores)

    # 인덱스 생성
    index_data = splitter.create_index()

    # 파일 저장
    splitter.save_grid_files('docs/data/grid')
    splitter.save_index(index_data, 'docs/data/grid_index.json')

    # 백업용 전체 데이터도 저장
    logger.info("전체 데이터 백업 저장 중...")
    with open('data/stores_with_coords.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open('docs/data/stores_with_coords.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("="*60)
    logger.info("완료!")
    logger.info("")
    logger.info("생성된 파일:")
    logger.info("  - docs/data/grid_index.json (인덱스)")
    logger.info(f"  - docs/data/grid/*.json ({splitter.stats['grids']}개 그리드 파일)")
    logger.info("  - docs/data/stores_with_coords.json (백업)")
    logger.info("="*60)


if __name__ == '__main__':
    main()
