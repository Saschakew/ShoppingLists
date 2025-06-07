from server import app
from flask import request, Response
from flask_cors import CORS
import json

def handler(event, context):
    with app.app_context():
        # Create a test request context
        with app.test_request_context(
            path=event['path'],
            method=event['httpMethod'],
            headers=event.get('headers', {}),
            query_string=event.get('queryStringParameters', {}),
            json=event.get('body') if event.get('body') else None
        ):
            try:
                # Process the request
                response = app.full_dispatch_request()
                
                # Prepare the response
                response_data = {
                    'statusCode': response.status_code,
                    'headers': dict(response.headers),
                    'body': response.get_data(as_text=True)
                }
                
                return response_data
                
            except Exception as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': str(e)})
                }
