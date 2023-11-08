from flask import Flask, jsonify, request
from uuid import uuid4
from blockChain import *
import threading
import argparse

parser = argparse.ArgumentParser(description="输入一个节点所处的端口号")
parser.add_argument("port", type=int)
args = parser.parse_args()
#这就是我们的节点（矿机）
app = Flask(__name__)
#todo：将节点名字改成bitcoin规范
node_name = str(uuid4()).replace('-', '')


blockchain = BlockChain(node_name, urllib.parse.urlparse(f'http://0.0.0.0:{args.port}'), args.port)

# 要求当前节点检验并考虑接受一个链
@app.route('/chain/check', methods=['POST'])
def check_chain():
    jsonOBJ = request.get_json()
    chain = json.loads(jsonOBJ)
    changed = False
    if len(chain) > len(blockchain.chain) and blockchain.valid_chain(chain):
        blockchain.lock.acquire()
        # double check!!!
        if len(chain) > len(blockchain.chain) and blockchain.valid_chain(chain):
            blockchain.chain = chain
            changed = True
        blockchain.lock.release()
    if changed:
        return f"{blockchain.url.geturl()} accepts your chain!", 201
    else:
        return f"{blockchain.url.geturl()} refused your chain!", 403

@app.route('/chain/fetch', methods=['GET'])
#返回当前区块链，供别的节点下载
def fetch_chain():
    response={
        'chain':blockchain.chain,
        'length':len(blockchain.chain)
    }
    return jsonify(response), 200

#接受一个交易
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    jsonOBJ = request.get_json()

    required=['fr', 'to', 'amount']
    if not all (k in jsonOBJ for k in required):
        return 'Missing keys!', 400
    index = blockchain.newTransaction(jsonOBJ['fr'], jsonOBJ['to'], jsonOBJ['amount'])
    response ={'message': f'your transaction will be added to block {index}'}

    # 201表示成功创建资源
    return jsonify(response), 201

@app.route('/nodes/register', methods=['POST'])
def register():
    node = request.get_json()['node']
    print("try registering "+node)
    if node:
        blockchain.register_node(node)
        return "success!", 200
    else:
        return "give me a node location please.", 400

def miner_task():
    # 工作至死！！！
    blockchain.introduce()
    while True:
        blockchain.mine()

if __name__ == '__main__':
    blockchain.introduce()
    blockchain.check_all()
    miner = threading.Thread(target=miner_task)
    miner.start()
    app.run(host='0.0.0.0', port=args.port)


