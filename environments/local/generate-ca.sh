#!/usr/bin/env bash
# Generates the throwaway local-development root CA for the a2a-langgraph stack.
#
# Scope: the ROOT CA only (a self-signed cert with CA:TRUE). Leaf/server certs for
# dex, agentgateway, etc. are signed later, once deploy/compose.yaml defines the
# service hostnames that become their SANs.
#
# The CA private key (ca.key) is gitignored and must never be committed.
set -euo pipefail

CERT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CA_KEY="${CERT_DIR}/ca.key"
CA_CRT="${CERT_DIR}/ca.crt"

if [[ -f "${CA_KEY}" || -f "${CA_CRT}" ]]; then
  echo "CA already exists in ${CERT_DIR} (ca.key/ca.crt) — refusing to overwrite." >&2
  echo "Delete them first if you intend to regenerate the root." >&2
  exit 1
fi

openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes \
  -keyout "${CA_KEY}" -out "${CA_CRT}" -days 3650 \
  -subj "/O=a2a-langgraph/CN=a2a-langgraph Local Dev CA" \
  -addext "basicConstraints=critical,CA:TRUE,pathlen:0" \
  -addext "keyUsage=critical,keyCertSign,cRLSign"

chmod 600 "${CA_KEY}"

echo "Root CA written to ${CERT_DIR}:"
echo "  ca.crt  (public root cert — committed)"
echo "  ca.key  (private key — gitignored, do not commit)"
