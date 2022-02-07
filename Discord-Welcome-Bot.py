from datetime import datetime
from typing import Union

import discord
from discord.ext import commands
import discord.utils

import config


# Logs to bot-log channel message
async def log(client: commands.Bot, message: str):
    chan = client.get_channel(config.BOT_LOGS)
    await chan.send(message)


# Checks if user possesses a role in the allowed roles list.
def allowed(user: Union[discord.User, discord.Member]) -> bool:
    for role in user.roles:
        if role.id in config.ALLOWED_ROLES:
            return True

    return False


def main():
    # Set discord API intents
    intents = discord.Intents().all()

    # instantiate a new command-accepting bot
    client = commands.Bot(command_prefix=";", intents=intents)

    # Logs when the bot starts running
    @client.event
    async def on_ready():
        await log(client, "Reporting for duty.")
        return

    # Welcomes new members and dumps out member info to bot log on join.
    @client.event
    async def on_member_join(member: discord.Member):
        join_embed = discord.Embed(title="Member Joined",
                                   description=f"ID: {member.id}",
                                   color=0x0099ff)
        join_embed.set_author(name=f"{member.name}#{member.discriminator}",
                              icon_url=member.avatar_url)
        join_embed.set_thumbnail(url=member.avatar_url)
        join_embed.add_field(name="Join Time", value=member.joined_at.isoformat(sep="\n"))
        join_embed.add_field(name="Creation Time", value=member.created_at.isoformat(sep="\n"))
        join_embed.add_field(name="Has avatar?", value=("True" if member.avatar else "False"))
        join_embed.add_field(name="Flags", value=str(list(map(lambda f: f.name, member.public_flags.all()))))

        chan = client.get_channel(config.BOT_LOGS)
        await chan.send(embed=join_embed)

        if member.bot:
            return
        channel = client.get_channel(config.WELCOME_CHANNEL)
        await channel.send(config.WELCOME_MESSAGE.format(member.mention))
        return

    # Dump out member info when a member leaves
    @client.event
    async def on_member_remove(member: discord.Member):
        leave_embed = discord.Embed(title="Member Left",
                                    description=f"ID: {member.id}",
                                    color=0xff5733)
        leave_embed.set_author(name=f"{member.name}#{member.discriminator}",
                               icon_url=member.avatar_url)
        leave_embed.set_thumbnail(url=member.avatar_url)
        leave_embed.add_field(name="Leave Time", value=datetime.now().isoformat(sep="\n"))
        leave_embed.add_field(name="Creation Time", value=member.created_at.isoformat(sep="\n"))
        leave_embed.add_field(name="Has avatar?", value=("True" if member.avatar else "False"))
        leave_embed.add_field(name="Flags", value=str(list(map(lambda f: f.name, member.public_flags.all()))))

        chan = client.get_channel(config.BOT_LOGS)
        await chan.send(embed=leave_embed)
        return


    #Reaction Roles
    @client.event
    async def on_raw_reaction_add(payload):
        channel = client.get_channel(config.ROLES_CHANNEL)
        if payload.channel_id != channel.id:
            return
        if payload.emoji.is_custom_emoji:
            role_reaction = config.REACTION_ROLES.get(payload.emoji.name, None)
            if role_reaction is not None:
                api_role = payload.member.guild.get_role(role_reaction)
                await payload.member.add_roles(api_role)
                return
        else:
            role_reaction = config.REACTION_ROLES.get(str(payload.emoji), None)
            if role_reaction is not None:
                api_role = payload.member.guild.get_role(role_reaction)
                await payload.member.add_roles(api_role)
                return

    #Remove Reaction Roles
    @client.event
    async def on_raw_reaction_remove(payload):
        channel = client.get_channel(config.ROLES_CHANNEL)
        if payload.channel_id != channel.id:
            return
        guild = client.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if payload.emoji.is_custom_emoji:
            role_reaction = config.REACTION_ROLES.get(payload.emoji.name, None)
            if role_reaction is not None:
                api_role = guild.get_role(role_reaction)
                await member.remove_roles(api_role)
                return
        else:
            role_reaction = config.REACTION_ROLES.get(str(payload.emoji), None)
            if role_reaction is not None:
                api_role = guild.get_role(role_reaction)
                await member.remove_roles(api_role)
                return


    # add role
    @client.command()
    async def add(ctx: commands.Context, subcommand):
        if not allowed(ctx.author):
            await log(client, f"BLOCKED: {ctx.author.mention} attempted '{ctx.message.content}'")
            await ctx.message.add_reaction("⛔")
            await ctx.reply("Permission denied")
            return

        await log(client, f"{str(ctx.author)}: executed {ctx.message.content}")

        role_list = config.ROLES.get(subcommand, None)
        if role_list is None:
            await log(client, f"Exception: {ctx.author.mention}; No such command {subcommand}")
            await ctx.message.add_reaction("⛔")
            return

        for role in role_list:
            api_role = ctx.guild.get_role(role)
            try:
                for user in ctx.message.mentions:
                    await user.add_roles(api_role)
                    pass
            except discord.HTTPException as e:
                await log(client, f"Exception: {ctx.author.mention}; {e.text}")
            await ctx.message.add_reaction("✅")

    # remove role
    @client.command()
    async def remove(ctx: commands.Context, subcommand):
        if not allowed(ctx.author):
            await log(client, f"BLOCKED: {ctx.author.mention} attempted '{ctx.message.content}'")
            await ctx.message.add_reaction("⛔")
            await ctx.reply("Permission denied")
            return

        await log(client, f"{str(ctx.author)}: executed {ctx.message.content}")

        role_list = config.ROLES.get(subcommand, None)
        if role_list is None:
            await log(client, f"Exception: {ctx.author.mention}; No such command {subcommand}")
            await ctx.message.add_reaction("⛔")
            return

        for role in role_list:
            api_role = ctx.guild.get_role(role)
            try:
                for user in ctx.message.mentions:
                    await user.remove_roles(api_role)
                    pass
            except discord.HTTPException as e:
                await log(client, f"Exception: {ctx.author.mention}; {e.text}")
        await ctx.message.add_reaction("✅")

    # Test command do not use
    @client.command()
    async def test(ctx):
        if not allowed(ctx.author):
            await ctx.reply("Permission denied")
        else:
            await ctx.message.add_reaction(":white_check_mark:")
        return

    client.run(config.DISCORD_API_TOKEN)
    return


if __name__ == '__main__':
    main()
