import asyncio
import json
import os
from os import makedirs, path

import discord
import openai
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

load_dotenv()
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
openai.api_key = os.environ["OPENAI_API_KEY"]


def ChatGPT_core(content, system=False, user=None, send_response=True):
    jsonfile = f"./log/{user}/log.json"

    def validate_file_and_mkdir():
        try:
            if path.isfile(f"./log/{user}") is False:
                makedirs(f"./log/{user}")
        except FileExistsError:
            print("すでに存在するファイルのため、ファイルの作成をスキップしました。")
        with open(jsonfile, "w", encoding="utf-8") as f:
            json.dump([], f)

    validate_file_and_mkdir()

    def write_log(log):
        with open(jsonfile, encoding="utf-8") as f:
            listObj = []
            listObj = json.load(f)
            listObj.append(log)
        with open(jsonfile, "w", encoding="utf-8") as f:
            json.dump(listObj, f, indent=4, separators=(",", ": "), ensure_ascii=False)

    messages = {"role": "user", "content": content}
    if system == True:
        messages = {"role": "system", "content": content}

    log = messages
    write_log(log)

    if send_response == True:
        with open(jsonfile, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=loaded)

        res = response["choices"][0]["message"]["content"]
        log = {"role": "assistant", "content": res}
        write_log(log)

        return res


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Bot is Online!")


class Discord:
    chatgpt = discord.SlashCommandGroup(name="chatgpt", description="root commands")
    general = chatgpt.create_subgroup("general", description="general commands")
    setting = chatgpt.create_subgroup("setting", description="setting commands")
    debug = chatgpt.create_subgroup("debug", description="debug commands")

    bot.add_application_command(chatgpt)

    @general.command(name="chat", description="ChatGPTに質問したい時のコマンドです。")
    async def chat(
        ctx: discord.Interaction,
        content: discord.Option(
            discord.SlashCommandOptionType.string, "質問したい内容を記述してください"
        ),
    ):
        await ctx.response.defer(ephemeral=False)
        result = ChatGPT_core(content, False, ctx.user.id)

        await ctx.respond(result)

    @general.command(name="system", description="ChatGPTに定義したい時のコマンドです。")
    async def system(
        ctx: discord.Interaction,
        content: discord.Option(
            discord.SlashCommandOptionType.string,
            description="何を定義しますか？",
            choices=["You are a helpful assistant."],
        ),
        if_send: discord.Option(
            discord.SlashCommandOptionType.boolean, "定義と同時に、送信したい場合は `True` に設定してください"
        ) = False,
    ):
        await ctx.response.defer(ephemeral=False)
        result = ChatGPT_core(content, True, ctx.user.id, if_send)

        if if_send == True:
            await ctx.respond(result)
        else:
            await ctx.respond("ChatGPTに定義を設定しました。")

    @debug.command(name="ping", description="Botにpingを送信します。")
    async def ping(ctx):
        async with ctx.typing():
            await asyncio.sleep(2)

        await ctx.respond(f"pong!私が応答するのに、{bot.latency}msかかりました。")

    @setting.command(name="initialize_log", description="ログを初期化します。")
    async def initialize_log(ctx):
        try:
            if path.isfile(f"./log/{ctx.user.id}") is False:
                makedirs(f"./log/{ctx.user.id}")
        except FileExistsError:
            print("すでに存在するファイルのため、ファイルの作成をスキップしました。")
        with open(f"./log/{ctx.user.id}/log.json", "w", encoding="utf-8") as f:
            json.dump([], f)
        await ctx.respond("ログを初期化しました。")

    bot.run(DISCORD_TOKEN)
