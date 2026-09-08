# QATailEnd

QATailEnd is an agent for [QAshboard](https://github.com/AOSC-Dev/QAshboard), running on build hosts to call Ciel and to report build results.

## Configuration

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

To run - `cd QTailEnd && python3 main.py`

## Requirements

Use root or a no-password-sudo user to run the agent, as Ciel needs elevated permissions.
