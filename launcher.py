#!/usr/bin/env python3
"""
Cross-platform launcher for Data Analysis System
Supports Windows, macOS, and Linux
"""
import os
import sys
import subprocess
import platform
from pathlib import Path
import shutil


class Color:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Print colored header"""
    print(f"\n{Color.HEADER}{Color.BOLD}{'=' * 60}{Color.ENDC}")
    print(f"{Color.HEADER}{Color.BOLD}{text.center(60)}{Color.ENDC}")
    print(f"{Color.HEADER}{Color.BOLD}{'=' * 60}{Color.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Color.OKGREEN}✓ {text}{Color.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Color.OKCYAN}ℹ {text}{Color.ENDC}")


def print_warning(text):
    """Print warning message"""
    print(f"{Color.WARNING}⚠ {text}{Color.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Color.FAIL}✗ {text}{Color.ENDC}")


def get_system_info():
    """Get system information"""
    return {
        'os': platform.system(),
        'os_version': platform.version(),
        'python_version': platform.python_version(),
        'architecture': platform.machine(),
    }


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ is required, but you have {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_command(command):
    """Check if a command exists"""
    return shutil.which(command) is not None


def create_venv():
    """Create virtual environment"""
    venv_path = Path("venv")
    if venv_path.exists():
        print_info("Virtual environment already exists")
        return True
    
    print_info("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to create virtual environment")
        return False


def get_python_executable():
    """Get the Python executable path in venv"""
    system = platform.system()
    if system == "Windows":
        return Path("venv/Scripts/python.exe")
    else:
        return Path("venv/bin/python")


def get_pip_executable():
    """Get the pip executable path in venv"""
    system = platform.system()
    if system == "Windows":
        return Path("venv/Scripts/pip.exe")
    else:
        return Path("venv/bin/pip")


def install_dependencies():
    """Install Python dependencies"""
    print_info("Installing dependencies...")
    pip_exe = get_pip_executable()
    
    if not pip_exe.exists():
        print_error(f"pip not found at {pip_exe}")
        return False
    
    try:
        # Upgrade pip first
        subprocess.run(
            [str(pip_exe), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        
        # Install requirements
        subprocess.run(
            [str(pip_exe), "install", "-r", "requirements.txt"],
            check=True
        )
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print_info(".env file already exists")
        return True
    
    if not env_example_path.exists():
        print_warning(".env.example not found, creating basic .env")
        with open(env_path, 'w') as f:
            f.write("SECRET_KEY=your-secret-key-change-in-production\n")
            f.write("DEBUG=True\n")
    else:
        shutil.copy(env_example_path, env_path)
        print_success(".env file created from template")
    
    return True


def create_directories():
    """Create necessary directories"""
    dirs = ["data", "data/users", "data/uploads", "logs"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print_success("Required directories created")


def initialize_database():
    """Initialize database"""
    print_info("Initializing database...")
    python_exe = get_python_executable()
    
    try:
        result = subprocess.run(
            [str(python_exe), "init_admin.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("Database initialized")
            print(result.stdout)
        else:
            print_warning("Database may already be initialized")
        return True
    except Exception as e:
        print_warning(f"Database initialization: {e}")
        return True  # Not critical


def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the FastAPI server"""
    print_info(f"Starting server on {host}:{port}...")
    python_exe = get_python_executable()
    
    try:
        subprocess.run([str(python_exe), "app.py"])
    except KeyboardInterrupt:
        print_info("\nServer stopped by user")
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        return False
    
    return True


def run_tests():
    """Run test suite"""
    print_info("Running tests...")
    python_exe = get_python_executable()
    
    try:
        result = subprocess.run(
            [str(python_exe), "test_setup.py"],
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        print_error("Some tests failed")
        return False


def show_menu():
    """Show interactive menu"""
    print_header("Data Analysis System Launcher")
    
    print(f"{Color.BOLD}System Information:{Color.ENDC}")
    info = get_system_info()
    for key, value in info.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n{Color.BOLD}Available Commands:{Color.ENDC}")
    print("  1. 🚀 Start Server (default)")
    print("  2. 📦 Install/Update Dependencies")
    print("  3. 🧪 Run Tests")
    print("  4. 🔧 Initialize Database")
    print("  5. 🆕 Create Admin User")
    print("  6. 📊 System Status")
    print("  0. ❌ Exit")
    print()


def check_status():
    """Check system status"""
    print_header("System Status Check")
    
    checks = [
        ("Python 3.8+", check_python_version()),
        ("Virtual Environment", Path("venv").exists()),
        ("Dependencies", Path(get_pip_executable()).exists()),
        (".env File", Path(".env").exists()),
        ("Database", Path("data/app.db").exists()),
        ("Data Directory", Path("data").exists()),
    ]
    
    print()
    for name, status in checks:
        if status:
            print_success(f"{name}: OK")
        else:
            print_warning(f"{name}: Not Ready")
    print()


def setup():
    """Run initial setup"""
    print_header("Initial Setup")
    
    if not check_python_version():
        return False
    
    steps = [
        ("Creating virtual environment", create_venv),
        ("Installing dependencies", install_dependencies),
        ("Creating .env file", create_env_file),
        ("Creating directories", create_directories),
        ("Initializing database", initialize_database),
    ]
    
    for step_name, step_func in steps:
        print_info(f"Step: {step_name}")
        if not step_func():
            print_error(f"Setup failed at: {step_name}")
            return False
        print()
    
    print_success("Setup completed successfully!")
    print()
    print(f"{Color.BOLD}Next steps:{Color.ENDC}")
    print("  1. Review and update .env file with your configuration")
    print("  2. Run this script again to start the server")
    print()
    
    return True


def main():
    """Main entry point"""
    os.chdir(Path(__file__).parent)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command in ['setup', 'install']:
            return 0 if setup() else 1
        elif command in ['start', 'run', 'serve']:
            return 0 if start_server() else 1
        elif command == 'test':
            return 0 if run_tests() else 1
        elif command == 'status':
            check_status()
            return 0
        elif command in ['help', '-h', '--help']:
            print("Usage: python launcher.py [command]")
            print("\nCommands:")
            print("  setup    - Run initial setup")
            print("  start    - Start the server")
            print("  test     - Run tests")
            print("  status   - Check system status")
            print("  help     - Show this help message")
            return 0
        else:
            print_error(f"Unknown command: {command}")
            return 1
    
    # Interactive mode
    venv_exists = Path("venv").exists()
    
    if not venv_exists:
        print_info("First time setup detected")
        response = input("Would you like to run setup now? (Y/n): ").strip().lower()
        if response != 'n':
            if not setup():
                return 1
    
    while True:
        show_menu()
        
        try:
            choice = input(f"{Color.BOLD}Enter your choice (default=1): {Color.ENDC}").strip()
            if not choice:
                choice = '1'
            
            if choice == '0':
                print_info("Goodbye!")
                break
            elif choice == '1':
                start_server()
            elif choice == '2':
                install_dependencies()
            elif choice == '3':
                run_tests()
            elif choice == '4':
                initialize_database()
            elif choice == '5':
                python_exe = get_python_executable()
                subprocess.run([str(python_exe), "init_admin.py"])
            elif choice == '6':
                check_status()
            else:
                print_warning("Invalid choice, please try again")
            
            input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print_info("\nGoodbye!")
            break
        except Exception as e:
            print_error(f"Error: {e}")
            input("\nPress Enter to continue...")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
