// 지도 관리 모듈
class MapManager {
    constructor() {
        this.map = null;
        this.markers = [];
        this.clusterer = null;
        this.userMarker = null;
        this.radiusCircle = null;
        this.geocoder = null;
    }

    /**
     * 지도 초기화
     */
    init() {
        const mapContainer = document.getElementById('map');
        const mapOption = {
            center: new kakao.maps.LatLng(CONFIG.DEFAULT_CENTER.lat, CONFIG.DEFAULT_CENTER.lng),
            level: CONFIG.DEFAULT_ZOOM
        };

        this.map = new kakao.maps.Map(mapContainer, mapOption);
        this.geocoder = new kakao.maps.services.Geocoder();

        // 마커 클러스터러 초기화
        this.clusterer = new kakao.maps.MarkerClusterer({
            map: this.map,
            averageCenter: true,
            minLevel: 5,
            disableClickZoom: true
        });

        // 지도 로딩 완료
        document.getElementById('mapLoading').style.display = 'none';
        console.log('카카오맵 초기화 완료');
    }

    /**
     * 주소를 좌표로 변환
     * @param {string} address - 주소
     * @returns {Promise<{lat: number, lng: number}>}
     */
    geocodeAddress(address) {
        return new Promise((resolve, reject) => {
            this.geocoder.addressSearch(address, (result, status) => {
                if (status === kakao.maps.services.Status.OK) {
                    resolve({
                        lat: parseFloat(result[0].y),
                        lng: parseFloat(result[0].x)
                    });
                } else {
                    reject(new Error('주소를 찾을 수 없습니다.'));
                }
            });
        });
    }

    /**
     * 사용자 위치 마커 표시
     * @param {number} lat - 위도
     * @param {number} lng - 경도
     */
    setUserLocation(lat, lng) {
        // 기존 마커 제거
        if (this.userMarker) {
            this.userMarker.setMap(null);
        }

        const position = new kakao.maps.LatLng(lat, lng);

        // 사용자 위치 마커 생성
        this.userMarker = new kakao.maps.Marker({
            position: position,
            map: this.map,
            zIndex: 100,
            image: new kakao.maps.MarkerImage(
                'https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/marker_red.png',
                new kakao.maps.Size(24, 35)
            )
        });

        // 지도 중심 이동
        this.map.setCenter(position);
    }

    /**
     * 반경 원 그리기
     * @param {number} lat - 중심 위도
     * @param {number} lng - 중심 경도
     * @param {number} radius - 반경 (미터)
     */
    drawRadiusCircle(lat, lng, radius) {
        // 기존 원 제거
        if (this.radiusCircle) {
            this.radiusCircle.setMap(null);
        }

        const center = new kakao.maps.LatLng(lat, lng);

        this.radiusCircle = new kakao.maps.Circle({
            center: center,
            radius: radius,
            strokeWeight: 2,
            strokeColor: CONFIG.MARKER_COLOR.USER,
            strokeOpacity: 0.8,
            strokeStyle: 'solid',
            fillColor: CONFIG.MARKER_COLOR.USER,
            fillOpacity: 0.1
        });

        this.radiusCircle.setMap(this.map);

        // 지도 레벨 조정
        const bounds = this.radiusCircle.getBounds();
        this.map.setBounds(bounds);
    }

    /**
     * 가맹점 마커 표시
     * @param {Array} stores - 가맹점 배열
     * @param {Function} onMarkerClick - 마커 클릭 콜백
     */
    displayStoreMarkers(stores, onMarkerClick) {
        // 기존 마커 제거
        this.clearMarkers();

        if (!stores || stores.length === 0) {
            return;
        }

        const markers = stores.map(store => {
            const position = new kakao.maps.LatLng(store.lat, store.lng);

            // 마커 생성
            const marker = new kakao.maps.Marker({
                position: position,
                title: store.name
            });

            // 마커 클릭 이벤트
            kakao.maps.event.addListener(marker, 'click', () => {
                onMarkerClick(store);
                // 지도 중심을 마커 위치로 이동
                this.map.setCenter(position);
            });

            return marker;
        });

        // 클러스터러에 마커 추가
        this.clusterer.addMarkers(markers);
        this.markers = markers;

        console.log(`${stores.length}개 가맹점 마커 표시 완료`);
    }

    /**
     * 모든 마커 제거
     */
    clearMarkers() {
        if (this.clusterer) {
            this.clusterer.clear();
        }
        this.markers = [];
    }

    /**
     * 특정 위치로 지도 이동
     * @param {number} lat - 위도
     * @param {number} lng - 경도
     */
    panTo(lat, lng) {
        const position = new kakao.maps.LatLng(lat, lng);
        this.map.panTo(position);
    }

    /**
     * 지도 레벨 설정
     * @param {number} level - 지도 레벨
     */
    setLevel(level) {
        this.map.setLevel(level);
    }

    /**
     * 현재 지도 중심 좌표 가져오기
     * @returns {{lat: number, lng: number}}
     */
    getCenter() {
        const center = this.map.getCenter();
        return {
            lat: center.getLat(),
            lng: center.getLng()
        };
    }
}

// 전역 인스턴스 생성
const mapManager = new MapManager();
