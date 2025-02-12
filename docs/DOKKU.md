# Dokku Deploy

Dokku Deploy Notes

### Step 1 - SSH to your server and create the app with the config vars

```sh
# replace IP with your server's IP
ssh -i ~/path/to/your/key root@IP
```

```sh
# we are using tgvn as the app name
dokku apps:create tgvn
# set the config vars
dokku config:set tgvn TELEGRAM_BOT_TOKEN=
dokku config:set tgvn GROQ_API_KEY=
```

### Step 2 - Deploy the app

```sh
ssh-add ~/path/to/your/key
# replace IP with your server's IP
git remote add dokku dokku@IP:tgvn
git push dokku master
# Procfile runs the prod script
```
