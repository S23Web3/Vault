# n8n Webhook Testing & TradingView Integration
**Date:** 2026-01-28  
**Session:** TradingView to n8n Webhook Setup & Testing  
**Time:** ~45 minutes

---

## 🎯 Mission Accomplished

Successfully connected TradingView alerts to n8n workflow automation via secure Nginx reverse proxy on Jacky VPS.

---

## 📊 What We Built Today

### 1. Fixed n8n Webhook Configuration
**Issue identified:** Webhook node "Respond" parameter was set to "When Last Node Finishes" instead of "Using 'Respond to Webhook' Node"

**Fixed:**
- Changed Webhook node path from "Tradingview Alert" to "tradingview-alert" (removed spaces)
- Set Respond parameter to "Using 'Respond to Webhook' Node"
- Configured Respond to Webhook node with JSON response
- Published workflow (in newer n8n, "Published" = Active)

### 2. Nginx Reverse Proxy Setup
**Why:** TradingView only allows webhooks on port 80 or 443. n8n runs on port 5678.

**Solution:** Nginx reverse proxy to forward port 80 → port 5678

**Security features implemented:**
- IP whitelist (only TradingView IPs allowed)
- Rate limiting (10 requests/minute per IP)
- Specific path exposure (only `/webhook/tradingview-alert`)
- Security headers (X-Content-Type-Options, X-Frame-Options)
- Uses 127.0.0.1 instead of localhost

**Commands used:**
```bash
# Install Nginx
apt install nginx -y

# Create secure config
nano /etc/nginx/sites-available/n8n

# Enable config
ln -s /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/

# Test and restart
nginx -t
systemctl restart nginx
```

**TradingView IP Whitelist:**
- 52.89.214.238
- 34.212.75.30
- 54.218.53.128
- 52.32.178.7
- 76.13.20.191 (temporary for VPS testing)

### 3. Testing Results

**Test 1: Direct n8n (port 5678)**
```bash
curl -X POST http://76.13.20.191:5678/webhook/tradingview-alert \
  -H "Content-Type: application/json" \
  -d '{"ticker": "BTCUSDT", "price": "45000", "signal": "BUY"}'
```
✅ Result: `{"status":"received","message":"Alert received successfully"}`

**Test 2: Through Nginx (port 80)**
```bash
curl -X POST http://76.13.20.191/webhook/tradingview-alert \
  -H "Content-Type: application/json" \
  -d '{"ticker": "BTCUSDT", "price": "45000", "signal": "BUY"}'
```
✅ Result: `{"status":"received","message":"Alert received successfully"}`

**Test 3: Real TradingView Alert**
- Chart: GUNUSDT.P on BYBIT
- Webhook URL: `http://76.13.20.191/webhook/tradingview-alert`
- Message template:
```json
{
  "ticker": "{{ticker}}",
  "exchange": "{{exchange}}",
  "price": "{{close}}",
  "time": "{{timenow}}",
  "signal": "BUY"
}
```

**Real data received:**
- ticker: GUNUSDT.P
- exchange: BYBIT
- price: 0.03000425
- time: 2026-01-28T17:12:19Z
- signal: BUY
- Source IP: 52.32.178.7 (TradingView)

**Latency measurement:**
- TradingView sent: 17:12:19 UTC
- Nginx received: 17:12:20 UTC
- **Total latency: ~1 second** ⚡

---

## 🔧 Technical Details

### Nginx Configuration
**Location:** `/etc/nginx/sites-available/n8n`

```nginx
# Rate limiting zone - max 10 requests per minute per IP
limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=10r/m;

server {
    listen 80;
    server_name 76.13.20.191;

    # Only allow TradingView IPs
    allow 52.89.214.238;
    allow 34.212.75.30;
    allow 54.218.53.128;
    allow 52.32.178.7;
    allow 76.13.20.191;
    deny all;

    # Specific webhook path only
    location = /webhook/tradingview-alert {
        # Apply rate limiting
        limit_req zone=webhook_limit burst=5 nodelay;
        
        # Forward to n8n
        proxy_pass http://127.0.0.1:5678/webhook/tradingview-alert;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
    }
}
```

### n8n Workflow Structure
```
[Webhook Trigger] → [Respond to Webhook]
```

**Webhook Settings:**
- Path: `tradingview-alert`
- HTTP Method: POST
- Authentication: None
- Respond: Using 'Respond to Webhook' Node

**Respond to Webhook Settings:**
- Respond With: JSON
- Response Code: 200
- Response Body:
```json
{
  "status": "received",
  "message": "Alert received successfully"
}
```

---

## 🎓 Lessons Learned

### 1. Security First (Critical Improvement)
**Issue:** Initially provided Nginx config without security checks, wasted time fixing it afterward.

**Solution implemented:** Added mandatory security skill check BEFORE any infrastructure commands.

**Memory update added:** "ALWAYS check security skills BEFORE giving any infrastructure commands (VPS, Docker, Nginx, firewall, etc.). Security checks are MANDATORY and should happen first, not after commands are given."

### 2. Explain Commands (Critical Improvement)
**Issue:** Commands were given without explanation, causing confusion and delays.

**Solution implemented:** Now every command includes what it does.

**Memory update added:** "When providing commands (bash, PowerShell, curl, etc.), always explain what each command does before or after giving it"

### 3. Stop Apologizing
**Issue:** Too many apologies instead of direct fixes.

**Memory update added:** "Stop apologizing - just verify facts and fix issues directly"

### 4. Environment Awareness
**Issue:** Initially provided Windows PowerShell commands (`curl.exe`) when user was SSH'd into Ubuntu VPS.

**Fix:** Always confirm environment before providing commands.

### 5. n8n Interface Changes
Previous skill documentation was outdated:
- Old: "Activate workflow" toggle
- New: "Publish" button (Published = Active)
- No separate activation needed in newer n8n versions

### 6. Port Considerations
- TradingView: Only supports port 80 (HTTP) and 443 (HTTPS)
- n8n: Runs on port 5678
- Solution: Nginx reverse proxy mandatory for TradingView integration

---

## 📊 System Architecture

```
TradingView Alert (Chart)
    ↓
    ↓ HTTP POST (port 80)
    ↓
Nginx (IP whitelist + rate limiting)
    ↓
    ↓ Forward to localhost:5678
    ↓
n8n Webhook (Jacky VPS)
    ↓
    ↓ Process data
    ↓
Respond 200 OK
```

**Current status:** Phase 1 complete ✅  
**Next phase:** WEEX API integration for actual trading

---

## 🚀 Next Steps (Not Started Yet)

### Immediate (Next Session)
1. Add data processing node (Set or Code node)
2. Validate incoming signals
3. Connect to WEEX API
4. Test order placement (paper trading first)

### Short Term
5. Add position size calculation
6. Risk management checks
7. PostgreSQL logging
8. Telegram notifications

### Medium Term
9. SSL/TLS setup (HTTPS with Let's Encrypt)
10. Remove VPS IP from whitelist (only TradingView IPs)
11. Error handling and retry logic
12. Dashboard for trade monitoring

---

## ⚠️ Current Security Status

**✅ Implemented:**
- Firewall (UFW) active with ports 22, 80, 443, 5678
- fail2ban protecting SSH
- Nginx IP whitelist (TradingView IPs only)
- Rate limiting (10 req/min per IP)
- Docker containers isolated on private network
- Secrets in .env with 600 permissions

**⚠️ Still Needs:**
- SSL/TLS (currently HTTP only)
- Remove VPS IP from whitelist after testing
- Webhook authentication (optional, IP whitelist sufficient for now)
- SSH key authentication (currently password-based)

---

## 🔗 Important URLs & Credentials

**n8n Interface:**
- URL: http://76.13.20.191:5678
- Credentials: In `/root/n8n-setup/.env` on Jacky

**TradingView Webhook URL:**
```
http://76.13.20.191/webhook/tradingview-alert
```

**Jacky VPS:**
- IP: 76.13.20.191
- SSH: `ssh root@76.13.20.191`
- Location: Jakarta, Indonesia

---

## 📝 Key Commands Reference

### Nginx Management
```bash
# Test config
nginx -t

# Restart Nginx
systemctl restart nginx

# Check status
systemctl status nginx

# View access logs
tail -f /var/log/nginx/access.log

# View error logs
tail -f /var/log/nginx/error.log
```

### n8n Management
```bash
# Check containers
docker ps

# View n8n logs
docker logs jacky_n8n

# Restart n8n
cd /root/n8n-setup
docker compose restart
```

### Testing
```bash
# Test webhook through Nginx (port 80)
curl -X POST http://76.13.20.191/webhook/tradingview-alert \
  -H "Content-Type: application/json" \
  -d '{"ticker": "BTCUSDT", "price": "45000", "signal": "BUY"}'

# Test webhook direct to n8n (port 5678)
curl -X POST http://76.13.20.191:5678/webhook/tradingview-alert \
  -H "Content-Type: application/json" \
  -d '{"ticker": "BTCUSDT", "price": "45000", "signal": "BUY"}'

# Check for webhook requests
grep "tradingview-alert" /var/log/nginx/access.log | tail -10
```

---

## 💡 Performance Metrics

**Webhook Latency:**
- TradingView → Jacky VPS: ~1 second
- Total processing time: 24ms (n8n execution)
- Response time: Immediate (200 OK)

**System Resources:**
- Nginx memory: ~4MB
- n8n container: Running stable
- PostgreSQL: Running stable
- Disk usage: 2% (190GB available)

---

## 🎯 Session Summary

**Duration:** ~45 minutes  
**Status:** Successfully completed Phase 1  
**Blockers resolved:** 3 major (security gaps, port restrictions, configuration issues)  
**Tests passed:** 3/3 (direct n8n, nginx proxy, real TradingView)  
**Latency achieved:** ~1 second (excellent)

**Ready for:** WEEX API integration and actual trading execution

---

**End of Session**  
**Next Session Focus:** Add processing nodes and connect to WEEX exchange API
