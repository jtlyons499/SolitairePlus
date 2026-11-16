import asyncio
import queue
import threading
import time
import unittest
from relay_server import RelayServer
from relay_transport import RelayPeer

class RelayTests(unittest.TestCase):
    def setUp(self):
        self.loop=asyncio.new_event_loop()
        self.thread=threading.Thread(target=self.loop.run_forever,daemon=True)
        self.thread.start()
        self.relay=RelayServer()
        async def start():
            return await asyncio.start_server(self.relay.handle,'127.0.0.1',0,limit=65536)
        self.server=asyncio.run_coroutine_threadsafe(start(),self.loop).result(3)
        self.address='127.0.0.1:'+str(self.server.sockets[0].getsockname()[1])
        self.peers=[]
    def tearDown(self):
        for p in self.peers:p.close()
        async def stop():
            self.server.close()
            await self.server.wait_closed()
            await asyncio.sleep(.1)
            tasks=[t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for t in tasks:t.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
        asyncio.run_coroutine_threadsafe(stop(),self.loop).result(3)
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(3)
        self.loop.close()
    def wait(self,p,kind):
        deadline=time.monotonic()+4
        while time.monotonic()<deadline:
            try:m=p.inbox.get(timeout=.05)
            except queue.Empty:continue
            if m.get('type')==kind:return m
        self.fail('Timed out waiting for '+kind)
    def pair(self):
        host=RelayPeer(True,self.address,'Host');self.peers.append(host)
        self.wait(host,'status')
        guest=RelayPeer(False,self.address,'Guest',host.code);self.peers.append(guest)
        self.assertEqual(self.wait(host,'hello')['name'],'Guest')
        self.assertEqual(self.wait(guest,'hello')['name'],'Host')
        return host,guest
    def test_pair_forward_disconnect(self):
        host,guest=self.pair()
        guest.send({'type':'action','action':'fold','revision':0})
        self.assertEqual(self.wait(host,'action')['action'],'fold')
        host.send({'type':'state','revision':2})
        self.assertEqual(self.wait(guest,'state')['revision'],2)
        guest.close()
        self.assertIn('disconnected',self.wait(host,'disconnected')['text'])
    def test_invalid_and_full_room(self):
        bad=RelayPeer(False,self.address,'Bad','ZZZZZZZZ');self.peers.append(bad)
        self.assertIn('not found',self.wait(bad,'disconnected')['text'])
        host,guest=self.pair()
        third=RelayPeer(False,self.address,'Third',host.code);self.peers.append(third)
        self.assertIn('two players',self.wait(third,'disconnected')['text'])
        guest.send({'type':'action','action':'check_call'})
        self.assertEqual(self.wait(host,'action')['action'],'check_call')
