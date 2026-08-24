import sqlite3

import discord
from discord import app_commands
from discord.ext import commands


DB = "role_giver.db"


class RoleButton(discord.ui.Button):
    def __init__(
        self,
        role_id: int,
        label: str,
        emoji: str | None = None
    ):
        super().__init__(
            label=label,
            emoji=emoji,
            style=discord.ButtonStyle.secondary,
            custom_id=f"role_giver:{role_id}"
        )

        self.role_id = role_id

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        cog = interaction.client.get_cog("RoleGiver")

        if cog:
            await cog.toggle_role(
                interaction,
                self.role_id
            )


class RoleView(discord.ui.View):
    def __init__(self, buttons=None):
        super().__init__(timeout=None)

        if buttons:
            for button in buttons:
                self.add_item(
                    RoleButton(
                        role_id=button["role_id"],
                        label=button["label"],
                        emoji=button["emoji"]
                    )
                )


class RoleGiver(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.db = sqlite3.connect(DB)
        self.db.row_factory = sqlite3.Row

        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS panels (
                message_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS buttons (
                message_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                emoji TEXT,
                PRIMARY KEY (message_id, role_id)
            );
        """)

        self.db.commit()

        self.restore_views()

    def cog_unload(self):
        self.db.close()

    # =========================
    # DB
    # =========================

    def get_panel(self, message_id: int):
        return self.db.execute(
            """
            SELECT *
            FROM panels
            WHERE message_id = ?
            """,
            (message_id,)
        ).fetchone()

    def get_buttons(self, message_id: int):
        return self.db.execute(
            """
            SELECT *
            FROM buttons
            WHERE message_id = ?
            ORDER BY rowid
            """,
            (message_id,)
        ).fetchall()

    # =========================
    # Persistent View
    # =========================

    def restore_views(self):
        panels = self.db.execute(
            """
            SELECT message_id
            FROM panels
            """
        ).fetchall()

        for panel in panels:
            buttons = self.get_buttons(
                panel["message_id"]
            )

            self.bot.add_view(
                RoleView(buttons),
                message_id=panel["message_id"]
            )

    # =========================
    # 룰기버
    # =========================

    @app_commands.command(
        name="룰기버",
        description="역할 선택 패널을 관리합니다."
    )
    @app_commands.describe(
        action="실행할 작업",
        message_id="역할을 추가할 패널의 메시지 ID",
        role="지급할 역할",
        label="버튼에 표시할 이름",
        emoji="버튼 이모지"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(
                name="패널 생성",
                value="create"
            ),
            app_commands.Choice(
                name="역할 추가",
                value="add"
            )
        ]
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def role_giver(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        message_id: str | None = None,
        role: discord.Role | None = None,
        label: str | None = None,
        emoji: str | None = None
    ):
        if action.value == "create":
            await self.create_panel(interaction)
            return

        if action.value == "add":
            await self.add_role(
                interaction,
                message_id,
                role,
                label,
                emoji
            )

    # =========================
    # 패널 생성
    # =========================

    async def create_panel(
        self,
        interaction: discord.Interaction
    ):
        embed = discord.Embed(
            title="역할 선택",
            description=(
                "원하는 역할의 버튼을 눌러주세요.\n"
                "이미 가지고 있는 역할을 누르면 역할이 제거됩니다."
            ),
            color=discord.Color.blurple()
        )

        message = await interaction.channel.send(
            embed=embed,
            view=RoleView()
        )

        self.db.execute(
            """
            INSERT INTO panels (
                message_id,
                guild_id,
                channel_id
            )
            VALUES (?, ?, ?)
            """,
            (
                message.id,
                interaction.guild.id,
                interaction.channel.id
            )
        )

        self.db.commit()

        await interaction.response.send_message(
            "역할 패널을 만들었어요.",
            ephemeral=True
        )

    # =========================
    # 역할 추가
    # =========================

    async def add_role(
        self,
        interaction: discord.Interaction,
        message_id: str | None,
        role: discord.Role | None,
        label: str | None,
        emoji: str | None
    ):
        if not message_id:
            return await interaction.response.send_message(
                "`message_id`를 입력해주세요.",
                ephemeral=True
            )

        if role is None:
            return await interaction.response.send_message(
                "`role`을 입력해주세요.",
                ephemeral=True
            )

        if not label:
            return await interaction.response.send_message(
                "`label`을 입력해주세요.",
                ephemeral=True
            )

        try:
            message_id = int(message_id)
        except ValueError:
            return await interaction.response.send_message(
                "메시지 ID가 올바르지 않아요.",
                ephemeral=True
            )

        panel = self.get_panel(message_id)

        if panel is None:
            return await interaction.response.send_message(
                "등록된 역할 패널이 아니에요.",
                ephemeral=True
            )

        if panel["guild_id"] != interaction.guild.id:
            return await interaction.response.send_message(
                "이 서버의 패널이 아니에요.",
                ephemeral=True
            )

        if role.is_default():
            return await interaction.response.send_message(
                "@everyone은 사용할 수 없어요.",
                ephemeral=True
            )

        if role.managed:
            return await interaction.response.send_message(
                "봇이나 연동 서비스가 관리하는 역할은 사용할 수 없어요.",
                ephemeral=True
            )

        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                "봇보다 높거나 같은 역할은 지급할 수 없어요.",
                ephemeral=True
            )

        self.db.execute(
            """
            INSERT OR REPLACE INTO buttons (
                message_id,
                role_id,
                label,
                emoji
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                message_id,
                role.id,
                label,
                emoji
            )
        )

        self.db.commit()

        channel = interaction.guild.get_channel(
            panel["channel_id"]
        )

        if channel is None:
            return await interaction.response.send_message(
                "패널 채널을 찾을 수 없어요.",
                ephemeral=True
            )

        try:
            message = await channel.fetch_message(
                message_id
            )
        except discord.NotFound:
            return await interaction.response.send_message(
                "패널 메시지를 찾을 수 없어요.",
                ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "패널 메시지를 확인할 권한이 없어요.",
                ephemeral=True
            )

        buttons = self.get_buttons(message_id)

        await message.edit(
            view=RoleView(buttons)
        )

        self.bot.add_view(
            RoleView(buttons),
            message_id=message_id
        )

        await interaction.response.send_message(
            f"{role.mention} 역할 버튼을 추가했어요.",
            ephemeral=True
        )

    # =========================
    # 역할 지급 / 제거
    # =========================

    async def toggle_role(
        self,
        interaction: discord.Interaction,
        role_id: int
    ):
        if interaction.guild is None:
            return

        role = interaction.guild.get_role(role_id)

        if role is None:
            return await interaction.response.send_message(
                "이 역할은 더 이상 존재하지 않아요.",
                ephemeral=True
            )

        if role.is_default() or role.managed:
            return await interaction.response.send_message(
                "이 역할은 사용할 수 없어요.",
                ephemeral=True
            )

        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                "봇이 이 역할을 관리할 수 없어요.",
                ephemeral=True
            )

        member = interaction.user

        try:
            if role in member.roles:
                await member.remove_roles(
                    role,
                    reason="Role giver"
                )

                await interaction.response.send_message(
                    f"{role.mention} 역할을 제거했어요.",
                    ephemeral=True
                )

            else:
                await member.add_roles(
                    role,
                    reason="Role giver"
                )

                await interaction.response.send_message(
                    f"{role.mention} 역할을 지급했어요.",
                    ephemeral=True
                )

        except discord.Forbidden:
            await interaction.response.send_message(
                "역할을 변경할 권한이 없어요.",
                ephemeral=True
            )

    # =========================
    # 패널 삭제 감지
    # =========================

    @commands.Cog.listener()
    async def on_message_delete(
        self,
        message: discord.Message
    ):
        panel = self.get_panel(message.id)

        if panel is None:
            return

        self.db.execute(
            """
            DELETE FROM buttons
            WHERE message_id = ?
            """,
            (message.id,)
        )

        self.db.execute(
            """
            DELETE FROM panels
            WHERE message_id = ?
            """,
            (message.id,)
        )

        self.db.commit()

    # =========================
    # 패널 채널 삭제 감지
    # =========================

    @commands.Cog.listener()
    async def on_guild_channel_delete(
        self,
        channel: discord.abc.GuildChannel
    ):
        panels = self.db.execute(
            """
            SELECT message_id
            FROM panels
            WHERE channel_id = ?
            """,
            (channel.id,)
        ).fetchall()

        for panel in panels:
            self.db.execute(
                """
                DELETE FROM buttons
                WHERE message_id = ?
                """,
                (panel["message_id"],)
            )

            self.db.execute(
                """
                DELETE FROM panels
                WHERE message_id = ?
                """,
                (panel["message_id"],)
            )

        self.db.commit()


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleGiver(bot))