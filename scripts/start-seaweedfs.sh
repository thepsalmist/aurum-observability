#!/bin/sh
set -eu

SEAWEEDFS_S3_CONFIG="${SEAWEEDFS_S3_CONFIG:-/tmp/seaweedfs-s3.json}"
SEAWEEDFS_HOST="${SEAWEEDFS_HOST:-seaweedfs}"

cat > "$SEAWEEDFS_S3_CONFIG" <<EOF
{
  "identities": [
    {
      "name": "local-publisher",
      "credentials": [
        {
          "accessKey": "${SEAWEEDFS_S3_ACCESS_KEY}",
          "secretKey": "${SEAWEEDFS_S3_SECRET_KEY}"
        }
      ],
      "actions": ["Admin", "Read", "Write", "List", "Tagging"]
    }
  ]
}
EOF

exec weed server \
  -s3 \
  -s3.config="$SEAWEEDFS_S3_CONFIG" \
  -ip="$SEAWEEDFS_HOST" \
  -dir=/data \
  -master.port=9333 \
  -volume.port=8080 \
  -filer.port=8888 \
  -s3.port=8333
