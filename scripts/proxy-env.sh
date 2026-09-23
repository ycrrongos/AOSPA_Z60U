#!/usr/bin/env bash
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export no_proxy=localhost,127.0.0.1
export NO_PROXY=localhost,127.0.0.1

# Preserve real home for Cursor transcripts / credentials before overlaying HOME.
export AOSPA_CERRO_REAL_HOME="${AOSPA_CERRO_REAL_HOME:-${HOME}}"

# repo sync calls `git var GIT_COMMITTER_IDENT` and needs a user identity.
# Do not write ~/.gitconfig (AGENTS). Use an isolated HOME overlay instead.
_CERRO_GIT_HOME="${AOSPA_CERRO_GIT_HOME:-/tmp/aospa-cerro-git-home}"
mkdir -p "${_CERRO_GIT_HOME}"
if [[ ! -f "${_CERRO_GIT_HOME}/.gitconfig" ]]; then
  cat >"${_CERRO_GIT_HOME}/.gitconfig" <<'EOF'
[user]
	name = ycrrongos
	email = 124893015+ycrrongos@users.noreply.github.com
EOF
fi
if [[ -z "${AOSPA_CERRO_KEEP_HOME:-}" ]]; then
  export HOME="${_CERRO_GIT_HOME}"
  if [[ -f "${AOSPA_CERRO_REAL_HOME}/.git-credentials" ]]; then
    git config --file "${_CERRO_GIT_HOME}/.gitconfig" \
      credential.helper "store --file=${AOSPA_CERRO_REAL_HOME}/.git-credentials"
  fi
fi
