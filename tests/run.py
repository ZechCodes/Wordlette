import wordlette.site
import asyncio


site = wordlette.site.Site(__file__)


loop = asyncio.get_event_loop()
loop.run_until_complete(site.setup())
print("Done")
