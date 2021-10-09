using Bot.Utils;
using Remora.Discord.API.Abstractions.Gateway.Events;
using Remora.Discord.API.Abstractions.Rest;
using Remora.Discord.Gateway.Responders;
using Remora.Results;
using System.Threading;
using System.Threading.Tasks;

namespace Bot.Calendar {
    public class MessageUpdateResponder : IResponder<IMessageUpdate> {
        private readonly MessageAPIs _apis;

        public MessageUpdateResponder(MessageAPIs apis) {
            _apis = apis;
        }

        public async Task<Result> RespondAsync(IMessageUpdate msg, CancellationToken ct = default) {
            if ((msg.Author.Value.IsBot.IsDefined(out var isBot) && isBot) ||
                (msg.Author.Value.IsSystem.IsDefined(out var isSystem) && isSystem)) {
                return Result.FromSuccess();
            }

            if (msg.ID.IsDefined(out var id)
                && msg.Timestamp.IsDefined(out var date)
                && date != null
                && msg.ChannelID.IsDefined(out var channelId)
                && msg.GuildID.IsDefined(out var guildId)
            ) {
                var channel = await _apis.channelAPI.GetChannelAsync(channelId, ct);

                if (!msg.IsPinned.Value && Config.IsFromConfiguredChannels(guildId.Value, channel.Entity.Name)) {
                    using var db = Database.Database.NewConnection();
                    await MessageProcessing.ProcessMessage(_apis, db, id.Value, msg.Content.Value, date.UtcDateTime, guildId.Value, channelId.Value, channel.Entity.Name.Value);
                }
            }

            return Result.FromSuccess();
        }
    }


}
