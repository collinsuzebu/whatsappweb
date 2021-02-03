#!/bin/sh
echo 'Setting up docker-host-ip'
export DOCKER_HOST_IP=$(docker network inspect --format='{{range .IPAM.Config}}{{.Gateway}}{{end}}' selenium | awk -F "/" 'NR==1{print $1}')
echo '   docker-host-ip='${DOCKER_HOST_IP}

echo 'Running docker-compose'
docker-compose -f docker-compose.yml up
