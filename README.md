#Install
```bash
sudo apt install python3-virtualenv libvirt-dev
git clone https://github.com/a13ssandr0/pydashboard.git
cd pydashboard
virtualenv .venv --copies
source .venv/bint/activate
pip install -r requirements.txt
```

#Run
```bash
source .venv/bin/activate
python pydashboard.py path/to/config.yml
```
