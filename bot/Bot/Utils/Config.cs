using dotenv.net;
using Remora.Discord.Core;
using System;
using System.Collections.Generic;
using System.IO;

namespace Bot.Utils {
    static class Config {
        private static IDictionary<string, string> _env;

        static Config() {
            _env = DotEnv.Read(new DotEnvOptions(ignoreExceptions: false, probeLevelsToSearch: 4));
        }

        public static void CheckMinimalSettings() {
            if (GetULong("DISCORD_SERVER_ID") == null) {
                throw new InvalidOperationException("DISCORD_SERVER_ID not configured");
            }
            if (GetValue("DISCORD_BOT_TOKEN") == null) {
                throw new InvalidOperationException(
                    "No bot token has been provided. Set the DISCORD_BOT_TOKEN environment variable to a valid token."
                );
            }
            if (GetValue("DB_PATH") == null) {
                throw new InvalidOperationException("No sqlite database path specified in DB_PATH env.");
            }
        }

        private static string? GetValue(string key) => DotEnv.Read()[key];

        private static int? GetInt(string key) {
            var str = GetValue(key);
            _ = int.TryParse(str, out var value);
            return value;
        }

        private static ulong? GetULong(string key) {
            var str = GetValue(key);
            _ = ulong.TryParse(str, out var value);
            return value;
        }

        private static bool? GetBool(string key) {
            var str = GetValue(key);
            _ = bool.TryParse(str, out var value);
            return value;
        }

        public static string DbPath {
            get {
                var path = GetValue("DB_PATH")!;
                return Path.GetFullPath(path);
            }
        }
        public static string BotToken => GetValue("DISCORD_BOT_TOKEN")!;
        public static ulong GuildId => GetULong("DISCORD_SERVER_ID")!.Value;
        public static bool ShouldBotBugPeople => GetBool("DISCORD_BOT_BUGGING_PEOPLE") ?? false;

        public static string? WebsiteUrl => GetValue("WEBSITE_URL");

        public static string[] ChannelNames =>
            GetValue("DISCORD_SERVER_CHANNEL_NAMES")?.Split(',') ?? Array.Empty<string>();

        public static bool IsConfiguredGuild(ulong guildId) {
            return GuildId == guildId;
        }

        public static bool IsFromConfiguredChannels(Optional<ulong> guildId, Optional<string> channelName) {
            return (!guildId.IsDefined(out var gid) || GuildId == gid)
                && (!channelName.IsDefined(out var name) || Array.Exists(ChannelNames, n => n == name));
        }
    }
}
