// 主頁面的JavaScript功能
let allResults = [];
let filteredResults = [];

// 載入所有結果
async function loadResults() {
  showLoading(true);

  try {
    const response = await fetch("/api/results");
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();

    if (data.status === "success") {
      allResults = data.files || [];
      filteredResults = [...allResults];
      updateUI();
      updateStatistics();
      console.log(`成功載入 ${allResults.length} 個結果`);
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
  try {
    const response = await fetch("/api/daily-deals");
    const data = await response.json();

    if (data.status === "success") {
      document.getElementById("dailyDealsCount").textContent =
        data.total_deals || 0;
    }
  } catch (error) {
    console.error("載入每日促銷統計失敗:", error);
    document.getElementById("dailyDealsCount").textContent = "0";
  }
}

// 更新UI
function updateUI() {
  const tableBody = document.getElementById("resultsTableBody");

  if (filteredResults.length === 0) {
    showEmptyMessage();
    return;
  }

  // 清空表格
  tableBody.innerHTML = "";

  // 添加結果行
  filteredResults.forEach((result) => {
    const row = createResultRow(result);
    tableBody.appendChild(row);
  });

  document.getElementById("emptyMessage").style.display = "none";
}

// 建立結果行
function createResultRow(result) {
  const row = document.createElement("tr");
  row.className = "fade-in";

  // 格式化時間
  const crawlTime = new Date(result.crawl_time).toLocaleString("zh-TW");

  // 平台標籤
  const platforms = result.platforms ? result.platforms.split(',') : [];
  const platformBadges = platforms
    .map(
      (platform) =>
        `<span class="badge bg-secondary me-1">${platform.toUpperCase()}</span>`
    )
    .join("");

  // 計算檔案大小（模擬值，因為我們沒有實際檔案大小資訊）
  const fileSize = result.total_products > 0 ? `${Math.max(1, Math.round(result.total_products * 0.5))} KB` : '487 Bytes';

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
            <div class="action-buttons">
                <button class="action-btn view-btn" onclick="viewResult(${
                  result.id
                })" title="查看詳細">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="action-btn manage-btn" onclick="manageProducts(${
                  result.id
                })" title="管理商品">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="action-btn download-btn" onclick="exportSession(${
                  result.id
                }, '${result.keyword}')" title="下載結果">
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
    if (result.platforms) {
        result.platforms.split(',').forEach((platform) => allPlatforms.add(platform));
    }
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
  const keyword = document.getElementById("searchKeyword").value.toLowerCase();
  const platform = document.getElementById("filterPlatform").value;

  filteredResults = allResults.filter((result) => {
    const matchKeyword =
      !keyword || result.keyword.toLowerCase().includes(keyword);
    const matchPlatform = !platform || (result.platforms && result.platforms.includes(platform));

    return matchKeyword && matchPlatform;
  });

  updateUI();
}

// 重新整理結果
function refreshResults() {
  // 檢查是否需要從GitHub同步新資料
  checkGitHubSync();
  
  loadResults();
  loadDailyDealsStats();
}

// 查看結果詳細
function viewResult(session_id) {
  window.location.href = `/view/${session_id}`;
}

// 顯示統計資訊
async function showStatistics(session_id) {
  try {
    const response = await fetch(`/api/statistics/${session_id}`);
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
                            <li><strong>平均價格:</strong> NT$ ${stats.price_stats.average ? stats.price_stats.average.toFixed(2) : 'N/A'}</li>
                            <li><strong>最低價格:</strong> NT$ ${stats.price_stats.min ? stats.price_stats.min.toLocaleString() : 'N/A'}</li>
                            <li><strong>最高價格:</strong> NT$ ${stats.price_stats.max ? stats.price_stats.max.toLocaleString() : 'N/A'}</li>
                        </ul>
                    </div>
                </div>
                
                <h6>各平台詳細</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>平台</th>
                                <th>商品數量</th>
                                <th>平均價格</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${Object.entries(stats.platforms)
                              .map(
                                ([platform, p_data]) => `
                                <tr>
                                    <td><span class="badge bg-secondary">${platform.toUpperCase()}</span></td>
                                    <td>${p_data.product_count.toLocaleString()}</td>
                                    <td>${p_data.average_price ? p_data.average_price.toFixed(2) : 'N/A'}</td>
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

// 下載結果 (功能已改變)
function downloadResult() {
  alert("下載功能已停用。所有數據現在統一儲存在資料庫中。");
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
function showEmptyMessage() {
  const spinner = document.getElementById("loadingSpinner");
  const table = document.querySelector(".table-responsive");
  const emptyMessage = document.getElementById("emptyMessage");
  
  if (spinner) spinner.style.display = "none";
  if (table) table.style.display = "none";
  if (emptyMessage) emptyMessage.style.display = "block";
}

// 格式化檔案大小
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

// 搜尋功能 - 即時搜尋
document.getElementById("searchKeyword").addEventListener("input", function () {
  clearTimeout(this.searchTimeout);
  this.searchTimeout = setTimeout(() => {
    applyFilters();
  }, 300);
});

// 平台篩選
document
  .getElementById("filterPlatform")
  .addEventListener("change", applyFilters);

// 跳轉到每日促銷頁面
document
  .getElementById("dailyDealsPage")
  .addEventListener("click", goToDailyDeals);

function goToDailyDeals() {
  window.location.href = "/daily-deals";
}

// 批量過濾功能
async function batchFilterResults() {
  const filterBtn = document.getElementById('batchFilterBtn');
  
  // 確認對話框
  if (!confirm('確定要批量過濾所有爬蟲結果嗎？這可能需要一些時間。')) {
    return;
  }
  
  // 顯示載入中
  if (filterBtn) {
    filterBtn.disabled = true;
    filterBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>批量過濾中...';
  }

  try {
    const response = await fetch('/api/products/filter-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const result = await response.json();

    if (result.status === 'success') {
      let message = `批量過濾完成！\n\n`;
      message += `處理檔案數: ${result.total_files}\n`;
      message += `總計商品: ${result.overall_statistics.total_original} → ${result.overall_statistics.total_filtered}\n`;
      message += `移除商品: ${result.overall_statistics.total_removed} 個 (${result.overall_statistics.overall_removal_rate}%)\n\n`;
      
      message += `詳細結果:\n`;
      result.filtered_files.forEach((file, index) => {
        if (file.status === 'success') {
          message += `${index + 1}. ${file.keyword}: ${file.original_count} → ${file.filtered_count} (-${file.removed_count})\n`;
        } else {
          message += `${index + 1}. ${file.input_file}: 失敗 - ${file.error}\n`;
        }
      });

      showAlert('批量過濾完成', message, 'success');
      
      // 重新載入結果列表
      loadResults();
    } else {
      showAlert('批量過濾失敗', result.error || '未知錯誤', 'error');
    }
  } catch (error) {
    console.error('批量過濾請求失敗:', error);
    showAlert('批量過濾失敗', '網路請求失敗，請稍後再試', 'error');
  } finally {
    // 恢復按鈕狀態
    if (filterBtn) {
      filterBtn.disabled = false;
      filterBtn.innerHTML = '<i class="fas fa-magic me-2"></i>批量過濾';
    }
  }
}

// 顯示提示訊息
function showAlert(title, message, type = 'info') {
  const alertClass = type === 'error' ? 'alert-danger' : 
                    type === 'success' ? 'alert-success' : 
                    'alert-info';
  
  const alertHtml = `
    <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
      <h6 class="alert-heading mb-2">${title}</h6>
      <p class="mb-0" style="white-space: pre-line;">${message}</p>
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
  `;
  
  // 在頁面頂部顯示提示
  const container = document.querySelector('.container');
  if (container) {
    container.insertAdjacentHTML('afterbegin', alertHtml);
  }
}

// GitHub資料同步功能
async function checkGitHubSync() {
  try {
    const response = await fetch('/api/check-github-sync');
    const data = await response.json();
    
    if (data.status === 'success') {
      if (data.needs_sync) {
        showSyncNotification(data.message, data.age_hours);
      }
    }
  } catch (error) {
    console.log('檢查GitHub同步狀態失敗:', error);
  }
}

function showSyncNotification(message, ageHours) {
  const alertHtml = `
    <div class="alert alert-warning alert-dismissible fade show" role="alert" id="syncAlert">
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <h6 class="alert-heading mb-1">📡 資料更新提醒</h6>
          <p class="mb-0">${message}</p>
          <small class="text-muted">點擊右側按鈕獲取GitHub上的最新促銷資料</small>
        </div>
        <div>
          <button type="button" class="btn btn-warning btn-sm me-2" onclick="syncGitHubData()">
            <i class="fas fa-sync-alt me-1"></i>同步最新資料
          </button>
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      </div>
    </div>
  `;
  
  const container = document.querySelector('.container');
  if (container) {
    // 移除舊的同步提醒
    const oldAlert = document.getElementById('syncAlert');
    if (oldAlert) oldAlert.remove();
    
    container.insertAdjacentHTML('afterbegin', alertHtml);
  }
}

async function syncGitHubData() {
  const syncBtn = document.querySelector('#syncAlert button[onclick="syncGitHubData()"]');
  if (syncBtn) {
    syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>同步中...';
    syncBtn.disabled = true;
  }
  
  try {
    const response = await fetch('/api/sync-github-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    
    if (data.status === 'success') {
      showAlert('成功', data.message, 'success');
      
      // 移除同步提醒
      const syncAlert = document.getElementById('syncAlert');
      if (syncAlert) syncAlert.remove();
      
      // 重新載入資料
      setTimeout(() => {
        loadResults();
        loadDailyDealsStats();
      }, 1000);
      
    } else {
      showAlert('同步失敗', data.message, 'error');
    }
    
  } catch (error) {
    showAlert('同步錯誤', '無法連接到服務器，請稍後再試', 'error');
  }
}

// 添加自動檢查到頁面載入
document.addEventListener("DOMContentLoaded", function () {
  console.log("=== 頁面載入完成，開始初始化... ===");
  
  // 立即執行 loadResults
  console.log("立即執行 loadResults...");
  loadResults();
  
  // 添加額外調試
  setTimeout(() => {
    console.log("2秒後檢查狀態...");
    console.log("allResults length:", allResults ? allResults.length : "undefined");
    console.log("filteredResults length:", filteredResults ? filteredResults.length : "undefined");
    
    // 如果沒有數據，手動重新調用
    if (!allResults || allResults.length === 0) {
      console.log("沒有數據，重新調用loadResults...");
      loadResults();
    }
  }, 2000);
});

// 獲取平台顯示名稱
function getPlatformDisplayName(platform) {
    const names = {
        'pchome_onsale': 'PChome特賣',
        'yahoo_rushbuy': 'Yahoo秒殺',
        'pchome': 'PChome',
        'yahoo': 'Yahoo',
        'carrefour': '家樂福',
        'routn': 'Routn'
    };
    return names[platform] || platform.toUpperCase();
}

// 格式化價格
function formatPrice(price) {
    if (!price || price === '價格未提供') return '價格洽詢';
    
    // 移除非數字字符，但保留小數點
    const numericPrice = price.toString().replace(/[^\d.]/g, '');
    const num = parseFloat(numericPrice);
    
    if (isNaN(num)) return price;
    
    return `NT$ ${num.toLocaleString()}`;
}

// 格式化時間
function formatTimeAgo(crawlTime) {
    if (!crawlTime) return '未知時間';
    
    const now = new Date();
    const crawlDate = new Date(crawlTime);
    const diffMs = now - crawlDate;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffDays > 0) {
        return `${diffDays}天前`;
    } else if (diffHours > 0) {
        return `${diffHours}小時前`;
    } else {
        return '剛剛更新';
    }
}

// 打開商品詳情
function openProductDetail(url, platform) {
    if (url && url !== '#' && url !== '') {
        window.open(url, '_blank');
    } else {
        alert(`無法開啟商品頁面 - ${platform}`);
    }
}

// ===== 新增的資料庫管理功能 =====

// 顯示資料庫管理模態框
function showDatabaseManagement() {
    const modal = new bootstrap.Modal(document.getElementById('databaseModal'));
    modal.show();
}

// 匯出會話結果
async function exportSession(sessionId, keyword) {
    try {
        const response = await fetch(`/api/result/${sessionId}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            // 準備匯出資料
            let csvContent = 'data:text/csv;charset=utf-8,';
            csvContent += '商品名稱,價格,平台,商品連結\n';
            
            Object.keys(data.results).forEach(platform => {
                if (data.results[platform] && data.results[platform].products) {
                    data.results[platform].products.forEach(product => {
                        const title = `"${product.title.replace(/"/g, '""')}"`;
                        const price = product.price || 0;
                        const url = product.url || '';
                        
                        csvContent += `${title},${price},${platform.toUpperCase()},"${url}"\n`;
                    });
                }
            });
            
            // 建立下載連結
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', `products_${keyword}_${sessionId}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            alert(`成功匯出關鍵字「${keyword}」的搜尋結果！`);
        } else {
            alert('匯出失敗: ' + data.error);
        }
    } catch (error) {
        console.error('匯出會話時出錯:', error);
        alert('匯出時發生錯誤');
    }
}

// 刪除特定搜尋會話
async function deleteSession(sessionId, keyword) {
    if (!confirm(`確定要刪除關鍵字「${keyword}」的搜尋結果嗎？這將同時刪除所有相關的商品資料。`)) {
        return;
    }

    try {
        const response = await fetch(`/api/session/${sessionId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            alert('刪除成功！');
            loadResults(); // 重新載入結果
        } else {
            alert('刪除失敗: ' + data.error);
        }
    } catch (error) {
        console.error('刪除會話時出錯:', error);
        alert('刪除時發生錯誤');
    }
}

// 管理商品
async function manageProducts(sessionId) {
    try {
        const response = await fetch(`/api/result/${sessionId}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            showProductManagementModal(data, sessionId);
        } else {
            alert('載入商品資料失敗: ' + data.error);
        }
    } catch (error) {
        console.error('載入商品時出錯:', error);
        alert('載入商品時發生錯誤');
    }
}

// 顯示商品管理模態框
function showProductManagementModal(data, sessionId) {
    const modal = new bootstrap.Modal(document.getElementById('productModal'));
    const modalBody = document.getElementById('productModalBody');
    
    let productsHtml = '';
    let totalProducts = 0;
    
    // 統計所有商品
    Object.keys(data.results).forEach(platform => {
        if (data.results[platform] && data.results[platform].products) {
            totalProducts += data.results[platform].products.length;
        }
    });
    
    modalBody.innerHTML = `
        <div class="mb-3">
            <h6>關鍵字: ${data.statistics.keyword} (總共 ${totalProducts} 個商品)</h6>
            <div class="btn-group mb-2">
                <button class="btn btn-outline-danger btn-sm" onclick="deleteFilteredProducts(${sessionId}, 0)">
                    刪除低價商品 (< NT$ 100)
                </button>
                <button class="btn btn-outline-warning btn-sm" onclick="deleteFilteredProducts(${sessionId}, 'duplicate')">
                    刪除重複商品
                </button>
                <button class="btn btn-outline-info btn-sm" onclick="exportProducts(${sessionId})">
                    匯出全部商品
                </button>
            </div>
            <div class="btn-group mb-3">
                <button class="btn btn-outline-secondary btn-sm" onclick="toggleAllProducts(true)">
                    全選
                </button>
                <button class="btn btn-outline-secondary btn-sm" onclick="toggleAllProducts(false)">
                    取消全選
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="batchOperateProducts('delete')">
                    刪除選中
                </button>
                <button class="btn btn-outline-success btn-sm" onclick="batchOperateProducts('export')">
                    匯出選中
                </button>
            </div>
        </div>
        <div class="table-responsive" style="max-height: 500px;">
            <table class="table table-sm table-hover">
                <thead class="table-dark sticky-top">
                    <tr>
                        <th width="5%">
                            <input type="checkbox" id="selectAllProducts" onchange="toggleAllProducts(this.checked)">
                        </th>
                        <th width="15%">圖片</th>
                        <th width="35%">商品名稱</th>
                        <th width="15%">價格</th>
                        <th width="10%">平台</th>
                        <th width="20%">操作</th>
                    </tr>
                </thead>
                <tbody id="productTableBody">
                    <!-- 商品列表將在這裡生成 -->
                </tbody>
            </table>
        </div>
    `;
    
    // 生成商品表格
    const tableBody = modalBody.querySelector('#productTableBody');
    let rowHtml = '';
    let productIndex = 0;
    
    Object.keys(data.results).forEach(platform => {
        if (data.results[platform] && data.results[platform].products) {
            data.results[platform].products.forEach(product => {
                const imageUrl = product.image_url || 'https://via.placeholder.com/50x50?text=無圖';
                const title = product.title || '無標題';
                const price = product.price || 0;
                const url = product.url || '#';
                
                rowHtml += `
                    <tr id="product-row-${productIndex}">
                        <td>
                            <input type="checkbox" class="product-checkbox" data-product-id="${productIndex}" 
                                   onchange="updateSelectAllCheckbox()">
                        </td>
                        <td>
                            <img src="${imageUrl}" 
                                 class="img-thumbnail" style="width: 50px; height: 50px; object-fit: cover;"
                                 onerror="this.src='https://via.placeholder.com/50x50?text=無圖'">
                        </td>
                        <td>
                            <small title="${title}">${title.length > 50 ? title.substring(0, 50) + '...' : title}</small>
                        </td>
                        <td>
                            <strong class="text-danger">NT$ ${price.toLocaleString()}</strong>
                        </td>
                        <td>
                            <span class="badge bg-secondary">${platform.toUpperCase()}</span>
                        </td>
                        <td>
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-primary btn-sm" 
                                        onclick="openProductDetail('${url}', '${platform}')"
                                        title="開啟商品頁面">
                                    <i class="fas fa-external-link-alt"></i>
                                </button>
                                <button class="btn btn-outline-danger btn-sm" 
                                        onclick="deleteProduct(${sessionId}, ${productIndex})"
                                        title="刪除商品">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
                productIndex++;
            });
        }
    });
    
    tableBody.innerHTML = rowHtml;
    modal.show();
}

// 更新全選checkbox狀態
function updateSelectAllCheckbox() {
    const allCheckboxes = document.querySelectorAll('.product-checkbox');
    const checkedCheckboxes = document.querySelectorAll('.product-checkbox:checked');
    const selectAllCheckbox = document.getElementById('selectAllProducts');
    
    if (selectAllCheckbox) {
        if (checkedCheckboxes.length === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (checkedCheckboxes.length === allCheckboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
        }
    }
}

// 清理舊資料
async function cleanOldSessions(days) {
    if (!confirm(`確定要刪除 ${days} 天前的所有搜尋資料嗎？`)) {
        return;
    }

    try {
        const response = await fetch(`/api/database/clean/${days}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            alert(`成功清理了 ${data.deleted_sessions || 0} 個搜尋會話和 ${data.deleted_products || 0} 個商品`);
            loadResults();
        } else {
            alert('清理失敗: ' + data.error);
        }
    } catch (error) {
        console.error('清理資料時出錯:', error);
        alert('清理時發生錯誤');
    }
}

// 清理空的搜尋結果
async function cleanEmptySessions() {
    if (!confirm('確定要刪除所有沒有商品的搜尋結果嗎？')) {
        return;
    }

    try {
        const response = await fetch('/api/database/clean-empty', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            alert(`成功清理了 ${data.deleted_sessions || 0} 個空的搜尋會話`);
            loadResults();
        } else {
            alert('清理失敗: ' + data.error);
        }
    } catch (error) {
        console.error('清理空資料時出錯:', error);
        alert('清理時發生錯誤');
    }
}

// 優化資料庫
async function optimizeDatabase() {
    try {
        const response = await fetch('/api/database/optimize', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            alert('資料庫優化完成！');
        } else {
            alert('優化失敗: ' + data.error);
        }
    } catch (error) {
        console.error('優化資料庫時出錯:', error);
        alert('優化時發生錯誤');
    }
}

// 備份資料庫
async function backupDatabase() {
    try {
        const response = await fetch('/api/database/backup', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            alert(`備份成功！檔案路徑: ${data.backup_file}`);
        } else {
            alert('備份失敗: ' + data.error);
        }
    } catch (error) {
        console.error('備份資料庫時出錯:', error);
        alert('備份時發生錯誤');
    }
}

// 獲取資料庫統計
async function getDatabaseStats() {
    try {
        const response = await fetch('/api/database/stats');
        const data = await response.json();
        
        if (data.status === 'success') {
            const stats = data.stats;
            const resultDiv = document.getElementById('databaseStatsResult');
            
            resultDiv.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h6><i class="fas fa-chart-bar me-2"></i>資料庫統計資訊</h6>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <ul class="list-unstyled">
                                    <li><strong>總搜尋會話:</strong> ${stats.total_sessions}</li>
                                    <li><strong>總商品數:</strong> ${stats.total_products.toLocaleString()}</li>
                                    <li><strong>空會話數:</strong> ${stats.empty_sessions}</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <ul class="list-unstyled">
                                    <li><strong>資料庫大小:</strong> ${stats.db_size}</li>
                                    <li><strong>最新資料:</strong> ${stats.latest_session_date}</li>
                                    <li><strong>最舊資料:</strong> ${stats.oldest_session_date}</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            alert('獲取統計失敗: ' + data.error);
        }
    } catch (error) {
        console.error('獲取統計時出錯:', error);
        alert('獲取統計時發生錯誤');
    }
}

// ===== 商品管理功能 =====

// 刪除單個商品 (預留功能，目前只顯示提示)
async function deleteProduct(sessionId, productIndex) {
    alert('單個商品刪除功能開發中，請使用批量操作');
}

// 刪除過濾商品
async function deleteFilteredProducts(sessionId, filterType) {
    let confirmMessage = '';
    let filterParam = '';
    
    if (filterType === 0) {
        confirmMessage = '確定要刪除所有價格低於 NT$ 100 的商品嗎？';
        filterParam = 'low_price';
    } else if (filterType === 'duplicate') {
        confirmMessage = '確定要刪除重複的商品嗎？';
        filterParam = 'duplicate';
    } else {
        alert('不支援的過濾類型');
        return;
    }
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    // 目前只顯示提示，實際API需要後端實現
    alert('批量刪除功能開發中，將在下個版本提供');
}

// 匯出商品清單
async function exportProducts(sessionId) {
    try {
        const response = await fetch(`/api/result/${sessionId}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            // 準備匯出資料
            let csvContent = 'data:text/csv;charset=utf-8,';
            csvContent += '商品名稱,價格,平台,商品連結\n';
            
            Object.keys(data.results).forEach(platform => {
                if (data.results[platform] && data.results[platform].products) {
                    data.results[platform].products.forEach(product => {
                        const title = `"${product.title.replace(/"/g, '""')}"`;
                        const price = product.price || 0;
                        const url = product.url || '';
                        
                        csvContent += `${title},${price},${platform.toUpperCase()},"${url}"\n`;
                    });
                }
            });
            
            // 建立下載連結
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', `products_session_${sessionId}_${data.statistics.keyword}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            alert('商品清單已匯出！');
        } else {
            alert('匯出失敗: ' + data.error);
        }
    } catch (error) {
        console.error('匯出商品時出錯:', error);
        alert('匯出時發生錯誤');
    }
}

// 全選/取消全選商品
function toggleAllProducts(checked) {
    const checkboxes = document.querySelectorAll('.product-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = checked;
    });
}

// 獲取選中的商品
function getSelectedProducts() {
    const checkboxes = document.querySelectorAll('.product-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.dataset.productId));
}

// 批量操作選中商品
async function batchOperateProducts(operation) {
    const selectedProducts = getSelectedProducts();
    
    if (selectedProducts.length === 0) {
        alert('請先選擇要操作的商品');
        return;
    }
    
    switch (operation) {
        case 'delete':
            if (confirm(`確定要刪除選中的 ${selectedProducts.length} 個商品嗎？`)) {
                alert('批量刪除功能開發中');
            }
            break;
        case 'export':
            alert('批量匯出功能開發中');
            break;
        default:
            alert('不支援的操作類型');
    }
}
