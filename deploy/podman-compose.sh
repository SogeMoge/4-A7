#!/bin/bash

up() {
    podman-compose pull
    podman-compose -f docker-compose.yml up -d
}

down() {
    podman-compose -f docker-compose.yml down
}

case $1 in
    up|down) "$1" ;;
esac

exit 0
