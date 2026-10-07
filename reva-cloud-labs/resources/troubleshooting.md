# 🆘 Troubleshooting Guide

[🏠 Home](../README.md)

> [!TIP]
> **Rule #1:** check the **region** in the top-right corner. It must say **Mumbai**. Half of all "it disappeared!" problems are a wrong region.

---

## 🔐 Account and console

| Problem | Fix |
|---|---|
| "Your account is being verified" / can't launch EC2 | New accounts can take a little while to activate. Ask your facilitator, and pair up with a neighbour in the meantime. |
| Can't find a service | Type its name in the top search bar (`EC2`, `S3`, `VPC`, `IAM`). |
| Budget creation page looks different | Any **Zero spend** budget template is fine. The name doesn't matter. |
| `$ID` is empty in CloudShell | Run `echo 'export ID=your-lab-id' >> ~/.bashrc && source ~/.bashrc`, or type the full bucket name instead of `$ID`. |

## 🖥️ EC2 and connecting

| Problem | Fix |
|---|---|
| No *Free tier eligible* instance type | Pick whichever of `t3.micro` / `t2.micro` shows the Free tier label. |
| **EC2 Instance Connect** fails to connect | 1) Wait until **Status check = 2/2 passed**. 2) Username must be `ubuntu`. 3) The instance needs a **public IP** (Auto-assign public IP = Enable). 4) The security group must allow **SSH (22) from 0.0.0.0/0**. |
| Instance has no public IP | You forgot *Auto-assign public IP → Enable*. Easiest fix: terminate it and launch again with it enabled. |
| "Primary IP address is already in use" | That private IP is taken. Terminate the old instance or pick another IP such as `10.0.1.11`. |
| Terminal froze / disconnected | Close the tab and click **Connect** again. Your work on the server is still there. |
| Backup: connect with the key from your PC | In PowerShell: `ssh -i $HOME\Downloads\reva-lab-key.pem ubuntu@<public-ip>` |

## 🐧 Linux commands

| Problem | Fix |
|---|---|
| `Could not get lock /var/lib/dpkg/lock-frontend` | The VM is still installing updates from its first boot. Run `cloud-init status --wait`, then retry. |
| `sudo: unable to resolve host …` | Only a warning, and the command still ran. Fix: `echo "127.0.1.1 $(hostname)" \| sudo tee -a /etc/hosts` |
| `Permission denied` when editing `/var/www/html` | Run `sudo chown -R ubuntu:ubuntu /var/www/html` |
| Stuck inside `nano` | `Ctrl + X` to exit (press `Y` then `Enter` to save). |
| Stuck inside `w3m` | Press `q` then `y`. |
| Stuck in `ping` or `tail -f` | Press `Ctrl + C`. |
| Pasting doesn't work in the browser terminal | Use `Ctrl + Shift + V`, or right-click → Paste. |

## 🌐 Networking and websites

| Problem | Likely cause and fix |
|---|---|
| `ping` shows 100% packet loss (Lab 1) | No **All ICMP - IPv4** inbound rule from `10.0.0.0/16`. That's expected until Step 6. |
| Website **times out** in the browser | Security group has no **HTTP 80** rule for your source, **or** you used the **private** IP instead of the **public** IP. |
| Browser shows "connection is not secure" / can't connect | You typed `https://`. Use **`http://`**. |
| **Connection refused** | Apache isn't running: `sudo systemctl start apache2` |
| Still see the Apache default page | The old `index.html` is still there. Check `ls -l /var/www/html` and hard-refresh with `Ctrl + F5`. |
| Page has no styling (plain text) | `style.css` is missing from `/var/www/html`, or its name is misspelled. |
| `{{NAME}}` still visible | The `sed` command didn't run, or the variables were empty. Run the Lab 2 Step 7 block again. |
| Website's IP changed | You stopped and started the instance. Use the new public IP. |
| QR code looks scrambled | Zoom out (`Ctrl + -`) and run the command again. |

## 🪣 S3

| Problem | Fix |
|---|---|
| "Bucket with the same name already exists" | Names are global. Add a suffix: `r23bsc042-cloud-drive-1`. |
| Object URL shows **AccessDenied** | ✅ Expected! The bucket is private. Use **Open** or a **presigned URL**. |
| Presigned URL shows **Request has expired** | ✅ Expected after the expiry time. Create a new one. |
| Can't find a deleted file / "Show versions" missing | Versioning is only on in the **assignments** bucket (Lab 4). |
| File "came back" after deleting (Lab 4) | You deleted the **delete marker**. That restores the file, as designed. |
| Can't delete a bucket | It isn't empty. Use **Empty** first, then **Delete**. |
| ETag has a `-` in it (e.g. `…-3`) | The file was uploaded in parts (multipart). Compare the hashes of the original and the downloaded copy instead. |
| Can't add metadata | Choose **Type: User defined**. The key is just `title` (the console adds `x-amz-meta-`). |

## 🏆 Capstone gallery

| Error message | Fix |
|---|---|
| `boto3 is not installed` | `sudo apt install -y python3-boto3`. If that fails: `sudo apt install -y python3-pip && sudo pip3 install boto3 --break-system-packages` |
| `No AWS credentials found` | Attach the role: **EC2 → Actions → Security → Modify IAM role**. Wait about 10 seconds. |
| `AccessDenied listing …` | The policy's bucket name doesn't exactly match your bucket. Check **both** `Resource` lines, then edit the policy in IAM. |
| `Bucket … does not exist` | Typo in `--bucket`. Copy the exact name from the S3 console. |
| Gallery page is empty | Images must be in folders (`Nature/…`), with `.jpg/.jpeg/.png/.gif/.webp` extensions. `Family/` is hidden on purpose. |
| Titles don't show | The metadata keys must be exactly `title` and `description` (lowercase). |
| New photo doesn't appear | Check the cron file: `cat /etc/cron.d/gallery-sync`. Check the log: `sudo tail /var/log/gallery-sync.log`. Wait 2 minutes. |
| `git pull` says "not a git repository" | Run `cd ~/reva-cloud-labs` first. |

---

Still stuck? Raise your hand 🙋. Your facilitator is here to help.
