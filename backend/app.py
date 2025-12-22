"""
Flask API Server
Provides REST API endpoints for the frontend to interact with the data processing backend.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import logging
from datetime import datetime
import tempfile

from data_processor import DataProcessor
from hierarchy_builder import HierarchyBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for Electron frontend

# Global data processor instance
data_processor = DataProcessor()
hierarchy_builder = None

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max file size


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/load', methods=['POST'])
def load_file():
    """
    Load Excel file from disk.
    
    Request body:
        {
            "file_path": "/path/to/file.xlsx"
        }
    
    Returns:
        {
            "success": bool,
            "data": {...} or "error": str
        }
    """
    global hierarchy_builder
    
    try:
        data = request.get_json()
        file_path = data.get('file_path') if data else None
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'No file path provided'
            }), 400
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': f'File not found: {file_path}'
            }), 404
        
        # Load file using data processor
        result = data_processor.load_excel_file(file_path)
        
        if result['success']:
            # Initialize hierarchy builder
            hierarchy_builder = HierarchyBuilder(data_processor.df)
            logger.info(f"Successfully loaded file with {result['rows']} rows")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in load_file: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Upload Excel file via multipart form data (for browser mode).
    
    Returns:
        {
            "success": bool,
            "data": {...} or "error": str
        }
    """
    global hierarchy_builder
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Save uploaded file to temp directory
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        logger.info(f"File uploaded to: {temp_path}")
        
        # Load file using data processor
        result = data_processor.load_excel_file(temp_path)
        
        if result['success']:
            # Initialize hierarchy builder
            hierarchy_builder = HierarchyBuilder(data_processor.df)
            logger.info(f"Successfully loaded uploaded file with {result['rows']} rows")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in upload_file: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/filters', methods=['GET'])
def get_filters():
    """
    Get available filter options.
    
    Returns:
        {
            "dates": [...],
            "entity_types": [...],
            "entity_sub_types": [...],
            "entity_names": [...]
        }
    """
    try:
        if data_processor.df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
        
        filters = data_processor.get_filter_options()
        
        return jsonify({
            'success': True,
            'filters': filters
        })
        
    except Exception as e:
        logger.error(f"Error in get_filters: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hierarchy', methods=['POST'])
def get_hierarchy():
    """
    Get hierarchical data structure.
    
    Request body:
        {
            "filters": {
                "date": str or null,
                "entity_type": str or null,
                "entity_sub_type": str or null,
                "entity_name": str or null
            },
            "max_transactions": int (optional, default 10000)
        }
    
    Returns:
        {
            "success": bool,
            "hierarchy": [...],
            "totals": {...}
        }
    """
    try:
        if hierarchy_builder is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
        
        data = request.get_json()
        filters = data.get('filters', {})
        max_transactions = data.get('max_transactions', 10000)
        
        # Build hierarchy
        hierarchy = hierarchy_builder.build_hierarchy(filters, max_transactions)
        
        # Get filtered dataframe for totals
        filtered_df = data_processor.get_filtered_data(filters)
        totals = data_processor.calculate_totals(filtered_df)
        
        return jsonify({
            'success': True,
            'hierarchy': hierarchy,
            'totals': totals,
            'count': len(filtered_df)
        })
        
    except Exception as e:
        logger.error(f"Error in get_hierarchy: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/data', methods=['POST'])
def get_data():
    """
    Get flat data for grid display.
    
    Request body:
        {
            "filters": {
                "date": str or null,
                "entity_type": str or null,
                "entity_sub_type": str or null,
                "entity_name": str or null
            }
        }
    
    Returns:
        {
            "success": bool,
            "data": [...],
            "totals": {...},
            "count": int
        }
    """
    try:
        if data_processor.df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
        
        data = request.get_json()
        filters = data.get('filters', {})
        
        # Get filtered data
        filtered_df = data_processor.get_filtered_data(filters)
        
        # Convert to list of dictionaries
        rows = filtered_df.to_dict('records')
        
        # Calculate totals
        totals = data_processor.calculate_totals(filtered_df)
        
        return jsonify({
            'success': True,
            'data': rows,
            'totals': totals,
            'count': len(rows)
        })
        
    except Exception as e:
        logger.error(f"Error in get_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export', methods=['POST'])
def export_data():
    """
    Export filtered data to Excel.
    
    Request body:
        {
            "filters": {...},
            "filename": str (optional)
        }
    
    Returns:
        Excel file download
    """
    try:
        if data_processor.df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
        
        data = request.get_json()
        filters = data.get('filters', {})
        filename = data.get('filename', f'export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        
        # Get filtered data
        filtered_df = data_processor.get_filtered_data(filters)
        
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, filename)
        
        # Export to Excel
        result = data_processor.export_to_excel(filtered_df, output_path, include_totals=True)
        
        if result['success']:
            return send_file(
                output_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error in export_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/totals', methods=['POST'])
def get_totals():
    """
    Get totals for filtered data.
    
    Request body:
        {
            "filters": {...}
        }
    
    Returns:
        {
            "success": bool,
            "totals": {...}
        }
    """
    try:
        if data_processor.df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
        
        data = request.get_json()
        filters = data.get('filters', {})
        
        # Get filtered data
        filtered_df = data_processor.get_filtered_data(filters)
        
        # Calculate totals
        totals = data_processor.calculate_totals(filtered_df)
        
        return jsonify({
            'success': True,
            'totals': totals,
            'count': len(filtered_df)
        })
        
    except Exception as e:
        logger.error(f"Error in get_totals: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 100 MB.'
    }), 413


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server error."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Run Flask server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='127.0.0.1',  # Only accept local connections
        port=port,
        debug=debug,
        threaded=True
    )

