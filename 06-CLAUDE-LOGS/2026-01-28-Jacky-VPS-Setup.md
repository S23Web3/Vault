# Jacky VPS Setup - Complete Session Log
**Date:** 2026-01-28
**Session:** VPS Infrastructure Setup & n8n Installation

---

## 🎯 Mission Accomplished Today

Set up complete trading automation infrastructure on Jacky (Jakarta VPS) with n8n workflow automation, PostgreSQL database, and secure configuration.

---

## 📦 What We Built

### 1. Jacky VPS Specifications
- **Hostname:** srv1280039.hstgr.cloud
- **IP Address:** 76.13.20.191
- **OS:** Ubuntu 24.04.3 LTS (Noble)
- **CPU:** 4 cores
- **RAM:** ~16GB
- **Disk:** 193GB (2% used, 190GB available)
- **Location:** Jakarta, Indonesia
- **Expiry:** 2027-01-18

### 2. Infrastructure Installed

**System Components:**
- ✅ Docker 29.2 (container platform)
- ✅ Docker Compose (multi-container orchestration)
- ✅ PostgreSQL 16 (database)
- ✅ n8n latest (workflow automation)
- ✅ UFW firewall (security)
- ✅ fail2ban (brute force protection)
- ✅ Essential tools (curl, wget, git, nano, htop, net-tools)

**Docker Containers Running:**
- `jacky_postgres` - PostgreSQL database on port 5432 (internal)
- `jacky_n8n` - n8n automation on port 5678 (external)

### 3. Security Configuration

**Firewall Rules (UFW):**
```
Port 22   - SSH (terminal access)
Port 80   - HTTP (webhooks)
Port 443  - HTTPS (SSL webhooks)
Port 5678 - n8n web interface
```

**Secrets Management:**
- All credentials stored in `/root/n8n-setup/.env` file
- File permissions: 600 (owner read/write only)
- Secrets NOT in docker-compose.yml (secure pattern)

**fail2ban:**
- Installed and running
- Auto-blocks brute force SSH attempts
- Ban time: 1 hour
- Max retries: 3

### 4. n8n Configuration

**Access:**
- URL: http://76.13.20.191:5678
- Status: Running and accessible
- Owner account: Created (Malik)
- Basic auth: Configured (credentials in .env)

**Environment Variables Set:**
- N8N_SECURE_COOKIE=false (temporary, will enable with SSL)
- N8N_HOST=76.13.20.191
- N8N_PORT=5678
- Database: PostgreSQL connection configured
- Timezone: Asia/Jakarta

**Webhook Status:**
- Test webhook created with path: "Tradingview Alert"
- Workflow: Published
- Issue: Path has spaces (needs fixing)
- Recommended path: `tradingview-alert` (no spaces)

---

## 🔧 Technical Details

### Directory Structure
```
/root/n8n-setup/
├── docker-compose.yml    # Container configuration
└── .env                  # Secrets (600 permissions)
```

### Docker Compose Configuration
**Services:**
1. **postgres** - Database backend
   - Image: postgres:16
   - Volume: postgres_data (persistent storage)
   - Network: n8n_network (isolated)

2. **n8n** - Workflow automation
   - Image: n8nio/n8n:latest
   - Port: 5678 exposed
   - Volume: n8n_data (persistent workflows)
   - Depends on: postgres
   - Network: n8n_network

**Volumes:**
- `postgres_data` - Database persistence
- `n8n_data` - Workflow and configuration persistence

### Key Commands Used

**System Management:**
```bash
# Update system
apt update && apt upgrade -y

# Start containers
cd /root/n8n-setup
docker compose up -d

# Check running containers
docker ps

# View logs
docker logs jacky_n8n
docker logs jacky_postgres

# Firewall status
ufw status numbered
```

**Security Commands:**
```bash
# Set file permissions
chmod 600 .env

# Check firewall
ufw status

# Check fail2ban
systemctl status fail2ban
```

---

## 🎓 Important Lessons Learned

### 1. Security First
- **Never store secrets in docker-compose.yml** - Use .env files with restricted permissions
- Questioned plaintext passwords in YAML - correct security instinct
- File permissions matter: 600 for secrets, 644 for configs

### 2. Skills Matter
- Created and uploaded **devops-security.skill** - Proactive security checking
- Created and uploaded **n8n-workflow-automation.skill** - n8n best practices
- Skills help catch security issues before they become problems
- My training data can be outdated - verify current interface

### 3. n8n Interface Changes
- Documentation in skill was outdated (based on old n8n version)
- Current n8n uses "Respond" dropdown (not "Response Mode")
- Activation is via menu, not obvious toggle switch
- Test mode vs Production mode distinction is critical

### 4. Webhook Path Best Practices
- Avoid spaces in webhook paths
- Use hyphens instead: `tradingview-alert` not `Tradingview Alert`
- Production URL: `/webhook/path`
- Test URL: `/webhook-test/path`

---

## 🐛 Issues Encountered & Solved

### Issue 1: Stuck apt Process
**Problem:** apt-get process running since Jan 23 (5 days), blocking updates
**Solution:** Killed stuck processes, removed lock files
```bash
kill -9 33694
rm -f /var/lib/apt/lists/lock
dpkg --configure -a
```

### Issue 2: n8n Secure Cookie Error
**Problem:** "Your n8n server is configured to use a secure cookie"
**Solution:** Added `N8N_SECURE_COOKIE=false` to environment variables
**Note:** Temporary fix, will enable with SSL/HTTPS later

### Issue 3: Webhook Not Registered
**Problem:** curl returns 404 "webhook not registered"
**Cause:** Workflow not activated (only published)
**Solution:** Need to activate workflow (still working on finding activation control)

### Issue 4: Webhook Path with Spaces
**Problem:** Path "Tradingview Alert" has spaces, causing URL encoding issues
**Status:** Needs to be changed to `tradingview-alert`
**Solution:** Edit webhook node, update path, republish

---

## 📝 Credentials Saved

**Obsidian Files Created:**
- `Tv.md` - TradingView credentials (KEEP SECURE)
- `claud.md` - Conversation log (auto-updated)

**VPS Access:**
```
SSH: ssh root@76.13.20.191
Password: [saved in your password manager]
```

**n8n Access:**
```
URL: http://76.13.20.191:5678
Username: admin
Password: [in /root/n8n-setup/.env file on Jacky]
```

**PostgreSQL:**
```
Host: localhost (internal to Docker)
Port: 5432
Database: n8n
User: n8n
Password: [in /root/n8n-setup/.env file]
```

---

## ⚠️ Security Notes

### Current Security Status
✅ **Good:**
- Firewall active and configured
- Secrets in .env with 600 permissions
- fail2ban protecting SSH
- Docker containers isolated on private network
- Basic auth on n8n enabled

⚠️ **Needs Improvement:**
- No SSL/HTTPS yet (using HTTP)
- n8n secure cookie disabled
- No webhook authentication yet
- Port 5678 publicly accessible

### Recommended Next Steps for Security
1. Set up Nginx reverse proxy
2. Configure SSL certificates (Let's Encrypt)
3. Add webhook authentication (API key/secret)
4. Enable n8n secure cookie
5. Consider SSH key authentication (disable password)
6. Close port 5678, route through Nginx only

---

## 🚀 Next Steps (Prioritized)

### Immediate (Next Session)
1. **Fix webhook path** - Change from "Tradingview Alert" to "tradingview-alert"
2. **Activate workflow** - Find and enable activation control
3. **Test webhook** - Verify curl command works
4. **Add second node** - Process webhook data (Set node or Function node)

### Short Term (This Week)
5. **Connect to WEEX API** - Add HTTP Request node for order placement
6. **Add validation** - IF node to check signal validity
7. **Add notifications** - Telegram node for trade alerts
8. **Test end-to-end** - TradingView → n8n → WEEX → Telegram

### Medium Term (Next Week)
9. **Set up Nginx** - Reverse proxy for SSL
10. **Configure SSL** - Let's Encrypt certificates
11. **Add webhook security** - API key authentication
12. **Database logging** - Store all trades in PostgreSQL
13. **Build dashboard** - Query and visualize trade history

### Long Term (Ongoing)
14. **Position management** - Check existing positions before opening new
15. **Risk management** - Calculate position sizes based on account balance
16. **Error handling** - Robust retry and failure notifications
17. **Monitoring** - Uptime tracking and performance metrics
18. **Backup strategy** - Automated workflow and database backups

---

## 💡 Key Insights

### Infrastructure Philosophy
- **Security first, convenience second** - Always question exposing credentials
- **Skills extend capabilities** - Adding skills improves output quality
- **Documentation ages** - Interfaces change, verify current state
- **Test before production** - Use test webhooks during development

### Trading System Architecture
```
TradingView (Chart) 
    ↓ Alert
Webhook (n8n receives signal)
    ↓ Validate
Process (calculate position, check risk)
    ↓ Execute
Exchange API (WEEX - place order)
    ↓ Log
Database (PostgreSQL - trade history)
    ↓ Notify
Telegram (confirmation message)
```

### VPS Management
- Keep system updated: `apt update && apt upgrade`
- Monitor disk space: `df -h`
- Check container health: `docker ps`
- View logs when debugging: `docker logs <container>`
- Firewall is your friend: `ufw status`

---

## 📚 Skills Created Today

### 1. devops-security.skill
**Purpose:** Proactive security checking for VPS, Docker, and infrastructure
**Covers:**
- Secrets management patterns
- Docker security best practices
- SSH hardening
- Firewall configuration
- fail2ban setup
- Common security pitfalls

### 2. n8n-workflow-automation.skill
**Purpose:** Comprehensive n8n workflow automation guide
**Covers:**
- Webhook setup and configuration
- TradingView integration
- API calls and HTTP requests
- Data manipulation
- Error handling
- Database integration
- Notifications
- Trading system workflows

**Status:** Both uploaded to Claude

---

## 🎯 Current Status Summary

**Infrastructure:** ✅ Fully operational
**Security:** ⚠️ Basic level (needs SSL/auth)
**n8n:** ⚠️ Running but workflow not activated
**Webhook:** ⚠️ Created but needs path fix and activation
**Database:** ✅ Running and connected
**Next Critical Task:** Activate workflow and test webhook

---

## 📞 Support Information

**If Things Go Wrong:**

1. **Can't SSH to Jacky:**
   - Check VPS is running in Hostinger panel
   - Verify IP hasn't changed: 76.13.20.191
   - Check firewall on your local network

2. **n8n not accessible:**
   ```bash
   docker ps  # Check if container is running
   docker logs jacky_n8n  # Check for errors
   docker compose restart  # Restart containers
   ```

3. **Database connection issues:**
   ```bash
   docker logs jacky_postgres  # Check database logs
   # Verify .env file has correct credentials
   ```

4. **Webhook not working:**
   - Verify workflow is activated (green/active state)
   - Check webhook path matches URL
   - Test with curl before using TradingView
   - Check n8n logs: `docker logs jacky_n8n`

---

## 🔗 Related Files

- `Tv.md` - TradingView credentials (SECURE)
- `claud.md` - Full conversation log
- `/root/n8n-setup/.env` - Environment variables on Jacky
- `/root/n8n-setup/docker-compose.yml` - Container config on Jacky

---

## 📊 System Health Checklist

Run these periodically:

```bash
# SSH to Jacky
ssh root@76.13.20.191

# Check disk space
df -h

# Check containers
docker ps

# Check system resources
htop

# Check firewall
ufw status

# Check fail2ban
fail2ban-client status

# Check for updates
apt update && apt list --upgradable

# View n8n logs
docker logs jacky_n8n --tail 50

# View PostgreSQL logs
docker logs jacky_postgres --tail 20
```

---

**End of Session Summary**
**Total Time:** ~2 hours
**Achievement:** Complete VPS infrastructure setup with n8n automation platform
**Status:** Ready for trading workflow development

**Next Session Focus:** Activate workflow, test webhook, build TradingView → WEEX automation
