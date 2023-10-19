# Commands that allow podman to start on system boot, works on podman-compose 1.0.4 on devel branch
# based on https://github.com/containers/podman-compose/issues/587#issuecomment-1630449218
USER=$(whoami)
# get podman-compose devel (in a virtuel env)
sudo apt install python3-virtualenv
python3 -m virtualenv ~/compose_venv
source ~/compose_venv/bin/activate
pip3 install https://github.com/containers/podman-compose/archive/devel.tar.gz
# run the venv compose as sudo
sudo ~/compose_venv/bin/podman-compose systemd -a create-unit
# no-sudo register the project (still with activated venv)
cd /opt/4-A7/deploy/
podman-compose -f docker-compose.yml systemd -a register
systemctl --user enable --now 'podman-compose@xwsbot'
sudo loginctl enable-linger $USER # start if uses is not logged in manually