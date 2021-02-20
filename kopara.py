import socket
import json
import hashlib
import binascii
from pprint import pprint
import time
import random

address = 'bc1qh5wqy43ccaqlfxw3t0sxrsk0ws5gy4x64j6x7h'
nonce   = hex(random.randint(0,2**32-1))[2:].zfill(8)

host    = 'solo.ckpool.org'
port    = 3333

print("address:{} nonce:{}".format(address,nonce))
print("host:{} port:{}".format(host,port))

while True==True:

  sock    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.connect((host,port))

  sock.sendall(b'{"id": 1, "method": "mining.subscribe", "params": []}\n')
  lines = sock.recv(1024).decode().split('\n')
  response = json.loads(lines[0])
  sub_details,extranonce1,extranonce2_size = response['result']

  sock.sendall(b'{"params": ["'+address.encode()+b'", "password"], "id": 2, "method": "mining.authorize"}\n')

  response = b''
  while response.count(b'\n') < 4 and not(b'mining.notify' in response):
      response += sock.recv(1024)

  responses = [json.loads(res) for res in response.decode().split('\n') if len(res.strip())>0 and 'mining.notify' in res]
  pprint(responses)

  job_id,prevhash,coinb1,coinb2,merkle_branch,version,nbits,ntime,clean_jobs \
      = responses[0]['params']

  target = (nbits[2:]+'00'*(int(nbits[:2],16) - 3)).zfill(64)
  print('nbits:{} target:{}\n'.format(nbits,target))

  extranonce2 = '00'*extranonce2_size

  coinbase = coinb1 + extranonce1 + extranonce2 + coinb2
  coinbase_hash_bin = hashlib.sha256(hashlib.sha256(binascii.unhexlify(coinbase)).digest()).digest()

  print('coinbase:\n{}\n\ncoinbase hash:{}\n'.format(coinbase,binascii.hexlify(coinbase_hash_bin)))
  merkle_root = coinbase_hash_bin
  for h in merkle_branch:
      merkle_root = hashlib.sha256(hashlib.sha256(merkle_root + binascii.unhexlify(h)).digest()).digest()

  merkle_root = binascii.hexlify(merkle_root).decode()

  merkle_root = ''.join([merkle_root[i]+merkle_root[i+1] for i in range(0,len(merkle_root),2)][::-1])

  print('merkle_root:{}\n'.format(merkle_root))

  blockheader = version + prevhash + merkle_root + nbits + ntime + nonce +\
      '000000800000000000000000000000000000000000000000000000000000000000000000000000000000000080020000'

  print('blockheader:\n{}\n'.format(blockheader))

  hash = hashlib.sha256(hashlib.sha256(binascii.unhexlify(blockheader)).digest()).digest()
  hash = binascii.hexlify(hash).decode()
  print('hash: {}'.format(hash))

  if hash < target :
      print('success!')
      payload = '{"params": ["'+address+'", "'+job_id+'", "'+extranonce2 \
          +'", "'+ntime+'", "'+nonce+'"], "id": 1, "method": "mining.submit"}\n'
      sock.sendall(payload)
      print(sock.recv(1024))
  else:
      print('failed mine')
