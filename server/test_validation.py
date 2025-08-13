#!/usr/bin/env python3
"""
Comprehensive validation testing script for the streaming backend server.
Tests all validation models and security features.
"""

import asyncio
import json
import sys
from typing import Dict, Any

import requests
from pydantic import ValidationError

# Import validation models
from models.validation import (
    TextAnalysisRequest,
    ChatMessageRequest,
    BulkAnalysisRequest,
    AnalysisResponse,
    ErrorResponse
)


def test_text_analysis_validation():
    """Test TextAnalysisRequest validation"""
    print("\n🧪 Testing TextAnalysisRequest validation...")
    
    # Valid request
    try:
        valid_request = TextAnalysisRequest(
            text="This is a positive message about streaming!",
            language="en",
            mode="basic",
            include_sentiment=True,
            include_toxicity=True
        )
        print("✅ Valid request passed validation")
    except ValidationError as e:
        print(f"❌ Valid request failed: {e}")
    
    # Test text length limits
    try:
        TextAnalysisRequest(text="")
        print("❌ Empty text should be rejected")
    except ValidationError:
        print("✅ Empty text correctly rejected")
    
    try:
        TextAnalysisRequest(text="x" * 10001)
        print("❌ Text over limit should be rejected")
    except ValidationError:
        print("✅ Text over limit correctly rejected")
    
    # Test malicious content detection
    malicious_texts = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "data:text/html,<script>alert('xss')</script>",
        "vbscript:msgbox('xss')",
        "<img src=x onerror=alert('xss')>",
        "expression(alert('xss'))",
        "url(javascript:alert('xss'))"
    ]
    
    for malicious_text in malicious_texts:
        try:
            TextAnalysisRequest(text=malicious_text)
            print(f"❌ Malicious text should be rejected: {malicious_text[:30]}...")
        except ValidationError:
            print(f"✅ Malicious text correctly rejected: {malicious_text[:30]}...")
    
    # Test analysis mode validation
    try:
        TextAnalysisRequest(
            text="Test message",
            mode="basic",
            include_emotions=True  # Should fail - emotions require advanced mode
        )
        print("❌ Invalid mode combination should be rejected")
    except ValidationError:
        print("✅ Invalid mode combination correctly rejected")
    
    try:
        TextAnalysisRequest(
            text="Test message",
            mode="basic",
            include_hate_speech=True  # Should fail - hate speech requires comprehensive
        )
        print("❌ Invalid hate speech mode should be rejected")
    except ValidationError:
        print("✅ Invalid hate speech mode correctly rejected")


def test_chat_message_validation():
    """Test ChatMessageRequest validation"""
    print("\n🧪 Testing ChatMessageRequest validation...")
    
    # Valid chat message
    try:
        valid_chat = ChatMessageRequest(
            message="Hello everyone! How is the stream going?",
            username="stream_viewer_123",
            channel_id="general_chat",
            timestamp=1642694400
        )
        print("✅ Valid chat message passed validation")
    except ValidationError as e:
        print(f"❌ Valid chat message failed: {e}")
    
    # Test username validation
    invalid_usernames = [
        "a",  # Too short
        "x" * 51,  # Too long
        "user@name",  # Invalid characters
        "user name",  # Spaces not allowed
        "admin",  # Reserved name
        "moderator",  # Reserved name
        "bot",  # Reserved name
    ]
    
    for username in invalid_usernames:
        try:
            ChatMessageRequest(
                message="Test message",
                username=username
            )
            print(f"❌ Invalid username should be rejected: {username}")
        except ValidationError:
            print(f"✅ Invalid username correctly rejected: {username}")
    
    # Test message spam detection
    try:
        ChatMessageRequest(
            message="aaaaaaaaaaaaa",  # Excessive repetition
            username="test_user"
        )
        print("❌ Spam message should be rejected")
    except ValidationError:
        print("✅ Spam message correctly rejected")
    
    # Test suspicious URLs
    suspicious_messages = [
        "Check out this link: http://suspicious.tk/malware",
        "Free money! Click bit.ly/scam",
        "Win prizes now! Buy cheap stuff today!"
    ]
    
    for message in suspicious_messages:
        try:
            ChatMessageRequest(
                message=message,
                username="test_user"
            )
            print(f"❌ Suspicious message should be rejected: {message[:30]}...")
        except ValidationError:
            print(f"✅ Suspicious message correctly rejected: {message[:30]}...")


def test_bulk_analysis_validation():
    """Test BulkAnalysisRequest validation"""
    print("\n🧪 Testing BulkAnalysisRequest validation...")
    
    # Valid bulk request
    try:
        valid_bulk = BulkAnalysisRequest(
            texts=["Message 1", "Message 2", "Message 3"],
            mode="basic"
        )
        print("✅ Valid bulk request passed validation")
    except ValidationError as e:
        print(f"❌ Valid bulk request failed: {e}")
    
    # Test batch size limits
    try:
        BulkAnalysisRequest(texts=[])
        print("❌ Empty texts list should be rejected")
    except ValidationError:
        print("✅ Empty texts list correctly rejected")
    
    try:
        BulkAnalysisRequest(texts=["text"] * 51)  # Over limit
        print("❌ Too many texts should be rejected")
    except ValidationError:
        print("✅ Too many texts correctly rejected")


async def test_server_endpoints(port: int = 55555):
    """Test server endpoints with actual HTTP requests"""
    print(f"\n🌐 Testing server endpoints on port {port}...")
    base_url = f"http://127.0.0.1:{port}"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            health_data = response.json()
            print(f"   Server version: {health_data.get('version')}")
            print(f"   AI enabled: {health_data.get('ai_enabled')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Health endpoint connection failed: {e}")
        return
    
    # Test analyze endpoint with valid request
    try:
        valid_payload = {
            "text": "This is a positive message about streaming!",
            "language": "en",
            "mode": "basic",
            "include_sentiment": True,
            "include_toxicity": True
        }
        
        response = requests.post(
            f"{base_url}/analyze",
            json=valid_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Analyze endpoint working with valid request")
            result = response.json()
            print(f"   Sentiment: {result.get('sentiment')}")
            print(f"   Toxic: {result.get('toxic')}")
            print(f"   AI enabled: {result.get('ai_enabled')}")
        else:
            print(f"❌ Analyze endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Analyze endpoint connection failed: {e}")
    
    # Test analyze endpoint with malicious request
    try:
        malicious_payload = {
            "text": "<script>alert('xss')</script>",
            "mode": "basic"
        }
        
        response = requests.post(
            f"{base_url}/analyze",
            json=malicious_payload,
            timeout=10
        )
        
        if response.status_code == 422:
            print("✅ Malicious request correctly rejected")
            error_data = response.json()
            print(f"   Error type: {error_data.get('error')}")
        else:
            print(f"❌ Malicious request should be rejected: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Malicious request test failed: {e}")
    
    # Test rate limiting (send many requests quickly)
    print("\n🚦 Testing rate limiting...")
    rate_limit_exceeded = False
    for i in range(10):  # Send 10 rapid requests
        try:
            response = requests.post(
                f"{base_url}/analyze",
                json={"text": f"Rate limit test {i}"},
                timeout=5
            )
            if response.status_code == 429:
                print(f"✅ Rate limit triggered after {i+1} requests")
                rate_limit_exceeded = True
                break
        except requests.exceptions.RequestException:
            break
    
    if not rate_limit_exceeded:
        print("⚠️  Rate limiting not triggered (may need more requests or server may be in development mode)")
    
    # Test chat analysis endpoint
    try:
        chat_payload = {
            "message": "Great stream! Thanks for the content!",
            "username": "viewer_123",
            "channel_id": "general_chat"
        }
        
        response = requests.post(
            f"{base_url}/analyze-chat",
            json=chat_payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Chat analysis endpoint working")
            result = response.json()
            print(f"   Username: {result.get('username')}")
            print(f"   Channel: {result.get('channel_id')}")
        else:
            print(f"❌ Chat analysis failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat analysis test failed: {e}")


def main():
    """Main test runner"""
    print("🔍 Starting comprehensive validation tests...")
    
    # Test validation models
    test_text_analysis_validation()
    test_chat_message_validation()
    test_bulk_analysis_validation()
    
    # Test server endpoints if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--test-server":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 55555
        print(f"\n🌐 Testing server endpoints on port {port}...")
        print("Make sure the server is running first!")
        
        try:
            asyncio.run(test_server_endpoints(port))
        except KeyboardInterrupt:
            print("\n⚠️  Server tests interrupted")
    
    print("\n✨ Validation tests completed!")
    print("\nTo test server endpoints, run:")
    print("python test_validation.py --test-server [port]")


if __name__ == "__main__":
    main()