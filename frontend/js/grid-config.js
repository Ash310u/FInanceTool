/**
 * AG Grid Configuration
 * Defines column definitions, formatters, and grid options
 */

// Number formatter with thousand separators and 2 decimal places
const numberFormatter = (params) => {
    if (params.value === null || params.value === undefined || params.value === '') {
        return '0.00';
    }
    return parseFloat(params.value).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
};

// Column definitions for the grid
const columnDefs = [
    {
        field: 'Date',
        headerName: 'Date',
        width: 120,
        pinned: 'left',
        sortable: true,
        filter: 'agTextColumnFilter',
        cellClass: 'hierarchy-cell'
    },
    {
        field: 'Entity Type',
        headerName: 'Entity Type',
        width: 180,
        sortable: true,
        filter: 'agTextColumnFilter'
    },
    {
        field: 'Entity Sub Type',
        headerName: 'Entity Sub Type',
        width: 180,
        sortable: true,
        filter: 'agTextColumnFilter'
    },
    {
        field: 'Entity Name',
        headerName: 'Entity Name',
        width: 220,
        sortable: true,
        filter: 'agTextColumnFilter',
        flex: 1
    },
    {
        field: 'Vch Type',
        headerName: 'Vch Type',
        width: 120,
        sortable: true,
        filter: 'agTextColumnFilter'
    },
    {
        field: 'Particulars',
        headerName: 'Particulars',
        width: 250,
        sortable: true,
        filter: 'agTextColumnFilter',
        flex: 2
    },
    {
        field: 'Cash Dr (R)',
        headerName: 'Cash Dr (R)',
        width: 140,
        sortable: true,
        filter: 'agNumberColumnFilter',
        type: 'numericColumn',
        cellClass: 'ag-cell-numeric',
        valueFormatter: numberFormatter,
        aggFunc: 'sum'
    },
    {
        field: 'Cash Cr (P)',
        headerName: 'Cash Cr (P)',
        width: 140,
        sortable: true,
        filter: 'agNumberColumnFilter',
        type: 'numericColumn',
        cellClass: 'ag-cell-numeric',
        valueFormatter: numberFormatter,
        aggFunc: 'sum'
    },
    {
        field: 'Bank Dr (R)',
        headerName: 'Bank Dr (R)',
        width: 140,
        sortable: true,
        filter: 'agNumberColumnFilter',
        type: 'numericColumn',
        cellClass: 'ag-cell-numeric',
        valueFormatter: numberFormatter,
        aggFunc: 'sum'
    },
    {
        field: 'Bank Cr (P)',
        headerName: 'Bank Cr (P)',
        width: 140,
        sortable: true,
        filter: 'agNumberColumnFilter',
        type: 'numericColumn',
        cellClass: 'ag-cell-numeric',
        valueFormatter: numberFormatter,
        aggFunc: 'sum'
    }
];

// Default grid options
const defaultGridOptions = {
    columnDefs: columnDefs,
    rowData: [],
    
    // Enable features
    enableRangeSelection: true,
    enableCellTextSelection: true,
    suppressRowClickSelection: true,
    
    // Row selection
    rowSelection: 'multiple',
    
    // Pagination
    pagination: false,
    
    // Virtual scrolling for performance
    rowModelType: 'clientSide',
    
    // Default column properties
    defaultColDef: {
        resizable: true,
        sortable: true,
        filter: true,
        floatingFilter: false,
        minWidth: 80
    },
    
    // Auto size columns
    autoSizeStrategy: {
        type: 'fitGridWidth',
        defaultMinWidth: 80
    },
    
    // Loading overlay
    overlayLoadingTemplate: '<span class="ag-overlay-loading-center">Loading data...</span>',
    overlayNoRowsTemplate: '<span class="ag-overlay-no-rows-center">No data to display</span>',
    
    // Animation
    animateRows: true,
    
    // Themes
    theme: 'ag-theme-alpine',
    
    // Events
    onGridReady: (params) => {
        // Grid is ready
        console.log('Grid ready');
    },
    
    onFirstDataRendered: (params) => {
        // Auto-size columns on first render
        params.api.autoSizeAllColumns();
    },
    
    onFilterChanged: (params) => {
        // Filter changed
        console.log('Filter changed');
    },
    
    onSortChanged: (params) => {
        // Sort changed
        console.log('Sort changed');
    }
};

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { columnDefs, defaultGridOptions, numberFormatter };
}

