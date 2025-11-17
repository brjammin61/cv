# MonadPulse Deployment: Complete Walkthrough (Start from Zero)

This guide assumes you've never deployed anything before. Follow every step exactly.

---

## STEP 1: Create a DigitalOcean Account (5 minutes)

### 1.1 Go to DigitalOcean

Open your browser and go to: **https://www.digitalocean.com/**

### 1.2 Sign Up

- Click **"Sign Up"** in the top right
- Enter your email address
- Create a password
- Click **"Sign Up"**
- Check your email and click the verification link

### 1.3 Add Payment Method

- After logging in, you'll be prompted to add a payment method
- Choose **Credit/Debit Card** or **PayPal**
- Enter your payment information
- DigitalOcean may charge $1 to verify your card (they'll refund it)

**Cost**: You'll pay ~$12/month for the VPS. You can cancel anytime.

---

## STEP 2: Create Your VPS (Droplet) (3 minutes)

### 2.1 Create New Droplet

After logging in to DigitalOcean:
- Click the green **"Create"** button in the top right
- Select **"Droplets"** from the dropdown

### 2.2 Choose Image

You'll see "Choose an image":
- Click **"Ubuntu"**
- Select **"22.04 (LTS) x64"**

### 2.3 Choose Size

Scroll down to "Choose Size":
- Click **"Regular"** (should be selected by default)
- Select the **$12/month** plan:
  - 2 GB RAM
  - 1 CPU
  - 50 GB SSD
  
(Don't pick the $6/month one - it only has 1GB RAM which isn't enough)

### 2.4 Choose Region

Scroll down to "Choose a datacenter region":
- Pick the region closest to you
- Examples: 
  - US: "New York 1" or "San Francisco 3"
  - Europe: "London 1" or "Frankfurt 1"
  - Asia: "Singapore 1"

### 2.5 Authentication

Scroll down to "Authentication":

**Option A: Password (Easier for beginners)**
- Select **"Password"**
- Enter a strong password (write it down!)
- Example: `MonadPulse2025!Secure`

**Option B: SSH Key (More secure, but requires setup)**
- If you already have an SSH key, select "SSH keys" and add it
- If you don't know what this means, use **Password** instead

### 2.6 Finalize and Create

- Scroll down past all other options (leave them as default)
- In the "Choose a hostname" box, enter: `monadpulse`
- Click the big green **"Create Droplet"** button at the bottom

### 2.7 Wait for Creation

- You'll see a progress bar
- Wait 30-60 seconds
- When it's done, you'll see your droplet with an IP address

### 2.8 Copy Your IP Address

- You'll see your droplet with an IP address like: `159.89.123.45`
- **COPY THIS IP ADDRESS** - you'll need it for the next steps
- Write it down or save it in a note

**Example**: `159.89.123.45`

---

## STEP 3: Connect to Your VPS (2 minutes)

Now you need to connect to your VPS from your computer.

### 3.1 Open Terminal

**On Mac:**
- Press `Cmd + Space`
- Type "Terminal"
- Press Enter

**On Windows:**
- Press `Windows Key + R`
- Type "cmd"
- Press Enter

**On Linux:**
- Press `Ctrl + Alt + T`

### 3.2 SSH Into Your VPS

In the terminal, type this command (replace `YOUR_IP` with your actual IP):

```bash
ssh root@YOUR_IP
```

**Example**:
```bash
ssh root@159.89.123.45
```

Press **Enter**

### 3.3 First Time Connection

You'll see a message like:
```
The authenticity of host '159.89.123.45' can't be established.
Are you sure you want to continue connecting (yes/no)?
```

Type: **yes**

Press **Enter**

### 3.4 Enter Password

You'll be prompted for a password.

- Type the password you created in Step 2.5
- **NOTE**: When you type, you won't see any characters appear (this is normal for security)
- Press **Enter**

### 3.5 Success!

You should now see something like:
```
Welcome to Ubuntu 22.04.3 LTS
root@monadpulse:~#
```

**Congratulations!** You're now connected to your VPS!

---

## STEP 4: Install Dependencies (5 minutes)

Now we'll install everything MonadPulse needs to run.

### 4.1 Download Setup Script

Copy and paste this **entire command** into your terminal:

```bash
curl -o setup.sh https://raw.githubusercontent.com/brjammin61/cv/claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE/monadpulse_backend/scripts/setup_server.sh
```

Press **Enter**

You should see:
```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  3456  100  3456    0     0  12345      0 --:--:-- --:--:-- --:--:-- 12345
```

### 4.2 Make Script Executable

Copy and paste:

```bash
chmod +x setup.sh
```

Press **Enter**

### 4.3 Run Setup Script

Copy and paste:

```bash
./setup.sh
```

Press **Enter**

### 4.4 Wait for Installation

You'll see a lot of text scrolling by. This is normal!

The script is installing:
- Docker (for running containers)
- Docker Compose (for managing multiple containers)
- Nginx (web server)
- Certbot (for SSL certificates)
- Node.js (for building the frontend)

**This will take 3-5 minutes**. Don't close the terminal!

### 4.5 Verify Success

When it's done, you'll see:
```
✅ Server setup complete!
```

To verify everything installed correctly, run:

```bash
docker --version
```

You should see something like: `Docker version 24.0.7`

---

## STEP 5: Deploy MonadPulse (10 minutes)

Now we'll actually deploy the MonadPulse application.

### 5.1 Download Deployment Script

Copy and paste this entire command:

```bash
curl -o deploy.sh https://raw.githubusercontent.com/brjammin61/cv/claude/monadpulse-backend-launch-01QaDPgtQw9qw3xurAzNScyE/monadpulse_backend/scripts/deploy.sh
```

Press **Enter**

### 5.2 Make Script Executable

Copy and paste:

```bash
chmod +x deploy.sh
```

Press **Enter**

### 5.3 Run Deployment

Copy and paste:

```bash
./deploy.sh
```

Press **Enter**

### 5.4 Watch the Magic Happen

The script will now:
1. Clone your GitHub repository
2. Install the backend (API + Database)
3. Build the React frontend
4. Configure Nginx
5. Start all services

You'll see output like:
```
📦 Cloning repository...
🐳 Starting backend services...
⚛️  Building React frontend...
🌐 Configuring Nginx...
✅ Deployment complete!
```

**This takes 5-10 minutes**. Be patient!

### 5.5 Verify Services Are Running

When deployment finishes, check that everything is running:

```bash
docker ps
```

You should see **3 containers** running:
- `monadpulse_backend-api-1`
- `monadpulse_backend-db-1`
- `monadpulse_backend-ingestor-1`

---

## STEP 6: Test Your Deployment (2 minutes)

Now let's verify everything works!

### 6.1 Test Backend API

From your terminal (still connected to VPS), run:

```bash
curl http://localhost:8000/health
```

You should see:
```json
{"status":"healthy","timestamp":"2025-11-17T...","database":"connected"}
```

If you see this, **your backend is working!** ✅

### 6.2 Test Frontend

Open your web browser on your **local computer** (not the VPS).

Go to: `http://YOUR_VPS_IP`

**Example**: `http://159.89.123.45`

You should see the **MonadPulse Dashboard**:
- 4 KPI cards at the top (Total MEV, Omega Partners, etc.)
- A chart showing 14-day MEV trends
- A leaderboard of validators

**If you see this, YOU'RE LIVE!** 🎉

---

## STEP 7: Access via VS Code (Optional, 5 minutes)

Now let's connect VS Code so you can edit files easily.

### 7.1 Install Remote SSH Extension

1. Open VS Code on your computer
2. Click the **Extensions** icon (left sidebar, looks like 4 squares)
3. Search for: **Remote - SSH**
4. Click **Install** on the one by Microsoft

### 7.2 Connect to Your VPS

1. Press `Cmd + Shift + P` (Mac) or `Ctrl + Shift + P` (Windows)
2. Type: **Remote-SSH: Connect to Host**
3. Click it
4. Type: `root@YOUR_VPS_IP` (example: `root@159.89.123.45`)
5. Press Enter
6. Enter your password when prompted
7. Wait for VS Code to connect (30 seconds)

### 7.3 Open MonadPulse Folder

1. In VS Code, click **File → Open Folder**
2. Type: `/opt/monadpulse`
3. Click **OK**

Now you can see and edit all your MonadPulse files in VS Code! 🎨

---

## STEP 8: What You Just Built

Your MonadPulse system is now:

✅ **Live on the internet** at `http://YOUR_VPS_IP`
✅ **Backend API** running on port 8000
✅ **React Frontend** with live charts and leaderboards
✅ **PostgreSQL Database** storing validator data
✅ **Auto-updating** validator data every 2 minutes
✅ **Auto-refreshing** dashboard every 5 seconds

---

## Common Issues & Solutions

### Issue 1: "Connection refused" when SSH-ing

**Solution**: 
- Wait 2 minutes (VPS might still be booting)
- Verify IP address is correct
- Check you're using the right password

### Issue 2: "docker: command not found"

**Solution**:
```bash
# Run this to reload your shell
source ~/.bashrc

# Try docker --version again
docker --version
```

### Issue 3: Frontend shows blank page

**Solution**:
```bash
# Check if Nginx is running
systemctl status nginx

# Check Nginx error logs
tail -f /var/log/nginx/error.log

# Restart Nginx
systemctl restart nginx
```

### Issue 4: Backend API not responding

**Solution**:
```bash
# Check if containers are running
docker ps

# View backend logs
cd /opt/monadpulse/monadpulse_backend
docker-compose logs api

# Restart backend
docker-compose restart
```

---

## Next Steps

### Immediate (Today)

1. ✅ Share your dashboard URL with friends: `http://YOUR_IP`
2. ✅ Test from your phone
3. ✅ Test from different browsers
4. ✅ Bookmark your VPS IP address

### This Week

1. Consider registering a domain (optional but professional)
2. Set up SSL with Let's Encrypt for HTTPS
3. Monitor logs for any issues
4. Test all dashboard features thoroughly

### Before Nov 24 (Mainnet Launch)

1. Read the Monad SDK integration guide in README
2. Prepare to integrate real validator data
3. Plan your soft launch in Monad Discord

---

## Helpful Commands

### View Backend Logs
```bash
cd /opt/monadpulse/monadpulse_backend
docker-compose logs -f
```

### Restart Everything
```bash
cd /opt/monadpulse/monadpulse_backend
docker-compose restart
systemctl restart nginx
```

### Stop Everything
```bash
cd /opt/monadpulse/monadpulse_backend
docker-compose down
systemctl stop nginx
```

### Start Everything
```bash
cd /opt/monadpulse/monadpulse_backend
docker-compose up -d
systemctl start nginx
```

### Check What's Running
```bash
docker ps                    # Docker containers
systemctl status nginx       # Nginx web server
```

---

## Cost Breakdown

- **VPS**: $12/month (DigitalOcean)
- **Domain**: $10-15/year (optional, from Namecheap/GoDaddy)
- **SSL**: FREE (Let's Encrypt)

**Total**: $12/month or $144/year

You can cancel anytime and won't be charged after cancellation.

---

## You Did It! 🚀

Your MonadPulse validator analytics dashboard is now live and running 24/7.

When Monad mainnet launches on **Nov 24, 2025**, you'll integrate the real SDK and start tracking actual validator performance!

---

## Need Help?

If you get stuck:
1. Re-read the section you're on carefully
2. Check "Common Issues & Solutions" above
3. Look at the logs: `docker-compose logs -f`
4. Double-check your IP address is correct
5. Make sure you didn't skip any steps

Remember: You can always destroy the droplet and start over if something goes wrong!
