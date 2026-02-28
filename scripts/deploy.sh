#!/bin/bash
# Deploy AAIA to LXC container

set -e

CONTAINER_ID=$1
BRANCH=${2:-main}

if [ -z "$CONTAINER_ID" ]; then
    echo "Usage: $0 <container-id> [branch]"
    exit 1
fi

echo "Deploying AAIA to container $CONTAINER_ID from branch $BRANCH..."

# Clone template (assuming you have template 100)
pct clone 100 $CONTAINER_ID
pct start $CONTAINER_ID

# Deploy from GitHub
pct exec $CONTAINER_ID -- bash -c "
cd /opt/aaia
git fetch origin
git checkout $BRANCH
nix build .#aaia
cp -r result/* /opt/aaia-deploy/
systemctl restart aaia 2>/dev/null || echo 'Service not found, starting manually'
/opt/aaia-deploy/bin/aaia &
"

echo "AAIA deployed to container $CONTAINER_ID"