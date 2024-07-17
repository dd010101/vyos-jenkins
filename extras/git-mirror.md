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

# uncomment if you want use automated backup, see the github-mirror-backup.sh for configuration
#/opt/vyos-jenkins/extras/mirror/github-mirror-backup.sh
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

snapshots=tar.gz zip
section-from-path=1
scan-path=/var/lib/git/repos

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

**Duply backups for github-mirror.sh**

Install additional dependencies:

```bash
apt install duply
```

You may need additional dependencies depending on the duplicity backend you want to use.

Create duply profile:

- Don't forget to update `TARGET` to your specific duplicity backend.
- Check `SOURCE` to match `ROOT_PATH` of github-mirror.sh.
- You may want to tune the `MAX_FULL_BACKUPS` and `MAX_FULLBKP_AGE`:
  - `duply github-mirror backup` will create new full after `MAX_FULLBKP_AGE` time period.
  - `duply github-mirror purgeFull --force` will automatically delete full backup (and its chain of increments)
    if number of full backups (chains) has reached `MAX_FULL_BACKUPS` value.
  - Thus, with `MAX_FULL_BACKUPS=3` and `MAX_FULLBKP_AGE=1M` duplicity will create increments until month elapses.
    Then it creates new full backup/chain and continues with increments. 
    If we have meet 4th month then oldest full backup/chain is removed.
    This will yield 2 full months of increments and partial third month with 1 to 30 days depending on the cycle,
    this results in rolling 60-90 days of coverage.

```bash
mkdir -p /etc/duply/github-mirror

cat << 'EOF' > /etc/duply/github-mirror/conf
# gpg encryption settings, simple settings:
#  GPG_KEY='disabled' - disables encryption alltogether
#  GPG_KEY='<key1>[,<key2>]'; GPG_PW='pass' - encrypt with keys,
#   sign if secret key of key1 is available use GPG_PW for sign & decrypt
#  Note: you can specify keys via all methods described in gpg manpage,
#        section "How to specify a user ID", escape commas (,) via backslash (\)
#        e.g. 'Mueller, Horst', 'Bernd' -> 'Mueller\, Horst, Bernd'
#        as they are used to separate the entries
#  GPG_PW='passphrase' - symmetric encryption using passphrase only
GPG_KEY='disabled'
GPG_PW='_GPG_PASSWORD_'

# backend, credentials & location of the backup target (URL-Format)
# generic syntax is
#   scheme://[user[:password]@]host[:port]/[/]path
# e.g.
#   sftp://bob:secret@backupserver.com//home/bob/dupbkp
# for details and available backends see duplicity manpage, section URL Format
#   http://duplicity.us/vers8/duplicity.1.html#url-format
# BE AWARE:
#   some backends (cloudfiles, S3 etc.) need additional env vars to be set to
#   work properly, read after the TARGET definition for more details.
# ATTENTION:
#   characters other than A-Za-z0-9.-_.~ in the URL have to be
#   replaced by their url encoded pendants, see
#     http://en.wikipedia.org/wiki/Url_encoding
#   if you define the credentials as TARGET_USER, TARGET_PASS below $ME
#   will try to url_encode them for you if the need arises.
TARGET=''
#TARGET_PASS=''

# base directory to backup
SOURCE='/opt/github-mirror'

# Number of full backups to keep. Used for the "purgeFull" command. 
# See duplicity man page, action "remove-all-but-n-full".
MAX_FULL_BACKUPS=3

# activates duplicity --full-if-older-than option (since duplicity v0.4.4.RC3) 
# forces a full backup if last full backup reaches a specified age, for the 
# format of MAX_FULLBKP_AGE see duplicity man page, chapter TIME_FORMATS
# Uncomment the following two lines to enable this setting.
MAX_FULLBKP_AGE=1M
DUPL_PARAMS="$DUPL_PARAMS --full-if-older-than $MAX_FULLBKP_AGE "

# sets duplicity --volsize option (available since v0.4.3.RC7)
# set the size of backup chunks to VOLSIZE MB instead of the default 25MB.
# VOLSIZE must be number of MB's to set the volume size to.
# Uncomment the following two lines to enable this setting. 
VOLSIZE=50
DUPL_PARAMS="$DUPL_PARAMS --volsize $VOLSIZE "

# more duplicity command line options can be added in the following way
# don't forget to leave a separating space char at the end
DUPL_PARAMS="$DUPL_PARAMS --progress "
EOF

cat << 'EOF' > /etc/duply/github-mirror/exclude
# although called exclude, this file is actually a globbing file list
# duplicity accepts some globbing patterns, even including ones here
# here is an example, this incl. only 'dir/bar' except it's subfolder 'foo'
# - dir/bar/foo
# + dir/bar
# - **
# for more details see duplicity manpage, section File Selection
# http://duplicity.nongnu.org/duplicity.1.html#sect9

EOF
```

Useful links:

- Basic usage: https://duply.net/Documentation
- Full configuration example: https://salsa.debian.org/joowie-guest/maintain_duply/-/blob/debian/2.4.1-1/duply?ref_type=tags#L853
  - Can also be created by running `duply NAME create`

Restore:

- List what backups we have:
  - `duply github-mirror status`
- We can restore the whole deal:
  - Latest: `duply github-mirror restore /some/destination`
  - Specific: `duply github-mirror restore /some/destination 2024-07-17T10:00:00+02:00`
- Or just part:
  - The path is relative to the `SOURCE`.
    - We can also list what is in the backup to see the path:
      - Latest: `duply github-mirror list`
      - Specific: `duply github-mirror list 2024-07-17T10:00:00+02:00`
  - Latest: `duply github-mirror fetch repos/vyos/vyos-1x.git /some/destination`
  - Specific: `duply github-mirror fetch repos/vyos/vyos-1x.git 2024-07-17T10:00:00+02:00`
