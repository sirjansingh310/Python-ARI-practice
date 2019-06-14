import ari
import logging

logging.basicConfig(level = logging.ERROR)
client = ari.connect('http://localhost:8088','asterisk','asterisk')

def on_dtmf(channel,event):
    try:
        digit = int(event.get('digit'))
        channel.play(media = 'sound:you-entered')
        channel.play(media = 'digits:'+str(digit))
    except:
        channel.play(media = 'sound:goodbye')

    
def on_start(channel_obj,event):
    channel = channel_obj.get('channel')
    channel.on_event('ChannelDtmfReceived',on_dtmf)
    channel.answer()
    channel.play(media='sound:hello-world')

client.on_channel_event('StasisStart',on_start)
client.run(apps = 'ari-app')