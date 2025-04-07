#!/bin/bash

up() {
    podman-compose -f stack.yml pull
    podman-compose -f stack.yml up -d
}

down() {
    podman-compose -f stack.yml down
}

case $1 in
    up|down) "$1" ;;
esac

exit 0
