// 結果詳情頁面的JavaScript功能
let resultData = null;
let allProducts = [];
let filteredProducts = [];
let currentPage = 1;
const itemsPerPage = 12;

// 頁面載入完成後初始化
document.addEventListener("DOMContentLoaded", function () {
  loadResultData();
  setupEventHandlers();
});

// 載入結果資料
async function loadResultData() {
  try {
    const response = await fetch(`/api/result/${filename}`);
    const data = await response.json();

    if (data.status === "success") {
      resultData = data.data;
      processResultData();
      updateUI();
    } else {
      console.error("載入結果失敗:", data.error);
      showError("載入結果失敗");
    }
  } catch (error) {
    console.error("載入結果時發生錯誤:", error);
    showError("載入結果時發生錯誤");
  } finally {
    hideLoading();
  }
}

// 處理結果資料
function processResultData() {
  allProducts = [];

  // 處理新格式（包含多個平台）
  if (resultData.results) {
    Object.values(resultData.results).forEach((platformResult) => {
      if (platformResult.products) {
        allProducts.push(...platformResult.products);
      }
    });
  }
  // 處理舊格式（單一平台）
  else if (resultData.products) {
    allProducts = resultData.products;
  }

  // 預設按價格由低到高排序
  allProducts.sort((a, b) => (a.price || 0) - (b.price || 0));

  // 初始化篩選結果
  filteredProducts = [...allProducts];

  // 更新標題
  const keyword = resultData.keyword || "未知";
  document.getElementById(
    "resultTitle"
  ).innerHTML = `<i class="fas fa-search me-2"></i>「${keyword}」搜尋結果`;
}

// 更新UI
function updateUI() {
  updateSummaryCards();
  updatePlatformFilter();
  renderProducts();
  updatePagination();
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
    // 渲染卡片視圖，清空列表視圖
    renderGridView(pageProducts);
    document.getElementById("productsTableBody").innerHTML = "";
  } else {
    // 渲染列表視圖，清空卡片視圖
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
  // 固定四個卡片一排，不使用響應式
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
        <div class="card product-card h-100">
            <img src="${product.image_url || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect width='200' height='200' fill='%23f8f9fa'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%236c757d'%3E無圖片%3C/text%3E%3C/svg%3E"}" 
                 class="card-img-top" alt="${product.title}"
                 onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'200\\' height=\\'200\\'%3E%3Crect width=\\'200\\' height=\\'200\\' fill=\\'%23f8f9fa\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dy=\\'.3em\\' fill=\\'%236c757d\\'%3E載入失敗%3C/text%3E%3C/svg%3E'">
            <div class="card-body d-flex flex-column">
                <h6 class="product-title">${product.title}</h6>
                <div class="mt-auto">
                    <div class="product-price">NT$ ${(
                      product.price || 0
                    ).toLocaleString()}</div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="product-platform ${platformClass}">${
    product.platform
  }</span>
                        <div class="btn-group">
                            <a href="${
                              product.url
                            }" target="_blank" class="btn btn-sm btn-outline-primary">
                                <i class="fas fa-external-link-alt"></i>
                            </a>
                            <button class="btn btn-sm btn-outline-success" onclick="compareProduct(${JSON.stringify(product).replace(/"/g, '&quot;')})">
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
  const tbody = document.getElementById("productsTableBody");
  tbody.innerHTML = "";

  products.forEach((product) => {
    const row = createProductRow(product);
    tbody.appendChild(row);
  });
}

// 建立商品列表行
function createProductRow(product) {
  const row = document.createElement("tr");
  row.innerHTML = `
        <td>
            <img src="${product.image_url || "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='60'%3E%3Crect width='60' height='60' fill='%23f8f9fa'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%236c757d' font-size='10'%3E無圖%3C/text%3E%3C/svg%3E"}" 
                 class="img-thumbnail" style="width: 60px; height: 60px; object-fit: cover;"
                 alt="${
                   product.title
                 }" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'60\\' height=\\'60\\'%3E%3Crect width=\\'60\\' height=\\'60\\' fill=\\'%23f8f9fa\\'/%3E%3Ctext x=\\'50%25\\' y=\\'50%25\\' text-anchor=\\'middle\\' dy=\\'.3em\\' fill=\\'%236c757d\\' font-size=\\'10\\'%3E載入失敗%3C/text%3E%3C/svg%3E'">
        </td>
        <td>
            <div class="product-title">${product.title}</div>
        </td>
        <td>
            <strong class="text-primary">NT$ ${(
              product.price || 0
            ).toLocaleString()}</strong>
        </td>
        <td>
            <span class="badge bg-secondary">${product.platform}</span>
        </td>
        <td>
            <div class="btn-group">
                <a href="${
                  product.url
                }" target="_blank" class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-external-link-alt me-1"></i>查看
                </a>
                <button class="btn btn-sm btn-outline-success" onclick="compareProduct(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                    <i class="fas fa-chart-line"></i>
                </button>
            </div>
        </td>
    `;

  return row;
}

// 更新分頁
function updatePagination() {
  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  const pagination = document.getElementById("pagination");

  if (totalPages <= 1) {
    pagination.innerHTML = "";
    return;
  }

  let paginationHTML = "";

  // 上一頁
  paginationHTML += `
        <li class="page-item ${currentPage === 1 ? "disabled" : ""}">
            <a class="page-link" href="#" onclick="changePage(${
              currentPage - 1
            })">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;

  // 頁碼
  const startPage = Math.max(1, currentPage - 2);
  const endPage = Math.min(totalPages, currentPage + 2);

  if (startPage > 1) {
    paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1)">1</a></li>`;
    if (startPage > 2) {
      paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    paginationHTML += `
            <li class="page-item ${i === currentPage ? "active" : ""}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
    }
    paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages})">${totalPages}</a></li>`;
  }

  // 下一頁
  paginationHTML += `
        <li class="page-item ${currentPage === totalPages ? "disabled" : ""}">
            <a class="page-link" href="#" onclick="changePage(${
              currentPage + 1
            })">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;

  pagination.innerHTML = paginationHTML;
}

// 變更頁面
function changePage(page) {
  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  if (page < 1 || page > totalPages) return;

  currentPage = page;
  renderProducts();
  updatePagination();

  // 滾動到頂部
  document.querySelector(".card-header").scrollIntoView({ behavior: "smooth" });
}

// 套用篩選
function applyFilters() {
  const platform = document.getElementById("platformFilter").value;
  const minPrice = parseFloat(document.getElementById("priceMin").value) || 0;
  const maxPrice =
    parseFloat(document.getElementById("priceMax").value) || Infinity;
  const sortBy = document.getElementById("sortBy").value;

  // 篩選
  filteredProducts = allProducts.filter((product) => {
    const matchPlatform = !platform || product.platform === platform;
    const price = product.price || 0;
    const matchPrice = price >= minPrice && price <= maxPrice;

    return matchPlatform && matchPrice;
  });

  // 排序
  switch (sortBy) {
    case "price_asc":
      filteredProducts.sort((a, b) => (a.price || 0) - (b.price || 0));
      break;
    case "price_desc":
      filteredProducts.sort((a, b) => (b.price || 0) - (a.price || 0));
      break;
    case "title_asc":
      filteredProducts.sort((a, b) => a.title.localeCompare(b.title));
      break;
    case "platform":
      filteredProducts.sort((a, b) => a.platform.localeCompare(b.platform));
      break;
  }

  currentPage = 1;
  renderProducts();
  updatePagination();
}

// 重設篩選
function resetFilters() {
  document.getElementById("platformFilter").value = "";
  document.getElementById("priceMin").value = "";
  document.getElementById("priceMax").value = "";
  document.getElementById("sortBy").value = "price_asc";

  filteredProducts = [...allProducts];
  currentPage = 1;
  renderProducts();
  updatePagination();
}

// 匯出結果
function exportResults() {
  const dataStr = JSON.stringify(resultData, null, 2);
  const dataBlob = new Blob([dataStr], { type: "application/json" });

  const link = document.createElement("a");
  link.href = URL.createObjectURL(dataBlob);
  link.download = filename;
  link.click();
}

// 設定事件處理器
function setupEventHandlers() {
  // 視圖模式切換
  document.getElementById("gridView").addEventListener("change", function () {
    if (this.checked) {
      document.getElementById("productsGrid").style.display = "block";
      document.getElementById("productsList").style.display = "none";
      // 重新渲染以確保只顯示卡片視圖
      renderProducts();
    }
  });

  document.getElementById("listView").addEventListener("change", function () {
    if (this.checked) {
      document.getElementById("productsGrid").style.display = "none";
      document.getElementById("productsList").style.display = "block";
      // 重新渲染以確保只顯示列表視圖
      renderProducts();
    }
  });

  // 篩選事件
  document
    .getElementById("platformFilter")
    .addEventListener("change", applyFilters);
  document.getElementById("sortBy").addEventListener("change", applyFilters);

  // 價格篩選（延遲執行）
  let priceTimeout;
  document.getElementById("priceMin").addEventListener("input", function () {
    clearTimeout(priceTimeout);
    priceTimeout = setTimeout(applyFilters, 500);
  });

  document.getElementById("priceMax").addEventListener("input", function () {
    clearTimeout(priceTimeout);
    priceTimeout = setTimeout(applyFilters, 500);
  });
}

// 顯示空狀態
function showEmptyState() {
  document.getElementById("emptyState").style.display = "block";
  document.getElementById("productsGrid").style.display = "none";
  document.getElementById("productsList").style.display = "none";
}

// 隱藏空狀態
function hideEmptyState() {
  document.getElementById("emptyState").style.display = "none";

  // 根據當前視圖模式顯示對應容器
  if (document.getElementById("gridView").checked) {
    document.getElementById("productsGrid").style.display = "block";
    document.getElementById("productsList").style.display = "none";
  } else {
    document.getElementById("productsGrid").style.display = "none";
    document.getElementById("productsList").style.display = "block";
  }
}

// 隱藏載入中
function hideLoading() {
  document.getElementById("loadingSpinner").style.display = "none";
  document.getElementById("mainContent").style.display = "block";
}

// 顯示錯誤
function showError(message) {
  document.getElementById("loadingSpinner").innerHTML = `
        <div class="text-center text-danger">
            <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
            <p>${message}</p>
            <button class="btn btn-primary" onclick="location.reload()">重新載入</button>
        </div>
    `;
}

// ==================== 商品比較功能 ====================

let currentComparisonProduct = null;

// 開始商品比較
async function compareProduct(product) {
  currentComparisonProduct = product;

  // 顯示彈窗
  const modal = new bootstrap.Modal(document.getElementById("comparisonModal"));
  modal.show();

  // 重置狀態
  showComparisonLoading();

  try {
    const response = await fetch("/api/products/compare", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        productName: product.title,
        platform: product.platform,
        price: product.price,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      showComparisonResults(data);
    } else {
      showComparisonError(data.error || "比較功能暫時無法使用");
    }
  } catch (error) {
    console.error("商品比較錯誤:", error);
    showComparisonError("網路連線錯誤，請稍後再試");
  }
}

// 顯示載入中狀態
function showComparisonLoading() {
  document.getElementById("comparisonLoading").style.display = "block";
  document.getElementById("comparisonResults").style.display = "none";
  document.getElementById("comparisonError").style.display = "none";
}

// 顯示比較結果
function showComparisonResults(data) {
  document.getElementById("comparisonLoading").style.display = "none";
  document.getElementById("comparisonError").style.display = "none";

  // 顯示目標商品
  document.getElementById("targetProduct").innerHTML = createTargetProductHTML(
    currentComparisonProduct
  );

  // 顯示統計資訊
  document.getElementById("comparisonStats").innerHTML = createStatsHTML(data);

  const similarProducts = data.similarProducts || [];

  if (similarProducts.length === 0) {
    document.getElementById("noSimilarProducts").style.display = "block";
    document.getElementById("similarProductsGroups").innerHTML = "";
  } else {
    document.getElementById("noSimilarProducts").style.display = "none";

    // 直接按匹配度排序顯示，不分組
    document.getElementById("similarProductsGroups").innerHTML = createSortedProductsHTML(similarProducts);
  }

  document.getElementById("comparisonResults").style.display = "block";
}

// 顯示錯誤狀態
function showComparisonError(errorMessage) {
  document.getElementById("comparisonLoading").style.display = "none";
  document.getElementById("comparisonResults").style.display = "none";
  document.getElementById("errorMessage").textContent = errorMessage;
  document.getElementById("comparisonError").style.display = "block";
}

// 創建目標商品 HTML
function createTargetProductHTML(product) {
  return `
    <div class="row align-items-center">
      <div class="col-md-2">
        <img src="${product.image_url || '/static/placeholder.png'}" 
             class="img-fluid rounded" alt="${product.title}"
             style="max-height: 80px;">
      </div>
      <div class="col-md-6">
        <h6 class="mb-1">${product.title}</h6>
        <small class="text-muted">${product.platform}</small>
      </div>
      <div class="col-md-4 text-end">
        <div class="h5 text-primary mb-0">NT$ ${(product.price || 0).toLocaleString()}</div>
      </div>
    </div>
  `;
}

// 創建統計資訊 HTML
function createStatsHTML(data) {
  return `
    <div class="row text-center">
      <div class="col-md-3">
        <div class="fw-bold">${data.totalCandidates || 0}</div>
        <small>候選商品</small>
      </div>
      <div class="col-md-3">
        <div class="fw-bold">${data.totalMatches || 0}</div>
        <small>總匹配</small>
      </div>
      <div class="col-md-3">
        <div class="fw-bold text-success">${data.highQualityMatches || 0}</div>
        <small>高品質匹配</small>
      </div>
      <div class="col-md-3">
        <div class="fw-bold">${Math.round((data.similarityThreshold || 0.8) * 100)}%</div>
        <small>相似度門檻</small>
      </div>
    </div>
  `;
}

// 創建按匹配度排序的商品列表 HTML
function createSortedProductsHTML(products) {
  // 確保商品已按相似度排序（降序）
  const sortedProducts = [...products].sort((a, b) => b.similarity - a.similarity);
  
  let html = `
    <div class="mb-3">
      <div class="d-flex align-items-center mb-3">
        <h6 class="mb-0 me-2">相似商品</h6>
        <span class="text-muted">(${sortedProducts.length} 個商品，按匹配度排序)</span>
      </div>
      <div class="row">
  `;

  sortedProducts.forEach((product) => {
    html += createSimilarProductHTML(product);
  });

  html += `
      </div>
    </div>
  `;

  return html;
}

// 按分類分組商品 (保留但不使用)
function groupProductsByCategory(products) {
  return products.reduce((groups, product) => {
    const category = getCategoryBySimilarity(product.similarity);
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(product);
    return groups;
  }, {});
}

// 根據相似度判斷分類
function getCategoryBySimilarity(similarity) {
  if (similarity >= 0.95) return "完全相同";
  if (similarity >= 0.85) return "高度相似";
  return "相似商品";
}

// 創建分組商品 HTML
function createGroupedProductsHTML(grouped) {
  let html = "";

  Object.entries(grouped).forEach(([category, products]) => {
    const categoryColor = getCategoryColor(category);

    html += `
      <div class="mb-4">
        <div class="d-flex align-items-center mb-3">
          <span class="badge ${categoryColor} me-2">${category}</span>
          <span class="text-muted">(${products.length} 個商品)</span>
        </div>
        <div class="row">
    `;

    products.forEach((product) => {
      html += createSimilarProductHTML(product);
    });

    html += `
        </div>
      </div>
    `;
  });

  return html;
}

// 獲取分類顏色
function getCategoryColor(category) {
  switch (category) {
    case "完全相同":
      return "bg-success";
    case "高度相似":
      return "bg-primary";
    case "相似商品":
      return "bg-warning";
    default:
      return "bg-secondary";
  }
}

// 創建相似商品 HTML
function createSimilarProductHTML(product) {
  const priceComparison = getPriceComparison(currentComparisonProduct.price, product.price);

  return `
    <div class="col-md-6 mb-3">
      <div class="card h-100">
        <div class="card-body">
          <div class="row align-items-center">
            <div class="col-3">
              <img src="${product.image_url || '/static/placeholder.png'}" 
                   class="img-fluid rounded" alt="${product.title}"
                   style="max-height: 60px;">
            </div>
            <div class="col-6">
              <h6 class="card-title mb-1" style="font-size: 0.9rem;">${product.title}</h6>
              <div class="small text-muted mb-1">${product.platform}</div>
              <div class="small">
                <span class="badge bg-info">相似度: ${Math.round(product.similarity * 100)}%</span>
              </div>
              ${product.reason ? `<div class="small text-muted mt-1">💡 ${product.reason}</div>` : ''}
            </div>
            <div class="col-3 text-end">
              <div class="fw-bold text-primary">NT$ ${product.price.toLocaleString()}</div>
              <div class="small ${priceComparison.color}">
                ${priceComparison.icon} ${priceComparison.text}
              </div>
              <a href="${product.url}" target="_blank" class="btn btn-sm btn-outline-primary mt-1">
                前往 <i class="fas fa-external-link-alt"></i>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;
}

// 計算價格比較
function getPriceComparison(currentPrice, comparePrice) {
  const diff = currentPrice - comparePrice;
  if (diff > 0) {
    return {
      type: "higher",
      text: `- $${diff.toLocaleString()}`,
      color: "text-success",
      icon: "📉",
    };
  } else if (diff < 0) {
    return {
      type: "lower",
      text: `+ $${Math.abs(diff).toLocaleString()}`,
      color: "text-danger",
      icon: "📈",
    };
  }
  return {
    type: "same",
    text: "相同價格",
    color: "text-muted",
    icon: "➖",
  };
}
