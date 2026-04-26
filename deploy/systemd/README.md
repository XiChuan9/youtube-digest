# systemd Deployment

Example layout:

```text
/opt/youtube-digest-hermes/
  .venv/
  .env
  config.json
  artifacts/
  newsletters/
  logs/
```

Install:

```bash
cd /opt/youtube-digest-hermes
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
cp config.example.json config.json
mkdir -p artifacts newsletters logs
sudo cp deploy/systemd/youtube-digest.service /etc/systemd/system/
sudo cp deploy/systemd/youtube-digest.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now youtube-digest.timer
```

Run once manually:

```bash
sudo systemctl start youtube-digest.service
sudo journalctl -u youtube-digest.service -n 100 --no-pager
```
