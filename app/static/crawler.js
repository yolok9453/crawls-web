// 爬蟲執行頁面的JavaScript功能
let availableCrawlers = [];
let currentResults = null;
let allProducts = [];
let filteredProducts = [];
let currentView = 'card';
let currentPage = 1;
const itemsPerPage = 12;

// 事件綁定
document.addEventListener("DOMContentLoaded", function () {
  // 初始化爬蟲平台列表
  loadCrawlers();
  
  // 設定表單處理器
  setupFormHandlers();
  
  // 篩選器事件監聽
  const platformFilter = document.getElementById("platformFilter");
  const minPriceFilter = document.getElementById("minPriceFilter");
  const maxPriceFilter = document.getElementById("maxPriceFilter");
  const sortSelect = document.getElementById("sortSelect");
  
  if (platformFilter) {
    platformFilter.addEventListener('change', filterAndSortProducts);
  }
  
  if (minPriceFilter) {
    minPriceFilter.addEventListener('input', debounce(filterAndSortProducts, 300));
  }
  
  if (maxPriceFilter) {
    maxPriceFilter.addEventListener('input', debounce(filterAndSortProducts, 300));
  }
  
  if (sortSelect) {
    sortSelect.addEventListener('change', filterAndSortProducts);
  }
  
  // 如果有緩存的結果，顯示它們
  if (cachedResults) {
    showResults(cachedResults);
  }
});

// 防抖函數
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// 載入可用的爬蟲
async function loadCrawlers() {
  console.log("開始載入爬蟲列表...");
  try {
    const response = await fetch("/api/crawlers");
    console.log("API回應狀態:", response.status);
    const data = await response.json();
    console.log("API回應數據:", data);

    if (data.status === "success") {
      availableCrawlers = data.crawlers;
      console.log("已載入爬蟲:", availableCrawlers);
      renderCrawlerOptions();
    } else {
      console.error("載入爬蟲列表失敗");
    }
  } catch (error) {
    console.error("載入爬蟲列表時發生錯誤:", error);
    // 如果API失敗，使用預設爬蟲列表
    availableCrawlers = ["pchome", "yahoo", "carrefour", "routn"];
    console.log("使用預設爬蟲列表:", availableCrawlers);
    renderCrawlerOptions();
  }
}

// 渲染爬蟲選項
function renderCrawlerOptions() {
  console.log("開始渲染爬蟲選項，爬蟲列表:", availableCrawlers);
  const container = document.getElementById("platformsList");
  
  if (!container) {
    console.error("找不到 platformsList 容器!");
    return;
  }
  
  container.innerHTML = "";

  availableCrawlers.forEach((crawler) => {
    console.log("添加爬蟲選項:", crawler);
    const div = document.createElement("div");
    div.className = "form-check";

    div.innerHTML = `
            <input class="form-check-input platform-checkbox" type="checkbox" 
                   value="${crawler}" id="platform_${crawler}" checked>
            <label class="form-check-label" for="platform_${crawler}">
                <i class="fas fa-shopping-cart me-2"></i>
                ${getPlatformDisplayName(crawler)}
            </label>
        `;

    container.appendChild(div);
  });
  
  console.log("爬蟲選項渲染完成");
}

// 獲取平台顯示名稱
function getPlatformDisplayName(platform) {
  const names = {
    'pchome': 'PChome',
    'yahoo': 'Yahoo購物',
    'carrefour': '家樂福',
    'routn': '露天拍賣'
  };
  return names[platform?.toLowerCase()] || platform?.toUpperCase() || '未知平台';
}

// 設定表單處理器
function setupFormHandlers() {
  // 全選功能
  document.getElementById("selectAll").addEventListener("change", function () {
    const checkboxes = document.querySelectorAll(".platform-checkbox");
    checkboxes.forEach((checkbox) => {
      checkbox.checked = this.checked;
    });
  });

  // 個別平台選擇
  document.addEventListener("change", function (e) {
    if (e.target.classList.contains("platform-checkbox")) {
      updateSelectAllState();
    }
  });

  // 表單提交
  document
    .getElementById("crawlerForm")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      startCrawl();
    });
}

// 更新全選狀態
function updateSelectAllState() {
  const checkboxes = document.querySelectorAll(".platform-checkbox");
  const selectAllCheckbox = document.getElementById("selectAll");
  const checkedCount = document.querySelectorAll(
    ".platform-checkbox:checked"
  ).length;

  if (checkedCount === checkboxes.length) {
    selectAllCheckbox.checked = true;
    selectAllCheckbox.indeterminate = false;
  } else if (checkedCount === 0) {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;
  } else {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = true;
  }
}

// 開始爬蟲
async function startCrawl() {
  // 獲取表單資料
  const keyword = document.getElementById("keyword").value.trim();
  const selectedPlatforms = Array.from(
    document.querySelectorAll(".platform-checkbox:checked")
  ).map((cb) => cb.value);
  
  // 獲取其他參數，如果元素不存在則使用默認值
  const maxProducts = document.getElementById("maxProducts") ? 
    parseInt(document.getElementById("maxProducts").value) : 100;
  const minPrice = document.getElementById("minPrice") ? 
    parseInt(document.getElementById("minPrice").value) : 0;
  const maxPrice = document.getElementById("maxPrice") ? 
    parseInt(document.getElementById("maxPrice").value) : 999999;

  // 驗證輸入
  if (!keyword) {
    alert("請輸入搜尋關鍵字");
    return;
  }

  if (selectedPlatforms.length === 0) {
    alert("請至少選擇一個爬蟲平台");
    return;
  }

  if (minPrice > maxPrice) {
    alert("最低價格不能大於最高價格");
    return;
  }

  // 顯示進度
  showProgress(true);
  updateProgressText("正在準備爬蟲任務...");

  try {
    const response = await fetch("/api/crawl", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        keyword: keyword,
        platforms: selectedPlatforms,
        max_products: maxProducts,
        min_price: minPrice,
        max_price: maxPrice,
      }),
    });

    const data = await response.json();

    if (data.status === "success") {
      currentResults = data;
      cachedResults = data;
      showProgress(false);
      showResults(data);
    } else {
      showProgress(false);
      showError(data.error || "爬蟲執行失敗");
    }
  } catch (error) {
    showProgress(false);
    showError("網路錯誤：" + error.message);
  }
}

// 顯示進度
function showProgress(show) {
  const progressCard = document.getElementById("progressCard");
  const resultCard = document.getElementById("resultCard");
  const startBtn = document.getElementById("startCrawlBtn");

  if (show) {
    progressCard.style.display = "block";
    resultCard.style.display = "none";
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>執行中...';
  } else {
    progressCard.style.display = "none";
    startBtn.disabled = false;
    startBtn.innerHTML = '<i class="fas fa-play me-2"></i>開始爬蟲';
  }
}

// 更新進度文字
function updateProgressText(text) {
  document.getElementById("progressText").textContent = text;
}

// 顯示結果
function showResults(data) {
  const resultCard = document.getElementById("resultCard");
  const summaryContainer = document.getElementById("resultSummary");
  
  // 設置搜尋關鍵字標題
  const keyword = document.getElementById("keyword").value.trim();
  document.getElementById("searchKeywordTitle").textContent = `「${keyword}」搜尋結果`;
  
  // 收集所有商品資料
  allProducts = [];
  let totalProducts = 0;
  let successCount = 0;
  let platforms = new Set();
  
  Object.entries(data.results || {}).forEach(([platform, result]) => {
    if (result.status === "success") {
      successCount++;
      totalProducts += result.total_products || 0;
      platforms.add(platform);
      
      // 將商品加入總列表
      if (result.products && Array.isArray(result.products)) {
        result.products.forEach(product => {
          allProducts.push({
            ...product,
            platform: platform,
            price_numeric: parsePrice(product.price)
          });
        });
      }
    }
  });
  
  // 計算價格範圍
  const prices = allProducts.map(p => p.price_numeric).filter(p => p > 0);
  const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
  const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;
  const avgPrice = prices.length > 0 ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : 0;
  
  // 更新摘要統計卡片
  summaryContainer.innerHTML = `
    <div class="col-lg-3 col-md-6 mb-3">
      <div class="card bg-primary text-white text-center">
        <div class="card-body">
          <h3>${allProducts.length}</h3>
          <p class="mb-0">總商品數</p>
        </div>
      </div>
    </div>
    <div class="col-lg-3 col-md-6 mb-3">
      <div class="card bg-success text-white text-center">
        <div class="card-body">
          <h3>${platforms.size}</h3>
          <p class="mb-0">平台數</p>
        </div>
      </div>
    </div>
    <div class="col-lg-3 col-md-6 mb-3">
      <div class="card bg-info text-white text-center">
        <div class="card-body">
          <h3>NT$ ${avgPrice.toLocaleString()}</h3>
          <p class="mb-0">平均價格</p>
        </div>
      </div>
    </div>
    <div class="col-lg-3 col-md-6 mb-3">
      <div class="card bg-warning text-white text-center">
        <div class="card-body">
          <h3>NT$ ${minPrice.toLocaleString()} - ${maxPrice.toLocaleString()}</h3>
          <p class="mb-0">價格範圍</p>
        </div>
      </div>
    </div>
  `;
  
  // 更新平台篩選下拉選單
  const platformFilter = document.getElementById("platformFilter");
  platformFilter.innerHTML = '<option value="all">全部平台</option>';
  
  platforms.forEach(platform => {
    const option = document.createElement("option");
    option.value = platform;
    option.textContent = getPlatformDisplayName(platform);
    platformFilter.appendChild(option);
  });
  
  // 初始化商品顯示
  filteredProducts = [...allProducts];
  currentPage = 1;
  filterAndSortProducts();
  
  resultCard.style.display = "block";
  resultCard.scrollIntoView({ behavior: "smooth" });
}

// 解析價格字串為數字
function parsePrice(priceStr) {
  if (!priceStr) return 0;
  
  // 移除所有非數字和小數點的字符
  const numericStr = priceStr.toString().replace(/[^\d.]/g, '');
  const price = parseFloat(numericStr);
  
  return isNaN(price) ? 0 : price;
}

// 獲取平台顯示名稱
// 篩選和排序商品
function filterAndSortProducts() {
  const platformFilter = document.getElementById("platformFilter").value;
  const minPriceFilter = parseFloat(document.getElementById("minPriceFilter").value) || 0;
  const maxPriceFilter = parseFloat(document.getElementById("maxPriceFilter").value) || Infinity;
  const sortBy = document.getElementById("sortSelect").value;
  
  // 篩選商品
  filteredProducts = allProducts.filter(product => {
    const platformMatch = platformFilter === 'all' || product.platform === platformFilter;
    const priceMatch = product.price_numeric >= minPriceFilter && product.price_numeric <= maxPriceFilter;
    
    return platformMatch && priceMatch;
  });
  
  // 排序商品
  filteredProducts.sort((a, b) => {
    switch (sortBy) {
      case 'price-asc':
        return a.price_numeric - b.price_numeric;
      case 'price-desc':
        return b.price_numeric - a.price_numeric;
      case 'name-asc':
        return (a.title || '').localeCompare(b.title || '');
      case 'name-desc':
        return (b.title || '').localeCompare(a.title || '');
      default:
        return 0;
    }
  });
  
  // 重置到第一頁
  currentPage = 1;
  
  // 更新顯示
  updateProductDisplay();
  updatePagination();
}

// 切換顯示方式
function switchView(viewType) {
  currentView = viewType;
  
  // 更新按鈕狀態
  document.getElementById('cardViewBtn').classList.toggle('active', viewType === 'card');
  document.getElementById('listViewBtn').classList.toggle('active', viewType === 'list');
  
  // 切換顯示區域
  document.getElementById('cardView').style.display = viewType === 'card' ? 'block' : 'none';
  document.getElementById('listView').style.display = viewType === 'list' ? 'block' : 'none';
  
  // 更新商品顯示
  updateProductDisplay();
}

// 更新商品顯示
function updateProductDisplay() {
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const pageProducts = filteredProducts.slice(startIndex, endIndex);
  
  // 更新商品數量資訊
  const totalCount = filteredProducts.length;
  const showingStart = totalCount > 0 ? startIndex + 1 : 0;
  const showingEnd = Math.min(endIndex, totalCount);
  
  document.getElementById('productCount').textContent = 
    `顯示 ${showingStart}-${showingEnd} 個商品，共 ${totalCount} 個`;
  
  if (currentView === 'card') {
    displayCardView(pageProducts);
  } else {
    displayListView(pageProducts);
  }
}

// 顯示卡片視圖
function displayCardView(products) {
  const container = document.getElementById('cardView');
  
  if (products.length === 0) {
    container.innerHTML = `
      <div class="col-12">
        <div class="text-center text-muted py-5">
          <i class="fas fa-search fa-3x mb-3"></i>
          <p>沒有找到符合條件的商品</p>
        </div>
      </div>
    `;
    return;
  }
  
  container.innerHTML = products.map(product => `
    <div class="col-xl-3 col-lg-3 col-md-6 col-sm-6 col-12 mb-4 product-col">
      <div class="card product-card h-100 shadow-sm fade-in">
        <div class="position-relative">
          <img src="${product.image_url || 'https://via.placeholder.com/250x200?text=No+Image'}" 
               class="card-img-top" 
               alt="${product.title || 'No Title'}"
               style="height: 220px; object-fit: cover; border-radius: 12px 12px 0 0;"
               onerror="this.src='https://via.placeholder.com/250x200?text=No+Image'">
          <div class="position-absolute top-0 start-0 m-2">
            <span class="badge platform-${product.platform?.toLowerCase()} product-platform">
              ${getPlatformDisplayName(product.platform)}
            </span>
          </div>
        </div>
        <div class="card-body d-flex flex-direction-column p-3">
          <h6 class="product-title fw-semibold text-dark mb-2" title="${product.title || 'No Title'}">
            ${truncateText(product.title || 'No Title', 60)}
          </h6>
          <div class="product-price text-danger fw-bold fs-4 mb-3">
            NT$ ${formatPrice(product.price) || 'N/A'}
          </div>
          <div class="mt-auto d-grid">
            <a href="${product.url || '#'}" target="_blank" class="btn btn-primary btn-sm">
              <i class="fas fa-external-link-alt me-2"></i>查看商品
            </a>
          </div>
        </div>
      </div>
    </div>
  `).join('');
  
  // 添加載入動畫
  setTimeout(() => {
    container.querySelectorAll('.product-card').forEach((card, index) => {
      card.style.animationDelay = `${index * 0.1}s`;
      card.classList.add('slide-up');
    });
  }, 100);
}

// 輔助函數：截斷文字和清理內容
function truncateText(text, maxLength) {
  if (!text) return 'No Title';
  
  // 清理文字：移除多餘空白、特殊字符、重複詞語
  let cleanText = text
    .replace(/\s+/g, ' ') // 替換多個空白為單個空白
    .replace(/[^\u4e00-\u9fa5\u0800-\u4e00a-zA-Z0-9\s\-\_\(\)\[\]\/]/g, '') // 只保留中文、英文、數字、基本符號
    .trim(); // 移除首尾空白
  
  // 移除重複的詞語（簡單去重）
  const words = cleanText.split(' ');
  const uniqueWords = [];
  words.forEach(word => {
    if (word && !uniqueWords.includes(word)) {
      uniqueWords.push(word);
    }
  });
  cleanText = uniqueWords.join(' ');
  
  // 截斷文字
  if (cleanText.length <= maxLength) return cleanText;
  
  // 智能截斷：在完整詞語處截斷
  const truncated = cleanText.substring(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');
  
  if (lastSpace > maxLength * 0.7) {
    return truncated.substring(0, lastSpace) + '...';
  }
  
  return truncated + '...';
}

// 輔助函數：格式化價格顯示
function formatPrice(price) {
  if (!price || price === 'N/A') return 'N/A';
  
  let numericPrice;
  
  if (typeof price === 'number') {
    numericPrice = price;
  } else {
    // 如果是字串，提取數字（支援各種格式）
    const cleanPrice = price.toString()
      .replace(/[^\d.,]/g, '') // 只保留數字、逗號、點
      .replace(/,/g, ''); // 移除逗號
    
    numericPrice = parseFloat(cleanPrice);
  }
  
  // 檢查是否為有效數字
  if (isNaN(numericPrice) || numericPrice <= 0) {
    return 'N/A';
  }
  
  // 格式化為台灣地區的數字格式
  return numericPrice.toLocaleString('zh-TW', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  });
}

// 顯示列表視圖
function displayListView(products) {
  const tbody = document.getElementById('productTableBody');
  
  if (products.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted py-4">
          <i class="fas fa-search fa-2x mb-3 d-block"></i>
          沒有找到符合條件的商品
        </td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = products.map(product => `
    <tr>
      <td style="width: 80px;">
        <img src="${product.image_url || 'https://via.placeholder.com/60x60?text=No+Image'}" 
             class="img-thumbnail" 
             style="width: 60px; height: 60px; object-fit: cover;"
             onerror="this.src='https://via.placeholder.com/60x60?text=No+Image'">
      </td>
      <td>
        <div class="fw-bold" title="${product.title || 'No Title'}" style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
          ${product.title || 'No Title'}
        </div>
      </td>
      <td>
        <span class="text-danger fw-bold">${product.price || 'N/A'}</span>
      </td>
      <td>
        <span class="badge bg-secondary">${getPlatformDisplayName(product.platform)}</span>
      </td>
      <td>
        <a href="${product.url || '#'}" target="_blank" class="btn btn-outline-primary btn-sm">
          <i class="fas fa-external-link-alt"></i> 查看
        </a>
      </td>
    </tr>
  `).join('');
}

// 更新分頁
function updatePagination() {
  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  const paginationContainer = document.getElementById('pagination');
  
  if (totalPages <= 1) {
    paginationContainer.innerHTML = '';
    return;
  }
  
  let paginationHTML = '';
  
  // 上一頁
  if (currentPage > 1) {
    paginationHTML += `
      <li class="page-item">
        <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">上一頁</a>
      </li>
    `;
  }
  
  // 頁碼
  const startPage = Math.max(1, currentPage - 2);
  const endPage = Math.min(totalPages, currentPage + 2);
  
  for (let i = startPage; i <= endPage; i++) {
    paginationHTML += `
      <li class="page-item ${i === currentPage ? 'active' : ''}">
        <a class="page-link" href="#" onclick="changePage(${i}); return false;">${i}</a>
      </li>
    `;
  }
  
  // 下一頁
  if (currentPage < totalPages) {
    paginationHTML += `
      <li class="page-item">
        <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">下一頁</a>
      </li>
    `;
  }
  
  paginationContainer.innerHTML = paginationHTML;
}

// 切換頁面
function changePage(page) {
  currentPage = page;
  updateProductDisplay();
  updatePagination();
  
  // 滾動到商品區域
  document.getElementById('resultCard').scrollIntoView({ 
    behavior: 'smooth', 
    block: 'start' 
  });
}

// 匯出結果
function exportResults() {
  if (!currentResults) {
    alert('沒有結果可以匯出');
    return;
  }
  
  const keyword = document.getElementById("keyword").value.trim();
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `crawler_results_${keyword}_${timestamp}.json`;
  
  const dataStr = JSON.stringify(currentResults, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  
  const link = document.createElement('a');
  link.href = URL.createObjectURL(dataBlob);
  link.download = filename;
  link.click();
}

// 查看詳細結果
function viewDetailedResults() {
  if (currentResults) {
    // 獲取結果檔案名稱
    const keyword = document.getElementById("keyword").value.trim();
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `crawler_results_${keyword}_${timestamp}.json`;

    // 跳轉到詳細頁面
    window.location.href = `/view/${filename}`;
  }
}

// 顯示錯誤
function showError(errorMessage) {
  document.getElementById("errorModalBody").textContent = errorMessage;
  const modal = new bootstrap.Modal(document.getElementById("errorModal"));
  modal.show();
}

// 重設表單
function resetForm() {
  document.getElementById("crawlerForm").reset();
  document.getElementById("selectAll").checked = false;
  document.getElementById("selectAll").indeterminate = false;

  // 重設進度和結果顯示
  document.getElementById("progressCard").style.display = "none";
  document.getElementById("resultCard").style.display = "none";

  currentResults = null;
}

// 設定視圖模式處理器（如果有需要）
function setupViewModeHandlers() {
  // 預留給未來功能
}

// 價格範圍驗證
document.getElementById("minPrice").addEventListener("change", function () {
  const minPrice = parseInt(this.value);
  const maxPrice = parseInt(document.getElementById("maxPrice").value);

  if (minPrice > maxPrice) {
    document.getElementById("maxPrice").value = minPrice;
  }
});

document.getElementById("maxPrice").addEventListener("change", function () {
  const maxPrice = parseInt(this.value);
  const minPrice = parseInt(document.getElementById("minPrice").value);

  if (maxPrice < minPrice) {
    document.getElementById("minPrice").value = maxPrice;
  }
});

// 商品數量驗證
document.getElementById("maxProducts").addEventListener("change", function () {
  const value = parseInt(this.value);
  if (value < 1) {
    this.value = 1;
  } else if (value > 1000) {
    this.value = 1000;
  }
});

// 頁面載入完成時檢查最近結果

