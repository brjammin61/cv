#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# MIMIC V3.1 HARDENED - DigitalOcean Deployment Script
# Full automated setup for production deployment
# ═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║    ███╗   ███╗██╗███╗   ███╗██╗ ██████╗    ██╗   ██╗██████╗    ██╗           ║"
echo "║    ████╗ ████║██║████╗ ████║██║██╔════╝    ██║   ██║╚════██╗  ███║           ║"
echo "║    ██╔████╔██║██║██╔████╔██║██║██║         ██║   ██║ █████╔╝  ╚██║           ║"
echo "║    ██║╚██╔╝██║██║██║╚██╔╝██║██║██║         ╚██╗ ██╔╝ ╚═══██╗   ██║           ║"
echo "║    ██║ ╚═╝ ██║██║██║ ╚═╝ ██║██║╚██████╗     ╚████╔╝ ██████╔╝██╗██║           ║"
echo "║    ╚═╝     ╚═╝╚═╝╚═╝     ╚═╝╚═╝ ╚═════╝      ╚═══╝  ╚═════╝ ╚═╝╚═╝           ║"
echo "║                                                                              ║"
echo "║                    HARDENED DEPLOYMENT SCRIPT                                ║"
echo "║                      DigitalOcean Edition                                    ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

INSTALL_DIR="/root/mimic_v3"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_USER="root"
DASHBOARD_PORT=8080
PYTHON_VERSION="3.11"

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

log_step() {
    echo -e "\n${GREEN}[STEP]${NC} $1"
}

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: SYSTEM UPDATE & DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════════

install_system_deps() {
    log_step "Updating system and installing dependencies..."

    apt-get update -y
    apt-get upgrade -y

    apt-get install -y \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-venv \
        python${PYTHON_VERSION}-dev \
        python3-pip \
        git \
        curl \
        wget \
        htop \
        tmux \
        nginx \
        certbot \
        python3-certbot-nginx \
        sqlite3 \
        jq \
        ufw

    log_info "System dependencies installed"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: FIREWALL CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

configure_firewall() {
    log_step "Configuring firewall..."

    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp      # HTTP
    ufw allow 443/tcp     # HTTPS
    ufw allow $DASHBOARD_PORT/tcp  # Dashboard

    echo "y" | ufw enable

    log_info "Firewall configured"
    ufw status
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: CREATE DIRECTORY STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

create_directories() {
    log_step "Creating directory structure..."

    mkdir -p $INSTALL_DIR
    mkdir -p $INSTALL_DIR/data
    mkdir -p $INSTALL_DIR/logs
    mkdir -p $INSTALL_DIR/models
    mkdir -p $INSTALL_DIR/backups

    log_info "Directories created at $INSTALL_DIR"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: COPY PROJECT FILES
# ═══════════════════════════════════════════════════════════════════════════════

copy_project_files() {
    log_step "Copying project files..."

    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

    # Copy all mimic_v3 files
    if [ -d "$SCRIPT_DIR" ]; then
        cp -r $SCRIPT_DIR/* $INSTALL_DIR/
        log_info "Project files copied"
    else
        log_error "Source directory not found: $SCRIPT_DIR"
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: PYTHON VIRTUAL ENVIRONMENT
# ═══════════════════════════════════════════════════════════════════════════════

setup_venv() {
    log_step "Setting up Python virtual environment..."

    cd $INSTALL_DIR

    python${PYTHON_VERSION} -m venv $VENV_DIR
    source $VENV_DIR/bin/activate

    pip install --upgrade pip wheel setuptools
    pip install -r requirements.txt

    log_info "Virtual environment ready at $VENV_DIR"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6: ENVIRONMENT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

setup_env_file() {
    log_step "Setting up environment configuration..."

    ENV_FILE="$INSTALL_DIR/.env"

    if [ ! -f "$ENV_FILE" ]; then
        cat > $ENV_FILE << 'ENVEOF'
# ═══════════════════════════════════════════════════════════════════════════════
# MIMIC V3.1 HARDENED - Environment Configuration
# ═══════════════════════════════════════════════════════════════════════════════

# Kalshi API Credentials
# Get these from: https://kalshi.com/settings/api
KALSHI_API_KEY=your_api_key_here
KALSHI_API_SECRET=your_api_secret_here

# Use demo API (true for paper trading on demo.kalshi.com)
KALSHI_DEMO_MODE=false

# Perplexity API (for News Oracle sentiment analysis)
# Get from: https://www.perplexity.ai/settings/api
PERPLEXITY_API_KEY=your_perplexity_key_here

# Trading Configuration
INITIAL_CAPITAL=1000.0
MAX_DAILY_LOSS=50.0
MAX_WEEKLY_LOSS=150.0
KELLY_FRACTION=0.25

# Dashboard
DASHBOARD_PORT=8080
DASHBOARD_ENABLED=true

# Logging
LOG_LEVEL=INFO
ENVEOF

        chmod 600 $ENV_FILE
        log_warn "Created .env file - EDIT THIS WITH YOUR API KEYS!"
        log_warn "Location: $ENV_FILE"
    else
        log_info ".env file already exists"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7: SYSTEMD SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

setup_systemd() {
    log_step "Setting up systemd service..."

    cat > /etc/systemd/system/mimic.service << SERVICEEOF
[Unit]
Description=MIMIC V3.1 HARDENED Trading System
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/python main_mimic.py --dashboard-port $DASHBOARD_PORT
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/mimic_stdout.log
StandardError=append:$INSTALL_DIR/logs/mimic_stderr.log

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
SERVICEEOF

    systemctl daemon-reload
    systemctl enable mimic.service

    log_info "Systemd service configured"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8: NGINX REVERSE PROXY (Optional)
# ═══════════════════════════════════════════════════════════════════════════════

setup_nginx() {
    log_step "Setting up Nginx reverse proxy..."

    cat > /etc/nginx/sites-available/mimic << 'NGINXEOF'
server {
    listen 80;
    server_name _;

    # Dashboard
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_read_timeout 86400;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8080/api/health;
    }
}
NGINXEOF

    ln -sf /etc/nginx/sites-available/mimic /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    nginx -t && systemctl restart nginx

    log_info "Nginx configured"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9: LOG ROTATION
# ═══════════════════════════════════════════════════════════════════════════════

setup_logrotate() {
    log_step "Setting up log rotation..."

    cat > /etc/logrotate.d/mimic << 'LOGEOF'
/root/mimic_v3/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload mimic > /dev/null 2>&1 || true
    endscript
}
LOGEOF

    log_info "Log rotation configured"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 10: BACKUP SCRIPT
# ═══════════════════════════════════════════════════════════════════════════════

setup_backup() {
    log_step "Setting up daily backup..."

    cat > $INSTALL_DIR/backup.sh << 'BACKUPEOF'
#!/bin/bash
# Daily backup script for MIMIC V3.1

BACKUP_DIR="/root/mimic_v3/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
cp /root/mimic_v3/data/mimic_data.db "$BACKUP_DIR/mimic_data_$TIMESTAMP.db"

# Backup models
tar -czf "$BACKUP_DIR/models_$TIMESTAMP.tar.gz" -C /root/mimic_v3 models/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
BACKUPEOF

    chmod +x $INSTALL_DIR/backup.sh

    # Add to crontab (daily at 3 AM)
    (crontab -l 2>/dev/null; echo "0 3 * * * $INSTALL_DIR/backup.sh >> $INSTALL_DIR/logs/backup.log 2>&1") | crontab -

    log_info "Daily backup configured (3 AM)"
}

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 11: CREATE MANAGEMENT COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

create_management_scripts() {
    log_step "Creating management scripts..."

    # Start script
    cat > $INSTALL_DIR/start.sh << 'EOF'
#!/bin/bash
sudo systemctl start mimic
echo "MIMIC V3.1 started"
sudo systemctl status mimic --no-pager
EOF

    # Stop script
    cat > $INSTALL_DIR/stop.sh << 'EOF'
#!/bin/bash
sudo systemctl stop mimic
echo "MIMIC V3.1 stopped"
EOF

    # Status script
    cat > $INSTALL_DIR/status.sh << 'EOF'
#!/bin/bash
echo "═══════════════════════════════════════════════════════════"
echo "MIMIC V3.1 HARDENED - System Status"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Service Status:"
sudo systemctl status mimic --no-pager
echo ""
echo "Dashboard: http://$(curl -s ifconfig.me):8080"
echo ""
echo "Recent Logs:"
tail -20 /root/mimic_v3/logs/mimic_cortex.log
EOF

    # Logs script
    cat > $INSTALL_DIR/logs.sh << 'EOF'
#!/bin/bash
tail -f /root/mimic_v3/logs/mimic_cortex.log
EOF

    # DB stats script
    cat > $INSTALL_DIR/db_stats.sh << 'EOF'
#!/bin/bash
echo "═══════════════════════════════════════════════════════════"
echo "MIMIC V3.1 - Database Statistics"
echo "═══════════════════════════════════════════════════════════"
sqlite3 /root/mimic_v3/data/mimic_data.db << 'SQL'
.mode column
.headers on
SELECT 'Whales Tracked' as metric, COUNT(*) as value FROM shadow_whales;
SELECT 'Total Trades' as metric, COUNT(*) as value FROM trade_history;
SELECT 'Open Positions' as metric, COUNT(*) as value FROM trade_history WHERE status = 'OPEN';
SELECT 'Total P&L' as metric, ROUND(SUM(pnl), 2) as value FROM trade_history WHERE pnl IS NOT NULL;
SQL
EOF

    chmod +x $INSTALL_DIR/*.sh

    log_info "Management scripts created"
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

main() {
    check_root

    install_system_deps
    configure_firewall
    create_directories
    copy_project_files
    setup_venv
    setup_env_file
    setup_systemd
    setup_nginx
    setup_logrotate
    setup_backup
    create_management_scripts

    echo -e "\n${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║                    DEPLOYMENT COMPLETE!                                      ║"
    echo "║                                                                              ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    echo "║                                                                              ║"
    echo "║  NEXT STEPS:                                                                 ║"
    echo "║                                                                              ║"
    echo "║  1. Edit your API keys:                                                      ║"
    echo "║     nano /root/mimic_v3/.env                                                 ║"
    echo "║                                                                              ║"
    echo "║  2. Start the system:                                                        ║"
    echo "║     systemctl start mimic                                                    ║"
    echo "║                                                                              ║"
    echo "║  3. View the dashboard:                                                      ║"
    printf "║     http://%-45s            ║\n" "$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR_IP'):8080"
    echo "║                                                                              ║"
    echo "║  4. Monitor logs:                                                            ║"
    echo "║     /root/mimic_v3/logs.sh                                                   ║"
    echo "║                                                                              ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    echo "║                                                                              ║"
    echo "║  MANAGEMENT COMMANDS:                                                        ║"
    echo "║    ./start.sh    - Start MIMIC                                               ║"
    echo "║    ./stop.sh     - Stop MIMIC                                                ║"
    echo "║    ./status.sh   - View status                                               ║"
    echo "║    ./logs.sh     - Tail logs                                                 ║"
    echo "║    ./db_stats.sh - Database statistics                                       ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Run main function
main "$@"
