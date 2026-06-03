# NexPay — Deployment on Google Cloud (free $300 credit)

Same architecture and on-VM steps as `DEPLOYMENT.md` — only **VM creation +
firewall** differ (and they're simpler than Oracle). Use this file for those two
steps, then follow `DEPLOYMENT.md` §2–8 for everything else (Java, jars,
systemd, Nginx, HTTPS).

> Use the **$300 free-trial credit** on an **e2-medium (4 GB)** VM — NOT the
> always-free e2-micro (1 GB), which is too small for 6 Spring services.

---

## 1. Activate the free trial
Console → **Start my free trial** → grants **$300 / 90 days** (card for identity,
not charged). An e2-medium costs ~$24/mo, so the credit lasts ~12 months.

## 2. Create the VM

**Compute Engine → VM instances → Create instance**

| Field | Value |
|-------|-------|
| Name | `nexpay` |
| Region | `asia-south1` (Mumbai) — pick one near you |
| Machine type | **e2-medium** (2 vCPU, 4 GB). (e2-small / 2 GB also works) |
| Boot disk | **Ubuntu 22.04 LTS**, ~25 GB standard |
| Firewall | ✅ **Allow HTTP traffic** + ✅ **Allow HTTPS traffic** |

### SSH key
Expand **Advanced options → Security → Manage Access → Add manually generated SSH key**,
and paste your public key (the `ssh-ed25519 …` line, also at `~/Desktop/nexpay-ssh-key.pub`).

> GCP derives the Linux username from the key comment. Our key comment is
> `nexpay-oracle-20260530`, so the login user will be **`nexpay-oracle-20260530`**,
> not `ubuntu`. Two options:
> - Easiest: before pasting, change the comment to `ubuntu` so the user is `ubuntu`
>   (matches the systemd units). Re-export the key with:
>   `ssh-keygen -y -f ~/.ssh/id_ed25519 | sed 's/$/ ubuntu/'`
> - Or keep it and set `User=<that-name>` in the systemd units (sed replace `ubuntu`).

Click **Create**. The VM gets an **External IP** immediately (no capacity waits).

## 3. Firewall
Ticking *Allow HTTP/HTTPS* during creation opens **80/443** — done. Ports
8080–8089 stay closed to the internet (reached only via Nginx/localhost), exactly
as intended. No OS-level iptables editing needed (unlike Oracle).

## 4. Connect
```bash
ssh ubuntu@<EXTERNAL_IP>          # or ssh <key-comment-user>@<EXTERNAL_IP>
```
(or use the **SSH** button in the console for a browser terminal)

---

## 5. Everything else → follow `DEPLOYMENT.md`
From here it's identical:
- §2 install `openjdk-21-jdk` + `nginx`
- §3 build jars locally (already done → `dist/*.jar`) + `npm run build`
- §4 `scp` jars + configs + frontend up
- §5 systemd units → `systemctl enable --now`
- §6 Nginx conf → reload → visit `http://<EXTERNAL_IP>/`
- §7 optional domain + HTTPS (certbot)
- §8 day-2 ops

## Cost watch
- e2-medium ≈ $24/mo, covered by the $300 credit (~12 months).
- To stretch it: use **e2-small** (2 GB, ~$12/mo) — still runs all 6 with
  modest heap caps (`JAVA_TOOL_OPTIONS=-Xmx320m` in `nexpay.env`).
- After the credit, either downsize to the always-free e2-micro (needs trimming)
  or move to managed Postgres + a small paid VM. For a demo, 90 days+ is plenty.
