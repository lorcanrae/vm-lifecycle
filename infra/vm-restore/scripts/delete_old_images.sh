#!/usr/bin/env bash
set -e

PREFIX=$1

latest_image=$(gcloud compute images list \
  --filter="name ~ '^${PREFIX}-'" \
  --sort-by="~creationTimestamp" \
  --limit=1 \
  --format="value(name)")

echo "Preserving latest image: $latest_image"

gcloud compute images list \
  --filter="name ~ '^${PREFIX}-'" \
  --format="value(name)" |
grep -v "$latest_image" |
while read image; do
  echo "Deleting old image: $image"
  gcloud compute images delete "$image" --quiet
done
