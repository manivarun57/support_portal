#!/usr/bin/env python3
"""
DynamoDB Manager for P1 Incidents
Multi-tenant architecture: Multiple clients, each with multiple users
"""

import os
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

class DynamoDBManager:
    """
    Manages P1 incidents in DynamoDB with multi-client support
    
    Table Design:
    - Table Name: P1Incidents
    - Partition Key: client_id (for multi-tenant isolation)
    - Sort Key: incident_id (unique incident identifier)
    - GSI: incident_id-index (for quick lookups by incident_id)
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        self.table_name = os.getenv('DYNAMODB_P1_TABLE', 'P1Incidents')
        self.table = self.dynamodb.Table(self.table_name)
        
        print(f"✅ DynamoDB Manager initialized - Table: {self.table_name}")
    
    def create_p1_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new P1 incident in DynamoDB
        
        Args:
            incident_data: {
                'client_id': 'merchant_xxx',
                'client_name': 'TechCorp Inc.',
                'user_id': 'user_xxx',
                'user_name': 'John Doe',
                'user_email': 'john@techcorp.com',
                'ticket_id': 'TKT-xxx',
                'incident_id': 'P1-xxx',
                'subject': 'Critical issue',
                'description': 'Details...',
                'category': 'P1 Critical',
                'priority': 'P1',
                'slack_channel_id': 'C0A10UFAT9N',
                'slack_thread_ts': '1234567890.123456'
            }
        """
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            # Primary Keys
            'client_id': incident_data['client_id'],
            'incident_id': incident_data['incident_id'],
            
            # Client/Merchant Info
            'client_name': incident_data.get('client_name', 'Unknown'),
            
            # User Info
            'user_id': incident_data['user_id'],
            'user_name': incident_data.get('user_name', 'Unknown'),
            'user_email': incident_data.get('user_email', ''),
            
            # Ticket Info
            'ticket_id': incident_data['ticket_id'],
            'subject': incident_data['subject'],
            'description': incident_data['description'],
            'category': incident_data.get('category', 'P1 Critical'),
            'priority': incident_data.get('priority', 'P1'),
            
            # Slack Integration
            'slack_channel_id': incident_data.get('slack_channel_id', ''),
            'slack_thread_ts': incident_data.get('slack_thread_ts', ''),
            'slack_notification_sent': True if incident_data.get('slack_thread_ts') else False,
            'slack_notification_sent_at': timestamp if incident_data.get('slack_thread_ts') else None,
            
            # Email Notification
            'email_notification_sent': incident_data.get('email_notification_sent', False),
            'email_notification_sent_at': incident_data.get('email_notification_sent_at'),
            
            # Status
            'status': 'active',
            'created_at': timestamp,
            'updated_at': timestamp,
            'resolved_at': None,
            
            # Slack Messages (array of messages in thread)
            'slack_messages': []
        }
        
        try:
            self.table.put_item(Item=item)
            print(f"✅ P1 Incident stored in DynamoDB: {incident_data['incident_id']} for client {incident_data['client_id']}")
            return item
        except Exception as e:
            print(f"❌ DynamoDB put_item failed: {e}")
            raise
    
    def get_incident_by_id(self, client_id: str, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific P1 incident"""
        try:
            response = self.table.get_item(
                Key={
                    'client_id': client_id,
                    'incident_id': incident_id
                }
            )
            return response.get('Item')
        except Exception as e:
            print(f"❌ DynamoDB get_item failed: {e}")
            return None
    
    def get_incident_by_incident_id_only(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Get incident by incident_id only (using GSI)
        Useful when you don't know the client_id
        """
        try:
            response = self.table.query(
                IndexName='incident_id-index',
                KeyConditionExpression=Key('incident_id').eq(incident_id)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            print(f"❌ DynamoDB query GSI failed: {e}")
            return None
    
    def get_incidents_by_client(self, client_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get all P1 incidents for a specific client"""
        try:
            if status:
                response = self.table.query(
                    KeyConditionExpression=Key('client_id').eq(client_id),
                    FilterExpression=Attr('status').eq(status)
                )
            else:
                response = self.table.query(
                    KeyConditionExpression=Key('client_id').eq(client_id)
                )
            
            return response.get('Items', [])
        except Exception as e:
            print(f"❌ DynamoDB query failed: {e}")
            return []
    
    def get_active_incidents_by_client(self, client_id: str) -> List[Dict[str, Any]]:
        """Get all active P1 incidents for a client"""
        return self.get_incidents_by_client(client_id, status='active')
    
    def add_slack_message(self, client_id: str, incident_id: str, message_data: Dict[str, Any]) -> bool:
        """
        Add a Slack message to the incident's message history
        
        Args:
            message_data: {
                'message_ts': '1234567890.123456',
                'user': 'U123ABC',
                'text': 'Message content',
                'timestamp': '2025-12-02T10:30:00Z'
            }
        """
        try:
            self.table.update_item(
                Key={
                    'client_id': client_id,
                    'incident_id': incident_id
                },
                UpdateExpression='SET slack_messages = list_append(if_not_exists(slack_messages, :empty_list), :new_message), updated_at = :updated',
                ExpressionAttributeValues={
                    ':new_message': [message_data],
                    ':empty_list': [],
                    ':updated': datetime.utcnow().isoformat()
                }
            )
            print(f"✅ Slack message added to incident {incident_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to add Slack message: {e}")
            return False
    
    def update_incident_status(self, client_id: str, incident_id: str, status: str) -> bool:
        """Update incident status (active/resolved)"""
        try:
            timestamp = datetime.utcnow().isoformat()
            
            update_expr = 'SET #status = :status, updated_at = :updated'
            expr_values = {
                ':status': status,
                ':updated': timestamp
            }
            
            if status == 'resolved':
                update_expr += ', resolved_at = :resolved'
                expr_values[':resolved'] = timestamp
            
            self.table.update_item(
                Key={
                    'client_id': client_id,
                    'incident_id': incident_id
                },
                UpdateExpression=update_expr,
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues=expr_values
            )
            
            print(f"✅ Incident {incident_id} status updated to: {status}")
            return True
        except Exception as e:
            print(f"❌ Failed to update incident status: {e}")
            return False
    
    def update_slack_thread(self, client_id: str, incident_id: str, thread_ts: str) -> bool:
        """Update Slack thread timestamp after posting"""
        try:
            self.table.update_item(
                Key={
                    'client_id': client_id,
                    'incident_id': incident_id
                },
                UpdateExpression='SET slack_thread_ts = :thread_ts, slack_notification_sent = :sent, slack_notification_sent_at = :sent_at, updated_at = :updated',
                ExpressionAttributeValues={
                    ':thread_ts': thread_ts,
                    ':sent': True,
                    ':sent_at': datetime.utcnow().isoformat(),
                    ':updated': datetime.utcnow().isoformat()
                }
            )
            print(f"✅ Slack thread_ts updated for incident {incident_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to update Slack thread: {e}")
            return False
    
    def get_all_active_incidents(self) -> List[Dict[str, Any]]:
        """Get all active incidents across all clients (for dashboard)"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('status').eq('active')
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"❌ DynamoDB scan failed: {e}")
            return []
    
    def get_incident_by_ticket_id(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Find incident by ticket_id (requires scan - use sparingly)"""
        try:
            response = self.table.scan(
                FilterExpression=Attr('ticket_id').eq(ticket_id)
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            print(f"❌ Failed to find incident by ticket_id: {e}")
            return None


def create_dynamodb_table():
    """
    Create the DynamoDB table with proper indexes
    Run this once during deployment
    """
    dynamodb = boto3.client('dynamodb',
        region_name=os.getenv('AWS_REGION', 'us-east-1'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    table_name = os.getenv('DYNAMODB_P1_TABLE', 'P1Incidents')
    
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'client_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'incident_id', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'client_id', 'AttributeType': 'S'},
                {'AttributeName': 'incident_id', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'created_at', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'incident_id-index',
                    'KeySchema': [
                        {'AttributeName': 'incident_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'status-created_at-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'created_at', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'  # On-demand pricing (or use ProvisionedThroughput)
        )
        
        print(f"✅ DynamoDB table '{table_name}' created successfully!")
        print("Waiting for table to be active...")
        
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        
        print(f"✅ Table '{table_name}' is now active!")
        return True
        
    except dynamodb.exceptions.ResourceInUseException:
        print(f"⚠️ Table '{table_name}' already exists")
        return True
    except Exception as e:
        print(f"❌ Failed to create table: {e}")
        return False


if __name__ == "__main__":
    # Test or create table
    print("DynamoDB P1 Incidents Manager")
    print("=" * 50)
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'create-table':
        create_dynamodb_table()
    else:
        print("Usage:")
        print("  python dynamodb_manager.py create-table  - Create DynamoDB table")
