import ari
import logging
import requests

logging.basicConfig(level = logging.ERROR)
holdingBridge = None
client = ari.connect('http://localhost:8088','asterisk','asterisk')
def safeHangup(channel):
    """Safely hang up the specified channel"""
    try:
        channel.hangup()
        print "Hung up {}".format(channel.json.get('name'))
    except requests.HTTPError as e:
        if e.response.status_code != requests.codes.not_found:
            raise e


def safeBridgeDestroy(bridge):
    """Safely destroy the specified bridge"""
    try:
        bridge.destroy()
    except requests.HTTPError as e:
        if e.response.status_code != requests.codes.not_found:
            raise e
def findOrCreateHoldingBridge():
    global holdingBridge
    if holdingBridge:
        return holdingBridge

    bridges = [candidate for candidate in client.bridges.list() if candidate.json.get('type') == 'holding']
    
    if bridges:
        bridge = bridges[0]
        print 'Using bridge %s' %bridge.id
    else:
        bridge = client.bridges.create(type = 'holding')
        bridge.startMoh()
        print 'Created holding bridge %s' %bridge.id 
    holdingBridge = bridge 
    return holdingBridge

def onStart(channel_obj,ev):
    print 'In stasis start '
    channel = channel_obj.get('channel')
    channel_name = channel.json.get('name')
    args = ev.get('args')

    if not args:
        print "Error: {} didn't provide any arguments!".format(channel_name)
        return

    if args  and args[0] != 'inbound':
        #if arg is "dialed", we came to this function because of call from line 52, 
        #we are handling this on line 62. Ignore this call and return
        return
    waitBridge = findOrCreateHoldingBridge()
    waitBridge.addChannel(channel = channel.id)

    try:
        print "Dialing {}".format(args[1])
        outgoing = client.channels.originate(endpoint=args[1],
                                             app='bridge-dial',
                                             appArgs='dialed')
    except requests.HTTPError:
        print "Whoops, pretty sure %s wasn't valid" % args[1]
        channel.hangup()
        return

    channel.on_event('StasisEnd', lambda *args: safeHangup(outgoing))
    outgoing.on_event('StasisEnd', lambda *args: safeHangup(channel))

    def outgoingOnStart(channel_obj,ev):
        waitBridge = findOrCreateHoldingBridge()
        waitBridge.removeChannel(channel = channel.id)
        channel.answer()
        print "{} answered; bridging with {}".format(outgoing.json.get('name'),
                                                     channel.json.get('name'))
        
        mixBridge = client.bridges.create(type = 'mixing')
        mixBridge.addChannel(channel = [channel.id,outgoing.id])

         # Clean up the bridge when done
         
        channel.on_event('StasisEnd', lambda *args:
                         safeBridgeDestroy(mixBridge))
        outgoing.on_event('StasisEnd', lambda *args:
                          safeBridgeDestroy(mixBridge))
    outgoing.on_event('StasisStart',outgoingOnStart)

client.on_channel_event('StasisStart',onStart)
client.run( apps = 'bridge-dial')