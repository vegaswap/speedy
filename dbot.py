token = "NzUxMTE4Mjk2NzgyMjA5MDk1.X1EbbQ.d2Pbgb95mPnCbTzdOMGZlGyXU5w"

#cid ="751118296782209095"
#cs = "_LeCm1UY-mqXF0JL4rx2zYl4GvI5tIS1"

import discord
print (discord)

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run(token)