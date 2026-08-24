# cogs/ticket.py

import sqlite3
import discord

from discord.ext import commands
from discord import app_commands


DB = "ticket.db"


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="티켓 열기",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="ticket:open"
    )
    async def open(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        cog = interaction.client.get_cog("Ticket")

        if cog:
            await cog.create_ticket(interaction)


class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="티켓 닫기",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:close"
    )
    async def close(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        cog = interaction.client.get_cog("Ticket")

        if cog:
            await cog.close_ticket(interaction)


class Ticket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect(DB)
        self.db.row_factory = sqlite3.Row

        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS ticket_config (
                guild_id INTEGER PRIMARY KEY,

                category_id INTEGER NOT NULL,
                panel_channel_id INTEGER,

                support_role_id INTEGER,

                panel_message_id INTEGER,

                name_prefix TEXT DEFAULT 'ticket',
                max_tickets INTEGER DEFAULT 1,

                allow_user_close INTEGER DEFAULT 1,
                allow_admin_close INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS tickets (
                channel_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        self.db.commit()

        # persistent view
        self.bot.add_view(TicketView())
        self.bot.add_view(CloseView())

    def cog_unload(self):
        self.db.close()

    # --------------------------------------------------
    # DB
    # --------------------------------------------------

    def config(self, guild_id: int):
        return self.db.execute(
            """
            SELECT *
            FROM ticket_config
            WHERE guild_id = ?
            """,
            (guild_id,)
        ).fetchone()

    def ticket(self, channel_id: int):
        return self.db.execute(
            """
            SELECT *
            FROM tickets
            WHERE channel_id = ?
            """,
            (channel_id,)
        ).fetchone()

    def user_tickets(self, guild_id: int, user_id: int):
        return self.db.execute(
            """
            SELECT *
            FROM tickets
            WHERE guild_id = ?
            AND user_id = ?
            """,
            (guild_id, user_id)
        ).fetchall()

    # --------------------------------------------------
    # 설정
    # --------------------------------------------------

    @app_commands.command(
        name="티켓설정",
        description="티켓 설정을 변경합니다."
    )
    @app_commands.describe(
        category="티켓이 생성될 카테고리",
        support_role="티켓을 볼 수 있는 관리자 역할",
        max_tickets="한 사람이 동시에 만들 수 있는 티켓 수",
        name_prefix="티켓 채널 이름 앞부분"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setting(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        support_role: discord.Role,
        max_tickets: app_commands.Range[int, 1, 10] = 1,
        name_prefix: str = "ticket"
    ):
        old = self.config(interaction.guild.id)

        panel_channel_id = old["panel_channel_id"] if old else None
        panel_message_id = old["panel_message_id"] if old else None

        self.db.execute(
            """
            INSERT INTO ticket_config (
                guild_id,
                category_id,
                panel_channel_id,
                support_role_id,
                panel_message_id,
                name_prefix,
                max_tickets
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(guild_id)
            DO UPDATE SET
                category_id = excluded.category_id,
                support_role_id = excluded.support_role_id,
                name_prefix = excluded.name_prefix,
                max_tickets = excluded.max_tickets
            """,
            (
                interaction.guild.id,
                category.id,
                panel_channel_id,
                support_role.id,
                panel_message_id,
                name_prefix,
                max_tickets
            )
        )

        self.db.commit()

        await interaction.response.send_message(
            "티켓 설정을 저장했어요.\n\n"
            f"**카테고리** › {category.mention}\n"
            f"**열람 역할** › {support_role.mention}\n"
            f"**최대 티켓** › {max_tickets}개\n"
            f"**이름** › `{name_prefix}-사용자명`",
            ephemeral=True
        )

    # --------------------------------------------------
    # 패널
    # --------------------------------------------------

    @app_commands.command(
        name="티켓패널",
        description="현재 채널에 티켓 패널을 생성합니다."
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def panel(self, interaction: discord.Interaction):
        config = self.config(interaction.guild.id)

        if config is None:
            return await interaction.response.send_message(
                "`/티켓설정`을 먼저 해주세요.",
                ephemeral=True
            )

        embed = discord.Embed(
            title="문의 티켓",
            description=(
                "문의가 필요하다면 아래 버튼을 눌러주세요.\n\n"
                "🎫 **티켓 열기**\n"
                "개인 문의 채널이 생성됩니다."
            ),
            color=discord.Color.blurple()
        )

        message = await interaction.channel.send(
            embed=embed,
            view=TicketView()
        )

        self.db.execute(
            """
            UPDATE ticket_config
            SET
                panel_channel_id = ?,
                panel_message_id = ?
            WHERE guild_id = ?
            """,
            (
                interaction.channel.id,
                message.id,
                interaction.guild.id
            )
        )

        self.db.commit()

        await interaction.response.send_message(
            "티켓 패널을 생성했어요.",
            ephemeral=True
        )

    # --------------------------------------------------
    # 티켓 생성
    # --------------------------------------------------

    async def create_ticket(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        config = self.config(interaction.guild.id)

        if config is None:
            return await interaction.response.send_message(
                "티켓 설정이 되어있지 않아요.",
                ephemeral=True
            )

        category = interaction.guild.get_channel(
            config["category_id"]
        )

        if not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "티켓 카테고리를 찾을 수 없어요.",
                ephemeral=True
            )

        current = self.user_tickets(
            interaction.guild.id,
            interaction.user.id
        )

        # DB에는 남아있지만 실제 채널이 삭제된 경우 정리
        valid = []

        for ticket in current:
            channel = interaction.guild.get_channel(
                ticket["channel_id"]
            )

            if channel:
                valid.append(channel)
            else:
                self.db.execute(
                    """
                    DELETE FROM tickets
                    WHERE channel_id = ?
                    """,
                    (ticket["channel_id"],)
                )

        self.db.commit()

        if len(valid) >= config["max_tickets"]:
            mentions = "\n".join(
                channel.mention for channel in valid
            )

            return await interaction.response.send_message(
                f"이미 열려있는 티켓이 있어요.\n{mentions}",
                ephemeral=True
            )

        support_role = interaction.guild.get_role(
            config["support_role_id"]
        )

        overwrites = {
            interaction.guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),

            interaction.user:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                ),

            interaction.guild.me:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_messages=True
                )
        }

        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )

        await interaction.response.defer(ephemeral=True)

        name = f"{config['name_prefix']}-{interaction.user.name}"

        channel = await interaction.guild.create_text_channel(
            name=name[:100],
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created by {interaction.user}"
        )

        self.db.execute(
            """
            INSERT INTO tickets (
                channel_id,
                guild_id,
                user_id
            )
            VALUES (?, ?, ?)
            """,
            (
                channel.id,
                interaction.guild.id,
                interaction.user.id
            )
        )

        self.db.commit()

        embed = discord.Embed(
            title="티켓이 생성되었습니다.",
            description=(
                f"{interaction.user.mention}님의 문의 채널입니다.\n\n"
                "문의 내용을 남겨주세요.\n"
                "문의가 끝났다면 아래 버튼으로 티켓을 닫을 수 있습니다."
            ),
            color=discord.Color.green()
        )

        await channel.send(
            content=interaction.user.mention,
            embed=embed,
            view=CloseView()
        )

        await interaction.followup.send(
            f"티켓을 생성했어요. {channel.mention}",
            ephemeral=True
        )

    # --------------------------------------------------
    # 티켓 닫기
    # --------------------------------------------------

    async def close_ticket(self, interaction: discord.Interaction):
        if not interaction.guild:
            return

        ticket = self.ticket(interaction.channel.id)

        if ticket is None:
            return await interaction.response.send_message(
                "티켓 채널이 아니에요.",
                ephemeral=True
            )

        config = self.config(interaction.guild.id)

        is_owner = ticket["user_id"] == interaction.user.id

        is_admin = interaction.user.guild_permissions.manage_channels

        support = (
            config
            and config["support_role_id"]
            and interaction.guild.get_role(
                config["support_role_id"]
            )
            and interaction.guild.get_role(
                config["support_role_id"]
            ) in interaction.user.roles
        )

        if is_owner:
            if not config["allow_user_close"]:
                return await interaction.response.send_message(
                    "티켓을 닫을 수 없어요.",
                    ephemeral=True
                )

        elif support or is_admin:
            if not config["allow_admin_close"]:
                return await interaction.response.send_message(
                    "티켓을 닫을 수 없어요.",
                    ephemeral=True
                )

        else:
            return await interaction.response.send_message(
                "티켓을 닫을 권한이 없어요.",
                ephemeral=True
            )

        await interaction.response.send_message(
            "티켓을 닫는 중이에요.",
            ephemeral=True
        )

        self.db.execute(
            """
            DELETE FROM tickets
            WHERE channel_id = ?
            """,
            (interaction.channel.id,)
        )

        self.db.commit()

        await interaction.channel.delete(
            reason=f"Ticket closed by {interaction.user}"
        )

    # --------------------------------------------------
    # 채널이 외부에서 삭제됐을 때 DB 정리
    # --------------------------------------------------

    @commands.Cog.listener()
    async def on_guild_channel_delete(
        self,
        channel: discord.abc.GuildChannel
    ):
        self.db.execute(
            """
            DELETE FROM tickets
            WHERE channel_id = ?
            """,
            (channel.id,)
        )

        self.db.commit()


async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))