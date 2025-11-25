#!/bin/bash
# Open port 8000 for API access

echo "Opening port 8000 in firewall..."

# Check if ufw is active
if command -v ufw &> /dev/null; then
    echo "UFW detected - allowing port 8000"
    sudo ufw allow 8000/tcp
    sudo ufw status
elif command -v firewall-cmd &> /dev/null; then
    echo "Firewalld detected - allowing port 8000"
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --reload
    sudo firewall-cmd --list-ports
else
    echo "No firewall detected or iptables in use"
fi

echo ""
echo "Testing API access..."
curl -s http://localhost:8000/stats/kpi | head -c 100
echo ""
echo ""
echo "Done! Try accessing http://143.110.144.231:8000/stats/kpi from your browser"
