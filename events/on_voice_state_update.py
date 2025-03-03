import discord
import time
from discord.ext import commands

from utils.constants import RED_COLOR, GREEN_COLOR, YELLOW_COLOR
from utils.utils import discord_time
import datetime

class OnVoiceStateUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        This event is triggered when a member's voice state is updated.
        :param member (discord.Member): The member whose voice state was updated.
        :param before (discord.VoiceState): The member's voice state before the update.
        :param after (discord.VoiceState): The member's voice state after the update.
        """
        
        sett = await self.bot.settings.find_by_id(member.guild.id)
        guild = member.guild
        if not sett:
            return
        if sett.get("moderation_module", {}).get("enabled", False) is False:
                return
        if sett.get("moderation_module", {}).get("audit_log") is None:
            return
        guild_log_channel = guild.get_channel(sett["moderation_module"]["audit_log"])
        if not guild_log_channel:
            return

        webhooks = await guild_log_channel.webhooks()
        cyni_webhook = None
        for webhook in webhooks:
            if webhook.name == "Cyni":
                cyni_webhook = webhook
                break
        
        if not cyni_webhook:
            bot_avatar = await self.bot.user.avatar.read()
            try:
                cyni_webhook = await guild_log_channel.create_webhook(name="Cyni", avatar=bot_avatar)
            except discord.HTTPException:
                cyni_webhook = None

        action_time = discord_time(datetime.datetime.now())
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                    title= " ",
                    description=f"{member.mention} joined voice channel {after.channel.mention} on {action_time}",
                    color=YELLOW_COLOR
                ).set_author(
                    name=member,
                ).set_footer(
                    text=f"User ID: {member.id}"
                )
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)

        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                    title= " ",
                    description=f"{member.mention} left voice channel {before.channel.mention} on {action_time}",
                    color=RED_COLOR
                ).set_author(
                    name=member,
                ).set_footer(
                    text=f"User ID: {member.id}"
                )
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)

        elif before.channel is not None and after.channel is not None:
            embed = discord.Embed(
                    title= " ",
                    description=f"{member.mention} moved from voice channel {before.channel.mention} to {after.channel.mention} on {action_time}",
                    color=GREEN_COLOR
                ).set_author(
                    name=member,
                ).set_footer(
                    text=f"User ID: {member.id}"
                )
            if cyni_webhook:
                await cyni_webhook.send(embed=embed)
            else:
                await guild_log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OnVoiceStateUpdate(bot))