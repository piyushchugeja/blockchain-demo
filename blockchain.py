import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests

# Part 1 - Building a Blockchain

class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(self.proof_of_work(self.get_temp_block('0')))

    def create_block(self, block):
        self.chain.append(block)
        self.transactions = self.transactions[5:]
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hash(encoded_block)

    def proof_of_work(self, temp_block):
        new_proof = 1
        check_proof = False
        while check_proof is False:
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
        previous_block = self.get_previous_block()
        return "Your transaction has been added to pool."

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                print(block['previous_hash'])
                print(self.hash(previous_block))
                return False
            if not self.hash(block).startswith('000'):
                print(self.hash(block))
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
    
# Create merkle tree
def get_merkle_root(transactions):
    if len(transactions) == 0:
        return None

    if len(transactions) == 1:
        return hash(transactions[0])

    # hash all transactions before building merkle tree
    hashed_transactions = []
    for i in range(len(transactions)):
        hashed_transactions.append(hash(transactions[i]))

    # build merkle tree
    level = 0
    while len(hashed_transactions) > 1:
        if len(hashed_transactions) % 2 != 0:
            hashed_transactions.append(hashed_transactions[-1])

        new_transactions = []
        for i in range(0, len(hashed_transactions), 2):
            combined = hashed_transactions[i] + hashed_transactions[i+1]
            hash_combined = hash(combined)
            new_transactions.append(hash_combined)
        hashed_transactions = new_transactions
        level += 1

    # return the root of the merkle tree
    return hashed_transactions[0]

# Helper function to hash
def hash(value):
    return hashlib.sha256(str(value).encode('utf-8')).hexdigest()

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating a Blockchain
b = Blockchain()

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    # Mining a new block    
    if len(b.transactions) > 0:
        previous_block = b.get_previous_block()
        previous_hash = b.hash(previous_block)
        temp_block = b.proof_of_work(b.get_temp_block(previous_hash))
        block = b.create_block(temp_block)
        response = {'message': 'Congratulations, you just mined a block!',
                    'index': block['index'],
                    'timestamp': block['timestamp'],
                    'nonce': block['nonce'],
                    'previous_hash': block['previous_hash']}
    else:
        response = {'message': 'No transactions to mine'}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': b.chain,
                'length': len(b.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = b.is_chain_valid(b.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    # Method to create transaction in the b
    json = request.get_json()
    sender = json['sender']
    receiver = json['receiver']
    amount = json['amount']
    response = {'message': b.create_transaction(sender, receiver, amount)}
    return jsonify(response), 201

@app.route('/get_transactions', methods = ['GET'])
def get_transactions():
    response = {'transactions': b.transactions}
    return jsonify(response), 200

# Running the app
app.run(host = '0.0.0.0', port = 5000)