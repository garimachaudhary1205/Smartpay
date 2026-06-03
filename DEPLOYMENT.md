# NexPay — Deployment Guide (Free Oracle Cloud VM)

Deploys the whole stack on **one free Oracle Cloud "Always Free" VM**:
the 6 Spring Boot services + Nginx serving the React build and proxying the API.

Because every service talks to the others over `localhost`, putting them all on
**one host** means those URLs keep working with **zero code changes**. Nginx
serves the frontend and reverse-proxies `/api` + `/auth` to the gateway, so the
browser is **same-origin** → **no CORS needed**, and `REACT_APP_API_URL` stays unset.

```
                     Internet
                        │  :80 / :443
                ┌───────▼────────┐
                │  Nginx          │  serves React build (/var/www/nexpay)
                │                 │  proxies /api,/auth → 127.0.0.1:8080
                └───────┬─────────┘
                  ┌──────▼───────┐
                  │ Gateway 8080 │  JWT auth
                  └──┬──┬──┬──┬──┘
            8081 user│  │  │  │8089 reward
          8082 txn ──┘  │  │  └── 8084 notify
                  8083 wallet
                   └── file-based H2 in /opt/nexpay/data/*.mv.db
```

> **Why Oracle Always Free:** its `VM.Standard.A1.Flex` ARM shape gives up to
> **4 cores / 24 GB RAM free forever, with no sleeping** — plenty for 6 Spring
> services. (AWS/Azure free tiers give ~1 GB, too small for all 6.)

---

## 0. Prerequisites

- An **Oracle Cloud** account (free signup; needs a card for identity, not charged).
- On your **local machine**: this repo, JDK 20+, Node 18+, and an SSH key.

---

## 1. Provision the VM

1. Oracle Console → **Compute → Instances → Create Instance**.
2. **Image & shape:** Ubuntu 22.04, shape **`VM.Standard.A1.Flex`** (Ampere/ARM).
   Set **2 OCPU / 12 GB** (well within the Always Free limit).
3. Add your **SSH public key**.
4. Create. Note the **public IP**.

### Open the ports (Oracle has TWO firewalls — both must allow traffic)
- **Cloud security list:** VCN → Subnet → Security List → add **Ingress** rules
  for **TCP 80** and **TCP 443** from `0.0.0.0/0`.
- **OS firewall** (Oracle Ubuntu ships locked-down iptables):
  ```bash
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
  sudo netfilter-persistent save
  ```
  Leave **8080–8089 closed** to the world — they're only reached via Nginx/localhost.

---

## 2. Install Java + Nginx on the VM

```bash
ssh ubuntu@<VM_IP>
sudo apt update
sudo apt install -y openjdk-21-jdk nginx
java -version          # confirm 21 (runs the release-20 jars fine)
```

---

## 3. Build the artifacts (on your local machine)

```bash
# from the repo root
bash deploy/build-all.sh          # → dist/*.jar  (6 service jars)

cd smartpay-frontend
npm install
npm run build                     # → build/   (REACT_APP_API_URL stays unset)
cd ..
```

---

## 4. Copy everything to the VM

```bash
ssh ubuntu@<VM_IP> 'sudo mkdir -p /opt/nexpay/data /var/www/nexpay && sudo chown -R ubuntu:ubuntu /opt/nexpay /var/www/nexpay'

# backend jars
scp dist/*.jar ubuntu@<VM_IP>:/opt/nexpay/

# env file + systemd units + nginx conf
scp deploy/nexpay.env.example ubuntu@<VM_IP>:/opt/nexpay/nexpay.env
scp deploy/systemd/*.service  ubuntu@<VM_IP>:/tmp/
scp deploy/nginx/nexpay.conf  ubuntu@<VM_IP>:/tmp/

# frontend build
scp -r smartpay-frontend/build/* ubuntu@<VM_IP>:/var/www/nexpay/
```

Then on the VM, set a real JWT secret:
```bash
sed -i "s|replace-with-a-long-random-secret-at-least-32-characters|$(openssl rand -base64 48)|" /opt/nexpay/nexpay.env
```

---

## 5. Install & start the services (systemd)

```bash
sudo mv /tmp/nexpay-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now \
  nexpay-user nexpay-wallet nexpay-reward nexpay-notification \
  nexpay-transaction nexpay-gateway

# check status / logs
systemctl status 'nexpay-*' --no-pager
journalctl -u nexpay-gateway -f      # follow a service's logs
```

Each service runs from `/opt/nexpay`, so their H2 files land in
`/opt/nexpay/data/*.mv.db` and **persist across restarts and reboots**.

---

## 6. Configure Nginx

```bash
sudo mv /tmp/nexpay.conf /etc/nginx/sites-available/nexpay
sudo ln -s /etc/nginx/sites-available/nexpay /etc/nginx/sites-enabled/nexpay
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Now visit **`http://<VM_IP>/`** — the NexPay UI loads, and signup/login/wallet/
send-money all work through the same origin.

---

## 7. (Optional) Domain + HTTPS

1. Point an A record for your domain at `<VM_IP>`.
2. Set `server_name your-domain.com;` in the Nginx conf.
3. ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```
   Free Let's Encrypt cert, auto-renew. Done.

---

## 8. Day-2 operations

| Task | Command |
|------|---------|
| Restart a service | `sudo systemctl restart nexpay-wallet` |
| Tail logs | `journalctl -u nexpay-gateway -f` |
| Back up data | `cp -r /opt/nexpay/data ~/nexpay-backup-$(date +%F)` |
| Redeploy a service | rebuild → `scp dist/<svc>.jar ...` → `sudo systemctl restart nexpay-<svc>` |
| Redeploy frontend | `npm run build` → `scp -r build/* ...:/var/www/nexpay/` |

---

## Alternative: frontend on Vercel instead of the VM
If you'd rather host the UI on Vercel (git-push deploys, CDN):
1. Import the `smartpay-frontend` repo on Vercel.
2. Set env var **`REACT_APP_API_URL = https://<your-vm-domain>`**.
3. The gateway already allows `*.vercel.app` via CORS (`application.yml`), so
   cross-origin calls work. (Add your custom domain to that allow-list too.)
   In this mode you don't serve the build from Nginx — but you still need the
   gateway reachable over HTTPS, so keep steps 1–7 for the backend.

---

## Notes & limits
- **H2 persists on the VM disk** — survives restarts/reboots. Back it up (table above).
  It does **not** auto-replicate; if you outgrow it, migrate to managed Postgres
  (Neon free tier), schema-per-service, ~no code changes.
- **Kafka is not deployed** — rewards/notifications were decoupled to REST, so the
  core app needs no broker. (The dormant Kafka code stays for future use.)
- **JWT secret** is read from `JWT_SECRET` (gateway + user-service). Keep it secret
  and identical for both; rotating it logs everyone out.
