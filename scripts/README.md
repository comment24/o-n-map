# 데이터 수집 스크립트 가이드

온누리 상품권 가맹점 데이터를 수집하고 JSON으로 변환하는 스크립트입니다.

## 📋 준비사항

### 1. Python 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 카카오 REST API 키 설정

`.env` 파일 생성:

```bash
KAKAO_REST_API_KEY=your_rest_api_key_here
```

또는 환경변수로 설정:

```bash
export KAKAO_REST_API_KEY=your_rest_api_key_here
```

## 🚀 사용 방법

### 자동 실행 (전체 프로세스)

```bash
# 전체 프로세스 한 번에 실행
chmod +x scripts/run_all.sh
./scripts/run_all.sh
```

### 수동 실행 (단계별)

#### 1단계: 데이터 다운로드

```bash
python scripts/fetch_data.py
```

**중요**: 자동 다운로드가 제한될 수 있습니다.

**수동 다운로드 방법:**
1. https://www.data.go.kr/data/3060079/fileData.do 접속
2. 파일 데이터 탭에서 최신 파일 다운로드 (Excel 또는 CSV)
3. 다운로드한 파일을 `data/raw/` 폴더로 이동

#### 2단계: 주소 → 좌표 변환 (Geocoding)

```bash
python scripts/geocode.py
```

- 카카오 REST API 키 필요
- 약 10,000개 기준 15-20분 소요
- 캐시 사용으로 재실행 시 빠름

#### 3단계: JSON 생성

```bash
python scripts/generate_json.py
```

출력 파일:
- `data/stores.json` - 프론트엔드에서 사용
- `data/metadata.json` - 통계 정보

## 📂 파일 구조

```
scripts/
├── fetch_data.py       # 공공데이터 다운로드 및 정제
├── geocode.py          # 주소 → 좌표 변환
├── generate_json.py    # JSON 파일 생성
└── run_all.sh          # 전체 프로세스 실행

data/
├── raw/                # 원본 및 중간 데이터
│   ├── *.xlsx          # 다운로드한 원본 파일
│   ├── cleaned_stores.csv
│   ├── geocoded_stores.csv
│   ├── geocode_cache.json
│   └── geocode_failed.csv
├── stores.json         # 최종 데이터 (프론트엔드용)
└── metadata.json       # 통계 정보
```

## 🔄 GitHub Actions 자동화

### 설정 방법

1. **GitHub Secrets 설정**
   - Repository Settings > Secrets and variables > Actions
   - New repository secret 클릭
   - Name: `KAKAO_REST_API_KEY`
   - Value: 카카오 REST API 키 입력

2. **수동 실행**
   - GitHub 저장소 > Actions 탭
   - "Update Onnuri Store Data" 워크플로우 선택
   - "Run workflow" 클릭

3. **자동 실행**
   - 매주 일요일 오전 12시 (KST)에 자동 실행
   - 변경사항이 있으면 자동 커밋

### 데이터 업데이트 확인

```bash
# 최종 데이터 확인
cat data/stores.json | jq '.totalStores'

# 메타데이터 확인
cat data/metadata.json | jq '.'
```

## 🐛 문제 해결

### Geocoding 실패가 많은 경우

1. `data/raw/geocode_failed.csv` 파일 확인
2. 주소 형식 수정
3. 다시 실행 (캐시로 인해 성공한 것은 건너뜀)

### API 키 오류

```bash
# 환경변수 확인
echo $KAKAO_REST_API_KEY

# .env 파일 확인
cat .env
```

### 파일 인코딩 문제

Excel 파일을 CSV로 변환할 때:
- UTF-8 with BOM으로 저장
- Excel에서: "CSV UTF-8" 형식 선택

## 📊 데이터 품질 체크

```bash
# 전체 가맹점 수
wc -l data/raw/cleaned_stores.csv

# Geocoding 성공률
python -c "
import pandas as pd
df = pd.read_csv('data/raw/geocoded_stores.csv')
success = len(df[df['lat'].notna()])
total = len(df)
print(f'성공률: {success/total*100:.1f}% ({success}/{total})')
"
```

## 💡 팁

1. **캐시 활용**: Geocoding은 시간이 오래 걸리므로 캐시가 자동 저장됩니다.
2. **Rate Limiting**: 카카오 API는 초당 10건 제한이 있으므로 자동으로 조절됩니다.
3. **증분 업데이트**: 새 데이터만 Geocoding하려면 기존 캐시를 유지하세요.

## 📞 문의

문제가 발생하면 GitHub Issues에 등록해주세요.
