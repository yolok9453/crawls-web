// 主頁面的JavaScript功能
let allResults = [];
let filteredResults = [];
let searchCache = new Map(); // 搜尋快取
let updateTimeout; // 防抖計時器

// 添加版本控制和快取清理
const APP_VERSION = '2.0.0';
const CACHE_VERSION = 'v2.0.0';

// 檢查和清理舊快取
function clearOldCache() {
  const currentVersion = localStorage.getItem('app_version');
  if (currentVersion !== APP_VERSION) {
    localStorage.clear();
    sessionStorage.clear();
    searchCache.clear();
    localStorage.setItem('app_version', APP_VERSION);
    console.log('🧹 已清理舊版本快取');
  }
}

// 頁面載入完成後初始化
document.addEventListener("DOMContentLoaded", function () {
  // 確保只初始化一次
  if (window.crawlerAppInitialized) {
    return;
  }
  window.crawlerAppInitialized = true;
  
  clearOldCache();
  loadResults();
  loadPlatforms();
  loadDailyDealsStats(); // 載入每日促銷統計
  
  // 綁定事件監聽器
  setupEventListeners();
});

// 載入所有結果
async function loadResults() {
  showLoading(true);

  try {
    const response = await fetch("/api/results");
    const data = await response.json();

    if (data.status === "success") {
      allResults = data.files;
      filteredResults = [...allResults];
      updateUI();
      updateStatistics();
    } else {
      console.error("載入結果失敗:", data.error);
      showEmptyMessage();
    }
  } catch (error) {
    console.error("載入結果時發生錯誤:", error);
    showEmptyMessage();
  } finally {
    showLoading(false);
  }
}

// 載入可用平台
async function loadPlatforms() {
  try {
    const response = await fetch("/api/crawlers");
    const data = await response.json();

    if (data.status === "success") {
      const platformSelect = document.getElementById("filterPlatform");
      data.crawlers.forEach((platform) => {
        const option = document.createElement("option");
        option.value = platform;
        option.textContent = platform.toUpperCase();
        platformSelect.appendChild(option);
      });
    }
  } catch (error) {
    console.error("載入平台列表失敗:", error);
  }
}

// 載入每日促銷統計
async function loadDailyDealsStats() {
  // 防止重複調用
  if (loadDailyDealsStats.loading) {
    return;
  }
  loadDailyDealsStats.loading = true;
  
  try {
    const response = await fetch("/api/daily-deals", {
      method: 'GET',
      headers: {
        'Cache-Control': 'no-cache'
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();

    if (data.status === "success") {
      const countElement = document.getElementById("dailyDealsCount");
      if (countElement) {
        countElement.textContent = data.total_deals || 0;
      }
    } else {
      console.warn("每日促銷 API 回傳非成功狀態:", data);
      const countElement = document.getElementById("dailyDealsCount");
      if (countElement) {
        countElement.textContent = "0";
      }
    }
  } catch (error) {
    console.error("載入每日促銷統計失敗:", error);
    const countElement = document.getElementById("dailyDealsCount");
    if (countElement) {
      countElement.textContent = "0";
    }
  } finally {
    loadDailyDealsStats.loading = false;
  }
}

// 更新UI（防抖版本）
function updateUI() {
  // 清除之前的計時器
  clearTimeout(updateTimeout);
  
  // 設定新的計時器，50ms 後執行更新
  updateTimeout = setTimeout(() => {
    updateUIImmediate();
  }, 50);
}

// 立即更新UI（實際執行函數）
function updateUIImmediate() {
  const tableBody = document.getElementById("resultsTableBody");
  const emptyMessage = document.getElementById("emptyMessage");
  const tableContainer = document.querySelector(".table-responsive");

  if (filteredResults.length === 0) {
    // 顯示空訊息，隱藏表格
    if (emptyMessage) emptyMessage.style.display = "block";
    if (tableContainer) tableContainer.style.display = "none";
    return;
  }

  // 有結果時，隱藏空訊息，顯示表格
  if (emptyMessage) emptyMessage.style.display = "none";
  if (tableContainer) tableContainer.style.display = "block";

  // 清空表格
  if (tableBody) {
    tableBody.innerHTML = "";

    // 添加結果行
    filteredResults.forEach((result) => {
      const row = createResultRow(result);
      tableBody.appendChild(row);
    });
  }
}

// 建立結果行
function createResultRow(result) {
  const row = document.createElement("tr");
  row.className = "fade-in";

  // 格式化時間
  const crawlTime = new Date(result.crawl_time).toLocaleString("zh-TW");

  // 格式化檔案大小
  const fileSize = formatFileSize(result.file_size);

  // 平台標籤
  const platformBadges = result.platforms
    .map(
      (platform) =>
        `<span class="badge bg-secondary me-1">${platform.toUpperCase()}</span>`
    )
    .join("");

  row.innerHTML = `
        <td>
            <strong>${result.keyword}</strong>
        </td>
        <td>
            <span class="text-primary fw-bold">${result.total_products.toLocaleString()}</span>
        </td>
        <td>
            ${platformBadges}
        </td>
        <td>
            <small class="text-muted">${crawlTime}</small>
        </td>
        <td>
            <small class="text-muted">${fileSize}</small>
        </td>
        <td>
            <div class="btn-group btn-group-sm" role="group">
                <button class="btn btn-outline-primary" onclick="viewResult('${
                  result.filename
                }')" title="查看詳細">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-outline-info" onclick="showStatistics('${
                  result.filename
                }')" title="統計資訊">
                    <i class="fas fa-chart-bar"></i>
                </button>
                <button class="btn btn-outline-success" onclick="downloadResult('${
                  result.filename
                }')" title="下載">
                    <i class="fas fa-download"></i>
                </button>
            </div>
        </td>
    `;

  return row;
}

// 更新統計資訊
function updateStatistics() {
  const totalFiles = allResults.length;
  const totalProducts = allResults.reduce(
    (sum, result) => sum + result.total_products,
    0
  );

  // 獲取唯一平台數
  const allPlatforms = new Set();
  allResults.forEach((result) => {
    result.platforms.forEach((platform) => allPlatforms.add(platform));
  });

  // 最新爬蟲時間
  const latestResult = allResults.length > 0 ? allResults[0] : null;
  const latestTime = latestResult
    ? new Date(latestResult.crawl_time).toLocaleDateString("zh-TW")
    : "無";

  // 更新統計卡片
  document.getElementById("totalFiles").textContent = totalFiles;
  document.getElementById("totalProducts").textContent =
    totalProducts.toLocaleString();
  document.getElementById("totalPlatforms").textContent = allPlatforms.size;
  document.getElementById("latestCrawl").textContent = latestTime;
}

// 套用篩選
function applyFilters() {
  const keyword = document.getElementById("searchKeyword").value.trim();
  const platform = document.getElementById("filterPlatform").value;

  // 如果有關鍵字搜尋，使用 API 搜尋
  if (keyword) {
    performSearch(keyword, platform);
  } else {
    // 無關鍵字時，只篩選平台
    filteredResults = allResults.filter((result) => {
      const matchPlatform = !platform || result.platforms.includes(platform);
      return matchPlatform;
    });
    updateUI();
  }
}

// 執行 API 搜尋
async function performSearch(keyword, platform = '') {
  if (!keyword.trim()) {
    // 無關鍵字時，只篩選平台，不要遞歸調用
    filteredResults = allResults.filter((result) => {
      const matchPlatform = !platform || result.platforms.includes(platform);
      return matchPlatform;
    });
    updateUI();
    return;
  }

  // 檢查快取
  const cacheKey = `${keyword}_${platform}`;
  if (searchCache.has(cacheKey)) {
    const cachedData = searchCache.get(cacheKey);
    filteredResults = cachedData.results;
    updateUI();
    updateSearchStats(cachedData.total, keyword);
    return;
  }

  showLoading(true);
  
  try {
    const params = new URLSearchParams({
      keyword: keyword,
      limit: 100
    });
    
    if (platform && platform !== 'all') {
      params.append('platform', platform);
    }

    const response = await fetch(`/api/search?${params}`);
    const data = await response.json();

    if (data.status === 'success') {
      // 將搜尋結果轉換為與現有格式相容的結構
      const searchResults = data.products.map(product => ({
        keyword: keyword,
        filename: `search_${keyword}_${Date.now()}.json`,
        crawl_time: product.crawl_time || new Date().toISOString(),
        platforms: [product.platform || 'unknown'],
        total_products: 1,
        products: [product]
      }));

      filteredResults = searchResults;
      
      // 儲存到快取（最多快取 20 個搜尋結果）
      if (searchCache.size >= 20) {
        const firstKey = searchCache.keys().next().value;
        searchCache.delete(firstKey);
      }
      searchCache.set(cacheKey, {
        results: searchResults,
        total: data.total,
        timestamp: Date.now()
      });
      
      updateUI();
      updateSearchStats(data.total, keyword);
    } else {
      console.error('搜尋失敗:', data.error);
      showEmptyMessage(`搜尋「${keyword}」沒有找到結果`);
    }
  } catch (error) {
    console.error('搜尋時發生錯誤:', error);
    showEmptyMessage('搜尋時發生錯誤，請稍後再試');
  } finally {
    showLoading(false);
  }
}

// 更新搜尋統計
function updateSearchStats(total, keyword) {
  const statsElement = document.querySelector('.search-stats');
  if (statsElement) {
    statsElement.textContent = `找到 ${total} 個「${keyword}」的搜尋結果`;
  }
}

// 重新整理結果
function refreshResults() {
  loadResults();
  loadDailyDealsStats();
}

// 查看結果詳細
function viewResult(filename) {
  window.location.href = `/view/${filename}`;
}

// 顯示統計資訊
async function showStatistics(filename) {
  try {
    const response = await fetch(`/api/statistics/${filename}`);
    const data = await response.json();

    if (data.status === "success") {
      const stats = data.statistics;
      const modalBody = document.getElementById("statsModalBody");

      modalBody.innerHTML = `
                <div class="row mb-3">
                    <div class="col-md-6">
                        <h6>基本資訊</h6>
                        <ul class="list-unstyled">
                            <li><strong>關鍵字:</strong> ${stats.keyword}</li>
                            <li><strong>總商品數:</strong> ${stats.total_products.toLocaleString()}</li>
                            <li><strong>平台數量:</strong> ${
                              Object.keys(stats.platforms).length
                            }</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6>價格統計</h6>
                        <ul class="list-unstyled">
                            <li><strong>平均價格:</strong> NT$ ${stats.price_stats.average.toFixed(
                              2
                            )}</li>
                            <li><strong>最低價格:</strong> NT$ ${stats.price_stats.min.toLocaleString()}</li>
                            <li><strong>最高價格:</strong> NT$ ${stats.price_stats.max.toLocaleString()}</li>
                        </ul>
                    </div>
                </div>
                
                <h6>各平台詳細</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>平台</th>
                                <th>狀態</th>
                                <th>商品數量</th>
                                <th>執行時間</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${Object.entries(stats.platforms)
                              .map(
                                ([platform, data]) => `
                                <tr>
                                    <td><span class="badge bg-secondary">${platform.toUpperCase()}</span></td>
                                    <td>
                                        ${
                                          data.status === "success"
                                            ? '<i class="fas fa-check-circle text-success"></i> 成功'
                                            : '<i class="fas fa-times-circle text-danger"></i> 失敗'
                                        }
                                    </td>
                                    <td>${data.product_count.toLocaleString()}</td>
                                    <td>${data.execution_time.toFixed(2)}s</td>
                                </tr>
                            `
                              )
                              .join("")}
                        </tbody>
                    </table>
                </div>
            `;

      const modal = new bootstrap.Modal(document.getElementById("statsModal"));
      modal.show();
    }
  } catch (error) {
    console.error("載入統計資訊失敗:", error);
    alert("載入統計資訊失敗");
  }
}

// 下載結果
function downloadResult(filename) {
  const link = document.createElement("a");
  link.href = `/api/result/${filename}`;
  link.download = filename;
  link.click();
}

// 顯示載入狀態
function showLoading(show) {
  const spinner = document.getElementById("loadingSpinner");
  const table = document.querySelector(".table-responsive");

  if (show) {
    spinner.style.display = "block";
    if (table) table.style.display = "none";
  } else {
    spinner.style.display = "none";
    if (table) table.style.display = "block";
  }
}

// 顯示空訊息
function showEmptyMessage(message) {
  const emptyMessage = document.getElementById("emptyMessage");
  const tableContainer = document.querySelector(".table-responsive");
  
  if (emptyMessage) {
    emptyMessage.style.display = "block";
    // 如果有自定義訊息，更新顯示文字
    if (message) {
      const messageText = emptyMessage.querySelector('p');
      if (messageText) {
        messageText.textContent = message;
      }
    }
  }
  
  if (tableContainer) {
    tableContainer.style.display = "none";
  }
}

// 格式化檔案大小
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// 設定事件監聽器
function setupEventListeners() {
  // 搜尋功能 - 即時搜尋（增加防抖時間）
  const searchInput = document.getElementById("searchKeyword");
  if (searchInput && !searchInput.hasAttribute('data-listener-added')) {
    searchInput.addEventListener("input", function () {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => {
        applyFilters();
      }, 500); // 增加到 500ms 減少頻繁搜尋
    });
    searchInput.setAttribute('data-listener-added', 'true');
  }

  // 平台篩選
  const platformSelect = document.getElementById("filterPlatform");
  if (platformSelect && !platformSelect.hasAttribute('data-listener-added')) {
    platformSelect.addEventListener("change", applyFilters);
    platformSelect.setAttribute('data-listener-added', 'true');
  }
}

// 跳轉到每日促銷頁面
function goToDailyDeals() {
  window.location.href = "/daily-deals";
}
