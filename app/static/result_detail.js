// 結果詳情頁面的JavaScript功能
let sessionData = null;
let allProducts = [];
let filteredProducts = [];
let currentPage = 1;
const itemsPerPage = 12;
let sessionId = null;

// 頁面載入完成後初始化
document.addEventListener("DOMContentLoaded", function () {
  console.log("結果詳情頁面載入完成，開始初始化...");
  
  // 從 URL 中獲取 session_id
  const pathParts = window.location.pathname.split('/');
  sessionId = pathParts[pathParts.length - 1];
  
  console.log("URL路徑:", window.location.pathname);
  console.log("解析的 session_id:", sessionId);
  
  if (sessionId && !isNaN(sessionId)) {
    console.log("開始載入結果資料...");
    loadResultData();
    setupEventHandlers();
  } else {
    console.error("無效的任務 ID:", sessionId);
    showError("無效的任務 ID");
    hideLoading();
  }
});

// 顯示錯誤信息
function showError(message) {
  document.getElementById("loadingSpinner").style.display = "none";
  document.getElementById("mainContent").style.display = "none";
  
  // 創建錯誤顯示元素
  const errorDiv = document.createElement("div");
  errorDiv.className = "alert alert-danger text-center";
  errorDiv.innerHTML = `
    <i class="fas fa-exclamation-triangle fa-2x mb-3"></i>
    <h4>載入失敗</h4>
    <p>${message}</p>
    <button class="btn btn-primary" onclick="window.history.back()">返回</button>
  `;
  
  document.querySelector(".container").appendChild(errorDiv);
}

// 隱藏載入動畫
function hideLoading() {
  document.getElementById("loadingSpinner").style.display = "none";
  document.getElementById("mainContent").style.display = "block";
}

// 載入結果資料
async function loadResultData() {
  console.log(`開始載入 session ${sessionId} 的資料...`);
  
  try {
    const apiUrl = `/api/result/${sessionId}`;
    console.log("API URL:", apiUrl);
    
    const response = await fetch(apiUrl);
    console.log("API 響應狀態:", response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log("API 響應資料:", data);

    if (data.status === "success") {
      sessionData = data.data.session;
      allProducts = data.data.products;
      console.log("Session 資料:", sessionData);
      console.log("商品數量:", allProducts.length);
      
      processResultData();
      updateUI();
      console.log("資料載入完成！");
    } else {
      console.error("載入結果失敗:", data.error);
      showError(data.error || "載入結果失敗");
    }
  } catch (error) {
    console.error("載入結果時發生錯誤:", error);
    showError(`載入結果時發生錯誤: ${error.message}`);
  } finally {
    hideLoading();
  }
}

// 處理結果資料
function processResultData() {
  // 預設按價格由低到高排序
  allProducts.sort((a, b) => (a.price || 0) - (b.price || 0));

  // 初始化篩選結果
  filteredProducts = [...allProducts];

  // 更新標題
  const keyword = sessionData.keyword || "未知";
  document.getElementById(
    "resultTitle"
  ).innerHTML = `<i class="fas fa-search me-2"></i>「${keyword}」搜尋結果 (ID: ${sessionId})`;
}

// 更新UI
function updateUI() {
  updateSummaryCards();
  updatePlatformFilter();
  applyFilters(); // Apply filters to show initial view correctly
}

// 更新摘要卡片
function updateSummaryCards() {
  const totalProducts = allProducts.length;
  const uniquePlatforms = new Set(allProducts.map((p) => p.platform)).size;

  // 計算價格統計
  const prices = allProducts.map((p) => p.price || 0).filter((p) => p > 0);
  const avgPrice =
    prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0;
  const minPrice = prices.length > 0 ? Math.min(...prices) : 0;
  const maxPrice = prices.length > 0 ? Math.max(...prices) : 0;

  document.getElementById("summaryCards").innerHTML = `
        <div class="col-md-3">
            <div class="card bg-primary text-white">
                <div class="card-body text-center">
                    <h3>${totalProducts.toLocaleString()}</h3>
                    <p class="mb-0">總商品數</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-success text-white">
                <div class="card-body text-center">
                    <h3>${uniquePlatforms}</h3>
                    <p class="mb-0">平台數</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-info text-white">
                <div class="card-body text-center">
                    <h3>NT$ ${avgPrice.toFixed(0)}</h3>
                    <p class="mb-0">平均價格</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-warning text-white">
                <div class="card-body text-center">
                    <h3>NT$ ${minPrice} - ${maxPrice}</h3>
                    <p class="mb-0">價格範圍</p>
                </div>
            </div>
        </div>
    `;
}

// 更新平台篩選
function updatePlatformFilter() {
  const platforms = [...new Set(allProducts.map((p) => p.platform))];
  const filterSelect = document.getElementById("platformFilter");

  filterSelect.innerHTML = '<option value="">全部平台</option>';
  platforms.forEach((platform) => {
    const option = document.createElement("option");
    option.value = platform;
    option.textContent = platform;
    filterSelect.appendChild(option);
  });
}

// 渲染商品
function renderProducts() {
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const pageProducts = filteredProducts.slice(startIndex, endIndex);

  // 更新篩選資訊
  document.getElementById("filterInfo").textContent = `顯示 ${
    startIndex + 1
  }-${Math.min(endIndex, filteredProducts.length)} 個商品，共 ${
    filteredProducts.length
  } 個`;

  if (pageProducts.length === 0) {
    showEmptyState();
    return;
  }

  hideEmptyState();

  // 根據當前視圖模式只渲染對應的視圖
  if (document.getElementById("gridView").checked) {
    renderGridView(pageProducts);
    document.getElementById("productsTableBody").innerHTML = "";
  } else {
    renderListView(pageProducts);
    document.getElementById("productsGrid").innerHTML = "";
  }
}

// 渲染卡片視圖
function renderGridView(products) {
  const container = document.getElementById("productsGrid");
  container.innerHTML = "";

  products.forEach((product) => {
    const card = createProductCard(product);
    container.appendChild(card);
  });
}

// 建立商品卡片
function createProductCard(product) {
  const col = document.createElement("div");
  col.className = "product-col mb-4";
  col.style.cssText = `
    width: 25%;
    flex: 0 0 25%;
    max-width: 25%;
    padding: 0 0.75rem;
    box-sizing: border-box;
  `;

  const platformClass = `platform-${product.platform
    .toLowerCase()
    .replace(/\s+/g, "")}`;
  col.innerHTML = `
        <div class="card product-card h-100 ${product.is_filtered_out ? 'filtered-out' : ''}">
            <img src="${product.image_url || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect width='200' height='200' fill='%23f8f9fa'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%236c757d'%3E無圖片%3C/text%3E%3C/svg%3E"}" 
                 class="card-img-top" alt="${product.title}"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'%3E%3Crect width=\'200\' height=\'200\' fill=\'%23f8f9fa\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\' fill=\'%236c757d\'%3E載入失敗%3C/text%3E%3C/svg%3E'">
            <div class="card-body d-flex flex-column">
                <h6 class="product-title">${product.title}</h6>
                <div class="mt-auto">
                    <div class="product-price">NT$ ${(product.price || 0).toLocaleString()}</div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="product-platform ${platformClass}">${product.platform}</span>
                        <div class="btn-group">
                            <a href="${product.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-external-link-alt"></i>
                            </a>
                            <button class="btn btn-sm btn-outline-success" onclick='compareProduct(${JSON.stringify(product).replace(/'/g, "\\'")})'>
                                <i class="fas fa-chart-line"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

  return col;
}

// 渲染列表視圖
function renderListView(products) {
  const container = document.getElementById("productsTableBody");
  container.innerHTML = "";

  products.forEach((product) => {
    const row = createProductRow(product);
    container.appendChild(row);
  });
}

// 建立商品行
function createProductRow(product) {
  const platformClass = `platform-${product.platform
    .toLowerCase()
    .replace(/\s+/g, "")}`;
  const row = document.createElement("tr");
  row.className = "align-middle";

  row.innerHTML = `
        <td class="text-center">
            <img src="${product.image_url || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Crect width='100' height='100' fill='%23f8f9fa'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%236c757d'%3E無圖片%3C/text%3E%3C/svg%3E'}" 
                 alt="${product.title}" width="100" height="100"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'100\' height=\'100\'%3E%3Crect width=\'100\' height=\'100\' fill=\'%23f8f9fa\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\' fill=\'%236c757d\'%3E載入失敗%3C/text%3E%3C/svg%3E'">
        </td>
        <td>
            <div class="fw-bold">${product.title}</div>
            <div class="text-muted">
                <span class="product-platform ${platformClass}">${product.platform}</span>
            </div>
        </td>
        <td class="text-end">
            <div class="product-price">NT$ ${(product.price || 0).toLocaleString()}</div>
        </td>
        <td class="text-end">
            <button class="btn btn-sm btn-outline-success" onclick='compareProduct(${JSON.stringify(product).replace(/'/g, "\\'")})'>
                <i class="fas fa-chart-line"></i>
            </button>
        </td>
    `;

  return row;
}

// 設定事件處理器
function setupEventHandlers() {
  document.getElementById("platformFilter").addEventListener("change", (e) => {
    const selectedPlatform = e.target.value;
    filterProducts(selectedPlatform);
  });

  document.getElementById("priceSortAsc").addEventListener("click", () => {
    sortProducts("asc");
  });

  document.getElementById("priceSortDesc").addEventListener("click", () => {
    sortProducts("desc");
  });

  document.getElementById("resetFilters").addEventListener("click", () => {
    resetFilters();
  });

  document.getElementById("gridView").addEventListener("change", () => {
    renderProducts();
  });

  document.getElementById("listView").addEventListener("change", () => {
    renderProducts();
  });

  // 頁碼按鈕事件委派
  document.getElementById("pagination").addEventListener("click", (e) => {
    if (e.target.matches(".page-link")) {
      const newPage = parseInt(e.target.dataset.page);
      if (newPage !== currentPage) {
        currentPage = newPage;
        renderProducts();
      }
    }
  });
}

// 篩選商品
function filterProducts(selectedPlatform) {
  // 根據選擇的平