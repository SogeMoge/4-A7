#!/bin/bash

up() {
    podman-compose -f docker-compose.maintenance.yml pull
    podman-compose -f docker-compose.maintenance.yml up -d
}

down() {
    podman-compose -f docker-compose.maintenance.yml down
}

case $1 in
    up|down) "$1" ;;
esac

exit 0
