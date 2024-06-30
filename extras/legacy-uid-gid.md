UID / GID issue
--

Most of Jenkinfiles do respect your UID/GID but not all, for
example https://github.com/vyos/vyos-build/blob/equuleus/packages/linux-kernel/Jenkinsfile has hardcoded UID and GID to
1006 and this will fail build if you don't have 1006:1006 user.

That's why we want change Jenkins to 1006/1006:

Note: you need to end all processes of this user before changing UID. If you get message that some process is using
given user then end this process and repeat the process.

```
systemctl stop jenkins.service
usermod -u 1006 jenkins
groupmod -g 1006 jenkins
chown -R jenkins:jenkins /var/lib/jenkins/ /var/cache/jenkins/ /var/log/jenkins/
```
