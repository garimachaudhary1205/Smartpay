#!/usr/bin/env bash
#
# Build all NexPay backend services into runnable JARs under ./dist/.
# Run from the repo root:  bash deploy/build-all.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
SERVICES=(api-gateway user-service transaction-service wallet-service notification-service reward-service)

mkdir -p "$DIST"

for svc in "${SERVICES[@]}"; do
  echo "==> Building $svc"
  ( cd "$ROOT/$svc" && ./mvnw -q clean package -Dmaven.test.skip=true )
  # spring-boot repackages to target/<artifactId>-<version>.jar; rename to a
  # stable name so the systemd units don't depend on the version string.
  jar=$(ls "$ROOT/$svc"/target/${svc}-*.jar | head -1)
  cp "$jar" "$DIST/$svc.jar"
  echo "    -> dist/$svc.jar"
done

echo
echo "Done. JARs are in $DIST/"
echo "Copy them to the VM:  scp dist/*.jar ubuntu@<VM_IP>:/opt/nexpay/"
