# install of unibot

install python3, see https://docs.python-guide.org/starting/install3/osx/

install pip3, see https://stackoverflow.com/questions/34573159/how-to-install-pip3-on-my-mac

```
mkdir trading && cd trading
git clone https://github.com/defiprophetsdev/speedy
git clone https://github.com/defiprophetsdev/ethwrap
cd ethwrap && pip3 install .
cd speedy
```

edit secrets.toml

```
touch secrets.toml
and put in the file
PRIVATEKEY = "ff..."
INFURA_KEY = "06..."
```

install packages
```
pip3 install requirements.txt
```

try running basic trader
```
python3 trader.py
```

