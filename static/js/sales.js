/**
 * EXPIRYGUARD AI — QUICK SALES WORKFLOW
 * Fast barcode lookup, quantity steppers, atomic stock deduction & receipt update
 */

let activeProduct = null;
let currentQuantity = 1;
let salesCameraReader = null;

function updateSalesTotal() {
  if (!activeProduct) return;
  const unitPrice = activeProduct.price;
  const total = Math.round(currentQuantity * unitPrice * 100) / 100;
  
  const totalDisplay = document.getElementById('sales-bill-total');
  const sellBtn = document.getElementById('btn-execute-sale');
  
  if (totalDisplay) totalDisplay.textContent = `₹${total.toFixed(2)}`;
  if (sellBtn) {
    sellBtn.textContent = `Complete Sale (₹${total.toFixed(2)})`;
    sellBtn.disabled = (currentQuantity <= 0 || currentQuantity > activeProduct.available_quantity);
  }
}

function setQuantity(val) {
  if (!activeProduct) return;
  const num = parseInt(val, 10);
  if (isNaN(num) || num < 1) {
    currentQuantity = 1;
  } else if (num > activeProduct.available_quantity) {
    currentQuantity = activeProduct.available_quantity;
    showSalesToast(`Cannot exceed available stock (${activeProduct.available_quantity} available)`, "warning");
  } else {
    currentQuantity = num;
  }
  
  document.getElementById('stepper-qty').textContent = currentQuantity;
  updateSalesTotal();
}

function adjustQuantity(delta) {
  setQuantity(currentQuantity + delta);
}

async function lookupProductForSale(barcode) {
  const cleanBarcode = barcode.trim();
  if (!cleanBarcode) {
    showSalesToast("Please enter or scan a barcode.", "warning");
    return;
  }

  const findBtn = document.getElementById('btn-lookup-product');
  if (findBtn) {
    findBtn.disabled = true;
    findBtn.textContent = "Finding...";
  }

  try {
    const res = await fetch(`/api/sales/lookup/${encodeURIComponent(cleanBarcode)}`);
    const data = await res.json();

    if (data.found && data.product) {
      activeProduct = data.product;
      currentQuantity = 1;

      // Populate UI
      document.getElementById('sales-item-name').textContent = activeProduct.product_name;
      document.getElementById('sales-item-barcode').textContent = activeProduct.barcode;
      document.getElementById('sales-item-stock').textContent = activeProduct.available_quantity;
      document.getElementById('sales-item-price').textContent = `₹${activeProduct.price.toFixed(2)}`;
      
      document.getElementById('stepper-qty').textContent = "1";
      document.getElementById('sales-bill-card').style.display = 'block';
      
      updateSalesTotal();
      showSalesToast(`Found: ${activeProduct.product_name}`, "info");
    } else {
      activeProduct = null;
      document.getElementById('sales-bill-card').style.display = 'none';
      showSalesToast(data.message || "Product not found in your inventory.", "danger");
    }
  } catch (err) {
    console.error("Lookup error:", err);
    showSalesToast("Failed to connect to server.", "danger");
  } finally {
    if (findBtn) {
      findBtn.disabled = false;
      findBtn.textContent = translateKey('sales_lookup_btn', 'Find Product');
    }
  }
}

async function executeSale() {
  if (!activeProduct) return;
  
  if (currentQuantity <= 0) {
    showSalesToast("Quantity sold must be at least 1.", "warning");
    return;
  }

  if (currentQuantity > activeProduct.available_quantity) {
    showSalesToast(`Cannot sell ${currentQuantity}. Only ${activeProduct.available_quantity} units available.`, "danger");
    return;
  }

  const sellBtn = document.getElementById('btn-execute-sale');
  sellBtn.disabled = true;
  sellBtn.textContent = "Processing Sale...";

  try {
    const res = await fetch('/api/sales/record', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        barcode: activeProduct.barcode,
        quantity_sold: currentQuantity
      })
    });

    const data = await res.json();

    if (data.success) {
      showSalesToast(data.message, "success");
      
      // Update UI stock
      activeProduct.available_quantity = data.remaining_stock;
      document.getElementById('sales-item-stock').textContent = data.remaining_stock;

      // Add to recent sales table dynamically
      prependRecentSaleRow({
        product_name: activeProduct.product_name,
        quantity_sold: data.sold_qty,
        unit_price: activeProduct.price,
        total_amount: data.total_amount,
        remaining: data.remaining_stock,
        timestamp: "Just now"
      });

      // Reset or adjust
      if (data.remaining_stock <= 0) {
        currentQuantity = 0;
        document.getElementById('stepper-qty').textContent = "0";
        sellBtn.disabled = true;
        sellBtn.textContent = "Out of Stock";
      } else {
        currentQuantity = 1;
        document.getElementById('stepper-qty').textContent = "1";
        updateSalesTotal();
      }
      
      // Play ding sound
      playSaleBeep();
    } else {
      showSalesToast(data.message || "Sale failed.", "danger");
      sellBtn.disabled = false;
      updateSalesTotal();
    }
  } catch (err) {
    console.error("Sale error:", err);
    showSalesToast("Server error recording sale.", "danger");
    sellBtn.disabled = false;
    updateSalesTotal();
  }
}

function prependRecentSaleRow(sale) {
  const tableBody = document.getElementById('recent-sales-tbody');
  const emptyRow = document.getElementById('no-sales-row');
  if (emptyRow) emptyRow.remove();

  if (!tableBody) return;

  const row = document.createElement('tr');
  row.className = "flash-highlight";
  row.innerHTML = `
    <td><strong>${sale.product_name}</strong></td>
    <td><span class="badge badge-pink">${sale.quantity_sold} sold</span></td>
    <td>₹${sale.unit_price}</td>
    <td><strong>₹${sale.total_amount}</strong></td>
    <td><span class="badge badge-success">${sale.remaining} left</span></td>
    <td><small class="text-muted">${sale.timestamp}</small></td>
  `;
  tableBody.insertBefore(row, tableBody.firstChild);
}

function playSaleBeep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.setValueAtTime(880, ctx.currentTime + 0.1); // A5
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
    osc.start();
    osc.stop(ctx.currentTime + 0.3);
  } catch (e) {}
}

function showSalesToast(msg, type = "info") {
  const container = document.getElementById('sales-toast-area');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.innerHTML = `<span>${msg}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

// Camera Scanner Modal for Sales
function openSalesScannerModal() {
  const modal = document.getElementById('sales-camera-modal');
  if (!modal) return;
  modal.classList.add('active');

  if (typeof ZXing !== 'undefined') {
    salesCameraReader = new ZXing.BrowserMultiFormatReader();
    const videoElem = document.getElementById('sales-scanner-video');
    salesCameraReader.decodeFromConstraints({
      video: { facingMode: { ideal: "environment" } }
    }, videoElem, (result) => {
      if (result) {
        const code = result.getText();
        closeSalesScannerModal();
        document.getElementById('sales-barcode-input').value = code;
        lookupProductForSale(code);
      }
    });
  }
}

function closeSalesScannerModal() {
  const modal = document.getElementById('sales-camera-modal');
  if (modal) modal.classList.remove('active');
  if (salesCameraReader) {
    salesCameraReader.reset();
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const lookupBtn = document.getElementById('btn-lookup-product');
  const barcodeInput = document.getElementById('sales-barcode-input');
  
  if (lookupBtn && barcodeInput) {
    lookupBtn.addEventListener('click', () => lookupProductForSale(barcodeInput.value));
    barcodeInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        lookupProductForSale(barcodeInput.value);
      }
    });
  }

  const minusBtn = document.getElementById('btn-stepper-minus');
  const plusBtn = document.getElementById('btn-stepper-plus');
  if (minusBtn && plusBtn) {
    minusBtn.addEventListener('click', () => adjustQuantity(-1));
    plusBtn.addEventListener('click', () => adjustQuantity(1));
  }

  const sellBtn = document.getElementById('btn-execute-sale');
  if (sellBtn) {
    sellBtn.addEventListener('click', executeSale);
  }

  const openCamBtn = document.getElementById('btn-open-sales-scanner');
  if (openCamBtn) {
    openCamBtn.addEventListener('click', openSalesScannerModal);
  }

  const closeCamBtn = document.getElementById('btn-close-sales-scanner');
  if (closeCamBtn) {
    closeCamBtn.addEventListener('click', closeSalesScannerModal);
  }
});
