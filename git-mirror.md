GIT mirror
--

If you want simple & light self-hosted mirror of this or any other GIT repository, then you may use something 
like these examples. I assume Debian and nginx as webserver, but you can easily translate the idea to whatever 
Linux or webserver you like.

This uses gitweb as viewer and git-http-backend for HTTP clone support. Both of these tools are part of git project.

**Install dependencies**

```
apt install nginx git gitweb fcgiwrap
```

**Prepare GIT repositories and keep them up to date**

You want to use such script to first clone bare repositories and then periodically update them.

The `/your/path/vyos-build-git-mirror.sh` script:

```
#!/bin/bash
set -e

destination="/var/lib/git"
sources=(
    "https://github.com/dd010101/vyos-jenkins.git"
    "https://github.com/dd010101/vyos-build.git"
    "https://github.com/dd010101/vyos-missing.git"
)

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

Run this first time to clone repositories:

```
chown -R www-data: /var/lib/git
su - www-data -s /bin/bash -c "/your/path/vyos-build-git-mirror.sh"
```

To keep repositories up to date execute this script periodically for example with CRON:

```
0 * * * * www-data /your/path/vyos-build-git-mirror.sh
```

**gitweb configuration**

We want to change `$projectroot` and also it's good idea to add `@git_base_url_list` so the gitweb shows
repository URL meant for cloning.

Modify `/etc/gitweb.conf`:

1) Update `$projectroot` to `/var/lib/git` (`$projectroot = "/var/lib/git"`) - if not already set.
2) Add `@git_base_url_list` with `https://git.some.tld` value (`@git_base_url_list = "https://git.some.tld"`).

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

    root /usr/share/gitweb;

    location = / {
        rewrite .* /index.cgi last;
    }

    location = /index.cgi {
        include fastcgi_params;
        fastcgi_param SCRIPT_NAME $uri;
        fastcgi_param GITWEB_CONFIG /etc/gitweb.conf;
        fastcgi_pass unix:/var/run/fcgiwrap.socket;
    }

    location ~ (^/.+) {
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME /usr/lib/git-core/git-http-backend;
        fastcgi_param GIT_HTTP_EXPORT_ALL "";
        fastcgi_param GIT_PROJECT_ROOT /var/lib/git;
        fastcgi_param PATH_INFO $1;
        fastcgi_param LANGUAGE en_US.UTF-8;
        fastcgi_pass unix:/var/run/fcgiwrap.socket;
    }
}
```

The `git-http-backend` will use your system language and will send messages in this language to whoever
interacts with it - like with git clone. English-speaking GIT server is more common and that's why I would
recommend using `en_US.UTF-8`. If you have other system locale then you can add `en_US.UTF-8` as secondary
via `dpkg-reconfigure locales` - pick your locale as default and `git-http-backend` can use english via `LANGUAGE`
variable.

This gives your `https://git.some.tld` for viewing and `git clone https://git.some.tld/repository.git` support.
The gitweb viewer shows URL for cloning for each repository in summary section.
