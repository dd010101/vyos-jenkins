GIT mirror
--

If you want simple & light self-hosted mirror of this or any other GIT repository, then you may use something 
like these examples. I assume Debian and nginx as webserver, but you can easily translate the idea to whatever 
Linux or webserver you like.

These examples use cgit as web viewer and git-http-backend for read-only HTTP clone support.

**Install dependencies**

```
apt install nginx git cgit fcgiwrap
```

**Prepare GIT repositories and keep them up to date**

You want to use such script to first clone bare repositories and then periodically update them.

See and obtain the `extras/mirror/github-mirror.sh` script.

Example usage of `update-mirrors.sh`:

```bash
#!/usr/bin/env bash
set -e

githubMirror="/opt/vyos-jenkins/extras/mirror/github-mirror.sh"
export ROOT_PATH="/var/lib/git"

export NAMESPACE="vyos"
export GITHUB_KIND="org"
export GITHUB_SUBJECT="vyos"
$githubMirror

export NAMESPACE="dd010101"
export GITHUB_KIND="user"
export GITHUB_SUBJECT="dd010101"
$githubMirror
```

You may also mirror GIT repositories directly:

```bash
#!/usr/bin/env bash
set -e

destination="/var/lib/git/dd010101"
sources=(
    "https://github.com/dd010101/vyos-jenkins.git"
    "https://github.com/dd010101/vyos-build.git"
    "https://github.com/dd010101/vyos-missing.git"
)

if [ ! -f "$destination" ]; then
    mkdir -p "$destination"
fi

for gitUrl in "${sources[@]}"
do
    directory=$(echo "$gitUrl" | grep -oP '([^/]+).git')
    fullPath="$destination/$directory"
    if [ -d "$fullPath" ]; then
        echo "Updating $gitUrl in $fullPath"
        git -C "$fullPath" remote update
    else
        echo "Cloning $gitUrl as $fullPath"
        mkdir -p "$fullPath"
        git -C "$fullPath" clone --mirror "$gitUrl" .
    fi
done
```

Run the mirror script(s) first time to clone repositories:

```bash
adduser --system --group --disabled-password -d /var/lib/git git
chown -R git: /var/lib/git
su - git -s /bin/bash -c "/your/path/update-mirrors.sh"
```

To keep repositories up to date execute the script(s) periodically for example with CRON:

```
0 * * * * git /your/path/update-mirrors.sh
```

**cgit configuration**

Modify `/etc/cgitrc` and append following:

```
clone-prefix=https://git.some.tld

css=/cgit.css
logo=/cgit.png
root-title=My mirror
root-desc=Welcome to my mirror
max-repo-count=0

section-from-path=1
scan-path=/var/lib/git/repos

snapshots=tar.gz zip
virtual-root=/
```

Adjust the values as you wish. It's important to set the `clone-prefix` to your URL.

**nginx vhost**

Replace `git.some.tld` with your domain and also adjust HTTPS certificates as needed. You may as well use whatever
configuration you like and just pickup location blocks to make git side work with your favorite nginx vhost.

```
server {
    listen 80;
    listen [::]:80;

    server_name git.some.tld;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;

    ssl_certificate /etc/letsencrypt/live/git.some.tld/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/git.some.tld/privkey.pem;

    server_name git.some.tld;

    root /usr/share/cgit;

    location / {
        try_files $uri @cgit;
    }

    location @cgit {
        fastcgi_param SCRIPT_FILENAME /usr/lib/cgit/cgit.cgi;
        fastcgi_param PATH_INFO $uri;
        fastcgi_param QUERY_STRING $args;
        fastcgi_param HTTP_HOST $server_name;
        fastcgi_pass unix:/var/run/fcgiwrap.socket;
        include fastcgi_params;
    }

    location ~ /.+/(info/refs|git-upload-pack) {
        client_max_body_size 0;
        fastcgi_param SCRIPT_FILENAME /usr/lib/git-core/git-http-backend;
        fastcgi_param GIT_HTTP_EXPORT_ALL "";
        fastcgi_param GIT_PROJECT_ROOT /var/lib/git/repos;
        fastcgi_param PATH_INFO $uri;
        fastcgi_param LANGUAGE en_US.UTF-8;
        fastcgi_pass unix:/var/run/fcgiwrap.socket;
        include fastcgi_params;
    }
}
```

The `git-http-backend` will use your system language and will send messages in this language to whoever
interacts with it - like with git clone. English-speaking GIT server is more common and that's why I would
recommend using `en_US.UTF-8`. If you have other system locale then you can add `en_US.UTF-8` as secondary
via `dpkg-reconfigure locales` - pick your locale as default and `git-http-backend` can use english via `LANGUAGE`
variable.

This gives your `https://git.some.tld` for viewing 
and `git clone https://git.some.tld/namespace/repository.git` support.
The cgit web viewer shows URL for cloning for each repository in summary section.
