#!/bin/bash

################################################################################
# Crude Oil Algorithmic Trading System - Setup Script
#
# This script automates the setup process for Unix-based systems (Linux, Mac)
# For Windows, see INSTALLATION.md for manual setup instructions
#
# Usage: bash setup.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}║    Crude Oil Algorithmic Trading System - Setup           ║${NC}"
    echo -e "${BLUE}║                                                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Python is installed
check_python() {
    print_info "Checking Python installation..."

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        print_success "Python $PYTHON_VERSION found"

        # Check if version is 3.9+
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 9 ]; then
            print_success "Python version is compatible (>= 3.9)"
        else
            print_error "Python 3.9+ required (found $PYTHON_VERSION)"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.9 or later."
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_info "Creating Python virtual environment..."

    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping..."
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

# Activate virtual environment and install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    cd PythonML
    pip install -r requirements.txt
    cd ..

    print_success "Python dependencies installed"
}

# Create directory structure
create_directories() {
    print_info "Creating directory structure..."

    mkdir -p data
    mkdir -p models
    mkdir -p logs
    mkdir -p backtest_results

    print_success "Directories created"
}

# Generate sample data
generate_sample_data() {
    print_info "Would you like to generate sample data for testing? (y/n)"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        source venv/bin/activate
        cd Utils
        python data_fetcher.py --source sample --bars 1000 --output ../data --filename sample_crude_oil.csv
        cd ..
        print_success "Sample data generated: data/sample_crude_oil.csv"
    else
        print_info "Skipping sample data generation"
    fi
}

# Train ML models
train_models() {
    print_info "Would you like to train ML models now? (y/n)"
    print_warning "Note: This requires historical data and may take several minutes"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        if [ -f "data/sample_crude_oil.csv" ]; then
            source venv/bin/activate
            cd PythonML
            python train_models.py --data ../data/sample_crude_oil.csv --output ../models
            cd ..
            print_success "ML models trained and saved to models/"
        else
            print_error "No historical data found. Please generate or import data first."
        fi
    else
        print_info "Skipping model training"
    fi
}

# Test ML server
test_ml_server() {
    print_info "Would you like to test the ML server? (y/n)"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Starting ML server... (Press Ctrl+C to stop)"
        source venv/bin/activate
        cd PythonML
        timeout 5 python ml_signal_server.py --host 127.0.0.1 --port 5555 &
        SERVER_PID=$!
        cd ..

        sleep 2

        # Test connection
        python3 -c "import zmq; ctx = zmq.Context(); sock = ctx.socket(zmq.REQ); sock.connect('tcp://127.0.0.1:5555'); sock.send_json({'request_type': 'health_check'}); response = sock.recv_json(); print('Server response:', response)"

        if [ $? -eq 0 ]; then
            print_success "ML server test successful"
        else
            print_error "ML server test failed"
        fi

        # Kill server
        kill $SERVER_PID 2>/dev/null
    else
        print_info "Skipping ML server test"
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    Setup Complete!                         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Next Steps:${NC}"
    echo ""
    echo "1. Activate the virtual environment:"
    echo -e "   ${YELLOW}source venv/bin/activate${NC}"
    echo ""
    echo "2. Start the ML server:"
    echo -e "   ${YELLOW}cd PythonML && python ml_signal_server.py${NC}"
    echo ""
    echo "3. For NinjaTrader setup (Windows only):"
    echo -e "   ${YELLOW}See INSTALLATION.md for detailed instructions${NC}"
    echo ""
    echo "4. Generate historical data (optional):"
    echo -e "   ${YELLOW}python Utils/data_fetcher.py --source yahoo --symbol CL=F${NC}"
    echo ""
    echo "5. Train ML models:"
    echo -e "   ${YELLOW}python PythonML/train_models.py --data data/your_data.csv${NC}"
    echo ""
    echo "6. Read the documentation:"
    echo -e "   ${YELLOW}See README.md for complete feature guide${NC}"
    echo ""
    echo -e "${BLUE}Support:${NC}"
    echo "  GitHub: https://github.com/yourusername/CrudeOilAlgoSystem"
    echo "  Issues: https://github.com/yourusername/CrudeOilAlgoSystem/issues"
    echo ""
    echo -e "${YELLOW}Happy Trading! 🚀${NC}"
    echo ""
}

# Main execution
main() {
    print_header

    check_python
    create_venv
    install_dependencies
    create_directories
    generate_sample_data
    train_models
    test_ml_server

    print_next_steps
}

# Run main function
main
