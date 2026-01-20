# Example Input Files

## sample_input.json

This file demonstrates the expected JSON schema for blog post input.

## Security Warning

**IMPORTANT: Never store real passwords in JSON files!**

The `sns_pw` field in `sample_input.json` is intentionally left empty.
For production use, provide passwords through one of these secure methods:

1. **Environment Variables (Recommended)**
   ```bash
   export NBLOG_PW_EXAMPLE_AT_NAVER_COM=your_password
   ```

2. **External Secrets File**
   ```bash
   nblog post input.json --all --secrets-file /path/to/secrets.json
   ```

   The secrets file should be:
   - Stored outside the repository
   - Added to `.gitignore`
   - Protected with appropriate file permissions (chmod 600)

3. **JSON Input (Not Recommended)**
   - Only use for testing with dummy accounts
   - Never commit real passwords to version control

## Environment Variable Naming

For an email like `user@naver.com`, the environment variable name is:
```
NBLOG_PW_USER_AT_NAVER_COM
```

The CLI `doctor` command will show you the exact environment variable names needed:
```bash
nblog doctor input.json
```
