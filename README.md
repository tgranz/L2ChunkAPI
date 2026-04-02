# L2ChunkAPI

**A simple API interface with AWS listener to return the latest chunk volume ID and key of each NEXRAD station.**

## Example
`http://localhost:500/latest?station=KABR`
```json
{
  "KABR": {
    "chunk_id": 55,
    "chunk_type": "E",
    "datetime": "2026-04-02T00:20:49",
    "key": "KABR/30/20260402-002049-055-E",
    "l2_version": "V06",
    "latest_volume_id": 30
  }
}
```

You can then call a fetch to the given key and use the chunk_id to fetch all chunks from this finished scan using the following naming scheme:

```text
KABR/30/20260402-002049-001-S
KABR/30/20260402-002049-002-I
KABR/30/20260402-002049-003-I
KABR/30/20260402-002049-...-I
KABR/30/20260402-002049-055-E
```

## Usage
1. Install Python
2. Run `python -m pip install json flask boto3`. (Everything else should come preinstalled)
3. You need an AWS console account. Get one [here](https://aws.amazon.com/console/). Head to the "IAM" page, go to "Users" > "Create User".
4. After adding the user, go to the user's page, find "Add Permissions" > "Attach Policies Directly" > search "admin" > select "AdministratorAccess".
5. Now go to the "Security Credentials" tab > "Create Access Key" > select "Command Line Interface (CLI)".
6. Once you can view your access key and secret access key, open your terminal and type:

`$env:AWS_ACCESS_KEY_ID="..."` <- set this to the value under "Access Key"

`$env:AWS_SECRET_ACCESS_KEY="..."` <- set this to the value under "Secret Access Key"

`$env:AWS_DEFAULT_REGION="us-east-1"`

7. AWS is now authenticated in your environment.
8. Create a `database.json` file and just add brackets: `{}`
9. You can now run `python main.py`.

## More info
https://github.com/awslabs/open-data-docs/tree/main/docs/noaa/noaa-nexrad

https://registry.opendata.aws/noaa-nexrad/