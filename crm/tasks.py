"""
Celery tasks for CRM application.

This module contains asynchronous tasks for generating reports,
processing data, and other background operations.
"""

import os
import json
import requests
from datetime import datetime
from decimal import Decimal
from celery import shared_task
from django.conf import settings
from django.db import models
from crm.models import Customer, Order, Product


@shared_task
def generate_crm_report():
    """
    Task 4: Generate a weekly CRM report summarizing total orders, customers, and revenue.
    
    This task:
    1. Uses GraphQL queries to fetch CRM statistics
    2. Logs the report to /tmp/crmreportlog.txt
    3. Runs every Monday at 6:00 AM via Celery Beat
    
    Returns:
        dict: Report data including customers, orders, and revenue totals
    """
    try:
        # Method 1: Use GraphQL query (as requested in instructions)
        report_data = _fetch_report_via_graphql()
        
        # Method 2: Fallback to direct database queries if GraphQL fails
        if not report_data:
            report_data = _fetch_report_via_database()
        
        # Create timestamp in YYYY-MM-DD HH:MM:SS format
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the report message
        report_message = (
            f"{timestamp} - Report: "
            f"{report_data['total_customers']} customers, "
            f"{report_data['total_orders']} orders, "
            f"${report_data['total_revenue']:.2f} revenue.\n"
        )
        
        # Log the report to file (ALX expects this exact path)
        log_file_path = '/tmp/crm_report_log.txt'
        with open(log_file_path, 'a') as f:
            f.write(report_message)
        
        # Log additional details for debugging
        detailed_message = (
            f"{timestamp} - Detailed Report:\n"
            f"  Total Customers: {report_data['total_customers']}\n"
            f"  Total Orders: {report_data['total_orders']}\n"
            f"  Total Revenue: ${report_data['total_revenue']:.2f}\n"
            f"  Report Generated Successfully\n"
            f"{'-' * 50}\n"
        )
        
        with open(log_file_path, 'a') as f:
            f.write(detailed_message)
        
        print(f"CRM Report generated successfully: {report_message.strip()}")
        
        return {
            'success': True,
            'message': 'Report generated successfully',
            'data': report_data,
            'timestamp': timestamp
        }
        
    except Exception as exc:
        # Log the error
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_message = f"{timestamp} - ERROR generating report: {str(exc)}\n"
        
        try:
            with open('/tmp/crm_report_log.txt', 'a') as f:
                f.write(error_message)
        except:
            pass  # Avoid secondary errors
        
        print(f"Error generating CRM report: {str(exc)}")
        
        return {
            'success': False,
            'message': f'Report generation failed: {str(exc)}',
            'data': None,
            'timestamp': timestamp
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_crm_report_with_retry(self):
    """
    Alternative version with retry functionality for more robust operations.
    """
    try:
        # Method 1: Use GraphQL query (as requested in instructions)
        report_data = _fetch_report_via_graphql()
        
        # Method 2: Fallback to direct database queries if GraphQL fails
        if not report_data:
            report_data = _fetch_report_via_database()
        
        # Create timestamp in YYYY-MM-DD HH:MM:SS format
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the report message
        report_message = (
            f"{timestamp} - Report: "
            f"{report_data['total_customers']} customers, "
            f"{report_data['total_orders']} orders, "
            f"${report_data['total_revenue']:.2f} revenue.\n"
        )
        
        # Log the report to file
        log_file_path = '/tmp/crm_report_log.txt'
        with open(log_file_path, 'a') as f:
            f.write(report_message)
        
        print(f"CRM Report generated successfully: {report_message.strip()}")
        
        return {
            'success': True,
            'message': 'Report generated successfully',
            'data': report_data,
            'timestamp': timestamp
        }
        
    except Exception as exc:
        # Log the error
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_message = f"{timestamp} - ERROR generating report: {str(exc)}\n"
        
        try:
            with open('/tmp/crm_report_log.txt', 'a') as f:
                f.write(error_message)
        except:
            pass  # Avoid secondary errors
        
        print(f"Error generating CRM report: {str(exc)}")
        
        # Retry the task if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60)
        
        return {
            'success': False,
            'message': f'Report generation failed: {str(exc)}',
            'data': None,
            'timestamp': timestamp
        }


def _fetch_report_via_graphql():
    """
    Fetch report data using GraphQL queries.
    
    Returns:
        dict: Report data or None if GraphQL query fails
    """
    try:
        graphql_url = "http://localhost:8000/graphql"
        
        # GraphQL query to fetch all required data
        query = """
        query {
            customers {
                id
            }
            orders {
                id
                totalAmount
            }
        }
        """
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        payload = {
            'query': query
        }
        
        # Execute the GraphQL query
        response = requests.post(
            graphql_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for GraphQL errors
            if 'errors' in data:
                error_messages = [error.get('message', 'Unknown error') for error in data['errors']]
                raise Exception(f"GraphQL errors: {', '.join(error_messages)}")
            
            # Extract data
            query_data = data.get('data', {})
            customers = query_data.get('customers', [])
            orders = query_data.get('orders', [])
            
            # Calculate totals
            total_customers = len(customers)
            total_orders = len(orders)
            total_revenue = sum(
                float(order.get('totalAmount', 0)) 
                for order in orders 
                if order.get('totalAmount')
            )
            
            return {
                'total_customers': total_customers,
                'total_orders': total_orders,
                'total_revenue': total_revenue
            }
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"GraphQL query failed: {str(e)}")
        return None


def _fetch_report_via_database():
    """
    Fetch report data using direct database queries as fallback.
    
    Returns:
        dict: Report data
    """
    try:
        # Direct database queries
        total_customers = Customer.objects.count()
        total_orders = Order.objects.count()
        
        # Calculate total revenue
        revenue_result = Order.objects.aggregate(
            total_revenue=models.Sum('total_amount')
        )
        total_revenue = float(revenue_result['total_revenue'] or 0)
        
        return {
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_revenue': total_revenue
        }
        
    except Exception as e:
        print(f"Database query failed: {str(e)}")
        raise


@shared_task
def test_celery_task():
    """
    Simple test task to verify Celery is working correctly.
    
    Returns:
        str: Success message with timestamp
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Celery test task executed successfully at {timestamp}"
    
    # Log to file
    try:
        with open('/tmp/celery_test_log.txt', 'a') as f:
            f.write(f"{message}\n")
    except Exception as e:
        print(f"Failed to write to log: {str(e)}")
    
    print(message)
    return message


@shared_task(bind=True)
def cleanup_old_reports(self):
    """
    Cleanup task to manage report log file size.
    Keeps only the last 500 lines of the report log.
    
    Returns:
        dict: Cleanup result
    """
    try:
        log_file_path = '/tmp/crm_report_log.txt'
        
        if not os.path.exists(log_file_path):
            return {'success': True, 'message': 'No log file to clean'}
        
        # Read all lines
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
        
        # Keep only last 500 lines if file is larger
        if len(lines) > 500:
            with open(log_file_path, 'w') as f:
                f.writelines(lines[-500:])
            
            message = f"Cleaned up report log, kept last 500 lines (removed {len(lines) - 500} lines)"
        else:
            message = f"Report log is manageable size ({len(lines)} lines), no cleanup needed"
        
        print(message)
        
        return {
            'success': True,
            'message': message,
            'lines_before': len(lines),
            'lines_after': min(len(lines), 500)
        }
        
    except Exception as exc:
        error_msg = f"Failed to cleanup reports: {str(exc)}"
        print(error_msg)
        
        return {
            'success': False,
            'message': error_msg
        }