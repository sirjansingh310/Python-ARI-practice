import ari
import logging

logging.basicConfig(level = logging.ERROR)

client = ari.connect('http://localhost:8088','asterisk','asterisk')

bridge = [candidate for candidate in client.bridges.list() if candidate.json.get('bridge_type') == 'holding']

if bridge:
    bridge = bridge[0]
    print 'Using bridge %s' %(bridge.id)
else:
    bridge = client.bridges.create(type = 'holding')
    print 'Created a new bridge %s' %(bridge.id)

def on_start(channel_obj,event):
    channel = channel_obj.get('channel')
    print 'Channel %s just entered our application. Adding it to bridge %s' %(channel.json.get('name'),bridge.id)
    channel.answer()
    bridge.addChannel(channel = channel.id)
    bridge.startMoh()
def on_end(channel,event):
    print 'Channel %s left the application' %(channel.json.get('name'))
client.on_channel_event('StasisStart',on_start)
client.on_channel_event('StasisEnd',on_end)
client.run(apps = 'ari-app')