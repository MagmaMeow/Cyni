import discord
from discord.abc import User
from discord.ext import commands, tasks
from utils.mongo import Document
from utils.constants import BLANK_COLOR

from pkgutil import iter_modules
import logging
import os
import time

from dotenv import load_dotenv
import motor.motor_asyncio
from utils.utils import get_prefix

from Datamodels.Settings import Settings
from Datamodels.Analytics import Analytics
from Datamodels.Warning import Warnings
from Datamodels.StaffActivity import StaffActivity
from Datamodels.Errors import Errors
from Datamodels.Sessions import Sessions
from Datamodels.Infraction_log import Infraction_log
from Datamodels.Infraction_types import Infraction_type
from Datamodels.Giveaway import Giveaway
from Datamodels.Backup import Backup
from Datamodels.afk import AFK
from Datamodels.Erlc_keys import ERLC_Keys
from Datamodels.Applications import Applications
from Datamodels.Partnership import Partnership
from Datamodels.LOA import LOA
from Datamodels.YouTubeConfig import YouTubeConfig

from Tasks.loa_check import loa_check
from Tasks.GiveawayRoll import giveaway_roll

from utils.prc_api import PRC_API_Client
from decouple import config

load_dotenv()

intents = discord.Intents.default()
intents.presences = False
intents.message_content = True
intents.members = True
intents.messages = True
intents.moderation = True
intents.bans = True
intents.webhooks = True
intents.guilds = True

discord.utils.setup_logging(level=logging.INFO)

# --- BOT CLASS ---
class Bot(commands.AutoShardedBot):
    
    async def close(self):
        print('Closing...')
        await super().close()
        print('Closed!')

    async def is_owner(self, user: User) -> bool:
        return user.id in [
            1201129677457215558, # coding.nerd
            707064490826530888, # imlimiteds
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # MongoDB setup
        MONGODB_URI = os.getenv('MONGODB_URI')
        if not MONGODB_URI:
            raise RuntimeError("MONGODB_URI environment variable not set!")

        self.mongo = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
        self.db = self.mongo["cyni"] if os.getenv("PRODUCTION_TOKEN") else self.mongo["dev"]

        # Documents
        self.settings_document = Document(self.db, 'settings')
        self.analytics_document = Document(self.db, 'analytics')
        self.warnings_document = Document(self.db, 'warnings')
        self.actvity_document = Document(self.db, 'staff_activity')
        self.appeals_document = Document(self.db, 'ban_appeals')
        self.errors_document = Document(self.db, 'errors')
        self.sessions_document = Document(self.db, 'sessions')
        self.infraction_log_document = Document(self.db, 'infraction_log')
        self.infraction_types_document = Document(self.db, 'infraction_types')
        self.giveaway_document = Document(self.db, 'giveaways')
        self.backup_document = Document(self.db, 'backup')
        self.afk_document = Document(self.db,'afk')
        self.erlc_keys_document = Document(self.db, 'erlc_keys')
        self.applications_document = Document(self.db, 'applications')
        self.partnership_document = Document(self.db, 'partnership')
        self.loa_document = Document(self.db, 'loa')

    async def setup_hook(self) -> None:
        # Models
        self.settings = Settings(self.db, 'settings')
        self.analytics = Analytics(self.db, 'analytics')
        self.warnings = Warnings(self.db, 'warnings')
        self.staff_activity = StaffActivity(self.db, 'staff_activity')
        self.ban_appeals = Document(self.db, 'ban_appeals')
        self.errors = Errors(self.db, 'errors')
        self.sessions = Sessions(self.db, 'sessions')
        self.infraction_log = Infraction_log(self.db, 'infraction_log')
        self.infraction_types = Infraction_type(self.db, 'infraction_types')
        self.giveaways = Giveaway(self.db, 'giveaways')
        self.backup = Backup(self.db, 'backup')
        self.afk = AFK(self.db,'afk')
        self.erlc_keys = ERLC_Keys(self.db, 'erlc_keys')
        self.prc_api = PRC_API_Client(self, base_url=config('PRC_API_URL'), api_key=config('PRC_API_KEY'))
        self.applications = Applications(self.db, 'applications')
        self.partnership = Partnership(self.db, 'partnership')
        self.loa = LOA(self.db, 'loa')
        self.youtube_config = YouTubeConfig(self.db, 'youtube_config')
        
        # Load extensions
        Cogs = [m.name for m in iter_modules(['Cogs'], prefix='Cogs.')]
        Events = [m.name for m in iter_modules(['events'], prefix='events.')]
        EXT_EXTENSIONS = ["utils.api"]
        UNLOAD_EXTENSIONS = ["Cogs.Tickets", "Cogs.Applications"]
        DISCONTINUED_EXTENSIONS = ["Cogs.Backup"]

        for extension in EXT_EXTENSIONS + Cogs + Events:
            try:
                await self.load_extension(extension)
                logging.info(f'Loaded extension {extension}.')
            except Exception as e:
                logging.error(f'Failed to load extension {extension}.', exc_info=True)

        if os.getenv("PRODUCTION_TOKEN"):
            for extension in UNLOAD_EXTENSIONS:
                try:
                    await self.unload_extension(extension)
                    logging.info(f'Unloaded extension {extension}.')
                except Exception as e:
                    logging.error(f'Failed to unload extension {extension}.', exc_info=True)

        for extension in DISCONTINUED_EXTENSIONS:
            try:
                await self.unload_extension(extension)
                logging.info(f'Unloaded extension {extension}.')
            except Exception as e:
                logging.error(f'Failed to unload extension {extension}.', exc_info=True)

        logging.info("Connected to MongoDB")
        logging.info("Loaded all extensions.")

        # Start tasks
        change_status.start()
        loa_check.start(self)
        giveaway_roll.start(self)

        logging.info(f"Logged in as {bot.user}")
        await bot.tree.sync()

# --- BOT INSTANCE ---
bot = Bot(
    command_prefix=get_prefix,
    case_insensitive=True,
    intents=intents,
    help_command=None,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
    shard_count=1
)

# --- Other Globals ---
bot_debug_server = [1152949579407442050]
bot_shard_channel = 1203343926388330518
afk_users = {}
up_time = time.time()

# --- EVENTS ---
@bot.event
async def on_shard_ready(shard_id):
    embed = discord.Embed(
        title="Shard Connected",
        description=f"Shard ID `{shard_id}` connected successfully.",
        color=BLANK_COLOR
    )
    await bot.get_channel(bot_shard_channel).send(embed=embed)

@bot.event
async def on_shard_disconnect(shard_id):
    embed = discord.Embed(
        title="Shard Disconnected",
        description=f"Shard ID `{shard_id}` disconnected.",
        color=BLANK_COLOR
    )
    await bot.get_channel(bot_shard_channel).send(embed=embed)

# --- TASKS ---
@tasks.loop(hours=1)
async def change_status():
    await bot.wait_until_ready()
    guild_count = len(bot.guilds)
    status = "Watching over " + str(guild_count) + "+ servers"
    await bot.change_presence(activity=discord.CustomActivity(name=status))

# --- RUN LOGIC ---
if os.getenv("PRODUCTION_TOKEN"):
    bot_token = os.getenv("PRODUCTION_TOKEN")
    logging.info("Production Token")
elif os.getenv("PREMIUM_TOKEN"):
    bot_token = os.getenv("PREMIUM_TOKEN")
    logging.info("Using Premium Token")
else:
    bot_token = os.getenv("DEV_TOKEN")
    logging.info("Using Development Token")

def run_whitelabel_bot(token: str):
    """Run a whitelabel version of the bot using a custom token."""
    logging.info("Running whitelabel bot")
    try:
        bot.run(token)
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

def run():
    try:
        bot.run(bot_token)
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    run()
