using Bot.Utils;
using Remora.Discord.API.Abstractions.Gateway.Events;
using Remora.Discord.API.Abstractions.Rest;
using Remora.Discord.Core;
using Remora.Discord.Gateway.Responders;
using Remora.Results;
using System.Threading;
using System.Threading.Tasks;

namespace Bot.Calendar {
    public class MessageCreateResponder : IResponder<IMessageCreate> {
        private readonly MessageAPIs _apis;

        public MessageCreateResponder(MessageAPIs apis) {
            _apis = apis;
        }

        public async Task<Result> RespondAsync(IMessageCreate msg, CancellationToken ct = default) {
            if ((msg.Author.IsBot.IsDefined(out var isBot) && isBot) ||
                (msg.Author.IsSystem.IsDefined(out var isSystem) && isSystem)) {
                return Result.FromSuccess();
            }

            var channel = await _apis.channelAPI.GetChannelAsync(msg.ChannelID, ct);
            var guildId = msg.GuildID.HasValue ? new Optional<ulong>(msg.GuildID.Value.Value) : new Optional<ulong>();

            if (!msg.IsPinned && Config.IsFromConfiguredChannels(guildId, channel.Entity.Name)) {
                using var db = Database.Database.NewConnection();
                await MessageProcessing.ProcessMessage(_apis, db, msg.ID.Value, msg.Content, msg.Timestamp.UtcDateTime, guildId.Value, msg.ChannelID.Value, channel.Entity.Name.Value);
            }

            return Result.FromSuccess();
        }
    }
}
