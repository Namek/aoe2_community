using Bot.Utils;
using Microsoft.Extensions.Logging;
using Remora.Discord.API.Abstractions.Gateway.Events;
using Remora.Discord.API.Abstractions.Rest;
using Remora.Discord.Gateway.Responders;
using Remora.Results;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Bot.Calendar {
    public class ReadyResponder : IResponder<IReady> {
        private MessageAPIs _ctx;

        public ReadyResponder(MessageAPIs ctx) {
            _ctx = ctx;
        }

        public async Task<Result> RespondAsync(IReady evt, CancellationToken ct = default) {
            var guilds = evt.Guilds
                .Select(async g => await _ctx.guildAPI.GetGuildAsync(g.GuildID))
                .Select(g => g.Result.Entity)
                .ToArray();

            var guildNames = guilds
                .Select(g => g.Name)
                .ToArray();

            _ctx.logger.LogInformation($"User is connected to the following guilds: {string.Join(", ", guildNames)}");
            var guild = guilds.FirstOrDefault(g => Config.IsConfiguredGuild(g.ID.Value));
            if (guild == null || guild.IsUnavailable == true) {
                return Result.FromError(new NotFoundError($"Guild {Config.GuildId} not found"));
            }
            _ctx.logger.LogInformation($"...but only using the {guild.Name} (id: {guild.ID})");

            var channels = (await _ctx.guildAPI.GetGuildChannelsAsync(guild.ID, ct)).Entity
                .Where(ch => Config.ChannelNames.Any(name => name == ch.Name));

            _ctx.logger.LogInformation("channels to analyze: " + string.Join(", ", channels.Select(ch => ch.Name)));

            foreach (var channel in channels) {
                var messagesResult = (await _ctx.channelAPI.GetChannelMessagesAsync(channel.ID, ct: ct));
                _ctx.logger.LogInformation($"Messages for {channel.Name}: {messagesResult.Entity?.Count ?? 0}");

                if (messagesResult.IsSuccess && messagesResult.Entity != null) {
                    foreach (var msg in messagesResult.Entity) {
                        using (var db = Database.Database.NewConnection()) {
                            await MessageProcessing.ProcessMessage(_ctx, db, msg.ID.Value, msg.Content, msg.Timestamp.DateTime, channel.GuildID.Value.Value, msg.ChannelID.Value, channel.Name.Value);
                        }
                    }
                } else {
                    _ctx.logger.LogError(messagesResult.Error?.Message ?? $"get channel {channel.Name} messages: unknown error");
                }
            }

            using (var db = Database.Database.NewConnection()) {
                MessageProcessing.DeleteOldEvents(db);
            }

            return Result.FromSuccess();
        }
    }

    public record MessageAPIs(IDiscordRestGuildAPI guildAPI, IDiscordRestChannelAPI channelAPI, IDiscordRestUserAPI userAPI, ILogger<ReadyResponder> logger);
}
