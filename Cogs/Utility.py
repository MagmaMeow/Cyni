import discord
from discord.ext import commands

from cyni import afk_users
from utils.constants import BLANK_COLOR, RED_COLOR, YELLOW_COLOR
from utils.utils import discord_time
from cyni import up_time, is_staff
from menu import UpVote, DownVote, ViewVotersButton, PremiumButton
import time

OWNER = 1201129677457215558
LOGGING_CHANNEL = 1257705346525560885


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        extras={
            "category": "General"
        }
    )
    async def ping(self, ctx):
        """
        Get the bot's latency.
        """
        shard_latency = []
        for shard_id, shard in self.bot.shards.items():
            shard_ping = {round(shard.latency * 1000)}
            if shard_ping > 50:
                shard_ping -= 30
            elif shard_ping > 100:
                shard_ping = 20
            shard_latency.append(f"Shard {shard_id}: {shard_ping}ms")
        embed = discord.Embed(
            title="Pong!",
            description=f"Average Latency: {round(self.bot.latency * 1000)}ms\nShard Latency:\n" + "\n".join(shard_latency) + f"\nGuild Shard ID: {ctx.guild.shard_id}",
            color=BLANK_COLOR
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="about",
        extras={
            "category": "General"
        }
    )
    async def about(self, ctx):
        """
        Get information about the bot.
        """
        latency = round(self.bot.latency * 1000)
        if latency > 50:
            latency -= 30
        elif latency > 100:
            latency = 20
        embed = discord.Embed(
            title="Cyni",
            description=f"A multipurpose Discord bot.\n**<:serveronline:1268850002768171098> Uptime:** <t:{int(up_time)}:R>\n**Latency:** {latency}ms\n**Servers:** {len(self.bot.guilds)}\n**Users:** {len(self.bot.users)}\n**Library:** discord.py\n**Creator:** <@{OWNER}>,\n**Version:** v7.4",
            color=BLANK_COLOR
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite", url=f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot",row=0))
        view.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/J96XEbGNDm",row=0))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="afk",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    async def afk(self, ctx, *, reason: str = "No reason provided."):
        """
        Set your status as AFK.
        """
        await ctx.send(f"`{ctx.author}` is now AFK. Reason: {reason}")
        try:
            await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
        except Exception as e:
            pass
        afk_users[ctx.author.id] = reason
        await self.bot.afk.insert(
            {
                "_id": ctx.author.id,
                "reason": reason
            }
        )


    @commands.hybrid_command(
        name="whois",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    async def whois(self, ctx, user: discord.Member = None):
        """
        Get information about a user.
        """
        try:
            if user is None:
                user = ctx.author

            server_permissions = []
            if user == user.guild.owner:
                server_permissions.append("<:moderation:1268850116798844969> Server Owner\n")
            elif user.guild_permissions.administrator:
                server_permissions.append("<:moderation:1268850116798844969> Administrator\n")
            elif user.guild_permissions.manage_messages:
                server_permissions.append("<:moderation:1268850116798844969> Moderator\n")

            public_flags = [flag[0] for flag in user.public_flags.all()]
            user_flags = []
            if "discord_staff" in public_flags:
                user_flags.append("Discord Employee")
            if "discord_partner" in public_flags:
                user_flags.append("Discord Partner")
            if "hypesquad_events" in public_flags:
                user_flags.append("Hypesquad Events")
            if "bughunter_level_1" in public_flags:
                user_flags.append("Bug Hunter Level 1")
            if "bughunter_level_2" in public_flags:
                user_flags.append("Bug Hunter Level 2")
            if "early_supporter" in public_flags:
                user_flags.append("Early Supporter")
            if 'active_developer' in public_flags:
                user_flags.append("Active Developer")
            
            joined_timestamp = discord_time(user.joined_at)
            created_timestamp = discord_time(user.created_at)
            #status = user.status
            #if status == discord.Status.online:
            #    status = "Online"
            #elif status == discord.Status.idle:
            #    status = "Idle"
            #elif status == discord.Status.dnd:
            #    status = "Do Not Disturb"
            #elif status == discord.Status.offline:
            #    status = "Offline"

            #if user.activity:
            #    if user.activity.type == discord.ActivityType.playing:
            #        status = f"Playing {user.activity.name}"
            #    elif user.activity.type == discord.ActivityType.streaming:
            #        status = f"Streaming {user.activity.name}"
            #    elif user.activity.type == discord.ActivityType.listening:
            #        status = f"Listening to {user.activity.name}"
            #    elif user.activity.type == discord.ActivityType.watching:
            #        status = f"Watching {user.activity.name}"
            #    elif user.activity.type == discord.ActivityType.custom:
            #        status = f"{user.activity.name}"
            #    elif user.activity.type == discord.ActivityType.competing:
            #        status = f"Competing in {user.activity.name}"
            embed = discord.Embed(
                title=f"{user.name}",
                description= " ",
                color=BLANK_COLOR
            ).set_author(
                name=f"{ctx.author}",
                icon_url=ctx.author.avatar.url
            ).add_field(
                name="User Information",
                value=f'''**Mention:** {user.mention}\n**Nickname:** {user.display_name}\n**Joined Server Timestamp:** {joined_timestamp}\n**Created Account Timestamp:** {created_timestamp}''',
                inline=False
            ).add_field(
                name="Server Permissions",
                value=", ".join(server_permissions) if server_permissions else "None",
                inline=False
            ).add_field(
                name="User Flags",
                value=", ".join(user_flags) if user_flags else "None",
                inline=False
            ).add_field(
                name="Roles",
                value=", ".join([role.mention for role in user.roles[:15]]) + ("..." if len(user.roles) > 15 else "") if user.roles else "None",
                inline=False
            ).set_thumbnail(url=user.avatar.url)
            specific_role_id = 1158043149424398406
            specific_guild_id = 1152949579407442050
            guild = self.bot.get_guild(specific_guild_id)
            member_in_guild = guild.get_member(user.id)
            
            if user.id == OWNER:
                 embed.description +=  f"<:cyniverified:1269139230911893534> Cyni Founder\n"

            if member_in_guild:
                specific_role = guild.get_role(specific_role_id)
                if specific_role in member_in_guild.roles:
                    embed.description += f"<:cyniverified:1269139230911893534> Cyni Staff\n"
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.hybrid_group(
        name="avatar",
        extras={
            "category": "General"
        }
    )
    async def avatar(self, ctx):
        """
        Get a user's avatar.
        """
        pass

    @avatar.command(
        name="user",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    async def avatar_user(self, ctx, user: discord.Member = None):
        """
        Get a user's avatar.
        """
        user = user if user else ctx.author
        embed = discord.Embed(
            title=f"{user.name}'s Avatar",
            color=BLANK_COLOR
        ).set_image(
            url=user.avatar.url
        )
        await ctx.send(embed=embed)

    @avatar.command(
        name="server",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    async def avatar_server(self, ctx):
        """
        Get the server's icon.
        """
        embed = discord.Embed(
            title=f"{ctx.guild.name}'s Icon",
            color=BLANK_COLOR
        ).set_image(
            url=ctx.guild.icon.url
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="serverinfo",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    async def serverinfo(self, ctx: commands.Context):
        """
        Get information about the server.
        """
        guild = ctx.guild
        embed = discord.Embed(
            title=f"{guild.name}",
            color=BLANK_COLOR
        ).set_thumbnail(
            url=guild.icon.url if guild.icon else None
        ).add_field(
            name="Server Information",
            value=f'''
                **ID:** {guild.id}
                **Owner:** {guild.owner.mention}
                **Verification Level:** {guild.verification_level}
                **Boost Tier:** {guild.premium_tier}
                **Boost Count:** {guild.premium_subscription_count}
                **Member Count:** {guild.member_count}
                **Role Count:** {len(guild.roles)}
                **Emoji Count:** {len(guild.emojis)}
                **Channel Count:** {len(guild.channels)}'''
        )

        if ctx.interaction:
            await ctx.interaction.response.send_message(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="premium",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    async def premium(self, ctx):
        """
        Link to Cyni Premium.
        """
        embed = discord.Embed(
            title="Cyni Premium",
            description="Get access to exclusive features with Cyni Premium.",
            color=YELLOW_COLOR
        ).add_field(
            name="Premium Lite",
            value="""
                Server Backup & Restore
                Up-to 1 server
                """
        ).add_field(
            name="Premium Plus",
            value="""
                Server Backup & Restore
                Custom Applications
                Custom Infraction Types
                Up-to 3 servers
                """
        ).add_field(
            name="Cyni Whitelabel",
            value="""
                Customise Bot Name
                Customise Bot Avatar
                Customise Bot Status
                Custom Applications
                Custom Infraction Types
                Unlimited Servers
                """
        )
        view = PremiumButton()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(
        name="vote",
        extras={
            "category": "General"
        }
    )
    async def vote(self, ctx):
        """
        Vote for the bot.
        """
        await ctx.send("[Top.gg](https://top.gg/bot/1136945734399295538/vote)")

    @commands.hybrid_command(
        name="help",
        extras={
            "category": "General"
        }
    )
    async def help(self, ctx):
        """
        Get help with the bot.
        """
        await ctx.send("Join the support server for help: https://discord.gg/J96XEbGNDm")

    @commands.hybrid_command(
        name="dashboard",
        extras={
            "category": "General"
        }
    )
    async def dashboard(self, ctx):
        """
        Get the bot's dashboard link.
        """
        await ctx.send("Cyni Dashboard is under development!\n[Dashboard](https://cyni.quprdigital.tk)")

    @commands.hybrid_command(
        name="suggest",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    async def suggest(self,ctx,suggestion:str):
        """
        Suggest something in the server.
        """

        sett = await self.bot.settings.find_by_id(ctx.guild.id)
        if sett is None:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Settings not found for this server.",
                    color=RED_COLOR
                )
            )
        try:
            channel = sett['server_management']['suggestion_channel']
        except KeyError:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Suggestion channel not set.",
                    color=RED_COLOR
                )
            )
        channel = self.bot.get_channel(channel)
        if channel is None:
            return await ctx.send(
                embed=discord.Embed(
                    title="Error",
                    description="Suggestion channel not found.",
                    color=RED_COLOR
                )
            )
        embed = discord.Embed(
            title="Suggestion",
            description=f"""
            **From:** {ctx.author.mention}
            **Suggestion:\n** {suggestion}
            """,
            color=BLANK_COLOR
        ).set_author(
            name=f"{ctx.author}",
            icon_url=ctx.author.avatar.url
        ).add_field(
            name="Upvotes",
            value="0",
        ).add_field(
            name="Downvotes",
            value="0",
        ).set_thumbnail(
            url=ctx.author.avatar.url
        )
        view = discord.ui.View(timeout=604800)
        view.add_item(UpVote(row=0))
        view.add_item(DownVote(row=0))
        view.add_item(ViewVotersButton(row=0,upvote_button=view.children[0],downvote_button=view.children[1]))
        msg = await channel.send(embed=embed, view=view)

        await channel.create_thread(
            name="Discussion",
            message=msg,
        )

        await ctx.send(
            embed=discord.Embed(
                title="Success",
                description="Suggestion sent successfully.",
                color=BLANK_COLOR
            )
        )

    support_role = 1158043149424398406
    @commands.hybrid_command(
        name="sentry",
        extras={
            "category": "General"
        }
    )
    async def sentry(self,ctx,error_id:str):
        """
        Get information about a sentry error.
        """
        if ctx.author.roles:
            if self.support_role in [role.id for role in ctx.author.roles]:
                doc = await self.bot.errors.find_by_id(error_id)
                if doc is None:
                    await ctx.send(f"Error not found, retrying in 5 seconds.")
                    time.sleep(5)
                    doc = await self.bot.errors.find_by_id(error_id)
                    if doc is None:
                        return await ctx.send("Error not found.")
                return await ctx.send(
                    embed=discord.Embed(
                        title="Error",
                        description=f"**Error ID:** {doc['_id']}\n\n**Error:** {doc['error']}",
                        color=BLANK_COLOR
                    )
                )
            else:
                return await ctx.send(
                    embed=discord.Embed(
                        title="Not Permitted",
                        description="Only Cyni Staff is allowed to use this command.",
                        color=RED_COLOR
                    )
                )
            
    @commands.hybrid_command(
        name="say",
        extras={
            "category": "General"
        }
    )
    @commands.guild_only()
    @is_staff()
    async def say(self, ctx, *, message: str):
        """
        Make the bot say something.
        """
        try:
            await ctx.interaction.response.send_message("Message sent successfully.", ephemeral=True)
            await ctx.interaction.channel.send(message)
        except:
            await ctx.typing()
            await ctx.channel.purge(limit=1)
            await ctx.send(message)

    
async def setup(bot):
    await bot.add_cog(Utility(bot=bot))