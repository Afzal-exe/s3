# 🧹 Cleanup · Delete Everything (Stay at ₹0)

⏱️ **15 minutes** · 🎯 **Goal:** Remove every resource you created today, so your account never gets billed.

[🏠 Home](../README.md) · [← Capstone](../capstone-live-portfolio-gallery/README.md)

> [!CAUTION]
> Resources keep running (and can keep **costing money**) until you delete them. Closing the browser tab does **not** stop anything. Work through this list **in order**.

> [!TIP]
> Want to keep your portfolio? Take screenshots and a screen recording first. The code is safe on GitHub, and you can redeploy it in 10 minutes any time using Lab 2.

Check that the region is **Mumbai** before you start.

---

## 1 · EC2: terminate instances

**EC2 → Instances** → select **every** instance (`portfolio-server`, plus `web-server`/`web-client` if they're still there) → **Instance state → Terminate (delete) instance → Terminate**.

✅ Wait until they all show **Terminated**. They disappear from the list after about an hour.

## 2 · EC2: delete security groups and the key pair

1. **EC2 → Security Groups** → select `lab1-internal-sg` and `web-public-sg` → **Actions → Delete security groups**. (Leave the one named `default`: it can't be deleted.)
2. **EC2 → Key Pairs** → select `reva-lab-key` → **Actions → Delete**. Also delete the `.pem` file from your PC's Downloads folder.

> If a security group won't delete, an instance is still shutting down. Wait a minute and try again.

## 3 · VPC: delete your network

**VPC → Your VPCs** → select `reva-lab-vpc` → **Actions → Delete VPC** → type `delete` → **Delete**.

This also deletes its subnet, route table and internet gateway.

## 4 · S3: empty and delete all three buckets

A bucket must be **empty** before it can be deleted. For **each** bucket (`-cloud-drive`, `-assignments`, `-image-gallery`):

1. **S3 → Buckets** → select the bucket → **Empty** → type `permanently delete` → **Empty**. (For the versioned assignments bucket, this removes **all versions and delete markers** too.)
2. Select the bucket again → **Delete** → type the bucket name → **Delete bucket**.

<details>
<summary>🚀 Power-up: delete all three from CloudShell</summary>

```bash
for b in cloud-drive image-gallery; do
  aws s3 rb s3://$ID-$b --force          # empties and deletes
done

# The versioned bucket needs every version removed first:
aws s3api delete-objects --bucket $ID-assignments \
  --delete "$(aws s3api list-object-versions --bucket $ID-assignments \
  --query '{Objects: [Versions, DeleteMarkers][].{Key: Key, VersionId: VersionId}}' --output json)"
aws s3 rb s3://$ID-assignments

aws s3 ls     # should list none of today's buckets
```
</details>

## 5 · IAM: delete the role and policy

1. **IAM → Roles** → select `portfolio-gallery-role` → **Delete** → type the role name → **Delete**.
2. **IAM → Policies** → filter **Customer managed** → select `gallery-read-only` → **Actions → Delete** → type the name → **Delete**.

## 6 · Keep your safety net

**Keep** the `zero-spend-alert` budget from Lab 0. It's free, and it will email you if anything ever starts costing money.

---

## ✅ Final checklist

| Resource | Where to check | Should show |
|---|---|---|
| EC2 instances | EC2 → Instances | All *Terminated* (or none) |
| Security groups | EC2 → Security Groups | Only `default` |
| Key pair | EC2 → Key Pairs | None |
| VPC | VPC → Your VPCs | Only the default VPC |
| S3 buckets | S3 → Buckets | None of today's 3 buckets |
| IAM role/policy | IAM → Roles / Policies | Gone |

📸 **Screenshot:** The empty S3 bucket list and the terminated instances, as proof for your report.

🎉 **Well done!** You built networks, servers, websites, secure storage, versioned archives and an automated gallery today, and then cleaned it all up like a professional.

---

[🏠 Home](../README.md)
