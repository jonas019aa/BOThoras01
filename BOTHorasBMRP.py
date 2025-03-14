import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

monitored_channels = []
monitored_roles = {}
user_voice_start = {}
user_total_time = {}

@bot.event
async def on_ready():
    print(f'Logado como {bot.user}')

@bot.command()
async def cfghoras(ctx):
    await ctx.send("Informe o ID dos canais de voz que precisarão ser monitorados (separados por ponto e vírgula `;`):")
    
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel
    
    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        global monitored_channels
        monitored_channels = [int(ch.strip()) for ch in msg.content.split(';')]
        
        await ctx.send("Canais configurados com sucesso! Agora, informe o ID do cargo que deve ser monitorado:")
        
        msg = await bot.wait_for("message", check=check, timeout=60)
        role_id = int(msg.content.strip())
        
        monitored_roles[role_id] = monitored_channels
        await ctx.send("Configuração concluída com sucesso! O monitoramento está ativo.")
    except asyncio.TimeoutError:
        await ctx.send("Tempo esgotado! Execute o comando novamente para configurar.")
    except ValueError:
        await ctx.send("IDs inválidos! Certifique-se de inserir números corretos.")

@bot.command()
async def verify(ctx):
    if not monitored_channels:
        await ctx.send("Nenhum canal monitorado.")
        return
    
    response = "🔍 **Configurações Atuais:**\n\n"
    response += "🎙 **Canais Monitorados:**\n"
    for channel_id in monitored_channels:
        channel = bot.get_channel(channel_id)
        channel_name = channel.name if channel else "Desconhecido"
        response += f"- {channel_name} (ID: {channel_id})\n"
    
    if monitored_roles:
        response += "\n👥 **Cargos Vinculados:**\n"
        for role_id, channels in monitored_roles.items():
            role = ctx.guild.get_role(role_id)
            role_name = role.name if role else "Desconhecido"
            channel_names = [bot.get_channel(ch).name if bot.get_channel(ch) else "Desconhecido" for ch in channels]
            response += f"- Cargo: {role_name} (ID: {role_id})\n  ↳ Canais: {', '.join(channel_names)}\n"
    
    await ctx.send(response)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:  # Entrando no canal
        if after.channel.id in monitored_channels:
            user_voice_start[member.id] = asyncio.get_event_loop().time()
    elif before.channel is not None and after.channel is None:  # Saindo do canal
        if before.channel.id in monitored_channels and member.id in user_voice_start:
            time_spent = asyncio.get_event_loop().time() - user_voice_start.pop(member.id, 0)
            user_total_time[member.id] = user_total_time.get(member.id, 0) + time_spent
            print(f"{member.display_name} passou {time_spent:.2f} segundos no canal {before.channel.name}.")

@bot.command()
async def rank10(ctx):
    if not user_total_time:
        await ctx.send("Nenhum usuário tem tempo registrado ainda.")
        return
    
    sorted_users = sorted(user_total_time.items(), key=lambda x: x[1], reverse=True)[:10]
    
    embed = discord.Embed(title="🏆 **Top 10 Usuários com Mais Tempo em Voz**", color=discord.Color.gold())
    for i, (user_id, time_spent) in enumerate(sorted_users, 1):
        # Tentando recuperar o membro pelo ID
        member = ctx.guild.get_member(user_id)
        # Se o membro não for encontrado, tentamos usar o nome de usuário diretamente
        username = member.display_name if member else f"Desconhecido (ID: {user_id})"
        
        hours = int(time_spent // 3600)
        minutes = int((time_spent % 3600) // 60)
        embed.add_field(name=f"{i}. {username}", value=f"{hours}h {minutes}m", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def htotal(ctx):
    if not user_total_time:
        await ctx.send("Nenhum usuário tem tempo registrado ainda.")
        return
    
    embed = discord.Embed(title="⏳ **Tempo Total em Voz de Todos os Usuários**", color=discord.Color.green())
    
    # Ordena os usuários por tempo em ordem decrescente
    sorted_users = sorted(user_total_time.items(), key=lambda x: x[1], reverse=True)
    
    for user_id, time_spent in sorted_users:
        # Tentando recuperar o membro pelo ID
        member = ctx.guild.get_member(user_id)
        # Se o membro não for encontrado, tentamos usar o nome de usuário diretamente
        username = member.display_name if member else f"Desconhecido (ID: {user_id})"
        
        hours = int(time_spent // 3600)
        minutes = int((time_spent % 3600) // 60)
        
        # Adiciona a informação de tempo do usuário ao embed
        embed.add_field(name=username, value=f"{hours}h {minutes}m", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def meurank(ctx):
    user_id = ctx.author.id
    time_spent = user_total_time.get(user_id, 0)
    
    hours = int(time_spent // 3600)
    minutes = int((time_spent % 3600) // 60)
    
    embed = discord.Embed(title=f"👤 **Seu Rank - {ctx.author.display_name}**", color=discord.Color.blue())
    embed.add_field(name="Tempo em Voz", value=f"{hours}h {minutes}m", inline=False)
    
    await ctx.send(embed=embed)

# Comando para resetar as horas
@bot.command()
async def resethoras(ctx):
    global user_total_time, user_voice_start
    user_total_time.clear()  # Limpa as horas registradas
    user_voice_start.clear()  # Limpa os registros de entrada nas calls
    await ctx.send("Horas de todos os usuários foram zeradas com sucesso!")

bot.run("MTM0OTU1MDQ5NDUyMzMzMDYwMQ.GLi6aO.bOkyIwRelQ6DezDWt_El_pZ4kMFO8CqThiCPgM")
