# geventreactor

**geventreactor** is a gevent-powered **Twisted** reactor whose goal is to enable mixing of **gevent**- and **Twisted**-oriented code, allowing developers to benefit from the performance of **libevent** and **greenlet** while retaining access to the extensive functionality of **Twisted**.


## Differences From Similar Projects

- Unlike [corotwine], geventreactor does not provide a special base protocol whose subclasses are utilized in a blocking manner.
  - Twisted code looks like Twisted code and gevent code looks like gevent code. As a result, it should not be a challenge for users of either framework to use geventreactor, and standard documentation applies. The integration is so complete, however, that blocking code can be used in most standard Twisted methods.
- Unlike the Twisted hub for [Eventlet], geventreactor makes Twisted run on gevent, not the other way around.
  - Eventlet uses a pure-Python reactor loop, so there is not much to be gained from running Twisted on Eventlet. On the other hand, gevent uses the C-based libevent, which is more performant.
- Unlike gTwist (geventreactor's predecessor), geventreactor does not monkey-patch anything, and replaces the reactor in the recommended way.
  - The result is cleaner code and fewer quirks.

[corotwine]: https://launchpad.net/corotwine "corotwine"
[Eventlet]: http://eventlet.net/ "Eventlet"


## Module Contents

- `GeventReactor` is the gevent-powered reactor. Simply install it before you import `twisted.internet.reactor`:
  `import geventreactor; geventreactor.install()`
- `GeventResolver` is the gevent-powered DNS resolver. It is automatically installed in the `GeventReactor`, but can be used by itself à la `ThreadedResolver`
- `GeventThreadPool` manages greenlets in a group but exposes a Twisted-style thread pool interface. It helps `GeventReactor` work seamlessly with the functions in `twisted.internet.threads`.
- `waitForGreenlet` adapts a greenlet to a `Deferred` usable in Twisted methods
- `waitForDeferred` waits until a `Deferred` is fulfilled, blocking for a result or exception


## Example Code


### Client

```python
import geventreactor; geventreactor.install()
from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers

agent = Agent(reactor)

d = agent.request(
	'GET',
	'http://example.com/',
	Headers({'User-Agent': ['Twisted Web Client Example']}),
	None)

def cbResponse(ignored):
	print 'Response received'
d.addCallback(cbResponse)

def cbShutdown(ignored):
	reactor.stop()
d.addBoth(cbShutdown)

reactor.run()
```


### Server

```python
import gevent, time

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

def greencount():
	s = time.time()
	while 1:
		gevent.sleep(1)
		s0 = time.time()
		print s0-s-1
		s = s0

class TwistedFactory(Factory):
	class protocol(LineReceiver):
		delimiter = '\n'
		def connectionMade(self):
			print '+connection:',id(self)
			self.transport.write(self.factory.quote+'\r\n')
			def later(i):
				self.transport.write('%d from later()\r\n'%i)
			@gevent.Greenlet.spawn
			def ninja():
				gevent.sleep(1)
				self.transport.write('0 from ninja()\r\n')
				gevent.sleep(2)
				self.transport.write('2 from ninja()\r\n')
				reactor.callLater(1,later,3)
			reactor.callLater(2,later,1)
		def connectionLost(self,reason):
			print '-connection:',id(self),reason
		def lineReceived(self,data):
			self.stopcounter()
			data = data.strip()
			ldata = data.lower()
			if ldata == 'die':
				self.sendLine('stopping reactor')
				reactor.stop()
			elif ldata == 'quit':
				self.sendLine('quitting in 2 seconds')
				gevent.sleep(2)
				self.transport.loseConnection()
			elif ldata == 'delay':
				self.sendLine('waiting 10 seconds')
				gevent.sleep(10)
				self.sendLine('hi again')
			elif ldata == 'count':
				self.stopcounter()
				@gevent.Greenlet.spawn
				def count():
					i = 0
					while 1:
						gevent.sleep(1)
						self.sendLine('%d from count()'%i)
						i += 1
				self.counter = count
			else:
				self.sendLine(data)
		def stopcounter(self):
			try:
				self.counter.kill()
				del self.counter
			except AttributeError:
				pass
	def __init__(self,quote=None):
		self.quote = quote or 'An apple a day keeps the doctor away'

import geventreactor; geventreactor.install()
from twisted.internet import reactor
gevent.Greenlet.spawn(greencount)
reactor.listenTCP(8007,TwistedFactory('Welcome to the geventreactor demo!\r\ncount:\tstart a counter\r\ndelay:\tblock your session for 10 seconds\r\nquit:\tterminate your session after 2 seconds\r\ndie:\tstop the reactor\r\notherwise, simply echo'))
reactor.run()
```


## Known Quirks

Life would be perfect without these, right?

- You can use blocking code in many places, but not **everywhere**. Each protocol instance has two greenlets dedicated to input and output, so feel free to block in `doRead` (i.e. `dataReceived`, `lineReceived`, ...), and `doRead` won't be called multiple times simultaneously unless you make it do so (i.e. spawn a greenlet and return). Anything that runs in the reactor's greenlet (i.e. `callFromThread`, `callFromGreenlet`, `callLater`, ...) must not block. Deferred callbacks/errbacks should also not block, because they may be called from the reactor's greenlet. Of course, it is okay to spawn new greenlets when blocking is not advisable. So far, I know the following additional methods should not block:
  - `Protocol.connectionMade`
- While a reasonable attempt is made for performance, the main concern is compatibility with existing Twisted-oriented code. geventreactor is similar to selectreactor in terms of throughput, but it does not perform as well in the number of connections or Web requests processed per second. Please consider porting performance-critical parts of the project to gevent. Currently, compatibility and performance are tested using jcalderone's [twisted-benchmarks].

[twisted-benchmarks]: https://code.launchpad.net/~exarkun/+junk/twisted-benchmarks "twisted-benchmarks"


## License

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
