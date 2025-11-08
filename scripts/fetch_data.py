#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
온누리 상품권 가맹점 데이터 수집 스크립트

공공데이터포털에서 온누리 상품권 가맹점 데이터를 다운로드합니다.
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OnnuriDataFetcher:
    """온누리 상품권 가맹점 데이터 수집 클래스"""

    # 공공데이터포털 파일 다운로드 URL (최신 파일)
    # 실제 URL은 data.go.kr에서 확인 필요
    DATA_URL = "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=FILE_000000002951466&fileDetailSn=1"

    def __init__(self, output_dir='data/raw'):
        """
        Args:
            output_dir: 다운로드한 파일을 저장할 디렉토리
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def download_data(self):
        """
        공공데이터포털에서 데이터 파일 다운로드

        Returns:
            str: 다운로드한 파일 경로
        """
        logger.info("온누리 상품권 가맹점 데이터 다운로드 시작...")

        # 수동 다운로드 안내
        logger.warning("=" * 60)
        logger.warning("자동 다운로드가 제한될 수 있습니다.")
        logger.warning("다음 단계를 수행해주세요:")
        logger.warning("")
        logger.warning("1. https://www.data.go.kr/data/3060079/fileData.do 접속")
        logger.warning("2. '파일 데이터' 탭에서 최신 파일 다운로드")
        logger.warning("3. 다운로드한 파일을 data/raw/ 폴더로 이동")
        logger.warning("4. 파일명을 확인하고 load_data() 함수에서 경로 수정")
        logger.warning("=" * 60)

        # 자동 다운로드 시도 (작동하지 않을 수 있음)
        try:
            response = requests.get(self.DATA_URL, timeout=30)
            response.raise_for_status()

            # 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f'onnuri_stores_{timestamp}.xlsx'
            filepath = os.path.join(self.output_dir, filename)

            # 파일 저장
            with open(filepath, 'wb') as f:
                f.write(response.content)

            logger.info(f"다운로드 완료: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"자동 다운로드 실패: {e}")
            logger.info("수동으로 다운로드해주세요.")
            return None

    def load_data(self, filepath=None):
        """
        다운로드한 파일을 pandas DataFrame으로 로드

        Args:
            filepath: 파일 경로 (None이면 raw 폴더에서 최신 파일 찾기)

        Returns:
            pd.DataFrame: 가맹점 데이터
        """
        if filepath is None:
            # raw 폴더에서 Excel 파일 찾기
            files = [f for f in os.listdir(self.output_dir) if f.endswith(('.xlsx', '.xls', '.csv'))]
            if not files:
                raise FileNotFoundError(f"{self.output_dir}에 데이터 파일이 없습니다.")

            # 가장 최신 파일 선택
            files.sort(reverse=True)
            filepath = os.path.join(self.output_dir, files[0])

        logger.info(f"데이터 로드 중: {filepath}")

        # 파일 형식에 따라 로드
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        else:
            df = pd.read_excel(filepath, engine='openpyxl')

        logger.info(f"총 {len(df)}개 가맹점 로드 완료")
        logger.info(f"컬럼: {list(df.columns)}")

        return df

    def clean_data(self, df):
        """
        데이터 정제

        Args:
            df: 원본 DataFrame

        Returns:
            pd.DataFrame: 정제된 DataFrame
        """
        logger.info("데이터 정제 시작...")

        original_count = len(df)

        # 컬럼명 매핑 (실제 데이터 구조에 맞게 수정 필요)
        column_mapping = {
            '가맹점명': 'name',
            '소재지도로명주소': 'roadAddress',
            '소재지지번주소': 'address',
            '시장명': 'market',
            '업종': 'category',
            '취급품목': 'subCategory',
            '전화번호': 'phone'
        }

        # 존재하는 컬럼만 매핑
        actual_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=actual_mapping)

        # 필수 컬럼 확인
        required_columns = ['name', 'address']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"필수 컬럼 누락: {missing_columns}")
            logger.info(f"실제 컬럼: {list(df.columns)}")
            # 수동으로 컬럼 확인 필요

        # 중복 제거
        df = df.drop_duplicates(subset=['name', 'address'])
        logger.info(f"중복 제거: {original_count - len(df)}개")

        # 빈 값 제거
        df = df.dropna(subset=['name', 'address'])
        logger.info(f"빈 값 제거 후: {len(df)}개")

        # 상품권 유형 파싱 (실제 데이터 구조에 맞게 수정 필요)
        # 예: "충전식O, 지류O, 모바일X" 형식이라고 가정
        if '상품권종류' in df.columns:
            df['types'] = df['상품권종류'].apply(self._parse_types)
        else:
            # 기본값: 모든 유형 가능
            df['types'] = [['card', 'paper', 'mobile']] * len(df)

        logger.info(f"정제 완료: {len(df)}개 가맹점")

        return df

    def _parse_types(self, type_str):
        """
        상품권 유형 문자열 파싱

        Args:
            type_str: 상품권 유형 문자열

        Returns:
            list: 사용 가능한 유형 리스트
        """
        if pd.isna(type_str):
            return ['card', 'paper', 'mobile']

        types = []
        type_str = str(type_str).lower()

        if '충전' in type_str or 'card' in type_str:
            types.append('card')
        if '지류' in type_str or 'paper' in type_str:
            types.append('paper')
        if '모바일' in type_str or 'mobile' in type_str:
            types.append('mobile')

        return types if types else ['card', 'paper', 'mobile']

    def save_cleaned_data(self, df, output_path='data/raw/cleaned_stores.csv'):
        """
        정제된 데이터 저장

        Args:
            df: 정제된 DataFrame
            output_path: 출력 파일 경로
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"정제된 데이터 저장: {output_path}")


def main():
    """메인 함수"""
    fetcher = OnnuriDataFetcher()

    # 1. 데이터 다운로드 (수동 다운로드 권장)
    # fetcher.download_data()

    # 2. 데이터 로드
    try:
        df = fetcher.load_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.info("먼저 data/raw/ 폴더에 데이터 파일을 다운로드해주세요.")
        sys.exit(1)

    # 3. 데이터 정제
    df_cleaned = fetcher.clean_data(df)

    # 4. 저장
    fetcher.save_cleaned_data(df_cleaned)

    logger.info("=" * 60)
    logger.info("데이터 수집 완료!")
    logger.info(f"다음 단계: python scripts/geocode.py")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
