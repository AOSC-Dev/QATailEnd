# QATailEnd

## Quick preview

1. Find [QAshboard](https://github.com/AOSC-Dev/QAshboard) Service
2. rewrite [application.yaml](qate/config/application.yaml) file

```yaml
remote:
  # QAshboard Service URL
  qa: http://localhost:8000/
  # Self Id
  buildbot: buildbot-111
  # Use QAshboard Service Generate token
  token: 
ciel:
  # ciel work directory
  path: /ciel
  # ciel instance name
  instance: build-env
```

3. run `cd qate; python3 main.py`

## Require

1. Use ROOT User (`ciel` need) or "sudo" NOPASSWD
2. Keep the running user and the ciel/TREE directory permissions the same.

```shell
# It will automatically update the ABBS repository/checkout to the latest stable branch, which requires write permissions.
git fetch origin
git reset --hard origin/stable
```