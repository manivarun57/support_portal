#!/usr/bin/env python3
"""
Lambda Client - Invokes P1 Lambda Function from Main Application
This integrates with your existing app.py to offload P1 processing to Lambda
"""

import os
import json
import boto3
from typing import Dict, Any, Optional


class P1LambdaClient:
    """
    Client to invoke P1 Lambda function from main application
    Handles async invocation so main app doesn't wait for Lambda completion
    """
    
    def __init__(self):
        self.lambda_client = boto3.client('lambda',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        self.function_name = os.getenv('P1_LAMBDA_FUNCTION_NAME', 'P1IncidentHandler')
        self.enabled = os.getenv('USE_P1_LAMBDA', 'false').lower() == 'true'
        
        if self.enabled:
            print(f"✅ P1 Lambda Client initialized - Function: {self.function_name}")
        else:
            print("ℹ️ P1 Lambda disabled (set USE_P1_LAMBDA=true to enable)")
    
    def invoke_create_p1_incident(self, incident_data: Dict[str, Any], async_mode: bool = True) -> Optional[Dict[str, Any]]:
        """
        Invoke Lambda to create P1 incident
        
        Args:
            incident_data: {
                'client_id': 'merchant_xxx',
                'client_name': 'TechCorp Inc.',
                'user_id': 'user_xxx',
                'user_name': 'John Doe',
                'user_email': 'john@techcorp.com',
                'ticket_id': 'TKT-xxx',
                'subject': 'Critical issue',
                'description': 'Details...',
                'category': 'Infrastructure',
                'slack_channel_id': 'C0A10UFAT9N'
            }
            async_mode: If True, Lambda runs async (don't wait for response)
        
        Returns:
            Lambda response or None if async
        """
        if not self.enabled:
            print("⚠️ P1 Lambda not enabled")
            return None
        
        try:
            event = {
                'action': 'create_p1_incident',
                'data': incident_data
            }
            
            invocation_type = 'Event' if async_mode else 'RequestResponse'
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(event)
            )
            
            if async_mode:
                print(f"✅ P1 Lambda invoked asynchronously (StatusCode: {response['StatusCode']})")
                return {'async': True, 'status_code': response['StatusCode']}
            else:
                # Synchronous - parse response
                payload = json.loads(response['Payload'].read())
                body = json.loads(payload.get('body', '{}'))
                print(f"✅ P1 Lambda completed: {body.get('incident_id')}")
                return body
                
        except Exception as e:
            print(f"❌ Failed to invoke P1 Lambda: {e}")
            return None
    
    def get_incident(self, client_id: str, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get incident details from Lambda/DynamoDB"""
        if not self.enabled:
            return None
        
        try:
            event = {
                'action': 'get_incident',
                'data': {
                    'client_id': client_id,
                    'incident_id': incident_id
                }
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(event)
            )
            
            payload = json.loads(response['Payload'].read())
            body = json.loads(payload.get('body', '{}'))
            
            return body.get('incident') if body.get('success') else None
            
        except Exception as e:
            print(f"❌ Failed to get incident: {e}")
            return None
    
    def update_incident_status(self, client_id: str, incident_id: str, status: str) -> bool:
        """Update incident status via Lambda"""
        if not self.enabled:
            return False
        
        try:
            event = {
                'action': 'update_status',
                'data': {
                    'client_id': client_id,
                    'incident_id': incident_id,
                    'status': status
                }
            }
            
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='Event',  # Async
                Payload=json.dumps(event)
            )
            
            print(f"✅ Status update sent to Lambda (StatusCode: {response['StatusCode']})")
            return response['StatusCode'] == 202
            
        except Exception as e:
            print(f"❌ Failed to update status: {e}")
            return False


# For testing
if __name__ == "__main__":
    client = P1LambdaClient()
    
    test_incident = {
        'client_id': 'merchant_510eaea5f65f',
        'client_name': 'TechCorp Inc.',
        'user_id': 'user_aaa4ef7e984f',
        'user_name': 'Dheeraj',
        'user_email': 'dheeraj.narayanam@payintelli.com',
        'ticket_id': 'TKT-test-001',
        'subject': 'Test Critical Issue',
        'description': 'Testing Lambda integration',
        'category': 'Infrastructure',
        'slack_channel_id': os.getenv('SLACK_CHANNEL_ID', '')
    }
    
    print("Testing P1 Lambda invocation...")
    result = client.invoke_create_p1_incident(test_incident, async_mode=False)
    print(f"Result: {result}")
