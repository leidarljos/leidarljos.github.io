#!/usr/bin/env bash
# Install the Emacs and the Lisp org/build.sh needs, pinned.
#
# org/export.el loads htmlize from elpa/htmlize-20250724.1703 and
# engrave-faces from a straight checkout, then publishes with whichever
# Org is first on load-path. The committed handbook matches GNU Emacs
# 29.3 with Org 9.8.10. Emacs 29.3's bundled Org 9.6.15 does not: it
# omits the <code> inside <pre class="src"> and writes &#x2013; where
# these pages use &ndash;. Emacs 30.2 bundles Org 9.7.11, which still
# has that older src-block markup. Org 9.8.10 is the GNU ELPA release
# that reproduces the pages.
set -euo pipefail

# Ubuntu 24.04 ships this Emacs as emacs / emacs-nox 1:29.3+1-1ubuntu2.
# The handbook rebuild was measured on that build.
emacs_version="29.3"
emacs_deb="1:29.3+1-1ubuntu2"

# MELPA snapshot named by org/export.el (elpa/htmlize-20250724.1703).
htmlize_url="https://melpa.org/packages/htmlize-20250724.1703.tar"
htmlize_sha="61823f836172d2454c886fd1457a1fb131ff4a674557adad5509b9c10c1fbd36"

# GNU ELPA 0.3.1. Handbook source blocks are console and janet, and
# neither has a major mode, so export returns plain text. The library
# still has to load. Pin the ELPA release so the require cannot float.
engrave_url="https://elpa.gnu.org/packages/engrave-faces-0.3.1.tar"
engrave_sha="cae1c75df6cc25515c39cceb9e9b12eb30f9be56bb851440c34da4104ce7855a"

# GNU ELPA Org 9.8.10 (needs Emacs 28.2). Measured on Emacs 29.3 against
# the committed handbook: aside from the export minute and the random
# headline ids, the rebuild is byte-identical.
org_url="https://elpa.gnu.org/packages/org-9.8.10.tar"
org_sha="890a9dd5c4f1d279f6ed0b3d10670d796aaccb7fdc71a2a665cd153bec463f1d"

cache="${XDG_CACHE_HOME:-${HOME}/.cache}/ljos-handbook-emacs"
emacsd="${cache}/emacsd"
mkdir -p "${cache}/tarballs" "${cache}/stamps" "${cache}/bin"

apt_install() {
  export DEBIAN_FRONTEND=noninteractive
  if [ "$(id -u)" -eq 0 ]; then
    apt-get update
    apt-get install -y --no-install-recommends "$@"
  else
    sudo apt-get update
    sudo apt-get install -y --no-install-recommends "$@"
  fi
}

got="$(emacs --batch --eval '(princ emacs-version)' 2>/dev/null || true)"
if [ "${got}" != "${emacs_version}" ]; then
  apt_install "emacs-nox=${emacs_deb}" ca-certificates curl
  got="$(emacs --batch --eval '(princ emacs-version)' 2>/dev/null || true)"
fi
if [ "${got}" != "${emacs_version}" ]; then
  printf 'wanted GNU Emacs %s, found %s\n' "${emacs_version}" "${got:-nothing}" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  apt_install ca-certificates curl
fi

fetch() {
  local url="$1" sha="$2" dest="$3"
  if [ ! -f "${dest}" ] || ! echo "${sha}  ${dest}" | sha256sum -c - >/dev/null 2>&1; then
    curl -fsSL -o "${dest}.partial" "${url}"
    mv "${dest}.partial" "${dest}"
    echo "${sha}  ${dest}" | sha256sum -c -
  fi
}

# Place a tarball's top directory at ${final}. Skip when the pin matches.
place() {
  local name="$1" sha="$2" tarfile="$3" parent="$4" top="$5" final="$6"
  local stamp="${cache}/stamps/${name}"
  if [ -d "${final}" ] && [ -f "${stamp}" ] && [ "$(cat "${stamp}")" = "${sha}" ]; then
    return 0
  fi
  rm -rf "${final:?}" "${parent:?}/${top:?}"
  mkdir -p "${parent}"
  tar -C "${parent}" -xf "${tarfile}"
  if [ "${parent:?}/${top:?}" != "${final:?}" ]; then
    rm -rf "${final:?}"
    mv "${parent:?}/${top:?}" "${final:?}"
  fi
  printf '%s\n' "${sha}" > "${stamp}"
}

fetch "${htmlize_url}" "${htmlize_sha}" "${cache}/tarballs/htmlize-20250724.1703.tar"
fetch "${engrave_url}" "${engrave_sha}" "${cache}/tarballs/engrave-faces-0.3.1.tar"
fetch "${org_url}" "${org_sha}" "${cache}/tarballs/org-9.8.10.tar"

place htmlize "${htmlize_sha}" "${cache}/tarballs/htmlize-20250724.1703.tar" \
  "${emacsd}/elpa" "htmlize-20250724.1703" "${emacsd}/elpa/htmlize-20250724.1703"
place engrave "${engrave_sha}" "${cache}/tarballs/engrave-faces-0.3.1.tar" \
  "${emacsd}/.local/straight/repos" "engrave-faces-0.3.1" \
  "${emacsd}/.local/straight/repos/engrave-faces"
place org "${org_sha}" "${cache}/tarballs/org-9.8.10.tar" \
  "${emacsd}" "org-9.8.10" "${emacsd}/org-9.8.10"

system_emacs="$(PATH="/usr/bin:/bin" command -v emacs)"
cat > "${cache}/bin/emacs" <<EOF
#!/bin/sh
# %a in org-html-metadata-timestamp-format follows LC_TIME.
# C keeps the English weekday the handbook diff recognises.
export LC_TIME=C
export EMACSDIR='${emacsd}'
export EMACSLOADPATH='${emacsd}/org-9.8.10:'
exec '${system_emacs}' "\$@"
EOF
chmod +x "${cache}/bin/emacs"

if [ -n "${GITHUB_PATH:-}" ]; then
  printf '%s\n' "${cache}/bin" >> "${GITHUB_PATH}"
fi

probe="$("${cache}/bin/emacs" --batch --eval '(progn (require '\''org) (princ (format "emacs %s org %s" emacs-version (org-version))))' 2>/dev/null || true)"
printf '%s\n' "${probe}"
case "${probe}" in
  "emacs ${emacs_version} org 9.8.10") ;;
  *)
    printf 'unexpected toolchain: %s\n' "${probe}" >&2
    exit 1
    ;;
esac
