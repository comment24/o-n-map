#!/bin/bash
# 전체 데이터 수집 프로세스 실행 스크립트

set -e  # 에러 발생 시 중단

echo "=================================="
echo "온누리 상품권 데이터 수집 시작"
echo "=================================="
echo ""

# 1단계: 데이터 다운로드
echo "[1/3] 데이터 다운로드 및 정제..."
python scripts/fetch_data.py || {
    echo ""
    echo "⚠️  자동 다운로드 실패 또는 수동 다운로드 필요"
    echo "   data/raw/ 폴더에 Excel/CSV 파일이 있는지 확인하세요."
    echo ""
    read -p "계속 진행하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# 데이터 파일 존재 확인
if ! ls data/raw/*.{xlsx,xls,csv} 1> /dev/null 2>&1; then
    echo ""
    echo "❌ data/raw/ 폴더에 데이터 파일이 없습니다."
    echo "   https://www.data.go.kr/data/3060079/fileData.do 에서 다운로드해주세요."
    exit 1
fi

# 2단계: Geocoding
echo ""
echo "[2/3] 주소 → 좌표 변환 (Geocoding)..."
echo "   ⏱️  시간이 오래 걸릴 수 있습니다..."

# 환경변수 확인
if [ -z "$KAKAO_REST_API_KEY" ]; then
    if [ ! -f .env ]; then
        echo ""
        echo "❌ KAKAO_REST_API_KEY가 설정되지 않았습니다."
        echo "   .env 파일을 생성하거나 환경변수를 설정해주세요."
        exit 1
    fi
fi

python scripts/geocode.py

# 3단계: JSON 생성
echo ""
echo "[3/3] JSON 파일 생성..."
python scripts/generate_json.py

# 완료
echo ""
echo "=================================="
echo "✅ 데이터 수집 완료!"
echo "=================================="
echo ""
echo "생성된 파일:"
echo "  📄 data/stores.json"
echo "  📄 data/metadata.json"
echo ""

# 통계 출력
if command -v jq &> /dev/null; then
    echo "통계:"
    echo "  총 가맹점: $(jq '.totalStores' data/stores.json)"
    echo "  업데이트: $(jq -r '.lastUpdated' data/stores.json)"
else
    echo "💡 jq를 설치하면 통계를 볼 수 있습니다: sudo apt-get install jq"
fi

echo ""
echo "다음 단계:"
echo "  1. git add data/stores.json data/metadata.json"
echo "  2. git commit -m \"chore: update store data\""
echo "  3. git push"
echo ""
