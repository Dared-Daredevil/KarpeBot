# Bad command
# yes me is aware this is litterary the thanks but no thank
@bot.command(aliases=[], help="""
Thanks the specified user
Usage:
    - `badboi @user`
    - `badboi <user id>`
""")
async def badboi(ctx: commands.Context, member: commands.MemberConverter):
    if not member:
        await ctx.send("He was such a bad boi that he doesnt even exist anymore.")
        return
    if member.guild != ctx.guild:
        return
    if member.id == bot.user.id:
        await ctx.send("...No.")
        return
    if member.id == ctx.author.id:
        await ctx.send("yay dirty talk")
        return
    #if ctx.author.top_role.position <= member.top_role.position:
    #    await ctx.send("theres no reason for this shit to be in a comment but fine dick ass")
    #    return
    if not ctx.author.guild_permissions.manage_messages:
        return
    embed = discord.Embed(title = f"{ctx.author.name} has rekt {member.name}", description = "", color = discord.Colour(0x0088FF))
    await ctx.send(embed=embed)
