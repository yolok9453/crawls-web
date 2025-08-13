// 主頁面的JavaScript功能
let allResults = [];
let filteredResults = [];

// 頁面載入完成後初始化
document.addEventListener("DOMContentLoaded", function () {
  console.log("頁面載入完成，開始初始化...");
  loadResults();
  loadPlatforms();
  loadDailyDealsStats(); // 載入每日促銷統計
  
  // 添加調試信息
  setTimeout(() => {
    console.log("5秒後檢查載入狀態...");
    const spinner = document.getElementById("loadingSpinner");
    const table = document.querySelector(".table-responsive");
    const emptyMessage = document.getElementById("emptyMessage");
    
    console.log("載入動畫顯示狀態:", spinner?.style.display);
    console.log("表格顯示狀態:", table?.style.display);
    console.log("空訊息顯示狀態:", emptyMessage?.style.display);
    console.log("所有結果數量:", allResults.length);
    console.log("過濾結果數量:", filteredResults.length);
  }, 5000);
});

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
            <span class="badge ${result.status === 'success' ? 'bg-success' : 'bg-warning'}">${result.status}</span>
        </td>
        <td>
            <div class="btn-group btn-group-sm" role="group">
                <button class="btn btn-outline-primary" onclick="viewResult(${
                  result.id
                })" title="查看詳細">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-outline-info" onclick="showStatistics(${
                  result.id
                })" title="統計資訊">
                    <i class="fas fa-chart-bar"></i>
                </button>
                <button class="btn btn-outline-secondary" onclick="downloadResult()" title="下載功能已停用" disabled>
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
