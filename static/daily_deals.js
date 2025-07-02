// 每日促銷頁面的 JavaScript 功能

let allDeals = [];
let currentDeals = [];
let currentPage = 1;
const itemsPerPage = 12;
let currentPlatform = 'all'; // 當前選擇的平台

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    loadDailyDeals('all');
});

// 平台切換功能
function switchPlatform(platform) {
    // 更新按鈕狀態
    document.querySelectorAll('[data-platform]').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-platform="${platform}"]`).classList.add('active');
    
    // 載入對應平台的資料
    currentPlatform = platform;
    loadDailyDeals(platform);
    
    // 更新頁面描述
    updatePlatformDescription(platform);
}

// 更新平台描述
function updatePlatformDescription(platform) {
    const description = document.getElementById('platformDescription');
    const platformInfo = document.getElementById('platformInfo');
    
    switch(platform) {
        case 'pchome_onsale':
            description.textContent = '精選 PChome 線上購物每日特價商品';
            platformInfo.textContent = 'PChome';
            break;
        case 'yahoo_rushbuy':
            description.textContent = '精選 Yahoo 秒殺時時樂特價商品';
            platformInfo.textContent = 'Yahoo秒殺';
            break;
        default:
            description.textContent = '精選各大平台每日特價商品';
            platformInfo.textContent = '全部平台';
    }
}

// 批量預載入圖片
async function preloadImages(products) {
    const batchSize = 5; // 每批載入5張圖片
    const promises = [];
    
    for (let i = 0; i < products.length; i += batchSize) {
        const batch = products.slice(i, i + batchSize);
        const batchPromises = batch.map(product => {
            if (product.image_url) {
                return preloadImage(product.image_url).catch(err => {
                    console.warn(`圖片預載入失敗: ${product.image_url}`, err);
                    return null;
                });
            }
            return Promise.resolve(null);
        });
        
        promises.push(...batchPromises);
        
        // 每批之間延遲100ms，避免過度佔用網路
        if (i + batchSize < products.length) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
    }
    
    return Promise.allSettled(promises);
}

// 載入每日促銷資料（支援平台參數）
async function loadDailyDeals(platform = 'all') {
    showLoading(true);
    
    try {
        const url = `/api/daily-deals${platform !== 'all' ? `?platform=${platform}` : ''}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success') {
            allDeals = [];
            
            // 合併所有促銷商品
            data.daily_deals.forEach(deal => {
                allDeals = allDeals.concat(deal.products.map(product => ({
                    ...product,
                    crawl_time: deal.crawl_time,
                    source_platform: deal.platform
                })));
            });
            
            currentDeals = [...allDeals];
            updateStats(data);
            displayProducts();
            setupPagination();
            
            // 預載入商品圖片
            preloadImages(currentDeals);
        } else {
            showError('載入促銷商品失敗');
        }
    } catch (error) {
        console.error('Error loading daily deals:', error);
        showError('載入促銷商品時發生錯誤');
    } finally {
        showLoading(false);
    }
}

// 更新每日促銷資料
// 更新統計資訊
function updateStats(data) {
    document.getElementById('totalDeals').textContent = data.total_deals || 0;
    
    // 更新上次更新時間顯示
    if (data.latest_update) {
        const updateTime = new Date(data.latest_update);
        const now = new Date();
        
        // 檢查時間是否有效
        if (isNaN(updateTime.getTime())) {
            document.getElementById('lastUpdate').innerHTML = '時間格式錯誤';
            return;
        }
        
        const timeStr = updateTime.toLocaleString('zh-TW', {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // 計算相對時間
        const timeDiff = now - updateTime;
        const hours = Math.floor(timeDiff / (1000 * 60 * 60));
        const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
        
        let relativeTime = '';
        if (hours > 0) {
            relativeTime = `${hours} 小時前`;
        } else if (minutes > 0) {
            relativeTime = `${minutes} 分鐘前`;
        } else {
            relativeTime = '剛剛';
        }
        
        let updateInfo = `${timeStr}<br><small class="text-muted">${relativeTime}</small>`;
        
        // 加入各平台更新時間詳情
        if (data.platform_updates) {
            const platformDetails = [];
            if (data.platform_updates.pchome_onsale) {
                const pchomeTime = new Date(data.platform_updates.pchome_onsale);
                if (!isNaN(pchomeTime.getTime())) {
                    const pchomeStr = pchomeTime.toLocaleString('zh-TW', {
                        month: 'numeric',
                        day: 'numeric', 
                        hour: '2-digit', 
                        minute: '2-digit'
                    });
                    platformDetails.push(`PChome: ${pchomeStr}`);
                }
            }
            if (data.platform_updates.yahoo_rushbuy) {
                const yahooTime = new Date(data.platform_updates.yahoo_rushbuy);
                if (!isNaN(yahooTime.getTime())) {
                    const yahooStr = yahooTime.toLocaleString('zh-TW', {
                        month: 'numeric',
                        day: 'numeric', 
                        hour: '2-digit', 
                        minute: '2-digit'
                    });
                    platformDetails.push(`Yahoo: ${yahooStr}`);
                }
            }
            
            if (platformDetails.length > 0) {
                updateInfo += `<br><small class="text-muted">${platformDetails.join(' | ')}</small>`;
            }
        }
        
        // 添加下次更新時間資訊
        if (data.next_update_times) {
            const nextUpdates = Object.values(data.next_update_times).join(', ');
            updateInfo += `<br><small class="text-info">下次更新: ${nextUpdates}</small>`;
        }
        
        document.getElementById('lastUpdate').innerHTML = updateInfo;
    } else {
        document.getElementById('lastUpdate').innerHTML = '無更新資料';
    }
    
    // 計算價格範圍
    if (allDeals.length > 0) {
        const prices = allDeals.map(product => parsePrice(product.price)).filter(p => p > 0);
        if (prices.length > 0) {
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            document.getElementById('priceRange').textContent = 
                `$${minPrice.toLocaleString()} - $${maxPrice.toLocaleString()}`;
        }
    }
}

// 顯示商品
function displayProducts() {
    const container = document.getElementById('productsContainer');
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageProducts = currentDeals.slice(startIndex, endIndex);
    
    if (pageProducts.length === 0) {
        container.innerHTML = '';
        document.getElementById('emptyMessage').style.display = 'block';
        return;
    }
    
    document.getElementById('emptyMessage').style.display = 'none';
    
    // 使用 DocumentFragment 批量更新 DOM，減少重排
    const fragment = document.createDocumentFragment();
    
    pageProducts.forEach((product, index) => {
        // 獲取平台顯示名稱
        const platformName = getPlatformDisplayName(product.source_platform || product.platform);
        const platformIcon = getPlatformIcon(product.source_platform || product.platform);
        
        const productCard = document.createElement('div');
        productCard.className = 'col-lg-3 col-md-4 col-sm-6 mb-4';
        
        productCard.innerHTML = `
            <div class="card product-card h-100" onclick="showProductDetail('${escapeHtml(JSON.stringify(product))}')">
                <div class="position-relative">
                    <img class="card-img-top product-image" 
                         src="${product.image_url}"
                         alt="${product.title}" 
                         loading="lazy"
                         onerror="this.style.background='linear-gradient(45deg, #f8f9fa 25%, transparent 25%), linear-gradient(-45deg, #f8f9fa 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #f8f9fa 75%), linear-gradient(-45deg, transparent 75%, #f8f9fa 75%)'; this.style.backgroundSize='20px 20px'; this.style.backgroundPosition='0 0, 0 10px, 10px -10px, -10px 0px'; console.log('圖片載入失敗:', this.src);"
                         onload="this.style.opacity='1'; this.style.backgroundImage='none'; console.log('圖片載入成功:', this.src);"
                         style="background-color: #f8f9fa; min-height: 200px; opacity: 0.3; transition: opacity 0.5s ease;
                                background-image: linear-gradient(45deg, #e9ecef 25%, transparent 25%), 
                                                  linear-gradient(-45deg, #e9ecef 25%, transparent 25%), 
                                                  linear-gradient(45deg, transparent 75%, #e9ecef 75%), 
                                                  linear-gradient(-45deg, transparent 75%, #e9ecef 75%);
                                background-size: 20px 20px;
                                background-position: 0 0, 0 10px, 10px -10px, -10px 0px;">
                    <span class="deal-badge">
                        <i class="fas fa-fire"></i> 特惠
                    </span>
                </div>
                <div class="card-body d-flex flex-column">
                    <h6 class="card-title" title="${product.title}">
                        ${truncateText(product.title, 50)}
                    </h6>
                    <div class="mt-auto">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="price-tag">${formatPrice(product.price)}</span>
                        </div>
                        <small class="text-muted">
                            <i class="${platformIcon} me-1"></i>${platformName}
                        </small>
                    </div>
                </div>
            </div>
        `;
        
        fragment.appendChild(productCard);
    });
    
    // 一次性更新 DOM
    container.innerHTML = '';
    container.appendChild(fragment);
    
    // 簡單記錄圖片載入狀況
    console.log(`顯示 ${pageProducts.length} 個商品，頁面 ${currentPage}`);
}

// 獲取平台顯示名稱
function getPlatformDisplayName(platform) {
    switch(platform) {
        case 'pchome_onsale':
            return 'PChome 線上購物';
        case 'yahoo_rushbuy':
            return 'Yahoo 秒殺時時樂';
        default:
            return '未知平台';
    }
}

// 獲取平台圖標
function getPlatformIcon(platform) {
    switch(platform) {
        case 'pchome_onsale':
            return 'fas fa-shopping-cart';
        case 'yahoo_rushbuy':
            return 'fas fa-bolt';
        default:
            return 'fas fa-store';
    }
}

// 設定分頁
function setupPagination() {
    const totalPages = Math.ceil(currentDeals.length / itemsPerPage);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHtml = '';
    
    // 上一頁
    paginationHtml += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="goToPage(${currentPage - 1})">上一頁</a>
        </li>
    `;
    
    // 頁碼
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="goToPage(${i})">${i}</a>
            </li>
        `;
    }
    
    // 下一頁
    paginationHtml += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="goToPage(${currentPage + 1})">下一頁</a>
        </li>
    `;
    
    pagination.innerHTML = paginationHtml;
}

// 跳轉到指定頁面
function goToPage(page) {
    const totalPages = Math.ceil(currentDeals.length / itemsPerPage);
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        displayProducts();
        setupPagination();
        window.scrollTo(0, 0);
    }
}

// 顯示商品詳情
function showProductDetail(productJson) {
    try {
        const product = JSON.parse(productJson);
        const platform = product.source_platform || product.platform;
        const platformName = getPlatformDisplayName(platform);
        const platformIcon = getPlatformIcon(platform);
        
        // 根據平台設定按鈕文字和顏色
        let buttonText, buttonColor, alertText;
        if (platform === 'yahoo_rushbuy') {
            buttonText = '在 Yahoo 購物中心查看';
            buttonColor = 'danger';
            alertText = '這是來自 Yahoo 秒殺時時樂的促銷商品，價格和庫存可能隨時變動。';
        } else {
            buttonText = '在 PChome 查看';
            buttonColor = 'primary';
            alertText = '這是來自 PChome 線上購物的每日促銷商品，價格和庫存可能隨時變動。';
        }
        
        document.getElementById('productModalTitle').textContent = product.title;
        
        // 創建模態框內容
        const modalBody = document.getElementById('productModalBody');
        modalBody.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="text-center">
                        <img class="img-fluid rounded" alt="${product.title}"
                             style="background-color: #f8f9fa; min-height: 300px; width: 100%; object-fit: cover;">
                    </div>
                </div>
                <div class="col-md-6">
                    <h4 class="text-primary">${product.title}</h4>
                    <hr>
                    <div class="mb-3">
                        <h3 class="text-danger">
                            <i class="fas fa-tag me-2"></i>${formatPrice(product.price)}
                        </h3>
                    </div>
                    <div class="mb-3">
                        <strong><i class="${platformIcon} me-2"></i>平台：</strong>
                        <span class="badge bg-${buttonColor}">${platformName}</span>
                    </div>
                    <div class="mb-3">
                        <strong><i class="fas fa-fire me-2"></i>促銷類型：</strong>
                        <span class="badge bg-danger">每日特惠</span>
                    </div>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        ${alertText}
                    </div>
                </div>
            </div>
        `;
        
        // 延遲載入模態框圖片
        setTimeout(() => {
            const modalImg = modalBody.querySelector('img');
            if (modalImg && product.image_url) {
                modalImg.src = product.image_url;
                modalImg.onload = function() {
                    this.style.transition = 'opacity 0.3s ease';
                    this.style.opacity = '1';
                };
                modalImg.onerror = function() {
                    handleImageError(this);
                };
            }
        }, 100);
        
        // 動態更新按鈕
        const viewButton = document.getElementById('viewOnPlatform');
        viewButton.href = product.url;
        viewButton.innerHTML = `<i class="fas fa-external-link-alt me-2"></i>${buttonText}`;
        viewButton.className = `btn btn-${buttonColor}`;
        
        new bootstrap.Modal(document.getElementById('productModal')).show();
    } catch (error) {
        console.error('Error showing product detail:', error);
        showError('顯示商品詳情時發生錯誤');
    }
}

// 應用篩選
function applyFilters() {
    const searchTerm = document.getElementById('searchProduct').value.trim();
    const priceFilter = document.getElementById('priceFilter').value;
    
    // 如果有搜尋關鍵字，可以選擇使用 API 搜尋或本地篩選
    if (searchTerm && searchTerm.length >= 2) {
        // 對於關鍵字搜尋，先嘗試本地篩選
        performLocalSearch(searchTerm, priceFilter);
        
        // 可選：同時執行 API 搜尋來獲得更多結果
        // performAPISearch(searchTerm, priceFilter);
    } else {
        performLocalSearch(searchTerm, priceFilter);
    }
}

// 執行本地搜尋（適用於已載入的促銷商品）
function performLocalSearch(searchTerm = '', priceFilter = '') {
    const searchLower = searchTerm.toLowerCase();
    
    currentDeals = allDeals.filter(product => {
        // 搜尋篩選
        const matchesSearch = !searchLower || 
            product.title.toLowerCase().includes(searchLower) ||
            (product.description && product.description.toLowerCase().includes(searchLower));
        
        // 價格篩選
        let matchesPrice = true;
        if (priceFilter) {
            const price = parsePrice(product.price);
            const [minPrice, maxPrice] = priceFilter.split('-').map(Number);
            matchesPrice = price >= minPrice && price <= maxPrice;
        }
        
        return matchesSearch && matchesPrice;
    });
    
    currentPage = 1;
    displayProducts();
    setupPagination();
    
    // 更新搜尋統計
    if (searchTerm) {
        updateSearchInfo(currentDeals.length, searchTerm);
    }
}

// 執行 API 搜尋（可選功能，用於擴展搜尋結果）
async function performAPISearch(keyword, priceFilter = '') {
    if (!keyword.trim()) return;
    
    try {
        const params = new URLSearchParams({
            keyword: keyword,
            limit: 50
        });
        
        if (currentPlatform && currentPlatform !== 'all') {
            params.append('platform', currentPlatform);
        }

        const response = await fetch(`/api/search?${params}`);
        const data = await response.json();

        if (data.status === 'success' && data.products.length > 0) {
            // 將 API 搜尋結果加入到當前結果中（去重）
            const existingTitles = new Set(currentDeals.map(p => p.title));
            const newProducts = data.products.filter(p => !existingTitles.has(p.title));
            
            if (newProducts.length > 0) {
                currentDeals = [...currentDeals, ...newProducts];
                displayProducts();
                setupPagination();
            }
        }
    } catch (error) {
        console.error('API 搜尋錯誤:', error);
    }
}

// 更新搜尋資訊顯示
function updateSearchInfo(count, keyword) {
    const searchInfo = document.getElementById('searchInfo');
    if (searchInfo) {
        searchInfo.textContent = `找到 ${count} 個包含「${keyword}」的商品`;
        searchInfo.style.display = 'block';
    }
}

// 重新整理促銷商品
// 格式化價格顯示
function formatPrice(price) {
    if (typeof price === 'number') {
        return `$${price.toLocaleString()}`;
    }
    if (typeof price === 'string') {
        // 如果已經有 $ 符號，直接返回
        if (price.startsWith('$')) {
            return price;
        }
        // 嘗試解析為數字後格式化
        const numPrice = parseInt(price.replace(/[,$]/g, ''));
        if (!isNaN(numPrice)) {
            return `$${numPrice.toLocaleString()}`;
        }
    }
    return price;
}

// 解析價格字串
function parsePrice(priceStr) {
    if (!priceStr) return 0;
    if (typeof priceStr === 'number') return priceStr;
    return parseInt(priceStr.replace(/[,$]/g, '')) || 0;
}

// 截斷文字
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// HTML 轉義
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// 顯示載入動畫
function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'block' : 'none';
}

// 顯示錯誤訊息
function showError(message) {
    const emptyMessage = document.getElementById('emptyMessage');    emptyMessage.innerHTML = `
        <i class="fas fa-exclamation-triangle fa-3x mb-3 text-warning"></i>
        <h4>${message}</h4>
        <button class="btn btn-primary" onclick="loadDailyDeals()">重試</button>
    `;
    emptyMessage.style.display = 'block';
}

// 已移除手動更新函數，改為完全自動更新 (每 6 小時更新一次)

// 顯示成功訊息的輔助函數
function showSuccess(message) {
    // 創建成功提示
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 插入到頁面頂部
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 3秒後自動消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// 搜尋輸入框即時搜尋
document.getElementById('searchProduct').addEventListener('input', function() {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(applyFilters, 500);
});

// 價格篩選變更時自動應用
document.getElementById('priceFilter').addEventListener('change', applyFilters);

// 圖片載入成功處理
function handleImageLoad(img) {
    img.style.opacity = '1';
    img.classList.remove('loading', 'error');
}

// 圖片載入失敗處理
function handleImageError(img) {
    console.log('圖片載入失敗處理:', img.src);
    img.classList.add('error');
    img.style.opacity = '1';
    img.style.transition = 'opacity 0.3s ease';
    
    // 使用更簡潔的預設圖片
    const width = img.clientWidth || 300;
    const height = img.clientHeight || 200;
    
    img.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
        <rect width="${width}" height="${height}" fill="%23f8f9fa"/>
        <circle cx="${width/2}" cy="${height/2-20}" r="30" fill="%23dee2e6"/>
        <path d="M${width/2-15} ${height/2-25} L${width/2+15} ${height/2-15} L${width/2} ${height/2-5} Z" fill="%23adb5bd"/>
        <text x="${width/2}" y="${height/2+15}" text-anchor="middle" font-family="Arial" font-size="12" fill="%236c757d">圖片無法載入</text>
        <text x="${width/2}" y="${height/2+30}" text-anchor="middle" font-family="Arial" font-size="10" fill="%23adb5bd">點擊查看詳情</text>
    </svg>`;
}

// 測試特定圖片URL
function testImageUrl(url) {
    console.log('測試圖片URL:', url);
    const img = new Image();
    img.onload = function() {
        console.log('✅ 圖片可載入:', url);
    };
    img.onerror = function() {
        console.log('❌ 圖片載入失敗:', url);
    };
    img.src = url;
    return img;
}

// 預載入圖片
function preloadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
        img.src = src;
    });
}
