# Fix "password authentication failed for user postgres" (RDS + Secrets Manager)

This error means the value in **Secrets Manager** (`loan-engine/test/DATABASE_URL`) does not match the **RDS master password** for the `postgres` user.

## Option A: You know the correct RDS password

Update the secret with that password:

```powershell
cd c:\Users\omack\Intrepid\pythonFramework\cursor_loan_engine

.\deploy\aws\create-database-secret.ps1 -Region us-east-1 -Profile AWSAdministratorAccess-014148916722 -DBPassword "YourActualRdsPassword"
```

Use the **exact** password that works for the RDS instance (no extra spaces; if it contains `"` or `$`, use single quotes around it in PowerShell). The script adds `?sslmode=require` for RDS.

Then run init again:

```powershell
.\deploy\aws\init-database.ps1 -Region us-east-1 -Method ecs-task -Profile AWSAdministratorAccess-014148916722
```

## Option B: You don't know / don't remember the RDS password

1. **Reset the RDS master password**
   - AWS Console → **RDS** → **Databases** → select **loan-engine-test-db**
   - **Modify**
   - Under **Settings**, set **Master password** to a new password (e.g. a long random one; note it down)
   - Apply immediately and wait for the modification to finish

2. **Update the secret** with that new password:
   ```powershell
   .\deploy\aws\create-database-secret.ps1 -Region us-east-1 -Profile AWSAdministratorAccess-014148916722 -DBPassword "TheNewPasswordYouSet"
   ```

3. **Run init again:**
   ```powershell
   .\deploy\aws\init-database.ps1 -Region us-east-1 -Method ecs-task -Profile AWSAdministratorAccess-014148916722
   ```

## Optional: Force ECS to pick up the new secret

If the **running** app (not just the one-off init task) must use the new password, force a new deployment so new tasks pull the updated secret:

```powershell
aws ecs update-service --cluster loan-engine-test --service loan-engine-test --force-new-deployment --region us-east-1 --profile AWSAdministratorAccess-014148916722
```

The one-off init task always gets the latest secret when it starts, so after updating the secret you can run init-database without redeploying.
