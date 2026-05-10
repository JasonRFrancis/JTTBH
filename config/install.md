# JTTBH — Linode Production Server Setup

Target: Ubuntu 22.04 LTS on Linode  
Domain: https://jttbh.com  
Repo: https://github.com/JasonRFrancis/JTTBH

---

## 1. Provision the Linode

1. Log in to [cloud.linode.com](https://cloud.linode.com) and create a new Linode.
2. Choose **Ubuntu 22.04 LTS** as the image.
3. Pick a region and plan (Nanode 1 GB is enough to start).
4. Set a strong root password and optionally add your SSH public key.
5. Note the server's public IP address.

---

## 2. Point DNS to the server

In your domain registrar (or Linode DNS manager), create:

| Type | Name        | Value            |
|------|-------------|------------------|
| A    | jttbh.com   | `<server IP>`    |
| A    | www.jttbh.com | `<server IP>` |

DNS propagation can take a few minutes to a few hours. You can verify with:

```bash
dig +short jttbh.com
```

---

## 3. Initial server hardening (as root)

SSH into the server:

```bash
ssh root@<server-ip>
```

Update packages and install essentials:

```bash
apt update && apt upgrade -y
apt install -y git nginx mysql-server python3 python3-venv python3-pip certbot python3-certbot-nginx ufw
```

Configure the firewall:

```bash
ufw allow OpenSSH
ufw allow "Nginx Full"
ufw --force enable
```

Create a dedicated application user:

```bash
useradd -m -s /bin/bash jttbh
# Allow the jttbh user to restart its own service without a password
echo "jttbh ALL=(ALL) NOPASSWD: /bin/systemctl restart jttbh, /bin/systemctl start jttbh, /bin/systemctl stop jttbh, /bin/systemctl reload nginx, /bin/systemctl restart nginx, /bin/systemctl is-active jttbh" \
  > /etc/sudoers.d/jttbh
chmod 440 /etc/sudoers.d/jttbh
```

---

## 4. MySQL database setup (as root)

Secure MySQL:

```bash
mysql_secure_installation
```

Create the database and application user:

```bash
mysql -u root -p <<'EOF'
CREATE DATABASE IF NOT EXISTS jttbh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'jttbh'@'localhost' IDENTIFIED BY 'CHANGE_ME_STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON jttbh.* TO 'jttbh'@'localhost';
FLUSH PRIVILEGES;
EOF
```

> Replace `CHANGE_ME_STRONG_PASSWORD` with a real password and save it — you will need it in `.env.prod`.

---

## 5. Clone the repository (as jttbh user)

```bash
su - jttbh
git clone https://github.com/JasonRFrancis/JTTBH.git ~/JTTBH
```

---

## 6. Configure the production environment

```bash
cd ~/JTTBH
cp .env.example .env.prod
nano .env.prod
```

Fill in every value in `.env.prod`:

```
FLASK_ENV=production

# Generate with: python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<generated-secret>

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=jttbh
MYSQL_PASSWORD=<db-password-from-step-4>
MYSQL_DB=jttbh

GOOGLE_CLIENT_ID=<from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<from-google-cloud-console>
GOOGLE_REDIRECT_URI=https://jttbh.com/auth/oauth2callback

OAUTHLIB_INSECURE_TRANSPORT=0

SMTP_HOST=<your-smtp-host>
SMTP_PORT=587
SMTP_USER=<your-smtp-user>
SMTP_PASSWORD=<your-smtp-password>
SMTP_FROM=<from-address>
ADMIN_EMAIL=<admin-address>
```

Restrict permissions on the secrets file:

```bash
chmod 600 .env.prod
```

---

## 7. Run the setup script (as jttbh user)

```bash
cd ~/JTTBH
chmod +x config/setup_production.sh
./config/setup_production.sh
```

This script:
- Creates the Python virtual environment and installs dependencies
- Copies `.env.prod` → `.env`
- Writes the systemd unit `/etc/systemd/system/jttbh.service` and enables it
- Sets file permissions so nginx (`www-data`) can serve static files
- Writes the Nginx config `/etc/nginx/sites-available/jttbh`, enables it, and removes the default site

---

## 8. Import the database schema

```bash
mysql -u jttbh -p jttbh < ~/JTTBH/schema.sql
```

---

## 9. Obtain the TLS certificate (Let's Encrypt)

DNS must be pointing to the server before running this step.

```bash
# Run as root (or with sudo)
sudo certbot --nginx -d jttbh.com -d www.jttbh.com
```

Certbot will:
- Issue a free certificate from Let's Encrypt
- Automatically update the Nginx config with the certificate paths
- Set up automatic renewal via a systemd timer or cron job

Verify auto-renewal works:

```bash
sudo certbot renew --dry-run
```

---

## 10. Start the application

```bash
sudo systemctl start jttbh
sudo systemctl reload nginx
```

Check that everything is running:

```bash
sudo systemctl status jttbh
sudo systemctl status nginx
```

Open https://jttbh.com in a browser to confirm.

---

## 11. Deploying updates

After the initial setup, pull and deploy new code with the deploy script:

```bash
# Run as the jttbh user from the project root
cd ~/JTTBH
./config/deploy.sh
```

This script:
1. Pulls the latest code from `origin main`
2. Updates Python dependencies
3. Activates `.env.prod`
4. Restarts the `jttbh` service and Nginx
5. Verifies the service came back up

---

## Quick reference

| Task | Command |
|------|---------|
| View app logs | `journalctl -u jttbh -f` |
| Restart app | `sudo systemctl restart jttbh` |
| Reload Nginx | `sudo systemctl reload nginx` |
| Check Nginx config | `sudo nginx -t` |
| Renew certificate | `sudo certbot renew` |
| Connect to MySQL | `mysql -u jttbh -p jttbh` |
| Run deploy | `cd ~/JTTBH && ./config/deploy.sh` |
