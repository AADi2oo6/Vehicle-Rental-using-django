from django.db import connection
from django.core.cache import cache
import sqlparse # Import the new library

class QueryCaptureMiddleware:
    """
    This middleware captures SQL queries executed during a request
    and stores them in the Django cache for later viewing.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the request has the _viewing_queries flag, skip the middleware logic
        if getattr(request, '_viewing_queries', False):
            return self.get_response(request)

        response = self.get_response(request)
        
        is_html = 'text/html' in response.get('Content-Type', '')
        is_successful = response.status_code == 200

        if is_html and is_successful and connection.queries:
            all_queries = cache.get('all_sql_queries', [])
            
            separator = f"--- Queries for request: {request.path} ---"
            all_queries.append({'sql': separator, 'time': ''})

            for query in connection.queries:
                # Format the SQL query before storing it
                formatted_sql = sqlparse.format(query['sql'], reindent=True, keyword_case='upper')
                all_queries.append({'sql': formatted_sql, 'time': query['time']})

            cache.set('all_sql_queries', all_queries[-50:], timeout=600)
            
        return response
