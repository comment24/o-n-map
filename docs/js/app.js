// 메인 애플리케이션
class OnnuriMapApp {
    constructor() {
        this.currentLocation = null;
        this.storeData = null;
    }

    /**
     * 앱 초기화
     */
    async init() {
        console.log('온누리 상품권 지도 앱 시작');

        // 카카오맵 초기화
        mapManager.init();

        // 이벤트 리스너 등록
        this.setupEventListeners();

        // 데이터 로드
        await this.loadStoreData();

        console.log('앱 초기화 완료');
    }

    /**
     * 가맹점 데이터 로드
     */
    async loadStoreData() {
        try {
            const response = await fetch(CONFIG.DATA_URL);
            if (!response.ok) {
                throw new Error('데이터 로드 실패');
            }

            this.storeData = await response.json();
            filterManager.setStores(this.storeData.stores);

            // UI 업데이트
            this.updateInfoBar();

            console.log('데이터 로드 완료:', this.storeData.totalStores);
        } catch (error) {
            console.error('데이터 로드 에러:', error);
            this.showError('가맹점 데이터를 불러올 수 없습니다. 페이지를 새로고침해주세요.');
        }
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 현재 위치 버튼
        document.getElementById('currentLocationBtn').addEventListener('click', () => {
            this.getCurrentLocation();
        });

        // 주소 검색 (디바운스 적용)
        const addressInput = document.getElementById('addressInput');
        addressInput.addEventListener('input', debounce((e) => {
            this.searchAddress(e.target.value);
        }, 500));

        // 반경 선택
        document.querySelectorAll('input[name="radius"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.onRadiusChange(parseInt(e.target.value));
            });
        });

        // 카테고리 선택
        document.getElementById('categorySelect').addEventListener('change', (e) => {
            this.onCategoryChange(e.target.value);
        });

        // 상품권 유형 선택
        document.querySelectorAll('input[name="type"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.onTypesChange();
            });
        });

        // Dialog 닫기
        document.getElementById('dialogCloseBtn').addEventListener('click', () => {
            this.closeDialog();
        });
    }

    /**
     * 현재 위치 가져오기
     */
    getCurrentLocation() {
        if (!navigator.geolocation) {
            this.showError('위치 서비스를 지원하지 않는 브라우저입니다.');
            return;
        }

        const btn = document.getElementById('currentLocationBtn');
        btn.textContent = '📍 위치 확인 중...';
        btn.disabled = true;

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                this.setLocation(lat, lng);

                btn.textContent = '📍 현재 위치';
                btn.disabled = false;
            },
            (error) => {
                console.error('위치 에러:', error);
                this.showError('위치 정보를 가져올 수 없습니다. 위치 권한을 확인해주세요.');
                btn.textContent = '📍 현재 위치';
                btn.disabled = false;
            }
        );
    }

    /**
     * 주소 검색
     * @param {string} address - 검색할 주소
     */
    async searchAddress(address) {
        if (!address || address.trim().length < 2) {
            return;
        }

        try {
            const coords = await mapManager.geocodeAddress(address);
            this.setLocation(coords.lat, coords.lng);
        } catch (error) {
            console.error('주소 검색 에러:', error);
            // 에러는 무시 (입력 중일 수 있음)
        }
    }

    /**
     * 위치 설정 및 필터링
     * @param {number} lat - 위도
     * @param {number} lng - 경도
     */
    setLocation(lat, lng) {
        this.currentLocation = { lat, lng };

        // 지도에 사용자 위치 표시
        mapManager.setUserLocation(lat, lng);

        // 반경 원 그리기
        const radius = this.getSelectedRadius();
        mapManager.drawRadiusCircle(lat, lng, radius);

        // 필터 적용
        filterManager.setUserLocation(lat, lng);
        this.updateDisplay();
    }

    /**
     * 반경 변경
     * @param {number} radius - 반경 (미터)
     */
    onRadiusChange(radius) {
        filterManager.setRadius(radius);

        if (this.currentLocation) {
            mapManager.drawRadiusCircle(
                this.currentLocation.lat,
                this.currentLocation.lng,
                radius
            );
        }

        this.updateDisplay();
    }

    /**
     * 카테고리 변경
     * @param {string} category - 카테고리
     */
    onCategoryChange(category) {
        filterManager.setCategory(category);
        this.updateDisplay();
    }

    /**
     * 상품권 유형 변경
     */
    onTypesChange() {
        const types = Array.from(document.querySelectorAll('input[name="type"]:checked'))
            .map(cb => cb.value);
        filterManager.setTypes(types);
        this.updateDisplay();
    }

    /**
     * 화면 업데이트
     */
    updateDisplay() {
        const stores = filterManager.getFilteredStores();

        // 지도 마커 표시
        mapManager.displayStoreMarkers(stores, (store) => {
            this.showStoreDetail(store);
        });

        // 리스트 업데이트
        this.updateStoreList(stores);

        // 카운트 업데이트
        document.getElementById('filteredCount').textContent = `${stores.length}개`;
    }

    /**
     * 가맹점 리스트 업데이트
     * @param {Array} stores - 가맹점 배열
     */
    updateStoreList(stores) {
        const container = document.getElementById('storeListContainer');

        if (stores.length === 0) {
            container.innerHTML = '<div class="loading">해당 조건의 가맹점이 없습니다</div>';
            return;
        }

        container.innerHTML = stores.map(store => `
            <div class="store-item" data-id="${store.id}">
                <h3>${store.name}</h3>
                <div class="store-item-distance">${formatDistance(store.distance)}</div>
                <div class="store-item-category">${store.category || '기타'}</div>
            </div>
        `).join('');

        // 리스트 아이템 클릭 이벤트
        container.querySelectorAll('.store-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = parseInt(item.dataset.id);
                const store = filterManager.findStoreById(id);
                if (store) {
                    // 거리 정보 추가 (필터링된 것에서 찾기)
                    const filteredStore = stores.find(s => s.id === id);
                    if (filteredStore) {
                        this.showStoreDetail(filteredStore);
                        mapManager.panTo(store.lat, store.lng);
                    }
                }
            });
        });
    }

    /**
     * 가맹점 상세 정보 Dialog 표시
     * @param {Object} store - 가맹점 정보
     */
    showStoreDetail(store) {
        const dialog = document.getElementById('storeDialog');

        // 정보 채우기
        document.getElementById('dialogStoreName').textContent = store.name;
        document.getElementById('dialogAddress').textContent = store.address;
        document.getElementById('dialogCategory').textContent =
            store.subCategory ? `${store.category} > ${store.subCategory}` : store.category;
        document.getElementById('dialogTypes').textContent = formatStoreTypes(store.types);

        // 거리 (있는 경우만)
        if (store.distance !== undefined) {
            document.getElementById('dialogDistance').textContent = formatDistance(store.distance);
        }

        // 전화번호 (있는 경우만)
        const phoneElement = document.querySelector('.dialog-phone');
        const phoneBtn = document.getElementById('dialogPhoneBtn');
        if (store.phone && isValidPhone(store.phone)) {
            document.getElementById('dialogPhone').textContent = store.phone;
            phoneElement.style.display = 'block';
            phoneBtn.style.display = 'inline-block';
            phoneBtn.href = `tel:${store.phone}`;
        } else {
            phoneElement.style.display = 'none';
            phoneBtn.style.display = 'none';
        }

        // 네이버 URL
        const naverUrl = store.naverUrl ||
            generateNaverSearchUrl(store.name, store.address);
        document.getElementById('dialogNaverBtn').href = naverUrl;

        // 길찾기 URL (네이버 사용)
        const directionsUrls = generateDirectionsUrls(store.lat, store.lng, store.name);
        document.getElementById('dialogDirectionsBtn').href = directionsUrls.naver;

        // Dialog 표시
        dialog.showModal();
    }

    /**
     * Dialog 닫기
     */
    closeDialog() {
        const dialog = document.getElementById('storeDialog');
        dialog.close();
    }

    /**
     * 정보 바 업데이트
     */
    updateInfoBar() {
        if (!this.storeData) return;

        document.getElementById('storeCount').textContent =
            `가맹점: ${this.storeData.totalStores.toLocaleString()}개`;

        if (this.storeData.lastUpdated) {
            document.getElementById('lastUpdated').textContent =
                `업데이트: ${formatDate(this.storeData.lastUpdated)}`;
        }
    }

    /**
     * 선택된 반경 가져오기
     * @returns {number}
     */
    getSelectedRadius() {
        const selected = document.querySelector('input[name="radius"]:checked');
        return selected ? parseInt(selected.value) : CONFIG.RADIUS.SMALL;
    }

    /**
     * 에러 메시지 표시
     * @param {string} message - 에러 메시지
     */
    showError(message) {
        alert(message);
    }
}

// 앱 시작
kakao.maps.load(() => {
    const app = new OnnuriMapApp();
    app.init();
});
