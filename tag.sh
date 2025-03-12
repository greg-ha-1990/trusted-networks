#!/bin/sh

TAG_NAME="$1"
COMMIT="$2"

check()
{
    [ "x${TAG_NAME}" != "x" ] || return 1
    [ "x${COMMIT}" != "x" ] || return 1
    git show "${COMMIT}" 1>/dev/null 2>&1 || return 1
    return 0
}

exec_tag()
{
    git ls-remote --tags 2>/dev/null | sed 's/^.*\///g' | grep -E "^${TAG_NAME}$" 1>/dev/null 2>&1 && {
        echo "${TAG_NAME} already exist"
        return 1
    }
    git tag "${TAG_NAME}" "${COMMIT}" -m "${TAG_NAME}" && git push origin "${TAG_NAME}" && git ls-remote --tags| grep "${TAG_NAME}" 1>/dev/null 2>&1 && echo "create tag ${TAG_NAME} succeed" && return 0
    echo "create tag ${TAG_NAME} base ${COMMIT} failed"
    return 1
}

check || {
    echo "./tag.sh TAG_NAME COMMIT"
    exit 1
}
exec_tag


