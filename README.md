# hubchat

Github chat - a simple flask webapp that authenticates with github/oauth to enable DMs between github users.

## running

```bash
#!/usr/bin/env bash
export SECRET_KEY='key'
export GITHUB_CLIENT_ID='clientid'
export GITHUB_CLIENT_SECRET='clientsecret'
export MESSAGE_LIMIT='5'
flask run
```

## demo

[working demo](https://hubchat.adamthiede.com). No uptime guarantees.
