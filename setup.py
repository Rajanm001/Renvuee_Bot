#!/usr/bin/env python3
"""
Setup script for Telegram Revenue Copilot
Installs all dependencies and prepares the environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False

def install_requirements():
    """Install all Python requirements"""
    print("📦 Installing Python Dependencies...")
    
    # Core dependencies for the test script
    core_packages = [
        "groq==0.9.0",
        "sentence-transformers==2.2.2", 
        "requests==2.31.0",
        "python-dotenv==1.0.0"
    ]
    
    for package in core_packages:
        success = run_command(f"pip install {package}", f"Installing {package}")
        if not success:
            print(f"⚠️  Failed to install {package}, continuing...")
    
    # Install agent-specific requirements
    agent_dirs = [
        "agents/agentA_knowledge",
        "agents/agentB_dealflow", 
        "agents/intent_classifier"
    ]
    
    for agent_dir in agent_dirs:
        req_file = Path(agent_dir) / "requirements.txt"
        if req_file.exists():
            success = run_command(
                f"pip install -r {req_file}", 
                f"Installing requirements for {agent_dir}"
            )
            if success:
                print(f"✅ {agent_dir} dependencies installed")
            else:
                print(f"⚠️  Some dependencies for {agent_dir} may have failed")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "data/chroma",
        "logs",
        "uploads"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created {directory}")

def check_docker():
    """Check if Docker is available"""
    print("🐳 Checking Docker...")
    
    success = run_command("docker --version", "Checking Docker installation")
    if success:
        print("✅ Docker is available")
        
        # Check if docker-compose is available
        compose_success = run_command("docker-compose --version", "Checking Docker Compose")
        if compose_success:
            print("✅ Docker Compose is available")
            return True
        else:
            print("⚠️  Docker Compose not found, try 'docker compose' instead")
            return False
    else:
        print("⚠️  Docker not found - you can still run individual services")
        return False

def setup_environment():
    """Set up environment file"""
    print("🔧 Setting up environment...")
    
    env_file = Path(".env")
    env_sample = Path(".env.sample")
    
    if not env_file.exists() and env_sample.exists():
        # Copy sample to .env
        with open(env_sample, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ Created .env file from .env.sample")
        print("⚠️  Please edit .env file with your API keys!")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ No .env.sample file found")

def display_api_key_instructions():
    """Display instructions for getting API keys"""
    print("\n" + "=" * 60)
    print("🔑 REQUIRED API KEYS - ALL FREE!")
    print("=" * 60)
    
    print("\n1. 🤖 GROQ API KEY (Free, Fast LLM)")
    print("   • Go to: https://console.groq.com/")
    print("   • Sign up/Login")
    print("   • Go to API Keys section")
    print("   • Create new API key")
    print("   • Free tier: 6,000 requests/minute!")
    
    print("\n2. 📱 TELEGRAM BOT TOKEN (Free)")
    print("   • Open Telegram app")
    print("   • Message @BotFather")
    print("   • Send: /newbot")
    print("   • Follow instructions to create bot")
    print("   • Copy the bot token")
    
    print("\n3. 📊 GOOGLE SERVICE ACCOUNT (Free)")
    print("   • Go to: https://console.cloud.google.com/")
    print("   • Create new project or select existing")
    print("   • Enable APIs: Drive, Sheets, Calendar")
    print("   • Create Service Account")
    print("   • Download JSON key file")
    print("   • Base64 encode the JSON content")
    
    print("\n4. 🔄 N8N WEBHOOK URL (Free)")
    print("   • Sign up at: https://n8n.cloud/")
    print("   • Create new workflow")
    print("   • Add Webhook trigger")
    print("   • Copy webhook URL")
    print("   • Free tier: 5,000 executions/month")
    
    print("\n" + "=" * 60)
    print("📝 NEXT STEPS:")
    print("1. Get your API keys from above")
    print("2. Edit .env file with your keys")
    print("3. Run: python test_system.py")
    print("4. Start services: docker-compose up -d")
    print("5. Test again: python test_system.py")
    print("6. Deploy to Render and share with client!")
    print("=" * 60)

def main():
    """Main setup process"""
    print("🚀 Telegram Revenue Copilot Setup")
    print("=" * 60)
    
    # Install dependencies
    install_requirements()
    
    # Create directories
    create_directories()
    
    # Check Docker
    docker_available = check_docker()
    
    # Setup environment
    setup_environment()
    
    # Display API key instructions
    display_api_key_instructions()
    
    print("\n✅ Setup complete!")
    
    if docker_available:
        print("\n🐳 You can now run:")
        print("   docker-compose up -d    # Start all services")
        print("   python test_system.py   # Test everything")
    else:
        print("\n🔧 You can run individual services:")
        print("   cd agents/agentA_knowledge && python app.py")
        print("   cd agents/agentB_dealflow && python app.py") 
        print("   cd agents/intent_classifier && python app.py")

if __name__ == "__main__":
    main()