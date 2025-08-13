// 每日促銷頁面的 JavaScript 功能

let allDeals = [];
let currentDeals = [];
let currentPage = 1;
const itemsPerPage = 16;
let currentPlatform = 'all';

// 頁面載入時初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('頁面已載入，開始初始化');
    try {
        loadDailyDeals('all');
        checkIfUpdateInProgress();
    } catch (error) {
        console.error('初始化錯誤:', error);
        showError('頁面初始化失敗: ' + error.message);
    }
});

// 平台切換功能
function switchPlatform(platform) {
    console.log('切換平台:', platform);
    
    // 更新按鈕狀態
    document.querySelectorAll('[data-platform]').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(`[data-platform="${platform}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
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
    
    if (description) {
        switch(platform) {
            case 'pchome_onsale':
                description.textContent = '精選 PChome 線上購物每日特價商品';
                if (platformInfo) platformInfo.textContent = 'PChome';
                break;
            case 'yahoo_rushbuy':
                description.textContent = '精選 Yahoo 秒殺時時樂特價商品';
                if (platformInfo) platformInfo.textContent = 'Yahoo秒殺';
                break;
            default:
                description.textContent = '精選各大平台每日特價商品';
                if (platformInfo) platformInfo.textContent = '全部平台';
        }
    }
}

// 載入每日促銷資料
async function loadDailyDeals(platform = 'all') {
    console.log('載入每日促銷資料，平台:', platform);
    showLoading(true);
    
    try {
        const url = `/api/daily-deals${platform !== 'all' ? `?platform=${platform}` : ''}`;
        console.log('請求 URL:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('API 回應:', data);
        
        if (data.status === 'success') {
            allDeals = data.daily_deals.map(product => ({
                ...product,
                source_platform: product.platform,
                title: (product.title || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;'),
                price: product.price || 'N/A',
                image_url: product.image_url || 'https://via.placeholder.com/300x200?text=無圖片'
            }));
            
            currentDeals = [...allDeals];
            console.log('處理後的商品數量:', allDeals.length);
            
            updateStats(data);
            displayProducts();
            setupPagination();
        } else {
            console.error('API 回應錯誤:', data);
            showError('載入促銷商品失敗: ' + (data.message || '未知錯誤'));
        }
    } catch (error) {
        console.error('Error loading daily deals:', error);
        showError('載入促銷商品時發生錯誤: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// 圖片預載入函數
function preloadImage(url) {
    return new Promise((resolve, reject) => {
        if (!url || url === 'https://via.placeholder.com/200x150?text=無圖片') {
            reject('無效的圖片URL');
            return;
        }
        
        const img = new Image();
        img.onload = () => resolve(url);
        img.onerror = () => reject('圖片載入失敗');
        img.src = url;
        
        // 設定超時
        setTimeout(() => {
            reject('圖片載入超時');
        }, 5000);
    });
}

// 格式化時間顯示
function formatDateTime(dateTimeStr) {
    if (!dateTimeStr || dateTimeStr === '未知') {
        return '未知';
    }
    
    try {
        const date = new Date(dateTimeStr);
        if (isNaN(date.getTime())) {
            return '未知';
        }
        
        // 格式化為台灣時間格式：YYYY/MM/DD HH:mm
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}/${month}/${day} ${hours}:${minutes}`;
    } catch (error) {
        console.error('時間格式化錯誤:', error);
        return '未知';
    }
}

// 格式化價格顯示
function formatPrice(price, withHtml = false) {
    if (!price || price === 'N/A' || price === '未知') {
        return '價格未知';
    }
    
    // 如果價格已經包含貨幣符號，直接返回
    if (typeof price === 'string' && (price.includes('NT$') || price.includes('$') || price.includes('元'))) {
        return price;
    }
    
    // 移除非數字字符並嘗試解析
    const cleanPrice = price.toString().replace(/[^\d.-]/g, '');
    const numPrice = parseFloat(cleanPrice);
    
    if (isNaN(numPrice)) {
        return price; // 如果無法解析，返回原始值
    }
    
    // 格式化為台幣格式
    if (withHtml) {
        return `<span class="currency">NT$</span> ${numPrice.toLocaleString()}`;
    } else {
        return `NT$ ${numPrice.toLocaleString()}`;
    }
}

// 更新統計資訊
function updateStats(data) {
    console.log('更新統計資訊:', data);
    
    const totalDealsEl = document.getElementById('totalDeals');
    const lastUpdateEl = document.getElementById('lastUpdate');
    const priceRangeEl = document.getElementById('priceRange');
    
    if (totalDealsEl) {
        totalDealsEl.textContent = data.total_deals || allDeals.length;
    }
    
    if (lastUpdateEl) {
        lastUpdateEl.textContent = formatDateTime(data.last_update);
    }
    
    // 計算價格範圍
    if (priceRangeEl && allDeals.length > 0) {
        const prices = allDeals.map(product => {
            const cleanPrice = product.price.toString().replace(/[^\d.-]/g, '');
            return parseFloat(cleanPrice) || 0;
        }).filter(price => price > 0);
        
        if (prices.length > 0) {
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            priceRangeEl.textContent = `NT$ ${minPrice.toLocaleString()} - NT$ ${maxPrice.toLocaleString()}`;
        } else {
            priceRangeEl.textContent = '-';
        }
    }
}

// 顯示商品
function displayProducts() {
    console.log('顯示商品，數量:', currentDeals.length);
    
    const container = document.getElementById('productsContainer');
    const emptyMessage = document.getElementById('emptyMessage');
    
    if (!container) {
        console.error('找不到商品容器');
        return;
    }
    
    if (currentDeals.length === 0) {
        container.innerHTML = '';
        if (emptyMessage) emptyMessage.style.display = 'block';
        return;
    }
    
    if (emptyMessage) emptyMessage.style.display = 'none';
    
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageDeals = currentDeals.slice(startIndex, endIndex);
    
    console.log(`顯示第 ${currentPage} 頁商品，範圍: ${startIndex}-${endIndex}，商品數: ${pageDeals.length}`);
    
    container.innerHTML = pageDeals.map((product, index) => `
        <div class="col-lg-3 col-md-4 col-sm-6 mb-4">
            <div class="card product-card h-100" onclick="showProductDetail(${startIndex + index})">
                <div class="position-relative">
                    <img src="${product.image_url}" class="card-img-top product-image" 
                         alt="${product.title}" 
                         loading="lazy"
                         style="background-color: #f8f9fa;"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="d-none justify-content-center align-items-center product-image" style="background-color: #f8f9fa;">
                        <span class="text-muted text-center">
                            <i class="fas fa-image fa-2x"></i>
                            <br><small>圖片載入失敗</small>
                        </span>
                    </div>
                    <span class="deal-badge">${getPlatformDisplayName(product.source_platform)}</span>
                </div>
                <div class="card-body d-flex flex-column">
                    <h6 class="card-title" title="${product.title}">${product.title}</h6>
                    <div class="mt-auto">
                        <div class="price-tag mb-2">${formatPrice(product.price)}</div>
                        <small class="text-muted">
                            <i class="${getPlatformIcon(product.source_platform)} me-1"></i>
                            ${getPlatformDisplayName(product.source_platform)}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// 獲取平台顯示名稱
function getPlatformDisplayName(platform) {
    switch(platform) {
        case 'pchome_onsale': return 'PChome特價';
        case 'yahoo_rushbuy': return 'Yahoo秒殺';
        default: return platform || '未知平台';
    }
}

// 獲取平台圖示
function getPlatformIcon(platform) {
    switch(platform) {
        case 'pchome_onsale': return 'fas fa-shopping-cart';
        case 'yahoo_rushbuy': return 'fas fa-bolt';
        default: return 'fas fa-store';
    }
}

// 設置分頁
function setupPagination() {
    const totalPages = Math.ceil(currentDeals.length / itemsPerPage);
    const paginationEl = document.getElementById('pagination');
    
    if (!paginationEl) return;
    
    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // 上一頁
    if (currentPage > 1) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${currentPage - 1})">上一頁</a></li>`;
    }
    
    // 頁碼
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
            paginationHTML += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${i})">${i}</a></li>`;
        }
    }
    
    // 下一頁
    if (currentPage < totalPages) {
        paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${currentPage + 1})">下一頁</a></li>`;
    }
    
    paginationEl.innerHTML = paginationHTML;
}

// 跳轉頁面
function goToPage(page) {
    currentPage = page;
    displayProducts();
    setupPagination();
    window.scrollTo(0, 0);
}

// 顯示/隱藏載入中
function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

// 顯示錯誤訊息
function showError(message) {
    console.error('錯誤:', message);
    
    const container = document.getElementById('productsContainer');
    if (container) {
        container.innerHTML = `
            <div class="col-12">
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            </div>
        `;
    }
}

// 顯示商品詳情（完整版，包含商品比較）
async function showProductDetail(productIndex) {
    console.log('顯示商品詳情:', productIndex);
    
    if (productIndex < 0 || productIndex >= currentDeals.length) {
        console.error('商品索引無效:', productIndex);
        return;
    }
    
    const product = currentDeals[productIndex];
    console.log('選中的商品:', product);
    
    // 設定模態框標題
    const modalTitle = document.getElementById('productModalTitle');
    if (modalTitle) {
        modalTitle.textContent = product.title || '商品詳情';
    }
    
    // 設定查看平台連結
    const viewOnPlatform = document.getElementById('viewOnPlatform');
    if (viewOnPlatform && product.url) {
        viewOnPlatform.href = product.url;
        viewOnPlatform.style.display = 'inline-block';
    } else if (viewOnPlatform) {
        viewOnPlatform.style.display = 'none';
    }
    
    // 生成基本商品資訊
    const baseContent = `
        <div class="row">
            <div class="col-md-4">
                <img src="${product.image_url || 'https://via.placeholder.com/300x200?text=無圖片'}" 
                     class="img-fluid rounded" alt="${product.title}" 
                     onerror="this.src='https://via.placeholder.com/300x200?text=無圖片'">
            </div>
            <div class="col-md-8">
                <h4>${product.title}</h4>
                <div class="row">
                    <div class="col-sm-6">
                        <p><strong>價格:</strong> <span class="badge bg-danger fs-6">${formatPrice(product.price)}</span></p>
                        <p><strong>平台:</strong> ${getPlatformDisplayName(product.source_platform)}</p>
                        <p><strong>更新時間:</strong> ${formatDateTime(product.crawl_time)}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <a href="${product.url}" target="_blank" class="btn btn-primary">
                        <i class="fas fa-external-link-alt me-2"></i>在 ${getPlatformDisplayName(product.source_platform)} 查看
                    </a>
                </div>
            </div>
        </div>
    `;
    
    // 設定模態框內容
    const modalBody = document.getElementById('productModalBody');
    if (modalBody) {
        modalBody.innerHTML = baseContent + `
            <hr>
            <div id="relatedProductsSection">
                <h5><i class="fas fa-search me-2"></i>正在尋找相關商品...</h5>
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">搜尋中...</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    // 顯示模態框
    const modal = new bootstrap.Modal(document.getElementById('productModal'));
    modal.show();
    
    // 異步載入相關商品
    try {
        const result = await findRelatedProducts(product);
        updateModalWithRelatedProducts(product, result.products, result);
    } catch (error) {
        console.error('載入相關商品失敗:', error);
        const relatedSection = document.getElementById('relatedProductsSection');
        if (relatedSection) {
            relatedSection.innerHTML = `
                <h5><i class="fas fa-exclamation-triangle text-warning me-2"></i>相關商品載入失敗</h5>
                <p class="text-muted">無法載入相關商品資訊: ${error.message}</p>
                <div class="alert alert-info mt-2">
                    <small>
                        <strong>可能的原因：</strong><br>
                        • Gemini AI API 未配置或配額不足<br>
                        • 資料庫中沒有足夠的商品資料<br>
                        • 網路連線問題
                    </small>
                </div>
            `;
        }
    }
}

// 尋找相關商品
async function findRelatedProducts(product) {
    console.log('開始尋找相關商品:', product.title);
    
    try {
        const requestData = {
            productName: product.title,
            platform: product.source_platform,
            price: product.price,
            url: product.url
        };
        
        console.log('發送商品比較請求:', requestData);
        
        const response = await fetch('/api/products/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('API 回應狀態:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API 錯誤回應:', errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('相關商品 API 回應:', data);
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 檢查是否有訊息（例如沒有資料的情況）
        if (data.message) {
            console.warn('API 訊息:', data.message);
        }
        
        return {
            products: data.similarProducts || [],
            totalCandidates: data.totalCandidates || 0,
            totalMatches: data.totalMatches || 0,
            message: data.message
        };
        
    } catch (error) {
        console.error('尋找相關商品時發生錯誤:', error);
        throw error;
    }
}

// 更新模態框中的相關商品區域
function updateModalWithRelatedProducts(originalProduct, relatedProducts, result = {}) {
    const relatedSection = document.getElementById('relatedProductsSection');
    if (!relatedSection) return;
    
    // 調試：檢查相關商品資料
    console.log('相關商品資料:', relatedProducts);
    if (relatedProducts.length > 0) {
        console.log('第一個相關商品的圖片URL:', relatedProducts[0].image_url);
    }
    
    // 顯示統計資訊
    const stats = result.totalCandidates ? 
        `（從 ${result.totalCandidates} 個候選商品中找到 ${result.totalMatches || 0} 個匹配）` : '';
    
    if (!relatedProducts || relatedProducts.length === 0) {
        const message = result.message || '目前資料庫中沒有找到與此商品相似的其他商品。';
        relatedSection.innerHTML = `
            <h5><i class="fas fa-info-circle text-info me-2"></i>沒有找到相關商品</h5>
            <p class="text-muted">${message}</p>
            ${stats ? `<small class="text-muted">${stats}</small>` : ''}
        `;
        return;
    }
    
    const relatedHTML = relatedProducts.slice(0, 6).map(product => {
        const priceDiff = calculatePriceDifference(originalProduct.price, product.price);
        const similarityBadge = getSimilarityBadge(product.similarity);
        
        // 確保圖片URL有效
        const imageUrl = product.image_url && product.image_url !== '' ? 
            product.image_url : 
            'https://via.placeholder.com/200x150/f8f9fa/6c757d?text=無圖片';
        
        console.log(`商品 ${product.title?.substring(0, 20)}... 的圖片URL: ${imageUrl}`);
        
        return `
            <div class="col-md-4 mb-3">
                <div class="card h-100 related-product-card" onclick="window.open('${product.url}', '_blank')">
                    <div class="position-relative" style="height: 120px; overflow: hidden;">
                        <img src="${imageUrl}" 
                             class="card-img-top w-100 h-100" 
                             style="object-fit: cover; background-color: #f8f9fa;" 
                             alt="${product.title}" 
                             loading="lazy"
                             onload="this.style.opacity='1';"
                             onerror="console.log('圖片載入失敗:', this.src); this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <div class="d-none justify-content-center align-items-center w-100 h-100 position-absolute top-0 start-0" style="background-color: #f8f9fa;">
                            <span class="text-muted text-center">
                                <i class="fas fa-image fa-lg"></i>
                                <br><small>圖片無法載入</small>
                            </span>
                        </div>
                    </div>
                    <div class="card-body">
                        <h6 class="card-title" title="${product.title}">${product.title.length > 40 ? product.title.substring(0, 40) + '...' : product.title}</h6>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-primary">${formatPrice(product.price)}</span>
                            ${similarityBadge}
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">${product.platform}</small>
                            ${priceDiff.html}
                        </div>
                        <div class="mt-2">
                            <small class="text-muted" title="${product.reason || ''}">
                                ${(product.reason || '').length > 50 ? 
                                  (product.reason || '').substring(0, 50) + '...' : 
                                  (product.reason || '')}
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    relatedSection.innerHTML = `
        <h5><i class="fas fa-layer-group text-success me-2"></i>找到 ${relatedProducts.length} 個相關商品</h5>
        ${stats ? `<small class="text-muted mb-3 d-block">${stats}</small>` : ''}
        <div class="row">
            ${relatedHTML}
        </div>
        ${relatedProducts.length > 6 ? `<p class="text-muted mt-2">還有 ${relatedProducts.length - 6} 個相關商品未顯示</p>` : ''}
    `;
}

// 計算價格差異
function calculatePriceDifference(originalPrice, comparePrice) {
    const original = parseFloat(originalPrice.toString().replace(/[^\d.]/g, '')) || 0;
    const compare = parseFloat(comparePrice.toString().replace(/[^\d.]/g, '')) || 0;
    
    if (original === 0 || compare === 0) {
        return { difference: 0, html: '' };
    }
    
    const diff = compare - original;
    const percentage = ((diff / original) * 100).toFixed(1);
    
    if (Math.abs(diff) < 1) {
        return { difference: diff, html: '<small class="text-muted">價格相近</small>' };
    }
    
    if (diff > 0) {
        return { 
            difference: diff, 
            html: `<small class="text-danger">+$${diff.toFixed(0)} (+${percentage}%)</small>` 
        };
    } else {
        return { 
            difference: diff, 
            html: `<small class="text-success">-$${Math.abs(diff).toFixed(0)} (${percentage}%)</small>` 
        };
    }
}

// 獲取相似度徽章
function getSimilarityBadge(similarity) {
    const sim = parseFloat(similarity) || 0;
    
    if (sim >= 0.95) {
        return '<span class="badge bg-success" title="完全相同">100%</span>';
    } else if (sim >= 0.85) {
        return `<span class="badge bg-success" title="高度相似">${Math.round(sim * 100)}%</span>`;
    } else if (sim >= 0.75) {
        return `<span class="badge bg-warning" title="部分相似">${Math.round(sim * 100)}%</span>`;
    } else {
        return `<span class="badge bg-secondary" title="低相似度">${Math.round(sim * 100)}%</span>`;
    }
}

// 更新每日促銷商品數據
async function updateDailyDeals() {
    console.log('開始更新每日促銷商品');
    
    const updateButton = document.getElementById('updateButton');
    const updateIcon = document.getElementById('updateIcon');
    
    if (updateButton) {
        updateButton.disabled = true;
        updateButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>更新中...';
    }
    
    try {
        const response = await fetch('/api/update-daily-deals', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log('更新成功');
            alert('每日促銷更新已開始！\n\n系統將：\n1. 更新每日促銷商品\n2. 自動爬取相關商品豐富比較資料庫\n\n預計需要3-5分鐘完成。');
            setTimeout(() => {
                loadDailyDeals(currentPlatform);
            }, 1000);
        } else {
            console.error('更新失敗:', data.message);
            showError('更新失敗: ' + data.message);
        }
    } catch (error) {
        console.error('更新錯誤:', error);
        showError('更新時發生錯誤: ' + error.message);
    } finally {
        if (updateButton) {
            updateButton.disabled = false;
            updateButton.innerHTML = '<i class="fas fa-sync-alt me-1"></i>立即更新';
        }
    }
}

// 豐富商品資料庫
async function enrichProductDatabase() {
    console.log('開始豐富商品資料庫');
    
    const enrichButton = document.getElementById('enrichButton');
    
    if (enrichButton) {
        enrichButton.disabled = true;
        enrichButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>豐富中...';
    }
    
    try {
        const response = await fetch('/api/enrich-product-database', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log('資料庫豐富化已開始');
            alert('商品資料庫豐富化已開始！\n\n這將爬取多個熱門關鍵字的商品來豐富比較資料庫，\n預計需要5-10分鐘完成。\n\n完成後您可以獲得更好的商品比較結果。');
        } else {
            console.error('豐富化失敗:', data.message);
            alert('豐富化失敗: ' + data.message);
        }
    } catch (error) {
        console.error('豐富化錯誤:', error);
        alert('豐富化時發生錯誤: ' + error.message);
    } finally {
        if (enrichButton) {
            enrichButton.disabled = false;
            enrichButton.innerHTML = '<i class="fas fa-database me-1"></i>豐富資料庫';
        }
    }
}

// 檢查爬蟲狀態
async function checkCrawlerStatus() {
    try {
        const response = await fetch('/api/daily-deals/status');
        const data = await response.json();
        
        alert(`爬蟲狀態: ${data.status}\n最後更新: ${formatDateTime(data.last_update)}\n商品數量: ${data.total_deals || 0}`);
    } catch (error) {
        console.error('檢查狀態錯誤:', error);
        alert('檢查狀態時發生錯誤: ' + error.message);
    }
}

// 檢查是否有更新正在進行
async function checkIfUpdateInProgress() {
    try {
        const response = await fetch('/api/daily-deals/status');
        const data = await response.json();
        
        if (data.is_updating) {
            console.log('檢測到更新正在進行中');
            // 可以在這裡顯示更新狀態
        }
    } catch (error) {
        console.error('檢查更新狀態錯誤:', error);
    }
}

// 重新整理商品
function refreshDeals() {
    loadDailyDeals(currentPlatform);
}

// 應用篩選器（簡化版）
function applyFilters() {
    const searchInput = document.getElementById('searchProduct');
    const priceFilter = document.getElementById('priceFilter');
    
    let filteredDeals = [...allDeals];
    
    // 搜尋篩選
    if (searchInput && searchInput.value.trim()) {
        const searchTerm = searchInput.value.trim().toLowerCase();
        filteredDeals = filteredDeals.filter(product => 
            product.title.toLowerCase().includes(searchTerm)
        );
    }
    
    // 價格篩選
    if (priceFilter && priceFilter.value) {
        const priceRange = priceFilter.value.split('-');
        const minPrice = parseInt(priceRange[0]);
        const maxPrice = parseInt(priceRange[1]);
        
        filteredDeals = filteredDeals.filter(product => {
            const price = parseFloat(product.price.replace(/[^\d.]/g, '')) || 0;
            return price >= minPrice && price <= maxPrice;
        });
    }
    
    currentDeals = filteredDeals;
    currentPage = 1;
    displayProducts();
    setupPagination();
}

console.log('daily_deals.js 載入完成');
