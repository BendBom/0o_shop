// ============= CONFIG =============
const API_BASE = window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : window.location.origin;

// ============= STATE =============
let token = localStorage.getItem("oshop_token") || null;
let currentUser = null;
let searchTimeout = null;

// ============= API HELPER =============
async function api(method, path, body = null) {
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = "Bearer " + token;

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    const resp = await fetch(API_BASE + path, opts);
    if (resp.status === 204) return null;
    const data = await resp.json().catch(() => null);
    if (!resp.ok) {
        throw new Error(data?.detail || `Error ${resp.status}`);
    }
    return data;
}

// ============= NAVIGATION =============
function navigate(page) {
    document.querySelectorAll(".page").forEach(el => el.style.display = "none");
    const target = document.getElementById("page-" + page);
    if (target) target.style.display = "block";

    if (page === "catalog") loadProducts();
    if (page === "cart") loadCart();
    return false;
}

function updateNav() {
    const isLoggedIn = !!token;
    document.getElementById("nav-login").style.display = isLoggedIn ? "none" : "";
    document.getElementById("nav-register").style.display = isLoggedIn ? "none" : "";
    document.getElementById("nav-logout").style.display = isLoggedIn ? "" : "none";
    document.getElementById("nav-cart").style.display = isLoggedIn ? "" : "none";

    const userSpan = document.getElementById("nav-user");
    if (isLoggedIn && currentUser) {
        userSpan.style.display = "";
        userSpan.textContent = currentUser.username;
    } else {
        userSpan.style.display = "none";
    }
}

// ============= AUTH =============
async function handleLogin(event) {
    event.preventDefault();
    const msg = document.getElementById("login-msg");
    msg.textContent = "";
    msg.className = "form-msg";

    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;

    try {
        const data = await api("POST", "/api/auth/login", { username, password });
        token = data.access_token;
        localStorage.setItem("oshop_token", token);
        await fetchCurrentUser();
        updateNav();
        navigate("catalog");
    } catch (err) {
        msg.textContent = err.message;
    }
    return false;
}

async function handleRegister(event) {
    event.preventDefault();
    const msg = document.getElementById("register-msg");
    msg.textContent = "";
    msg.className = "form-msg";

    const username = document.getElementById("reg-username").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;

    try {
        await api("POST", "/api/auth/register", { username, email, password });
        msg.textContent = "Registration successful! Please login.";
        msg.className = "form-msg success";
        setTimeout(() => navigate("login"), 1500);
    } catch (err) {
        msg.textContent = err.message;
    }
    return false;
}

async function fetchCurrentUser() {
    try {
        currentUser = await api("GET", "/api/auth/me");
    } catch {
        currentUser = null;
        token = null;
        localStorage.removeItem("oshop_token");
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem("oshop_token");
    updateNav();
    navigate("catalog");
}

// ============= PRODUCTS =============
async function loadProducts() {
    const grid = document.getElementById("products-grid");
    const empty = document.getElementById("catalog-empty");
    const search = document.getElementById("search-input").value.trim();

    try {
        const params = search ? `?search=${encodeURIComponent(search)}` : "";
        const products = await api("GET", "/api/products/" + params);

        if (!products || products.length === 0) {
            grid.innerHTML = "";
            empty.style.display = "block";
            return;
        }

        empty.style.display = "none";
        grid.innerHTML = products.map(p => `
            <div class="product-card">
                <h3>${escapeHtml(p.name)}</h3>
                <div class="price">$${Number(p.price).toFixed(2)}</div>
                <div class="stock">In stock: ${p.stock}</div>
                ${p.description ? `<div class="description">${escapeHtml(p.description)}</div>` : ""}
                ${token ? `<button onclick="addToCart(${p.id})">Add to Cart</button>` : ""}
            </div>
        `).join("");
    } catch (err) {
        grid.innerHTML = `<p>Error loading products: ${escapeHtml(err.message)}</p>`;
    }
}

function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(loadProducts, 300);
}

// ============= CART =============
async function loadCart() {
    const container = document.getElementById("cart-items");
    const totalEl = document.getElementById("cart-total");
    const emptyEl = document.getElementById("cart-empty");
    const clearBtn = document.getElementById("clear-cart-btn");

    try {
        const items = await api("GET", "/api/cart/");

        if (!items || items.length === 0) {
            container.innerHTML = "";
            totalEl.textContent = "";
            emptyEl.style.display = "block";
            clearBtn.style.display = "none";
            updateCartCount(0);
            return;
        }

        emptyEl.style.display = "none";
        clearBtn.style.display = "";

        let total = 0;
        container.innerHTML = items.map(item => {
            const subtotal = item.product_price * item.quantity;
            total += subtotal;
            return `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <h3>${escapeHtml(item.product_name)}</h3>
                        <p>$${Number(item.product_price).toFixed(2)} x ${item.quantity} = $${subtotal.toFixed(2)}</p>
                    </div>
                    <div class="cart-item-actions">
                        <input type="number" min="1" value="${item.quantity}"
                               onchange="updateCartItem(${item.id}, this.value)">
                        <button class="danger" onclick="removeCartItem(${item.id})">Remove</button>
                    </div>
                </div>
            `;
        }).join("");

        totalEl.textContent = "Total: $" + total.toFixed(2);
        updateCartCount(items.length);
    } catch (err) {
        container.innerHTML = `<p>Error loading cart: ${escapeHtml(err.message)}</p>`;
    }
}

async function addToCart(productId) {
    try {
        await api("POST", "/api/cart/", { product_id: productId, quantity: 1 });
        const count = document.getElementById("cart-count");
        count.textContent = count.textContent ? `(${parseInt(count.textContent.replace(/\D/g, "") || "0") + 1})` : "(1)";
    } catch (err) {
        alert(err.message);
    }
}

async function updateCartItem(itemId, quantity) {
    const qty = parseInt(quantity);
    if (qty < 1) return;
    try {
        await api("PUT", `/api/cart/${itemId}`, { quantity: qty });
        loadCart();
    } catch (err) {
        alert(err.message);
    }
}

async function removeCartItem(itemId) {
    try {
        await api("DELETE", `/api/cart/${itemId}`);
        loadCart();
    } catch (err) {
        alert(err.message);
    }
}

async function clearCart() {
    try {
        await api("DELETE", "/api/cart/");
        loadCart();
    } catch (err) {
        alert(err.message);
    }
}

function updateCartCount(count) {
    const el = document.getElementById("cart-count");
    el.textContent = count > 0 ? `(${count})` : "";
}

// ============= UTILS =============
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ============= INIT =============
(async function init() {
    if (token) {
        await fetchCurrentUser();
    }
    updateNav();
    navigate("catalog");
})();
