# Commands that install docker andallow it to start on system boot
# based on https://docs.docker.com/engine/install/ubuntu/
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo service docker start
sudo service docker status

cd /opt/droids/4-A7
sudo cp deploy/bot/xwsbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable xwsbot.service

#========= extra block for github actions automation =========
# sudo touch /etc/sudoers.d/100_xwing
# echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/systemctl start xwsbot.service" | sudo EDITOR='tee -a' visudo -f /etc/sudoers.d/100_xwing
# echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop xwsbot.service" | sudo EDITOR='tee -a' visudo -f /etc/sudoers.d/100_xwing
# echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart xwsbot.service" | sudo EDITOR='tee -a' visudo -f /etc/sudoers.d/100_xwing

# cat > 51.xwsbot.rules<< EOF
# polkit.addRule(function(action, subject) {
#   if (action.id == "org.freedesktop.systemd1.manage-units" &&
#       (action.lookup("unit") == "xwsbot.service") &&
#       subject.user == "$(whoami)") {
#     return polkit.Result.YES;
#   }
# });
# EOF
# sudo mv 51.xwsbot.rules /etc/polkit-1/rules.d/51.xwsbot.rules
# sudo systemctl restart polkit.service

#========= extra block for github actions automation (maintenance version) =========
# sudo touch /etc/sudoers.d/101_xwing
# echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/systemctl start xwsbot.maintenance.service" | sudo EDITOR='tee -a' visudo -f /etc/sudoers.d/101_xwing
# echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop xwsbot.maintenance.service" | sudo EDITOR='tee -a' visudo -f /etc/sudoers.d/101_xwing
# echo "$(whoami) ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart xwsbot.maintenance.service" | sudo EDITOR='tee -a' visudo -f /etc/sudoers.d/101_xwing


# sudo cat > 51.xwsbot.maintenance.rules<< EOF
# polkit.addRule(function(action, subject) {
#   if (action.id == "org.freedesktop.systemd1.manage-units" &&
#       (action.lookup("unit") == "xwsbot.maintenance.service") &&
#       subject.user == "$(whoami)") {
#     return polkit.Result.YES;
#   }
# });
# EOF
# sudo mv 51.xwsbot.maintenance.rules /etc/polkit-1/rules.d/51.xwsbot.maintenance.rules
# sudo systemctl restart polkit.service