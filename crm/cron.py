import os
import json
import requests
from datetime import datetime
from django.conf import settings


def log_crm_heartbeat():
    """
    Task 2: Logs a heartbeat message every 5 minutes to confirm CRM health.
    Optionally queries the GraphQL hello field to verify endpoint responsiveness.
    """
    try:
        # Create timestamp in DD/MM/YYYY-HH:MM:SS format
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        message = f"{timestamp} CRM is alive"
        
        # Optional: Query GraphQL hello field to verify endpoint
        try:
            graphql_url = "http://localhost:8000/graphql"
            hello_query = """
            query {
                hello
            }
            """
            
            response = requests.post(
                graphql_url,
                json={'query': hello_query},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' not in data:
                    message += " - GraphQL endpoint responsive"
                else:
                    message += " - GraphQL endpoint has errors"
            else:
                message += " - GraphQL endpoint not responding"
                
        except Exception as e:
            message += f" - GraphQL check failed: {str(e)}"
        
        # Append message to log file (don't overwrite)
        message += "\n"
        with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
            f.write(message)
            
        print("Heartbeat logged successfully!")
            
    except Exception as e:
        # Fallback logging in case of errors
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        error_message = f"{timestamp} CRM heartbeat ERROR: {str(e)}\n"
        
        try:
            with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
                f.write(error_message)
        except:
            print(f"Failed to log heartbeat error: {str(e)}")


def update_low_stock():
    """
    Task 3: Executes the UpdateLowStockProducts GraphQL mutation and logs the results.
    Runs every 12 hours to update products with stock < 10.
    """
    try:
        # GraphQL endpoint URL
        graphql_url = "http://localhost:8000/graphql"
        
        # GraphQL mutation query
        mutation = """
        mutation {
            updateLowStockProducts {
                updatedProducts {
                    id
                    name
                    stock
                }
                message
                success
                count
            }
        }
        """
        
        # Prepare the request
        headers = {
            'Content-Type': 'application/json',
        }
        
        payload = {
            'query': mutation
        }
        
        # Execute the GraphQL mutation
        response = requests.post(
            graphql_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Check for GraphQL errors
            if 'errors' in data:
                error_messages = [error.get('message', 'Unknown error') for error in data['errors']]
                raise Exception(f"GraphQL errors: {', '.join(error_messages)}")
            
            # Extract mutation result
            mutation_result = data.get('data', {}).get('updateLowStockProducts', {})
            
            if not mutation_result:
                raise Exception("No mutation result returned")
            
            # Create timestamp
            timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
            
            # Prepare log message
            log_message = f"{timestamp} Low Stock Update Results:\n"
            log_message += f"Success: {mutation_result.get('success', False)}\n"
            log_message += f"Message: {mutation_result.get('message', 'No message')}\n"
            log_message += f"Products Updated: {mutation_result.get('count', 0)}\n"
            
            # Log each updated product with name and new stock level
            updated_products = mutation_result.get('updatedProducts', [])
            if updated_products:
                log_message += "Updated Products:\n"
                for product in updated_products:
                    product_name = product.get('name', 'Unknown')
                    new_stock = product.get('stock', 0)
                    product_id = product.get('id', 'Unknown')
                    log_message += f"  - ID: {product_id}, Name: {product_name}, New Stock: {new_stock}\n"
            else:
                log_message += "No products were updated.\n"
            
            log_message += "-" * 50 + "\n"
            
            # Write to log file
            with open('/tmp/low_stock_updates_log.txt', 'a') as f:
                f.write(log_message)
            
            print("Low stock update completed successfully!")
            
        else:
            # HTTP error
            error_msg = f"HTTP {response.status_code}: {response.text}"
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        # Network/connection errors
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        error_message = f"{timestamp} ERROR - Network error during low stock update: {str(e)}\n"
        error_message += "-" * 50 + "\n"
        
        with open('/tmp/low_stock_updates_log.txt', 'a') as f:
            f.write(error_message)
        
        print(f"Network error during low stock update: {str(e)}")
        
    except json.JSONDecodeError as e:
        # JSON parsing errors
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        error_message = f"{timestamp} ERROR - Invalid JSON response during low stock update: {str(e)}\n"
        error_message += "-" * 50 + "\n"
        
        with open('/tmp/low_stock_updates_log.txt', 'a') as f:
            f.write(error_message)
        
        print(f"JSON parsing error during low stock update: {str(e)}")
        
    except Exception as e:
        # General errors
        timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
        error_message = f"{timestamp} ERROR - Unexpected error during low stock update: {str(e)}\n"
        error_message += "-" * 50 + "\n"
        
        with open('/tmp/low_stock_updates_log.txt', 'a') as f:
            f.write(error_message)
        
        print(f"Error during low stock update: {str(e)}")


# Optional: Helper function to clear old log entries (can be called manually or scheduled)
def cleanup_old_logs():
    """
    Cleanup function to manage log file sizes.
    Keeps only the last 1000 lines of each log file.
    """
    log_files = [
        '/tmp/crm_heartbeat_log.txt',
        '/tmp/low_stock_updates_log.txt',
        '/tmp/order_reminders_log.txt',
        '/tmp/customer_cleanup_log.txt'
    ]
    
    for log_file in log_files:
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Keep only last 1000 lines
                if len(lines) > 1000:
                    with open(log_file, 'w') as f:
                        f.writelines(lines[-1000:])
                    
                    print(f"Cleaned up {log_file}, kept last 1000 lines")
                    
        except Exception as e:
            print(f"Error cleaning up {log_file}: {str(e)}")


# Optional: Test function to verify cron jobs work
def test_cron_functions():
    """
    Test function to manually verify that cron functions work correctly.
    Can be called from Django shell: python manage.py shell
    >>> from crm.cron import test_cron_functions
    >>> test_cron_functions()
    """
    print("Testing heartbeat function...")
    log_crm_heartbeat()
    
    print("Testing low stock update function...")
    update_low_stock()
    
    print("Cron function tests completed!")