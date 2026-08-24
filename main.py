import asyncio
import logging
import os
from typing import List

import discord
from discord.ext import commands

_logger = logging.getLogger("discord")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


class MyBot(commands.Bot):
    def __init__(self, intents: discord.Intents) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"), 
            intents=intents,
            help_command=None
        )
        self.initial_extensions: List[str] = [
            "cogs.ticket",
            "cogs.role_giver"
        ]

    async def setup_hook(self) -> None:
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                _logger.info(f"Successfully loaded extension: {extension}")
            except Exception as e:
                _logger.error(f"Failed to load extension {extension}.", exc_info=e)

        print("Synchronizing application commands...")
        synced = await self.tree.sync()
        print(f"Successfully synchronized {len(synced)} application commands globally.")

    async def on_ready(self) -> None:
        if self.user is not None:
            print(f"Logged in as {self.user.name} (ID: {self.user.id})")
        else:
            print("Logged in, but user profile could not be retrieved.")
            
        print("------")
        
        activity = discord.Activity(type=discord.ActivityType.listening, name="test")
        await self.change_presence(status=discord.Status.online, activity=activity)


async def main() -> None:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True

    bot = MyBot(intents=intents)

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError("DISCORD_TOKEN 환경 변수가 누락되었습니다. 환경 변수 설정을 확인하세요.")

    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is shutting down safely...")
