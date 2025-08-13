#!/usr/bin/env python3
"""
Simple test script to verify AI Manager modifications
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    from services.ai_manager import ai_manager
    
    print("=== AI Manager Test ===")
    print(f"Models loaded: {list(ai_manager.models.keys())}")
    print(f"Model statuses: {ai_manager.get_model_status()}")
    print(f"Performance stats: {ai_manager.get_performance_stats()}")
    
    # Test that models are actually accessible
    for model_type in ai_manager.model_priority:
        if model_type in ai_manager.models:
            print(f"✅ {model_type} model is loaded and accessible")
        else:
            print(f"❌ {model_type} model is NOT loaded")
    
    print("=== Test Complete ===")
    
except Exception as e:
    print(f"❌ Error during test: {e}")
    import traceback
    traceback.print_exc()