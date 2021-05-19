from web3 import Web3, IPCProvider
filter = w3.eth.filter('pending')
time.sleep(3)
hashes = filt.get_new_entries()
transactions = []
for hash in hashes:
    try:
        transac = w3.eth.getTransaction(hash)
        transactions.append(transac)
    except Exception as e:
        print(e)
print()
print(transactions)