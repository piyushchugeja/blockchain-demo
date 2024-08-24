import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 - Building a Blockchain

class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(self.proof_of_work(self.get_temp_block('0')))
        self.nodes = set()

    def create_block(self, block):
        self.chain.append(block)
        self.transactions = self.transactions[5:]  # Keep transactions to 5 per block
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hash(encoded_block)

    def proof_of_work(self, temp_block):
        new_proof = 1
        check_proof = False
        while not check_proof:
            temp_block['nonce'] = new_proof
            hash_operation = self.hash(temp_block)
            if hash_operation.startswith('000'):
                check_proof = True
            else:
                new_proof += 1
        return temp_block

    def create_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        return "Your transaction has been added to the pool."

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            if not self.hash(block).startswith('000'):
                return False
            previous_block = block
            block_index += 1
        return True

    def get_temp_block(self, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'nonce': 1,
                 'timestamp': str(datetime.datetime.now()),
                 'previous_hash': previous_hash,
                 'transactions': self.transactions[:5],
                 'merkle_root': get_merkle_root(self.transactions[:5])}
        return block

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# Helper function to hash
def hash(value):
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()

# Create Merkle tree root
def get_merkle_root(transactions):
    if len(transactions) == 0:
        return None

    if len(transactions) == 1:
        return hash(transactions[0])

    # hash all transactions before building the Merkle tree
    hashed_transactions = [hash(tx) for tx in transactions]

    while len(hashed_transactions) > 1:
        if len(hashed_transactions) % 2 != 0:
            hashed_transactions.append(hashed_transactions[-1])

        new_transactions = []
        for i in range(0, len(hashed_transactions), 2):
            combined = hashed_transactions[i] + hashed_transactions[i + 1]
            new_transactions.append(hash(combined))
        hashed_transactions = new_transactions

    return hashed_transactions[0]

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    if len(blockchain.transactions) > 0:
        previous_block = blockchain.get_previous_block()
        previous_hash = blockchain.hash(previous_block)
        temp_block = blockchain.proof_of_work(blockchain.get_temp_block(previous_hash))
        block = blockchain.create_block(temp_block)
        response = {'message': 'Congratulations, you just mined a block!',
                    'index': block['index'],
                    'timestamp': block['timestamp'],
                    'nonce': block['nonce'],
                    'previous_hash': block['previous_hash'],
                    'transactions': block['transactions']}
    else:
        response = {'message': 'No transactions to mine'}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    response = {'message': blockchain.create_transaction(json['sender'], json['receiver'], json['amount'])}
    return jsonify(response), 201

# Getting all transactions in the pool
@app.route('/get_transactions', methods=['GET'])
def get_transactions():
    response = {'transactions': blockchain.transactions}
    return jsonify(response), 200

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The Hadcoin Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Running the app
app.run(host='0.0.0.0', port=5000)