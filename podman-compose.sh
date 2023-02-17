#!/bin/bash

up() {
    podman-compose pull
    podman-compose up -d
}

down() {
    podman-compose down
}

case $1 in
    up|down) "$1" ;;
esac

exit 0
