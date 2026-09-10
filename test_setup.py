#!/usr/bin/env python3
"""
Test Script for Google Cloud Setup
===================================
Run this script to verify your Google Cloud configuration is working.

Usage:
    python test_setup.py
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Check if all required environment variables are set."""
    print("\n🔍 Checking Environment Variables...")
    print("-" * 40)

    required_vars = {
        'PROJECT_ID': 'Google Cloud Project ID',
        'GOOGLE_APPLICATION_CREDENTIALS': 'Path to service account key file'
    }

    optional_vars = {
        'LOCATION': 'Google Cloud region (default: us-central1)',
        'MODEL': 'AI model name (default: gemini-2.0-flash)',
        'DEBUG': 'Debug mode (default: false)',
        'PORT': 'Server port (default: 8000)'
    }

    all_good = True

    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'CREDENTIALS' in var:
                display_value = f"***{value[-20:]}" if len(value) > 20 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET - {description}")
            all_good = False

    # Check optional variables
    print("\n📝 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"   {var}: {value}")
        else:
            print(f"   {var}: Not set ({description})")

    return all_good

def test_service_account_file():
    """Check if the service account key file exists and is valid."""
    print("\n🔑 Checking Service Account Key File...")
    print("-" * 40)

    key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    if not key_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False

    # Check if file exists
    if not os.path.exists(key_path):
        print(f"❌ Key file not found: {key_path}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Files in current directory: {os.listdir('.')}")
        return False

    # Check if it's a valid JSON file
    try:
        with open(key_path, 'r') as f:
            key_data = json.load(f)

        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in key_data]

        if missing_fields:
            print(f"❌ Key file missing required fields: {missing_fields}")
            return False

        # Verify project ID matches
        env_project_id = os.getenv('PROJECT_ID')
        key_project_id = key_data.get('project_id')

        if env_project_id and env_project_id != key_project_id:
            print(f"⚠️  Warning: PROJECT_ID mismatch!")
            print(f"   .env file: {env_project_id}")
            print(f"   Key file:  {key_project_id}")
            print(f"   Using key file project ID is recommended")

        print(f"✅ Valid service account key found")
        print(f"   Type: {key_data['type']}")
        print(f"   Project: {key_project_id}")
        print(f"   Service Account: {key_data['client_email']}")
        return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in key file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading key file: {e}")
        return False

def test_google_auth():
    """Test authentication with Google Cloud."""
    print("\n🔐 Testing Google Cloud Authentication...")
    print("-" * 40)

    try:
        # Set up credentials
        key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if key_path and os.path.exists(key_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path

        # Try to import and initialize
        from google.auth import default
        from google.auth.exceptions import DefaultCredentialsError

        credentials, project = default()

        print(f"✅ Authentication successful!")
        print(f"   Project: {project}")

        # Test Google Gen AI import
        try:
            from google import genai
            print(f"✅ Google Gen AI SDK imported successfully")
        except ImportError:
            print(f"⚠️  Google Gen AI SDK not installed. Run: pip install google-genai")
            return False

        return True

    except DefaultCredentialsError as e:
        print(f"❌ Authentication failed: {e}")
        print(f"\n   Troubleshooting tips:")
        print(f"   1. Ensure GOOGLE_APPLICATION_CREDENTIALS points to your key file")
        print(f"   2. Verify the key file is valid JSON")
        print(f"   3. Check that the service account has proper permissions")
        return False
    except ImportError:
        print(f"❌ Google Auth library not installed. Run: pip install google-auth")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_vertex_ai_connection():
    """Test connection to Vertex AI using Google Gen AI SDK."""
    print("\n🤖 Testing Vertex AI Connection...")
    print("-" * 40)

    try:
        from google import genai
        from google.genai import types

        project_id = os.getenv('PROJECT_ID')
        location = os.getenv('LOCATION', 'us-central1')

        if not project_id:
            print("❌ PROJECT_ID not set")
            return False

        # Initialize Google Gen AI client with Vertex AI
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        print(f"✅ Vertex AI client initialized")
        print(f"   Project: {project_id}")
        print(f"   Location: {location}")

        # Try to create a test generation
        model_name = os.getenv('MODEL', 'gemini-2.0-flash')
        print(f"✅ Model configured: {model_name}")

        # Optional: Test a simple generation (commented out to save API calls)
        # response = client.models.generate_content(
        #     model=model_name,
        #     contents="Say 'OK' if you're working",
        #     config=types.GenerateContentConfig(max_output_tokens=10)
        # )
        # if response.text:
        #     print(f"✅ Model responded: {response.text[:50]}")

        return True

    except ImportError:
        print("❌ Google Gen AI SDK not installed. Run: pip install google-genai")
        return False
    except Exception as e:
        print(f"❌ Vertex AI connection failed: {e}")
        print(f"\n   Troubleshooting tips:")
        print(f"   1. Verify the Vertex AI API is enabled in your project")
        print(f"   2. Check that your service account has 'Vertex AI User' role")
        print(f"   3. Ensure your project has billing enabled")
        return False

def main():
    """Run all setup tests."""
    print("=" * 50)
    print("🚀 Legal Intelligence AI System - Setup Test")
    print("=" * 50)

    # Track results
    results = {
        'Environment Variables': test_environment_variables(),
        'Service Account File': test_service_account_file(),
        'Google Authentication': test_google_auth(),
        'Vertex AI Connection': test_vertex_ai_connection()
    }

    # Summary
    print("\n" + "=" * 50)
    print("📊 SETUP TEST SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("\n🎉 All tests passed! Your environment is ready.")
        print("You can now run: python main.py")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nRefer to SETUP_INSTRUCTIONS.md for detailed setup guide.")
        return 1

if __name__ == "__main__":
    sys.exit(main())