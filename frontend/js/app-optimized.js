/**
 * Optimized Application Logic
 * Enhanced with debouncing, caching, and efficient data handling
 */

// API Configuration
const API_BASE_URL = 'http://127.0.0.1:5000/api';

// Performance Configuration
const DEBOUNCE_DELAY = 300; // ms
const CACHE_DURATION = 60000; // 1 minute
const PAGINATION_SIZE = 1000; // Rows per page

// Global state
let gridApi = null;
let currentData = [];
let currentFilters = {
    date: '',
    entity_type: '',
    entity_sub_type: '',
    entity_name: ''
};
let currentFileName = '';
let filterOptions = {};

// Performance tracking
let performanceStats = {
    lastLoadTime: 0,
    lastFilterTime: 0,
    cacheHits: 0,
    cacheMisses: 0
};

// Response cache
const responseCache = new Map();

// Debounce timers
let debounceTimers = {};

// DOM Elements (cached for performance)
const dom = {};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Application initialized (optimized version)');
    
    // Cache DOM elements
    cacheDOMElements();
    
    // Check backend connection
    checkBackendConnection();
    
    // Initialize event listeners
    initEventListeners();
    
    // Initialize AG Grid
    initGrid();
    
    // Start performance monitoring
    startPerformanceMonitoring();
});

/**
 * Cache DOM elements for faster access
 */
function cacheDOMElements() {
    dom.loadFileBtn = document.getElementById('loadFileBtn');
    dom.exportBtn = document.getElementById('exportBtn');
    dom.refreshBtn = document.getElementById('refreshBtn');
    dom.fileInput = document.getElementById('fileInput');
    dom.clearFiltersBtn = document.getElementById('clearFiltersBtn');
    
    dom.filterDate = document.getElementById('filterDate');
    dom.filterEntityType = document.getElementById('filterEntityType');
    dom.filterEntitySubType = document.getElementById('filterEntitySubType');
    dom.filterEntityName = document.getElementById('filterEntityName');
    
    dom.loadingOverlay = document.getElementById('loadingOverlay');
    dom.loadingText = document.getElementById('loadingText');
    dom.emptyState = document.getElementById('emptyState');
    dom.filterSection = document.getElementById('filterSection');
    dom.infoBar = document.getElementById('infoBar');
    dom.gridSection = document.getElementById('gridSection');
    dom.totalsSection = document.getElementById('totalsSection');
    dom.statusText = document.getElementById('statusText');
    dom.fileName = document.getElementById('fileName');
    dom.totalRows = document.getElementById('totalRows');
}

/**
 * Initialize event listeners with debouncing
 */
function initEventListeners() {
    dom.loadFileBtn.addEventListener('click', () => dom.fileInput.click());
    dom.fileInput.addEventListener('change', handleFileSelect);
    dom.exportBtn.addEventListener('click', handleExport);
    dom.refreshBtn.addEventListener('click', handleRefresh);
    dom.clearFiltersBtn.addEventListener('click', clearFilters);
    
    // Filter change listeners with debouncing
    dom.filterDate.addEventListener('change', () => 
        debouncedFilterChange('date', dom.filterDate.value)
    );
    dom.filterEntityType.addEventListener('change', () => 
        debouncedFilterChange('entity_type', dom.filterEntityType.value)
    );
    dom.filterEntitySubType.addEventListener('change', () => 
        debouncedFilterChange('entity_sub_type', dom.filterEntitySubType.value)
    );
    dom.filterEntityName.addEventListener('change', () => 
        debouncedFilterChange('entity_name', dom.filterEntityName.value)
    );
}

/**
 * Debounced filter change handler
 */
function debouncedFilterChange(filterName, value) {
    // Clear existing timer
    if (debounceTimers[filterName]) {
        clearTimeout(debounceTimers[filterName]);
    }
    
    // Set new timer
    debounceTimers[filterName] = setTimeout(() => {
        handleFilterChange(filterName, value);
    }, DEBOUNCE_DELAY);
}

/**
 * Initialize AG Grid with optimizations
 */
function initGrid() {
    const gridOptions = {
        ...defaultGridOptions,
        
        // Performance optimizations
        suppressColumnVirtualisation: false,
        suppressRowVirtualisation: false,
        rowBuffer: 10,
        debounceVerticalScrollbar: true,
        
        // Efficient rendering
        animateRows: false,  // Disable for better performance
        suppressLoadingOverlay: true,
        
        // Pagination for large datasets
        pagination: true,
        paginationPageSize: PAGINATION_SIZE,
        paginationAutoPageSize: false,
        
        // Cache block size
        cacheBlockSize: 100,
        
        // Enable cell text selection
        enableCellTextSelection: true,
        ensureDomOrder: false,  // Better performance
    };
    
    const gridDiv = document.getElementById('myGrid');
    gridApi = agGrid.createGrid(gridDiv, gridOptions);
    
    console.log('Grid initialized with optimizations');
}

/**
 * Cached API call with automatic cache management
 */
async function cachedFetch(url, options = {}, cacheKey = null) {
    const key = cacheKey || `${url}:${JSON.stringify(options)}`;
    
    // Check cache
    if (responseCache.has(key)) {
        const { data, timestamp } = responseCache.get(key);
        const age = Date.now() - timestamp;
        
        if (age < CACHE_DURATION) {
            performanceStats.cacheHits++;
            console.log(`Cache hit: ${key} (age: ${age}ms)`);
            return data;
        } else {
            // Expired, remove from cache
            responseCache.delete(key);
        }
    }
    
    // Fetch from API
    performanceStats.cacheMisses++;
    const startTime = performance.now();
    
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            'Accept-Encoding': 'gzip',  // Request compression
            ...options.headers
        }
    });
    
    const data = await response.json();
    const elapsed = performance.now() - startTime;
    
    console.log(`API call: ${url} (${elapsed.toFixed(2)}ms)`);
    
    // Cache response
    responseCache.set(key, {
        data: data,
        timestamp: Date.now()
    });
    
    // Limit cache size
    if (responseCache.size > 50) {
        const firstKey = responseCache.keys().next().value;
        responseCache.delete(firstKey);
    }
    
    return data;
}

/**
 * Check backend connection
 */
async function checkBackendConnection() {
    try {
        const result = await cachedFetch(`${API_BASE_URL}/health`);
        if (result.status === 'ok') {
            console.log('Backend connected');
            updateStatus('Ready');
            
            // Display backend stats if available
            if (result.stats) {
                console.log('Backend stats:', result.stats);
            }
        }
    } catch (error) {
        console.error('Backend connection failed:', error);
        updateStatus('Backend connection failed', true);
        showError('Cannot connect to backend server. Please ensure it is running.');
    }
}

/**
 * Handle file selection with progress tracking
 */
async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    currentFileName = file.name;
    const filePath = file.path;
    
    console.log('Selected file:', filePath);
    
    showLoading('Loading Excel file...');
    const startTime = performance.now();
    
    try {
        // Clear cache on new file load
        responseCache.clear();
        
        const result = await fetch(`${API_BASE_URL}/load`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: filePath })
        });
        
        const data = await result.json();
        
        if (data.success) {
            const elapsed = performance.now() - startTime;
            performanceStats.lastLoadTime = elapsed;
            
            console.log(`File loaded successfully: ${data.rows} rows in ${elapsed.toFixed(2)}ms`);
            updateStatus(`Loaded ${data.rows} rows in ${(elapsed / 1000).toFixed(2)}s`);
            dom.fileName.textContent = currentFileName;
            
            // Get filter options
            await loadFilterOptions();
            
            // Load initial data
            await loadData();
            
            // Show UI
            showDataView();
            
            // Enable buttons
            dom.exportBtn.disabled = false;
            dom.refreshBtn.disabled = false;
            
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Error loading file:', error);
        showError('Failed to load file: ' + error.message);
    } finally {
        hideLoading();
        dom.fileInput.value = '';
    }
}

/**
 * Load filter options with caching
 */
async function loadFilterOptions() {
    try {
        const result = await cachedFetch(`${API_BASE_URL}/filters`);
        
        if (result.success) {
            filterOptions = result.filters;
            populateFilters();
        }
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

/**
 * Populate filter dropdowns efficiently
 */
function populateFilters() {
    // Use DocumentFragment for efficient DOM manipulation
    const populateSelect = (select, options, defaultText) => {
        const fragment = document.createDocumentFragment();
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = defaultText;
        fragment.appendChild(defaultOption);
        
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            fragment.appendChild(optionElement);
        });
        
        select.innerHTML = '';
        select.appendChild(fragment);
    };
    
    populateSelect(dom.filterDate, filterOptions.dates || [], 'All Dates');
    populateSelect(dom.filterEntityType, filterOptions.entity_types || [], 'All Types');
    populateSelect(dom.filterEntitySubType, filterOptions.entity_sub_types || [], 'All Sub Types');
    populateSelect(dom.filterEntityName, filterOptions.entity_names || [], 'All Names');
}

/**
 * Handle filter change with optimized data loading
 */
async function handleFilterChange(filterName, value) {
    currentFilters[filterName] = value;
    console.log('Filters changed:', currentFilters);
    
    // Reload data with new filters
    await loadData();
}

/**
 * Clear all filters
 */
async function clearFilters() {
    currentFilters = {
        date: '',
        entity_type: '',
        entity_sub_type: '',
        entity_name: ''
    };
    
    // Reset dropdowns
    dom.filterDate.value = '';
    dom.filterEntityType.value = '';
    dom.filterEntitySubType.value = '';
    dom.filterEntityName.value = '';
    
    // Reload data
    await loadData();
}

/**
 * Load data with caching and pagination
 */
async function loadData() {
    showLoading('Loading data...');
    const startTime = performance.now();
    
    try {
        const filterPayload = {
            date: currentFilters.date || null,
            entity_type: currentFilters.entity_type || null,
            entity_sub_type: currentFilters.entity_sub_type || null,
            entity_name: currentFilters.entity_name || null
        };
        
        // Generate cache key from filters
        const cacheKey = `data:${JSON.stringify(filterPayload)}`;
        
        const result = await cachedFetch(
            `${API_BASE_URL}/data`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filters: filterPayload })
            },
            cacheKey
        );
        
        if (result.success) {
            const elapsed = performance.now() - startTime;
            performanceStats.lastFilterTime = elapsed;
            
            currentData = result.data;
            
            // Update grid efficiently
            gridApi.setGridOption('rowData', currentData);
            
            // Update totals
            updateTotals(result.totals);
            
            // Update row count
            dom.totalRows.textContent = result.count.toLocaleString();
            
            updateStatus(`Showing ${result.count} rows (${elapsed.toFixed(2)}ms)`);
            
            console.log(`Data loaded: ${result.count} rows in ${elapsed.toFixed(2)}ms`);
            
        } else {
            throw new Error(result.error);
        }
        
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Failed to load data: ' + error.message);
    } finally {
        hideLoading();
    }
}

/**
 * Update totals display
 */
function updateTotals(totals) {
    const formatNumber = (num) => parseFloat(num).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    document.getElementById('totalCashDr').textContent = formatNumber(totals['Cash Dr (R)']);
    document.getElementById('totalCashCr').textContent = formatNumber(totals['Cash Cr (P)']);
    document.getElementById('totalBankDr').textContent = formatNumber(totals['Bank Dr (R)']);
    document.getElementById('totalBankCr').textContent = formatNumber(totals['Bank Cr (P)']);
}

/**
 * Handle export
 */
async function handleExport() {
    showLoading('Exporting to Excel...');
    
    try {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const filename = `financial_report_${timestamp}.xlsx`;
        
        const response = await fetch(`${API_BASE_URL}/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                filters: {
                    date: currentFilters.date || null,
                    entity_type: currentFilters.entity_type || null,
                    entity_sub_type: currentFilters.entity_sub_type || null,
                    entity_name: currentFilters.entity_name || null
                },
                filename: filename
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            updateStatus('Export completed');
            showSuccess('File exported successfully!');
            
        } else {
            throw new Error('Export failed');
        }
        
    } catch (error) {
        console.error('Error exporting:', error);
        showError('Failed to export: ' + error.message);
    } finally {
        hideLoading();
    }
}

/**
 * Handle refresh
 */
async function handleRefresh() {
    // Clear cache and reload
    responseCache.clear();
    await loadData();
}

/**
 * Start performance monitoring
 */
function startPerformanceMonitoring() {
    setInterval(() => {
        console.log('Performance Stats:', {
            cacheHits: performanceStats.cacheHits,
            cacheMisses: performanceStats.cacheMisses,
            hitRate: (performanceStats.cacheHits / 
                     (performanceStats.cacheHits + performanceStats.cacheMisses) * 100).toFixed(2) + '%',
            cacheSize: responseCache.size,
            lastLoadTime: performanceStats.lastLoadTime.toFixed(2) + 'ms',
            lastFilterTime: performanceStats.lastFilterTime.toFixed(2) + 'ms'
        });
    }, 60000); // Every minute
}

// UI Helper Functions
function showLoading(message = 'Loading...') {
    dom.loadingText.textContent = message;
    dom.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    dom.loadingOverlay.style.display = 'none';
}

function showDataView() {
    dom.emptyState.style.display = 'none';
    dom.filterSection.style.display = 'block';
    dom.infoBar.style.display = 'flex';
    dom.gridSection.style.display = 'block';
    dom.totalsSection.style.display = 'block';
}

function updateStatus(message, isError = false) {
    dom.statusText.textContent = message;
    dom.statusText.style.color = isError ? 'var(--error-color)' : 'var(--text-secondary)';
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    alert(message);
}

// Export for Electron
if (typeof window !== 'undefined') {
    window.app = {
        loadData,
        handleFileSelect,
        handleExport,
        clearFilters,
        performanceStats: () => performanceStats,
        cacheStats: () => ({
            size: responseCache.size,
            entries: Array.from(responseCache.keys())
        })
    };
}

