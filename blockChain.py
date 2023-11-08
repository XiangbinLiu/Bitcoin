# 实现区块和链。
# 可以向区块中添加进节点的交易池，节点可以把交易封装进区块并广播。

import hashlib
import json
import threading
import urllib.parse
from time import time

import requests

# 为了方便序列化，这两个类改用字典实现了，其类中的方法转移到了BlockChain类中

# class Transaction:
#     def __init__(self, fr, to, amount):
#         self.fr = fr
#         self.to = to
#         self.amount = amount
#
# class Block:
#
#         # todo：引入默克尔树
#     def __init__(self, index, transactions, proof, parentHash):
#         self.index = index
#         self.time = int(time())
#         self.transactions = transactions
#         self.proof = proof
#         self.parentHash = parentHash
#
#     def to_dict(self):
#         res = self.__dict__
#         if  len(res['transactions']) > 0:
#             list = Block.list_transform(res['transactions'])
#             t = res.copy()
#             t['transactions'] = list
#             return t
#         return res
#
#         # todo：修改为返回区块头的hash值
#         #序列化成json、转字节、哈希、转十六进制字符串
#         #排序的原因是json对象的属性顺序是不确定的
#

#
#     @staticmethod
#     def list_transform(transactions):
#         if len(transactions)==0:
#             return []
#         return [i.__dict__ for i in transactions]

class BlockChain:
        #构造函数
    def __init__(self, name, url, port):
        self.name = name
        self.chain = []
        self.transactionPool = []
        self.difficulty = 5
        self.nodes = set()
        #神造万物之始，天地渺渺茫茫
        self.chain.append({'index':0,
                           'time':int(time()),
                           'transactions':[],
                           'proof':0,
                           'parentHash':'0'*64})
        self.transactions_lock = threading.Lock()
        self.lock = threading.Lock()
        self.url = url
        self.port = port
        pass

    def register_node(self, address):
        parsed_url = urllib.parse.urlparse(address)
        self.nodes.add(address)

        #构造一个新的块，添加到区块末尾, 返回指
    def newBlock(self):
        # 下面中这个0是proof的初始值
        block = {'index':len(self.chain),
                 'time':int(time()),
                 'transactions':self.transactionPool,
                 'proof':0,
                 'parentHash':BlockChain.hash(self.chain[-1])}

        #挖矿ing...
        # 如果任务是找到合适的proof，使得hashD的十六进制转写有足够多前导零
        while BlockChain.hashD(block)[:self.difficulty] != '0'*self.difficulty:
            block['proof']+=1

        self.lock.acquire()
        self.chain.append(block)
        self.lock.release()

        self.transactions_lock.acquire()
        self.transactionPool = []
        self.transactions_lock.release()

        return block

        #将新来的交易放入交易池
    def newTransaction(self, fr, to, amount):
        self.transactionPool.append({'fr':fr, 'to':to, 'amount':amount})
        return self.chain[-1]['index']+1

        #返回区块链末尾的块
    def lastBlock(self):
        return self.chain[-1]

    def valid_chain(self, chain):
        i = 0
        while i<len(chain)-1:
            if chain[i+1].parentHash != BlockChain.hash(chain[i]):
                return False
            if BlockChain.hashD(chain[i+1])[:self.difficulty] != '0'*self.difficulty:
                return False
            i+=1
        return True

    def check_all(self):
        maxL = len(self.chain)
        longest_chain = None
        for node in self.nodes:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                chain = response.json()['chain']
                length = response.json()['length']
                if length>maxL and self.valid_chain(chain):
                        maxL = length
                        longest_chain = chain
        if longest_chain !=None:
            self.chain = longest_chain
            return True
        return False

        #挖矿
    def mine(self):
        # 上帝予你燃料
        # 交易池是临界资源，要上锁
        self.transactions_lock.acquire()
        self.newTransaction('0', self.name, 1)
        self.transactions_lock.release()
        block = self.newBlock()
        print(f"Block {self.chain[-1]['index']} forged!!!")
        for node in self.nodes:
            response = requests.post(f'http://{node}/chain/check', json=json.dumps(self.chain, sort_keys=True))
            print(f"{response.text}")

    def introduce(self):
        # 本来应该是要广播的，但是我只有一个ip，所以只能遍历端口号了
        for port in range(8300, self.port):
            print("try registering at node",f'0.0.0.0:{port}')
            response = requests.post(f'http://0.0.0.0:{port}/nodes/register', data=self.url.geturl())
            if response.status_code == 201:
                print(f'node 0.0.0.0:{port} 接受了我们的注册！！')
                self.nodes.add(urllib.parse.urlparse(f'http://0.0.0.0:{port}'))
            else:
                print(response.text)

    @staticmethod
    def hash(block):
        jsonOBJ = json.dumps(block, sort_keys=True)
        hashOBJ = hashlib.sha256(jsonOBJ.encode())
        return hashOBJ.hexdigest()

    @staticmethod
    def hashD(block):
        jsonOBJ = json.dumps(block, sort_keys=True)
        hashOBJ = hashlib.sha256(jsonOBJ.encode())

        # 对上一步结果再hash一遍
        hashOBJ = hashlib.sha256(hashOBJ.digest())
        return hashOBJ.hexdigest()



# bc = BlockChain()
# while True:
#     order = input().strip()
#     if order == '1':
#         fr, to, amount = input().split()
#         amount = int(amount)
#         bc.newTransaction(fr, to, amount)
#
#     elif order == '2':
#         bc.newBlock()
#     elif order == 'quit':
#         break


#
# bc = BlockChain()
# bc.newTransaction('mark', 'abi', 2)
# bc.newBlock()
# bc.newTransaction('abi', 'mark', 1)
# bc.newBlock()
