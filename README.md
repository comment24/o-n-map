# 온누리 상품권 사용처 지도

온누리 상품권을 사용할 수 있는 가맹점을 **위치 기반으로 빠르게 찾고**, 네이버 지도의 리뷰와 사진을 확인할 수 있는 웹 서비스입니다.

## ✨ 주요 기능

- 📍 **위치 기반 탐색**: 현재 위치 또는 목적지 중심으로 반경(1km/3km/5km) 내 가맹점 검색
- ⚡ **빠른 필터링**: 클라이언트에서 즉시 처리 (업종, 상품권 유형)
- 🗺️ **카카오맵**: 가맹점 위치 시각화 및 마커 클러스터링
- 🔗 **네이버 연동**: 상세 정보(리뷰, 사진, 가격)는 네이버 지도로 연결
- 📱 **모바일 최적화**: 반응형 디자인 (Mobile First)
- 🤖 **자동 업데이트**: GitHub Actions로 주기적 데이터 갱신

## 🛠️ 기술 스택

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Map**: 카카오맵 JavaScript API
- **Data Processing**: Python (pandas, requests)
- **CI/CD**: GitHub Actions
- **Deploy**: GitHub Pages

## 🚀 빠른 시작

### 1. 프론트엔드 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/comment24/o-n-map.git
cd o-n-map

# 로컬 서버 실행
cd public
python -m http.server 8000
```

브라우저에서 http://localhost:8000 열기

**참고**: 카카오 API 키는 이미 설정되어 있습니다 (`localhost:8000` 도메인 등록 필요)

### 2. 데이터 수집 (선택사항)

실제 온누리 가맹점 데이터로 업데이트하려면:

```bash
# Python 패키지 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
echo "KAKAO_REST_API_KEY=your_rest_api_key" > .env

# 데이터 수집 실행
./scripts/run_all.sh
```

자세한 내용은 [scripts/README.md](scripts/README.md)를 참조하세요.

## 📂 프로젝트 구조

```
o-n-map/
├── public/              # 프론트엔드 (GitHub Pages로 배포)
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── config.js    # 설정 (API 키 포함)
│       ├── utils.js     # 유틸리티 함수
│       ├── map.js       # 카카오맵 제어
│       ├── filter.js    # 위치 기반 필터링
│       └── app.js       # 메인 로직
│
├── scripts/             # 데이터 수집 스크립트
│   ├── fetch_data.py    # 공공데이터 다운로드
│   ├── geocode.py       # 주소 → 좌표 변환
│   ├── generate_json.py # JSON 생성
│   └── run_all.sh       # 전체 프로세스 실행
│
├── data/
│   ├── stores.json      # 가맹점 데이터 (프론트엔드용)
│   └── metadata.json    # 통계 정보
│
├── .github/workflows/
│   └── update-data.yml  # 자동 데이터 업데이트
│
└── SPEC.md              # 설계 문서
```

## 🔑 API 키 설정

### 카카오 개발자 계정

1. https://developers.kakao.com 접속 및 로그인
2. "내 애플리케이션" > "애플리케이션 추가하기"
3. **JavaScript 키**: 프론트엔드용 (이미 설정됨)
   - 플랫폼 설정에서 도메인 등록 (`localhost:8000`, GitHub Pages URL)
4. **REST API 키**: 데이터 수집용 (Geocoding)
   - `.env` 파일에 `KAKAO_REST_API_KEY=키입력`

### GitHub Secrets (자동화용)

1. Repository Settings > Secrets and variables > Actions
2. New repository secret
3. Name: `KAKAO_REST_API_KEY`, Value: REST API 키

## 📊 데이터 소스

- **출처**: [공공데이터포털 - 온누리상품권 가맹점](https://www.data.go.kr/data/3060079/fileData.do)
- **업데이트 주기**: 매주 일요일 오전 12시 (KST) 자동 업데이트
- **데이터 항목**: 가맹점명, 주소, 업종, 상품권 유형 등

## 🔄 GitHub Actions 워크플로우

자동으로 다음을 수행합니다:

1. 공공데이터포털에서 최신 가맹점 데이터 수집
2. 카카오 Geocoding API로 주소 → 좌표 변환
3. JSON 파일 생성 (`data/stores.json`)
4. 변경사항 자동 커밋 및 푸시

수동 실행: GitHub Actions 탭 > "Update Onnuri Store Data" > Run workflow

## 🌐 배포

GitHub Pages로 자동 배포:

1. Repository Settings > Pages
2. Source: Deploy from a branch
3. Branch: `main` (또는 현재 브랜치), Folder: `/public`
4. Save

배포 URL: `https://comment24.github.io/o-n-map/`

## 🐛 문제 해결

### 지도가 표시되지 않는 경우

1. 카카오 개발자 콘솔에서 도메인이 등록되었는지 확인
2. 브라우저 콘솔에서 에러 메시지 확인
3. API 키가 올바르게 입력되었는지 확인

### 위치 권한 에러

- HTTPS 또는 localhost에서만 Geolocation API가 작동합니다
- GitHub Pages는 자동으로 HTTPS 제공

### 데이터 업데이트 실패

- GitHub Actions 탭에서 워크플로우 로그 확인
- Secrets에 `KAKAO_REST_API_KEY`가 설정되었는지 확인

## 📝 라이선스

MIT License

## 🤝 기여

이슈와 PR은 언제나 환영합니다!

버그 리포트, 기능 제안, 문서 개선 등 모든 기여를 환영합니다.

## 📖 문서

- [SPEC.md](SPEC.md) - 상세 설계 문서
- [scripts/README.md](scripts/README.md) - 데이터 수집 가이드

## 🙏 감사

- 데이터 제공: 소상공인시장진흥공단, 공공데이터포털
- 지도 API: 카카오맵
- 호스팅: GitHub Pages
