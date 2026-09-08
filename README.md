# QATailEnd

QATailEnd is an agent for [QAshboard](https://github.com/AOSC-Dev/QAshboard), running on build hosts to call Ciel and to report build results.

## Configuration

The configuration must be named `application.yaml` under the `qate` folder.

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

To run - `cd qate && python3 main.py`, or alternatively, install a systemd service as follows:

```
[Unit]
Description=QATailEnd Agent
After=network.target

[Service]
Type=simple
Restart=always
RestartSec=30
ExecStart=/usr/bin/python3 main.py
WorkingDirectory=/path/to/qatailend/qate

[Install]
WantedBy=multi-user.target
```

## Requirements

Use root or a no-password-sudo user to run the agent, as Ciel needs elevated permissions.
