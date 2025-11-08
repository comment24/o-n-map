# 온누리 상품권 사용처 지도 프로젝트 설계 문서

## 📋 프로젝트 개요

### 목적
온누리 상품권 사용 가능 가맹점을 네이버 지도를 통해 시각적으로 조회할 수 있는 웹 서비스 제공

### 핵심 요구사항
- 프론트엔드 전용 (백엔드 없음)
- GitHub Actions를 통한 주기적 데이터 크롤링
- 정적 데이터 파일 생성 및 활용
- GitHub Pages를 통한 서비스 배포

---

## 🔍 리서치 결과

### 1. 데이터 소스

#### 온누리 상품권 가맹점 데이터
- **제공처**: 공공데이터포털 (data.go.kr)
- **데이터명**: 소상공인시장진흥공단_전국 온누리상품권 가맹점 현황
- **접근 방법**:
  - 파일 다운로드: 로그인 없이 가능
  - Open API: 회원가입 및 활용신청 필요 (REST API, JSON/XML 형식)
- **데이터 항목**:
  - 가맹점명
  - 소속 시장명
  - 소재지 (주소)
  - 취급 품목
  - 상품권 유형 (충전식카드/지류/모바일)
- **URL**: https://www.data.go.kr/data/3060079/fileData.do

### 2. 지도 API

#### 네이버 클라우드 플랫폼 Maps API
- **서비스**: Web Dynamic Map API
- **특징**:
  - JavaScript SDK 제공
  - 데스크톱 및 모바일 환경 최적화
  - 주요 웹 브라우저 완벽 지원
- **무료 이용량**:
  - 대표 계정 기준 월 무료 이용량 제공
  - Web Dynamic Map: 월 무료 호출 가능
  - Geocoding/Reverse Geocoding: 무료 이용량 제공
- **문서**:
  - 가이드: https://guide.ncloud-docs.com/docs/maps-web-sdk
  - 예제: https://navermaps.github.io/maps.js.ncp/docs/tutorial-digest.example.html
- **필요사항**: NAVER Cloud Platform 계정 및 API 인증키 발급

### 3. 자동화 시스템

#### GitHub Actions
- **스케줄링**: Cron 표현식을 통한 주기적 실행
- **워크플로우 위치**: `.github/workflows/*.yml`
- **주요 기능**:
  - 정해진 시간에 자동 실행
  - Python/Node.js 등 스크립트 실행 환경 제공
  - 결과물을 저장소에 자동 커밋
  - `workflow_dispatch`로 수동 실행 가능

#### GitHub Pages
- **호스팅**: 정적 사이트 무료 호스팅
- **배포**: `gh-pages` 브랜치 또는 `/docs` 폴더
- **HTTPS**: 기본 제공
- **커스텀 도메인**: 설정 가능

---

## 🏗️ 시스템 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────┐
│         GitHub Actions (Scheduled)              │
│  ┌───────────────────────────────────────────┐  │
│  │ 1. 공공데이터포털에서 가맹점 데이터 수집    │  │
│  │ 2. 주소 → 좌표 변환 (Geocoding)           │  │
│  │ 3. JSON 정적 파일 생성                    │  │
│  │ 4. 저장소에 자동 커밋                     │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         GitHub Repository                       │
│  ├── /data                                      │
│  │   ├── stores.json (가맹점 정보)             │
│  │   └── metadata.json (업데이트 정보)         │
│  ├── /src                                       │
│  │   ├── index.html                            │
│  │   ├── map.js                                │
│  │   └── styles.css                            │
│  └── /.github/workflows                         │
│      └── update-data.yml                        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         GitHub Pages (Static Hosting)           │
│  ┌───────────────────────────────────────────┐  │
│  │  웹 브라우저                               │  │
│  │  └── 정적 JSON 로드                       │  │
│  │  └── 네이버 지도 표시                     │  │
│  │  └── 마커로 가맹점 위치 표시               │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 데이터 플로우

1. **데이터 수집** (GitHub Actions - 주 1회 실행)
   ```
   공공데이터 API/파일
        ↓
   가맹점 정보 다운로드
        ↓
   주소 → 좌표 변환 (Geocoding)
        ↓
   JSON 파일 생성
        ↓
   Git 커밋 & 푸시
   ```

2. **사용자 조회** (브라우저)
   ```
   페이지 로드
        ↓
   stores.json 로드
        ↓
   네이버 지도 초기화
        ↓
   가맹점 마커 표시
        ↓
   검색/필터 기능
   ```

---

## 🛠️ 기술 스택

### Frontend
- **HTML5**: 기본 구조
- **CSS3**: 스타일링 (반응형 디자인)
- **Vanilla JavaScript**: 지도 제어 및 상호작용
  - 또는 **React/Vue.js** (선택사항)
- **네이버 Maps JavaScript API**: 지도 표시

### Data Processing (GitHub Actions)
- **Python 3.x**:
  - 데이터 크롤링/다운로드
  - CSV/Excel → JSON 변환
  - Geocoding API 호출
- **필요 라이브러리**:
  - `requests`: HTTP 요청
  - `pandas`: 데이터 처리
  - `openpyxl`: Excel 파일 처리

### CI/CD
- **GitHub Actions**: 자동화 워크플로우
- **GitHub Pages**: 정적 사이트 호스팅

### 외부 API
- **공공데이터포털 API**: 가맹점 데이터 조회
- **NAVER Cloud Maps API**:
  - Web Dynamic Map API: 지도 표시
  - Geocoding API: 주소 → 좌표 변환

---

## 📂 프로젝트 구조

```
o-n-map/
├── .github/
│   └── workflows/
│       └── update-data.yml          # 데이터 업데이트 자동화
│
├── scripts/
│   ├── fetch_data.py                # 공공데이터 수집
│   ├── geocode.py                   # 주소 → 좌표 변환
│   └── generate_json.py             # JSON 생성
│
├── data/
│   ├── stores.json                  # 가맹점 정보 (좌표 포함)
│   ├── metadata.json                # 데이터 메타정보
│   └── raw/                         # 원본 데이터 (optional)
│
├── public/ (or docs/)
│   ├── index.html                   # 메인 페이지
│   ├── css/
│   │   └── styles.css               # 스타일시트
│   ├── js/
│   │   ├── map.js                   # 지도 제어
│   │   ├── search.js                # 검색 기능
│   │   └── config.js                # 설정 (API 키 등)
│   └── assets/
│       └── images/                  # 이미지 리소스
│
├── .env.example                     # 환경변수 예시
├── .gitignore
├── README.md
└── SPEC.md                          # 이 문서
```

---

## 🔑 핵심 기능 명세

### 1. 지도 표시
- **기본 지도 로드**: 한국 전체 또는 서울 중심
- **가맹점 마커**: 모든 가맹점 위치 표시
- **마커 클러스터링**: 많은 마커를 그룹화하여 성능 최적화
- **마커 클릭**: 가맹점 상세 정보 팝업

### 2. 검색 기능
- **주소 검색**: 특정 지역의 가맹점 검색
- **가맹점명 검색**: 이름으로 검색
- **품목 필터**: 취급 품목별 필터링
- **상품권 유형 필터**: 충전식/지류/모바일 구분

### 3. 상세 정보 표시
- 가맹점명
- 주소
- 소속 시장명
- 취급 품목
- 상품권 유형

### 4. 사용자 경험
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- **현재 위치**: 사용자 위치 기반 주변 가맹점 표시
- **로딩 상태**: 데이터 로딩 중 표시
- **에러 핸들링**: 데이터 로드 실패 시 안내

---

## 🔄 데이터 업데이트 프로세스

### GitHub Actions 워크플로우

```yaml
name: Update Store Data

on:
  schedule:
    - cron: '0 2 * * 0'  # 매주 일요일 오전 2시 (KST 11시)
  workflow_dispatch:      # 수동 실행 가능

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
      - name: Setup Python
      - name: Install dependencies
      - name: Fetch data from public API
      - name: Geocode addresses
      - name: Generate JSON files
      - name: Commit and push changes
```

### 데이터 처리 단계

1. **원본 데이터 수집**
   - 공공데이터포털 API 호출 또는 파일 다운로드
   - CSV/Excel 형식 → Python pandas로 로드

2. **데이터 정제**
   - 중복 제거
   - 필수 필드 검증
   - 주소 표준화

3. **Geocoding**
   - 주소 → 위도/경도 변환
   - NAVER Geocoding API 사용
   - 캐싱으로 API 호출 최소화
   - Rate limiting 준수

4. **JSON 생성**
   ```json
   {
     "lastUpdated": "2025-11-08T00:00:00Z",
     "totalStores": 50000,
     "stores": [
       {
         "id": 1,
         "name": "가맹점명",
         "address": "서울시 강남구...",
         "market": "소속 시장명",
         "category": "취급품목",
         "types": ["card", "paper", "mobile"],
         "lat": 37.1234,
         "lng": 127.5678
       }
     ]
   }
   ```

5. **저장소 업데이트**
   - `data/stores.json` 갱신
   - `data/metadata.json` 갱신 (업데이트 시간, 통계 등)
   - Git commit 및 push

---

## 🔐 보안 및 API 키 관리

### 환경 변수
- **NAVER_CLIENT_ID**: 네이버 클라우드 API 클라이언트 ID
- **NAVER_CLIENT_SECRET**: 네이버 클라우드 API 시크릿
- **PUBLIC_DATA_API_KEY**: 공공데이터포털 API 키 (optional)

### GitHub Secrets
- GitHub Actions에서 사용할 비밀 키는 Repository Secrets에 저장
- 프론트엔드에서는 공개 API 키만 사용 (도메인 제한 설정)

### .gitignore
```
.env
.env.local
*.pyc
__pycache__/
node_modules/
data/raw/
.DS_Store
```

---

## 📊 데이터 스키마

### stores.json
```typescript
interface Store {
  id: number;
  name: string;              // 가맹점명
  address: string;           // 주소
  market?: string;           // 소속 시장명
  category?: string;         // 취급 품목
  types: string[];           // ["card", "paper", "mobile"]
  lat: number;               // 위도
  lng: number;               // 경도
}

interface StoreData {
  lastUpdated: string;       // ISO 8601 형식
  totalStores: number;
  stores: Store[];
}
```

### metadata.json
```typescript
interface Metadata {
  lastUpdated: string;
  dataSource: string;
  totalStores: number;
  geocodingRate: number;     // Geocoding 성공률
  regions: {
    [key: string]: number;   // 지역별 가맹점 수
  };
}
```

---

## 🎨 UI/UX 설계

### 레이아웃
```
┌─────────────────────────────────────┐
│  Header (타이틀, 검색바)              │
├──────────┬──────────────────────────┤
│          │                          │
│  Sidebar │     Map Area             │
│  (필터)  │     (네이버 지도)         │
│          │                          │
└──────────┴──────────────────────────┘
```

### 주요 컴포넌트
1. **Header**
   - 프로젝트 타이틀
   - 검색바 (주소/가맹점명)
   - 현재 위치 버튼

2. **Sidebar** (토글 가능)
   - 상품권 유형 필터
   - 품목 카테고리 필터
   - 검색 결과 리스트

3. **Map**
   - 네이버 지도
   - 가맹점 마커
   - 마커 클러스터
   - 정보 윈도우

4. **Info Window**
   - 가맹점 상세 정보
   - 길찾기 버튼
   - 공유 버튼

---

## 🚀 구현 단계

### Phase 1: 기본 인프라 (1주)
- [x] 리서치 및 설계 문서 작성
- [ ] GitHub 저장소 설정
- [ ] GitHub Actions 워크플로우 작성
- [ ] 데이터 수집 스크립트 개발
- [ ] Geocoding 스크립트 개발

### Phase 2: 프론트엔드 개발 (2주)
- [ ] HTML/CSS 레이아웃 구현
- [ ] 네이버 지도 연동
- [ ] 마커 표시 기능
- [ ] 검색 및 필터 기능
- [ ] 반응형 디자인 적용

### Phase 3: 최적화 및 배포 (1주)
- [ ] 성능 최적화 (마커 클러스터링)
- [ ] 에러 핸들링
- [ ] GitHub Pages 배포
- [ ] 테스트 및 버그 수정

### Phase 4: 고도화 (Optional)
- [ ] PWA 변환 (오프라인 지원)
- [ ] 사용자 즐겨찾기 기능
- [ ] 통계 대시보드
- [ ] 다국어 지원

---

## 📝 고려사항 및 제약

### 기술적 제약
- **Geocoding API 한도**: 네이버 클라우드 무료 이용량 내 사용
  - 전체 데이터를 한 번에 Geocoding 후 캐싱
  - 변경된 데이터만 업데이트
- **GitHub Actions 실행 시간**: 최대 6시간 제한
- **정적 파일 크기**: JSON 파일이 너무 크면 로딩 속도 저하
  - 지역별로 파일 분할 고려
  - 압축 (gzip) 활용

### 데이터 품질
- **주소 정확도**: 공공데이터의 주소 형식이 일관되지 않을 수 있음
- **Geocoding 실패**: 일부 주소는 좌표 변환 실패 가능
  - 실패한 경우 로그 기록 및 수동 보정

### 비용
- **무료 사용 가능**:
  - GitHub Actions: 공개 저장소 무제한
  - GitHub Pages: 무료
  - NAVER Cloud Maps API: 대표 계정 무료 이용량
  - 공공데이터포털: 무료 (일부 API는 신청 필요)

---

## 🔍 참고 자료

### 공식 문서
- 공공데이터포털: https://www.data.go.kr
- 네이버 클라우드 Maps: https://guide.ncloud-docs.com/docs/maps-web-sdk
- GitHub Actions: https://docs.github.com/en/actions
- GitHub Pages: https://docs.github.com/en/pages

### 예제 프로젝트
- 네이버 지도 API 예제: https://navermaps.github.io/maps.js.ncp/docs/tutorial-digest.example.html

---

## 📌 다음 단계

1. ✅ 리서치 및 설계 문서 작성 완료
2. ⏭️ NAVER Cloud Platform 계정 생성 및 API 키 발급
3. ⏭️ 공공데이터포털 회원가입 및 데이터 접근 테스트
4. ⏭️ 프로토타입 개발 시작
   - 샘플 데이터로 지도 표시 테스트
   - GitHub Actions 워크플로우 테스트

---

**문서 버전**: 1.0
**작성일**: 2025-11-08
**최종 수정일**: 2025-11-08
