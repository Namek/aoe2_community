using Bot.Database;
using Bot.Utils;
using Microsoft.Extensions.Logging;
using Remora.Discord.Core;
using SQLite;
using System;
using System.Threading.Tasks;
using static Bot.Database.Database;

namespace Bot.Calendar {
    static class MessageProcessing {
        public static async Task ProcessMessage(
            MessageAPIs apis, SQLiteConnection db, ulong messageId, string messageText,
            DateTime messageCreatedAt, ulong guildId, ulong channelId, string channelName
        ) {
            apis.logger.Log(LogLevel.Debug, $"ProcessMessage/1: {messageText}");
            var cleanedMentionsText = await MessageAnalysis.TransformMentionsToReadableForm(apis, messageText);
            apis.logger.Log(LogLevel.Debug, $"ProcessMessage/2: {cleanedMentionsText}");
            var text = MessageAnalysis.CleanupMessage(cleanedMentionsText);
            apis.logger.Log(LogLevel.Information, $"ProcessMessage/3: {text}");

            var dbMsg = db.GetMessageByOriginalId((long)messageId);
            var isContentNew = dbMsg == null || dbMsg.content != text;

            if (!isContentNew && (dbMsg?.is_parsed == 1)) {
                return;
            }

            var parsed = MessageAnalysis.AnalyzeMessageContent(text, messageCreatedAt);
            var isParsed = parsed != null && parsed.DateTime != null && !string.IsNullOrWhiteSpace(parsed.Content);

            var dbChannel = db.GetOrCreateMessageSource((long)guildId, (long)channelId, channelName);

            if (dbMsg == null) {
                dbMsg = new DbMessage() {
                    original_id = (long)messageId,
                    source_id = dbChannel.id,
                    content = text,
                    is_parsed = isParsed ? 1 : 0
                };
                db.Insert(dbMsg);
                dbMsg.id = SQLite3.LastInsertRowid(db.Handle);

            } else {
                db.UpdateMessageContent(dbMsg.id, text, isParsed);
            }

            var dbCalendar = db.GetCalendarEntryByMessageId(dbMsg.id);

            if (parsed != null && parsed.DateTime != null && parsed.Content != null) {
                string calendarEntryText = parsed.Versus != null && parsed.Group != null
                    ? $"{parsed.Group.Trim()} Ants\n{parsed.Versus.Value.Item1.Trim()} vs {parsed.Versus.Value.Item2.Trim()}"
                    : parsed.Content;

                var replyResult = await apis.channelAPI.CreateReactionAsync(new Snowflake(channelId), new Snowflake(messageId), "📅");

                if (dbCalendar == null) {
                    dbCalendar = new DbCalendarEntry() {
                        message_id = dbMsg.id,
                        datetime = parsed.DateTime.Value,
                        description = calendarEntryText
                    };
                    db.Insert(dbCalendar);
                    dbCalendar.id = SQLite3.LastInsertRowid(db.Handle);
                } else {
                    db.UpdateCalendarEntry(dbCalendar.id, parsed.DateTime.Value, calendarEntryText);
                }

                db.Commit();
            } else {
                if (dbCalendar != null) {
                    db.DeleteCalendarEntry(dbCalendar.id);
                }

                db.Commit();
                await apis.channelAPI.DeleteOwnReactionAsync(new Snowflake(channelId), new Snowflake(messageId), "📅");

                var channelMsg = await apis.channelAPI.GetChannelMessageAsync(new Snowflake(channelId), new Snowflake(messageId));
                var author = channelMsg.Entity.Author;
                var authorName = "<unknown>";
                if (channelMsg.IsSuccess) {
                    authorName = author?.Username ?? authorName;
                }

                apis.logger.LogError("I cannot parse this one by {author}:\n{text}", authorName, parsed);

                // when the message can't be parsed then ask user to edit it
                if (Config.ShouldBotBugPeople && isContentNew && author != null) {
                    var urlText = Config.WebsiteUrl != null ? @" {cfg.WEBSITE_URL}" : "";
                    var fixRequestMessage = @"Chcę umieścić wydarzenie do kalendarza{urlText}," +
                        @" ale nie widzę w tej wiadomości poprawnej daty i godziny." +
                        @" Zedytuj proszę swoją wiadomość na kanale {channel.name}:\n{message.content}\n\n" +
                        @"Przykład:\n\n10.08.2021 wtorek, godzina 20:00\nGreen Ants\n@Namek vs @Golik\n\n";
                    
                    var dmChannel = await apis.userAPI.CreateDMAsync(author.ID);
                    if (dmChannel.IsDefined()) {
                        await apis.channelAPI.CreateMessageAsync(dmChannel.Entity.ID, content: fixRequestMessage);
                    }
                }

            }
        }

        public static void DeleteMessage(SQLiteConnection db, ulong messageId, ulong channelId) {
            var dbMsg = db.GetMessageByOriginalId((long)messageId);

            if (dbMsg != null) {
                db.DeleteMessageWithCalendarEntries(dbMsg.id);
                db.Commit();
            }
        }

        public static void DeleteOldEvents(SQLiteConnection db) {
            db.DeleteCalendarEventsWithNoSourceMessages();
        }
    }
}
