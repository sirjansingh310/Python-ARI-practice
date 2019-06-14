import ari
import logging

logging.basicConfig(level = logging.ERROR)
client = ari.connect('http://localhost:8088','asterisk','asterisk')

    
def on_start(channel_obj,event):
    channel = channel_obj.get('channel')
    print 'In ARI'
    channel.answer()
    channel.play(media='sound:hello-world')

client.on_channel_event('StasisStart',on_start)
client.run(apps = 'hello-ari')