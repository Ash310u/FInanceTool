"""
Optimized Flask API Server
Enhanced with caching, compression, and performance monitoring.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import logging
from datetime import datetime
import tempfile
from functools import wraps
import time
import gzip
import io

from data_processor_optimized import DataProcessorOptimized
from hierarchy_builder_optimized import HierarchyBuilderOptimized

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global instances
data_processor = DataProcessorOptimized()
hierarchy_builder = None

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['JSON_SORT_KEYS'] = False  # Faster JSON serialization

# Response cache (for GET requests)
response_cache = {}
CACHE_MAX_SIZE = 100


def performance_monitor(f):
    """Decorator to monitor endpoint performance."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        elapsed = time.time() - start_time
        
        logger.info(f"{f.__name__} completed in {elapsed:.4f}s")
        
        # Add performance header
        if isinstance(result, tuple):
            response, status_code = result
            if isinstance(response, dict):
                response['_performance'] = {
                    'elapsed_ms': round(elapsed * 1000, 2)
                }
            return jsonify(response), status_code
        return result
    
    return decorated_function


def cache_response(timeout=60):
    """Decorator to cache GET request responses."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Only cache GET requests
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"{f.__name__}:{request.url}"
            
            # Check cache
            if cache_key in response_cache:
                cached_data, cache_time = response_cache[cache_key]
                age = time.time() - cache_time
                
                if age < timeout:
                    logger.debug(f"Cache hit for {f.__name__} (age: {age:.2f}s)")
                    return cached_data
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache result
            if len(response_cache) >= CACHE_MAX_SIZE:
                # Remove oldest
                oldest_key = next(iter(response_cache))
                del response_cache[oldest_key]
            
            response_cache[cache_key] = (result, time.time())
            
            return result
        
        return decorated_function
    return decorator


def compress_response(f):
    """Decorator to compress large responses."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)
        
        # Only compress large responses
        if isinstance(result, tuple):
            response, status_code = result
        else:
            response, status_code = result, 200
        
        # Check if client accepts gzip
        if 'gzip' in request.headers.get('Accept-Encoding', ''):
            # Compress if response is large
            response_json = jsonify(response).get_data()
            
            if len(response_json) > 1024:  # > 1KB
                compressed = gzip.compress(response_json)
                
                if len(compressed) < len(response_json):
                    logger.debug(f"Compressed response: {len(response_json)} -> {len(compressed)} bytes")
                    
                    from flask import Response
                    return Response(
                        compressed,
                        status=status_code,
                        headers={
                            'Content-Encoding': 'gzip',
                            'Content-Type': 'application/json',
                            'Content-Length': len(compressed)
                        }
                    )
        
        return jsonify(response), status_code
    
    return decorated_function


@app.route('/api/health', methods=['GET'])
@cache_response(timeout=30)
def health_check():
    """Health check endpoint with caching."""
    stats = data_processor.get_performance_stats() if data_processor else {}
    
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'stats': stats
    })


@app.route('/api/load', methods=['POST'])
@performance_monitor
def load_file():
    """
    Load Excel file with optimized processing.
    Clears caches on new file load.
    """
    global hierarchy_builder
    
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
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
        
        # Clear all caches
        response_cache.clear()
        
        # Load file
        result = data_processor.load_excel_file(file_path)
        
        if result['success']:
            # Initialize optimized hierarchy builder
            hierarchy_builder = HierarchyBuilderOptimized(data_processor.df)
            logger.info(f"Loaded file with {result['rows']} rows")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in load_file: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/filters', methods=['GET'])
@performance_monitor
@cache_response(timeout=300)  # Cache for 5 minutes
def get_filters():
    """
    Get filter options with caching.
    Uses pre-computed filter options from data processor.
    """
    try:
        if data_processor.df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
        
        # Get cached filter options
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
@performance_monitor
@compress_response
def get_hierarchy():
    """
    Get hierarchical data with caching and compression.
    Uses optimized hierarchy builder.
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
        
        # Build hierarchy (uses internal caching)
        hierarchy = hierarchy_builder.build_hierarchy(filters, max_transactions)
        
        # Get filtered dataframe for totals
        filtered_df = data_processor.get_filtered_data(filters)
        totals = data_processor.calculate_totals(filtered_df)
        
        return {
            'success': True,
            'hierarchy': hierarchy,
            'totals': totals,
            'count': len(filtered_df)
        }, 200
        
    except Exception as e:
        logger.error(f"Error in get_hierarchy: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/data', methods=['POST'])
@performance_monitor
@compress_response
def get_data():
    """
    Get flat data with optimization.
    Uses cached filtering.
    """
    try:
        if data_processor.df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
        
        data = request.get_json()
        filters = data.get('filters', {})
        limit = data.get('limit', None)  # Optional row limit
        offset = data.get('offset', 0)   # Optional offset for pagination
        
        # Get filtered data (uses caching)
        filtered_df = data_processor.get_filtered_data(filters)
        
        # Apply pagination if requested
        if limit:
            end = offset + limit
            paginated_df = filtered_df.iloc[offset:end]
        else:
            paginated_df = filtered_df
        
        # Convert to dict (efficient with orient='records')
        rows = paginated_df.to_dict('records')
        
        # Calculate totals
        totals = data_processor.calculate_totals(filtered_df)
        
        return {
            'success': True,
            'data': rows,
            'totals': totals,
            'count': len(filtered_df),
            'returned': len(rows),
            'offset': offset
        }, 200
        
    except Exception as e:
        logger.error(f"Error in get_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/export', methods=['POST'])
@performance_monitor
def export_data():
    """Export with optimized file generation."""
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
        
        # Export
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
@performance_monitor
def get_totals():
    """Get totals with caching."""
    try:
        if data_processor.df is None:
            return jsonify({
                'success': False,
                'error': 'No data loaded'
            }), 400
        
        data = request.get_json()
        filters = data.get('filters', {})
        
        # Get filtered data (cached)
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


@app.route('/api/stats', methods=['GET'])
@performance_monitor
def get_performance_stats():
    """Get detailed performance statistics."""
    try:
        data_stats = data_processor.get_performance_stats()
        hierarchy_stats = hierarchy_builder.get_cache_stats() if hierarchy_builder else {}
        
        return jsonify({
            'success': True,
            'data_processor': data_stats,
            'hierarchy_builder': hierarchy_stats,
            'api_cache_size': len(response_cache)
        })
        
    except Exception as e:
        logger.error(f"Error in get_performance_stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Manually clear all caches."""
    try:
        response_cache.clear()
        data_processor.clear_cache()
        
        if hierarchy_builder:
            hierarchy_builder.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'All caches cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
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
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting optimized Flask server on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info("Performance optimizations:")
    logger.info("  - Response caching enabled")
    logger.info("  - Data processor caching enabled")
    logger.info("  - Hierarchy builder memoization enabled")
    logger.info("  - Response compression enabled")
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=debug,
        threaded=True
    )

