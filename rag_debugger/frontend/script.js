const API_BASE_URL = "http://127.0.0.1:8000";

const elements = {
    categoryFilter: document.getElementById("categoryFilter"),
    ragBrief: document.getElementById("ragBrief"),
    resultCountBadge: document.getElementById("resultCountBadge"),
    results: document.getElementById("results"),
    resultsSection: document.getElementById("resultsSection"),
    resultsMeta: document.getElementById("resultsMeta"),
    resultsTitle: document.getElementById("resultsTitle"),
    searchButton: document.getElementById("searchButton"),
    searchInput: document.getElementById("searchInput"),
    statCategories: document.getElementById("statCategories"),
    statProducts: document.getElementById("statProducts"),
    statVarieties: document.getElementById("statVarieties"),
    statusPill: document.getElementById("statusPill"),
};

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function formatPrice(value) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
    })
        .format(Number(value || 0))
        .replace(/\u00a0/g, " ");
}

function truncateText(text, maxLength = 112) {
    if (!text || text.length <= maxLength) {
        return text;
    }
    return `${text.slice(0, maxLength - 1).trimEnd()}...`;
}

function getCategoryPalette(category) {
    const palettes = {
        Accessories: { start: "#F7FAFF", end: "#DEEAFE", accent: "#4F7BFF", accentSoft: "#C5D6FF", ink: "#163668" },
        Audio: { start: "#F3F8FF", end: "#D9E7FF", accent: "#3B82F6", accentSoft: "#BDD6FF", ink: "#15345E" },
        Computers: { start: "#F5F7FF", end: "#E0E7FF", accent: "#6366F1", accentSoft: "#C9CAFF", ink: "#1D2C62" },
        Creator: { start: "#FFF8F2", end: "#FFE4CC", accent: "#F59E0B", accentSoft: "#FFD7A0", ink: "#6C3B15" },
        Gaming: { start: "#FAF5FF", end: "#EBD9FF", accent: "#A855F7", accentSoft: "#DEC2FF", ink: "#462072" },
        Mobile: { start: "#F1FBFF", end: "#D7F5FF", accent: "#06B6D4", accentSoft: "#B6F0FF", ink: "#154A5D" },
        Office: { start: "#F8FAFC", end: "#E8EEF9", accent: "#64748B", accentSoft: "#D1D8E8", ink: "#334155" },
        "Smart Home": { start: "#F2FFF7", end: "#D9FBE7", accent: "#22C55E", accentSoft: "#BDF0CF", ink: "#1B5B34" },
        Wearables: { start: "#FFF6FB", end: "#FFE0F2", accent: "#EC4899", accentSoft: "#FFC5E5", ink: "#6B1F4A" },
    };
    return palettes[category] || palettes.Computers;
}

function getProductIcon(product) {
    const label = `${product.product_type || ""} ${product.name || ""}`.toLowerCase();

    if (label.includes("headset")) {
        return `<path d="M248 238c0-70 56-126 126-126s126 56 126 126v78h-42v-78c0-47-37-84-84-84s-84 37-84 84v78h-42z" fill="none" stroke="currentColor" stroke-width="22" stroke-linecap="round"/><rect x="220" y="292" width="46" height="82" rx="18" fill="currentColor"/><rect x="482" y="292" width="46" height="82" rx="18" fill="currentColor"/><path d="M490 328c34 2 54 18 54 44 0 22-18 36-44 36h-18" fill="none" stroke="currentColor" stroke-width="18" stroke-linecap="round"/><circle cx="484" cy="408" r="12" fill="currentColor"/>`;
    }
    if (label.includes("headphone")) {
        return `<path d="M248 238c0-70 56-126 126-126s126 56 126 126v68h-38v-68c0-47-37-84-84-84s-84 37-84 84v68h-38z" fill="none" stroke="currentColor" stroke-width="22" stroke-linecap="round"/><rect x="226" y="286" width="52" height="92" rx="22" fill="currentColor"/><rect x="442" y="286" width="52" height="92" rx="22" fill="currentColor"/><path d="M278 324h164" stroke="currentColor" stroke-width="16" stroke-linecap="round" opacity="0.55"/>`;
    }
    if (label.includes("earbud")) {
        return `<path d="M286 198c36 0 66 28 66 66 0 31-20 56-48 64v84c0 18-14 32-32 32s-32-14-32-32V264c0-36 18-66 46-66zM478 198c36 0 66 28 66 66v148c0 18-14 32-32 32s-32-14-32-32v-84c-28-8-48-33-48-64 0-38 30-66 66-66z" fill="currentColor"/>`;
    }
    if (label.includes("speaker") || label.includes("soundbar")) {
        return `<rect x="236" y="182" width="276" height="216" rx="34" fill="none" stroke="currentColor" stroke-width="22"/><circle cx="374" cy="248" r="42" fill="none" stroke="currentColor" stroke-width="20"/><circle cx="374" cy="248" r="14" fill="currentColor"/><circle cx="374" cy="336" r="30" fill="none" stroke="currentColor" stroke-width="18"/>`;
    }
    if (label.includes("keyboard")) {
        return `<rect x="186" y="212" width="376" height="178" rx="28" fill="none" stroke="currentColor" stroke-width="20"/><g fill="currentColor">${Array.from({ length: 15 }).map((_, index) => {
            const row = Math.floor(index / 5);
            const col = index % 5;
            return `<rect x="${228 + col * 62}" y="${248 + row * 42}" width="38" height="24" rx="6"/>`;
        }).join("")}</g>`;
    }
    if (label.includes("mouse")) {
        return `<rect x="282" y="170" width="156" height="244" rx="78" fill="none" stroke="currentColor" stroke-width="22"/><path d="M360 170v94" stroke="currentColor" stroke-width="20" stroke-linecap="round"/>`;
    }
    if (label.includes("watch") || label.includes("band")) {
        return `<rect x="300" y="132" width="120" height="80" rx="22" fill="none" stroke="currentColor" stroke-width="20"/><rect x="264" y="208" width="192" height="184" rx="48" fill="none" stroke="currentColor" stroke-width="22"/><circle cx="360" cy="300" r="46" fill="none" stroke="currentColor" stroke-width="18"/>`;
    }
    if (label.includes("ring")) {
        return `<circle cx="360" cy="286" r="98" fill="none" stroke="currentColor" stroke-width="34"/><circle cx="360" cy="286" r="44" fill="none" stroke="currentColor" stroke-width="14"/>`;
    }
    if (label.includes("chair")) {
        return `<path d="M278 244h164v92H278zM300 336v64M420 336v64M258 400h204M286 244v-52c0-28 22-50 50-50h48c32 0 58 26 58 58v44" fill="none" stroke="currentColor" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/>`;
    }
    if (label.includes("backpack")) {
        return `<path d="M278 206c0-44 36-80 82-80s82 36 82 80v18h24c26 0 48 22 48 48v126c0 28-22 50-48 50H254c-26 0-48-22-48-50V272c0-26 22-48 48-48h24z" fill="none" stroke="currentColor" stroke-width="20"/><path d="M314 224v-18c0-26 20-46 46-46s46 20 46 46v18" stroke="currentColor" stroke-width="18" stroke-linecap="round"/>`;
    }
    if (label.includes("camera") || label.includes("webcam") || label.includes("monitor")) {
        return `<rect x="204" y="174" width="312" height="196" rx="28" fill="none" stroke="currentColor" stroke-width="20"/><circle cx="360" cy="272" r="58" fill="none" stroke="currentColor" stroke-width="18"/><circle cx="360" cy="272" r="18" fill="currentColor"/><path d="M304 410h112M360 370v40" stroke="currentColor" stroke-width="18" stroke-linecap="round"/>`;
    }
    if (label.includes("ssd") || label.includes("hub") || label.includes("charger") || label.includes("adapter") || label.includes("bank")) {
        return `<rect x="216" y="194" width="288" height="180" rx="30" fill="none" stroke="currentColor" stroke-width="20"/><path d="M270 248h180M270 300h116M448 238v92" stroke="currentColor" stroke-width="18" stroke-linecap="round"/>`;
    }
    if (label.includes("tripod") || label.includes("gimbal")) {
        return `<path d="M360 160v176M360 160l-44 54M360 160l44 54M360 336l-76 108M360 336l76 108" fill="none" stroke="currentColor" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/><circle cx="360" cy="138" r="26" fill="currentColor"/>`;
    }
    if (label.includes("bulb") || label.includes("plug")) {
        return `<path d="M360 162c58 0 104 46 104 104 0 34-16 60-38 80-16 14-24 32-24 52h-84c0-20-8-38-24-52-22-20-38-46-38-80 0-58 46-104 104-104z" fill="none" stroke="currentColor" stroke-width="20"/><path d="M328 398h64M336 432h48" stroke="currentColor" stroke-width="18" stroke-linecap="round"/>`;
    }
    if (label.includes("laptop") || label.includes("monitor") || label.includes("stand")) {
        return `<rect x="228" y="188" width="264" height="154" rx="20" fill="none" stroke="currentColor" stroke-width="20"/><path d="M202 360h316l-32 44H234z" fill="none" stroke="currentColor" stroke-width="18" stroke-linejoin="round"/>`;
    }
    return `<rect x="232" y="186" width="256" height="188" rx="34" fill="none" stroke="currentColor" stroke-width="20"/><path d="M286 240h148M286 288h148M286 336h96" stroke="currentColor" stroke-width="18" stroke-linecap="round"/>`;
}

function buildProductArt(product) {
    const palette = getCategoryPalette(product.category);
    const icon = getProductIcon(product);
    const productLabel = escapeHtml(product.product_type || product.name);
    const brandLabel = escapeHtml(product.brand || "Catalog");
    const categoryLabel = escapeHtml(product.category || "Catalog");

    const svg = `
        <svg xmlns="http://www.w3.org/2000/svg" width="900" height="620" viewBox="0 0 900 620">
            <defs>
                <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="${palette.start}"/>
                    <stop offset="100%" stop-color="${palette.end}"/>
                </linearGradient>
                <linearGradient id="orb" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="${palette.accent}" stop-opacity="0.32"/>
                    <stop offset="100%" stop-color="${palette.accentSoft}" stop-opacity="0.08"/>
                </linearGradient>
                <linearGradient id="blob" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="${palette.accentSoft}" stop-opacity="0.94"/>
                    <stop offset="100%" stop-color="${palette.accent}" stop-opacity="0.26"/>
                </linearGradient>
            </defs>
            <rect width="900" height="620" rx="44" fill="url(#bg)"/>
            <circle cx="714" cy="120" r="132" fill="url(#orb)"/>
            <circle cx="154" cy="520" r="94" fill="rgba(255,255,255,0.44)"/>
            <path d="M172 148C250 82 390 82 468 150C520 196 544 276 514 334C484 392 400 420 318 408C242 396 180 348 160 282C146 232 148 184 172 148Z" fill="url(#blob)"/>
            <rect x="92" y="80" width="180" height="48" rx="24" fill="rgba(255,255,255,0.78)"/>
            <text x="124" y="112" fill="${palette.accent}" font-family="Montserrat, Arial, sans-serif" font-size="22" font-weight="800" letter-spacing="1.1">${brandLabel}</text>
            <g transform="translate(10 -6) scale(0.82)" fill="${palette.ink}" stroke="${palette.ink}" stroke-linecap="round" stroke-linejoin="round">${icon}</g>
            <text x="96" y="468" fill="${palette.ink}" font-family="Lexend, Montserrat, Arial, sans-serif" font-size="54" font-weight="800">${productLabel}</text>
            <text x="96" y="518" fill="${palette.accent}" font-family="Montserrat, Arial, sans-serif" font-size="22" font-weight="700" letter-spacing="4">${categoryLabel.toUpperCase()}</text>
            <circle cx="734" cy="498" r="20" fill="${palette.accent}" fill-opacity="0.24"/>
            <circle cx="782" cy="498" r="12" fill="${palette.accent}" fill-opacity="0.18"/>
            <circle cx="822" cy="498" r="8" fill="${palette.accent}" fill-opacity="0.12"/>
        </svg>
    `;

    return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function updateResultCount(count) {
    elements.resultCountBadge.textContent = `${count} ${count === 1 ? "item" : "items"}`;
}

function scrollToResults() {
    if (!elements.resultsSection) {
        return;
    }
    elements.resultsSection.scrollIntoView({
        behavior: "smooth",
        block: "start",
    });
}

function setEmptyState(message, metaText = "") {
    elements.results.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
    elements.resultsMeta.textContent = metaText;
    updateResultCount(0);
    elements.ragBrief.classList.add("is-hidden");
    elements.ragBrief.innerHTML = "";
}

function renderRagBrief(ragBrief) {
    if (!ragBrief) {
        elements.ragBrief.classList.add("is-hidden");
        elements.ragBrief.innerHTML = "";
        return;
    }

    const reasons = Array.isArray(ragBrief.reasons) ? ragBrief.reasons.slice(0, 2) : [];
    const topPick = ragBrief.top_pick || {};

    elements.ragBrief.innerHTML = `
        <div class="rag-main">
            <span class="rag-kicker">AI Recommendation Brief</span>
            <h3>${escapeHtml(ragBrief.headline || "Retrieval summary")}</h3>
            <p class="rag-summary">${escapeHtml(ragBrief.summary || "")}</p>
            <div class="rag-inline-metrics">
                <span class="rag-inline-chip"><strong>Top pick:</strong> ${escapeHtml(topPick.name || "--")}</span>
                <span class="rag-inline-chip"><strong>Category:</strong> ${escapeHtml(topPick.category || "--")}</span>
                <span class="rag-inline-chip"><strong>Price:</strong> ${escapeHtml(formatPrice(topPick.price_inr || 0))}</span>
            </div>
            <div class="rag-points">
                ${reasons.map((reason) => `<div class="rag-point">${escapeHtml(reason)}</div>`).join("")}
            </div>
        </div>
        <div class="rag-side">
            <article class="rag-metric comparison">
                <span class="rag-metric-label">Comparison</span>
                <span class="rag-metric-value">${escapeHtml(ragBrief.comparison || "")}</span>
            </article>
            <p class="rag-follow-up">${escapeHtml(ragBrief.follow_up || "")}</p>
        </div>
    `;
    elements.ragBrief.classList.remove("is-hidden");
}

function renderProducts(products, metaText, emptyMessage = "Product not available.") {
    if (!Array.isArray(products) || products.length === 0) {
        setEmptyState(emptyMessage, metaText);
        return;
    }

    elements.results.innerHTML = products
        .map((product) => {
            const imageUrl = buildProductArt(product);
            const scoreBadge = typeof product.score === "number"
                ? `<span class="badge score">AI Match ${Math.round(product.score_percent || 0)}%</span>`
                : `<span class="badge score">Featured</span>`;

            return `
            <article class="product-card">
                <div class="product-visual">
                    <img
                        class="product-image"
                        src="${imageUrl}"
                        alt="${escapeHtml(product.name)}"
                        loading="lazy"
                    >
                    <div class="price-chip">${escapeHtml(formatPrice(product.price_inr))}</div>
                </div>
                <div class="product-content">
                    <div class="product-top">
                        <span class="badge category">${escapeHtml(product.category)}</span>
                        ${scoreBadge}
                    </div>
                    <h3>${escapeHtml(product.name)}</h3>
                    <div class="product-meta">
                        <span>${escapeHtml(product.brand || "Catalog")}</span>
                        <span>${escapeHtml(product.product_type || product.category)}</span>
                    </div>
                    <p>${escapeHtml(truncateText(product.description))}</p>
                </div>
            </article>
            `;
        })
        .join("");

    elements.resultsMeta.textContent = metaText;
    updateResultCount(products.length);
}

function setStatusStats(status) {
    const categories = Array.isArray(status.categories) ? status.categories : [];
    elements.statProducts.textContent = status.indexed_products ?? "--";
    elements.statVarieties.textContent = status.catalog_varieties ?? "--";
    elements.statCategories.textContent = categories.length || "--";
}

async function loadStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        if (!response.ok) {
            throw new Error("Status request failed");
        }

        const status = await response.json();
        const categories = Array.isArray(status.categories) ? status.categories : [];
        const backendLabel = status.connected
            ? `${status.vector_backend} | ${status.embedding_model}`
            : "Backend offline";

        elements.statusPill.textContent = backendLabel;
        elements.statusPill.classList.toggle("warning", !status.connected || status.vector_backend !== "Endee");
        setStatusStats(status);

        elements.categoryFilter.innerHTML = [
            `<option value="">All Categories</option>`,
            ...categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`),
        ].join("");
    } catch (error) {
        elements.statusPill.textContent = "Backend offline";
        elements.statusPill.classList.add("warning");
        elements.statProducts.textContent = "--";
        elements.statVarieties.textContent = "--";
        elements.statCategories.textContent = "--";
    }
}

async function loadCatalogProducts({ limit = 12, category = "", title = "Catalog Highlights", shouldScroll = false } = {}) {
    elements.resultsTitle.textContent = title;
    setEmptyState("Loading product catalog...");

    try {
        const params = new URLSearchParams({ limit: String(limit) });
        if (category) {
            params.set("category", category);
        }

        const response = await fetch(`${API_BASE_URL}/products?${params.toString()}`);
        if (!response.ok) {
            throw new Error("Products request failed");
        }

        const data = await response.json();
        const categoryLabel = data.category || category;
        const metaText = categoryLabel
            ? `Showing ${data.count} curated products in ${categoryLabel}.`
            : `Showing ${data.count} highlighted products from the 250-item catalog.`;

        renderProducts(
            data.products,
            metaText,
            "No products available in this category yet.",
        );
        renderRagBrief(null);
        if (shouldScroll) {
            scrollToResults();
        }
    } catch (error) {
        setEmptyState("Unable to load products. Start the FastAPI backend and try again.", "Backend connection required.");
        if (shouldScroll) {
            scrollToResults();
        }
    }
}

async function searchProducts() {
    const query = elements.searchInput.value.trim();
    const category = elements.categoryFilter.value.trim();

    if (!query) {
        await loadCatalogProducts({
            limit: category ? 12 : 16,
            category,
            title: category ? `${category} Collection` : "Catalog Highlights",
            shouldScroll: true,
        });
        return;
    }

    elements.searchButton.disabled = true;
    elements.searchButton.textContent = "Searching...";
    elements.resultsTitle.textContent = "Recommended Products";
    setEmptyState("Finding semantically similar products...");

    try {
        const params = new URLSearchParams({
            query,
            top_k: "8",
        });

        if (category) {
            params.set("category", category);
        }

        const response = await fetch(`${API_BASE_URL}/recommend?${params.toString()}`);
        if (!response.ok) {
            throw new Error("Recommendation request failed");
        }

        const data = await response.json();
        const emptyMessage = data.message || "Product not available.";
        const metaText = data.available
            ? `Showing ${data.recommendations.length} AI-ranked matches${category ? ` in ${category}` : ""}. Powered by ${data.status.vector_backend}.`
            : emptyMessage;

        renderProducts(data.recommendations, metaText, emptyMessage);
        renderRagBrief(data.rag_brief);
        scrollToResults();
    } catch (error) {
        setEmptyState("Search failed. Check that the backend is running on port 8000.", "Backend error.");
        scrollToResults();
    } finally {
        elements.searchButton.disabled = false;
        elements.searchButton.textContent = "Search AI";
    }
}

elements.searchButton.addEventListener("click", searchProducts);
elements.searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        searchProducts();
    }
});

document.addEventListener("DOMContentLoaded", async () => {
    await loadStatus();
    await loadCatalogProducts();
});
