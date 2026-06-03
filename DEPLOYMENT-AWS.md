# NexPay — Deployment on AWS EC2 ($100 credit)

Same app, same on-VM steps as `DEPLOYMENT.md` — only **launch the EC2 instance +
security group** differ. Do those here, then follow `DEPLOYMENT.md` §2–8 for
Java, jars, systemd, Nginx, HTTPS.

> Use a **t3.medium (4 GB)** funded by your **$100 credit** — NOT the free-tier
> t3.micro (1 GB), which is too small for 6 Spring services.

---

## 1. Import your SSH key (once)
EC2 → **Network & Security → Key Pairs → Actions → Import key pair**
- Name: `nexpay-key`
- Paste the contents of `~/.ssh/id_ed25519.pub` (also on your Desktop).
- Import. (Ubuntu AMIs log in as `ubuntu` regardless of the key comment.)

## 2. Launch the instance
EC2 → **Instances → Launch instances**

| Field | Value |
|-------|-------|
| Name | `nexpay` |
| AMI | **Ubuntu Server 22.04 LTS** (64-bit x86) |
| Instance type | **t3.medium** (2 vCPU, 4 GB) — paid via your $100 credit |
| Key pair | `nexpay-key` (the one you just imported) |
| Storage | bump root volume to **25 GB** gp3 |

### Network settings (click "Edit") — security group
Tick these "Allow ... from" boxes:
- ✅ **Allow SSH (22)** — from **My IP** (safer) or Anywhere
- ✅ **Allow HTTP (80)** — from Anywhere
- ✅ **Allow HTTPS (443)** — from Anywhere

Leave **8080–8089 closed** — they're reached only via Nginx/localhost on the box.

**Launch instance.** It gets a **Public IPv4 address** in ~30s. No capacity waits.

## 3. Connect
```bash
ssh ubuntu@<PUBLIC_IPv4>
```
(uses your `~/.ssh/id_ed25519` automatically)

> If you see "permissions too open" for the key:
> `chmod 600 ~/.ssh/id_ed25519`

---

## 4. Everything else → follow `DEPLOYMENT.md` §2–8
Identical from here:
- §2 `sudo apt update && sudo apt install -y openjdk-21-jdk nginx`
- §3 jars already built (`dist/*.jar`) + `npm run build`
- §4 `scp` jars + configs + frontend up
- §5 systemd units → `sudo systemctl enable --now nexpay-*`
- §6 Nginx conf → reload → visit `http://<PUBLIC_IPv4>/`
- §7 optional domain + HTTPS (certbot)
- §8 day-2 ops

## Cost vs credit
- t3.medium ≈ **$30/mo** → $100 credit ≈ **3 months** free. Plenty for a demo.
- Stretch it: use **t3.small (2 GB)** ≈ $15/mo (~6 months) and add
  `JAVA_TOOL_OPTIONS=-Xmx320m` to `/opt/nexpay/nexpay.env` so 6 JVMs fit 2 GB.
- **Stop the instance** when not demoing to pause billing (EC2 → Instance state → Stop;
  the disk persists, you only pay a few cents/mo for storage).
