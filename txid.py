import toml
import web3
from web3 import Web3, HTTPProvider, WebsocketProvider

#b'72fdcf5b84a7767917c36efc7d0a0f26ca9db63969dda835d7a031f9add15751'
txid = b'0ff8df777a5790f592a0d3aab3226123fa2db6c0f91b9471dce02210ae6d4cb5'

secrets = toml.load("./secrets.toml")
privateKey = secrets["PRIVATEKEY"]
INFURA_KEY = secrets["INFURA_KEY"]                
INFURA_URL = "https://mainnet.infura.io/v3/" + INFURA_KEY
w3 = Web3(HTTPProvider(INFURA_URL))

#print ('\nhttps://etherscan.io/tx/{0}'.format(txid.hex()))

#tx = w3.eth.getTransaction(txid.hex())
#logging.info(f"tx {tx}")
#tx = w3.eth.getTransaction('0x5c504ed432cb51138bcf09aa5e8a410dd4a1e204ef84bfed1be16dfba1b22060')
tx = w3.eth.getTransaction('0x' + str(txid.decode("utf-8") ))
print (tx)

