/**
 * Main Application Logic
 * Handles UI interactions, API calls, and grid management
 */

// API Configuration
const API_BASE_URL = 'http://127.0.0.1:5000/api';

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

// DOM Elements
const loadFileBtn = document.getElementById('loadFileBtn');
const exportBtn = document.getElementById('exportBtn');
const refreshBtn = document.getElementById('refreshBtn');
const fileInput = document.getElementById('fileInput');
const clearFiltersBtn = document.getElementById('clearFiltersBtn');

const filterDate = document.getElementById('filterDate');
const filterEntityType = document.getElementById('filterEntityType');
const filterEntitySubType = document.getElementById('filterEntitySubType');
const filterEntityName = document.getElementById('filterEntityName');

const loadingOverlay = document.getElementById('loadingOverlay');
const loadingText = document.getElementById('loadingText');
const emptyState = document.getElementById('emptyState');
const filterSection = document.getElementById('filterSection');
const infoBar = document.getElementById('infoBar');
const gridSection = document.getElementById('gridSection');
const totalsSection = document.getElementById('totalsSection');
const statusText = document.getElementById('statusText');
const fileName = document.getElementById('fileName');
const totalRows = document.getElementById('totalRows');

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Application initialized');
    
    // Check backend connection
    checkBackendConnection();
    
    // Initialize event listeners
    initEventListeners();
    
    // Initialize AG Grid
    initGrid();
});

// Initialize event listeners
function initEventListeners() {
    loadFileBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    exportBtn.addEventListener('click', handleExport);
    refreshBtn.addEventListener('click', handleRefresh);
    clearFiltersBtn.addEventListener('click', clearFilters);
    
    // Filter change listeners
    filterDate.addEventListener('change', () => handleFilterChange('date', filterDate.value));
    filterEntityType.addEventListener('change', () => handleFilterChange('entity_type', filterEntityType.value));
    filterEntitySubType.addEventListener('change', () => handleFilterChange('entity_sub_type', filterEntitySubType.value));
    filterEntityName.addEventListener('change', () => handleFilterChange('entity_name', filterEntityName.value));
}

// Initialize AG Grid
function initGrid() {
    const gridDiv = document.getElementById('myGrid');
    gridApi = agGrid.createGrid(gridDiv, defaultGridOptions);
    console.log('Grid initialized');
}

// Check backend connection
async function checkBackendConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            console.log('Backend connected');
            updateStatus('Ready');
        } else {
            throw new Error('Backend not responding');
        }
    } catch (error) {
        console.error('Backend connection failed:', error);
        updateStatus('Backend connection failed', true);
        showError('Cannot connect to backend server. Please ensure it is running.');
    }
}

// Handle file selection
async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    currentFileName = file.name;
    
    console.log('Selected file:', currentFileName);
    
    showLoading('Loading Excel file...');
    
    try {
        let response;
        let result;
        
        // Check if running in Electron (has file.path) or browser
        if (file.path) {
            // Electron mode: send file path
            console.log('Using Electron mode with file path:', file.path);
            response = await fetch(`${API_BASE_URL}/load`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_path: file.path })
            });
            result = await response.json();
        } else {
            // Browser mode: upload file content
            console.log('Using browser mode with file upload');
            const formData = new FormData();
            formData.append('file', file);
            
            response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData  // Don't set Content-Type, let browser set it with boundary
            });
            result = await response.json();
        }
        
        if (result.success) {
            console.log('File loaded successfully:', result);
            updateStatus(`Loaded ${result.rows} rows`);
            fileName.textContent = currentFileName;
            
            // Get filter options
            await loadFilterOptions();
            
            // Load initial data
            await loadData();
            
            // Show UI
            showDataView();
            
            // Enable buttons
            exportBtn.disabled = false;
            refreshBtn.disabled = false;
            
        } else {
            throw new Error(result.error);
        }
        
    } catch (error) {
        console.error('Error loading file:', error);
        showError('Failed to load file: ' + error.message);
    } finally {
        hideLoading();
        // Clear file input
        fileInput.value = '';
    }
}

// Load filter options
async function loadFilterOptions() {
    try {
        const response = await fetch(`${API_BASE_URL}/filters`);
        const result = await response.json();
        
        if (result.success) {
            filterOptions = result.filters;
            populateFilters();
        }
    } catch (error) {
        console.error('Error loading filters:', error);
    }
}

// Populate filter dropdowns
function populateFilters() {
    // Clear existing options (except "All")
    filterDate.innerHTML = '<option value="">All Dates</option>';
    filterEntityType.innerHTML = '<option value="">All Types</option>';
    filterEntitySubType.innerHTML = '<option value="">All Sub Types</option>';
    filterEntityName.innerHTML = '<option value="">All Names</option>';
    
    // Populate dates
    if (filterOptions.dates) {
        filterOptions.dates.forEach(date => {
            const option = document.createElement('option');
            option.value = date;
            option.textContent = date;
            filterDate.appendChild(option);
        });
    }
    
    // Populate entity types
    if (filterOptions.entity_types) {
        filterOptions.entity_types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            filterEntityType.appendChild(option);
        });
    }
    
    // Populate entity sub types
    if (filterOptions.entity_sub_types) {
        filterOptions.entity_sub_types.forEach(subType => {
            const option = document.createElement('option');
            option.value = subType;
            option.textContent = subType;
            filterEntitySubType.appendChild(option);
        });
    }
    
    // Populate entity names
    if (filterOptions.entity_names) {
        filterOptions.entity_names.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            filterEntityName.appendChild(option);
        });
    }
}

// Handle filter change
async function handleFilterChange(filterName, value) {
    currentFilters[filterName] = value;
    console.log('Filters changed:', currentFilters);
    
    // Reload data with new filters
    await loadData();
}

// Clear all filters
async function clearFilters() {
    currentFilters = {
        date: '',
        entity_type: '',
        entity_sub_type: '',
        entity_name: ''
    };
    
    // Reset dropdowns
    filterDate.value = '';
    filterEntityType.value = '';
    filterEntitySubType.value = '';
    filterEntityName.value = '';
    
    // Reload data
    await loadData();
}

// Load data from API
async function loadData() {
    showLoading('Loading data...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filters: {
                    date: currentFilters.date || null,
                    entity_type: currentFilters.entity_type || null,
                    entity_sub_type: currentFilters.entity_sub_type || null,
                    entity_name: currentFilters.entity_name || null
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentData = result.data;
            
            // Update grid
            gridApi.setGridOption('rowData', currentData);
            
            // Update totals
            updateTotals(result.totals);
            
            // Update row count
            totalRows.textContent = result.count.toLocaleString();
            
            updateStatus(`Showing ${result.count} rows`);
            
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

// Update totals display
function updateTotals(totals) {
    document.getElementById('totalCashDr').textContent = 
        parseFloat(totals['Cash Dr (R)']).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    
    document.getElementById('totalCashCr').textContent = 
        parseFloat(totals['Cash Cr (P)']).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    
    document.getElementById('totalBankDr').textContent = 
        parseFloat(totals['Bank Dr (R)']).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    
    document.getElementById('totalBankCr').textContent = 
        parseFloat(totals['Bank Cr (P)']).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
}

// Handle export
async function handleExport() {
    showLoading('Exporting to Excel...');
    
    try {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const filename = `financial_report_${timestamp}.xlsx`;
        
        const response = await fetch(`${API_BASE_URL}/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
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
            // Get the blob
            const blob = await response.blob();
            
            // Create download link
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

// Handle refresh
async function handleRefresh() {
    await loadData();
}

// UI Helper Functions
function showLoading(message = 'Loading...') {
    loadingText.textContent = message;
    loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showDataView() {
    emptyState.style.display = 'none';
    filterSection.style.display = 'block';
    infoBar.style.display = 'flex';
    gridSection.style.display = 'block';
    totalsSection.style.display = 'block';
}

function hideDataView() {
    emptyState.style.display = 'flex';
    filterSection.style.display = 'none';
    infoBar.style.display = 'none';
    gridSection.style.display = 'none';
    totalsSection.style.display = 'none';
}

function updateStatus(message, isError = false) {
    statusText.textContent = message;
    statusText.style.color = isError ? 'var(--error-color)' : 'var(--text-secondary)';
}

function showError(message) {
    alert('Error: ' + message);
}

function showSuccess(message) {
    alert(message);
}

// Export functions for Electron
if (typeof window !== 'undefined') {
    window.app = {
        loadData,
        handleFileSelect,
        handleExport,
        clearFilters
    };
}

