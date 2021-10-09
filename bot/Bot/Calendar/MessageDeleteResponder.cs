using Microsoft.Extensions.Configuration;
using Remora.Discord.API.Abstractions.Gateway.Events;
using Remora.Discord.API.Abstractions.Rest;
using Remora.Discord.Gateway.Responders;
using Remora.Results;
using System.Threading;
using System.Threading.Tasks;

namespace Bot.Calendar {
    public class MessageDeleteResponder : IResponder<IMessageDelete> {
        private readonly IDiscordRestChannelAPI _channelAPI;
        private readonly IConfiguration _cfg;

        public MessageDeleteResponder(IDiscordRestChannelAPI channelAPI, IConfiguration cfg) {
            _channelAPI = channelAPI;
            _cfg = cfg;
        }

        public async Task<Result> RespondAsync(IMessageDelete evt, CancellationToken ct = default) {
            using (var db = Database.Database.NewConnection()) {
                MessageProcessing.DeleteMessage(db, evt.ID.Value, evt.ChannelID.Value);
            }

            return Result.FromSuccess();
        }
    }

}
