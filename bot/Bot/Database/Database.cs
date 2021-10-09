using Bot.Utils;
using SQLite;
using System;

namespace Bot.Database {
    public static class Database {

        public static SQLiteConnection NewConnection() {
            var connStr = new SQLiteConnectionString(Config.DbPath,
                SQLiteOpenFlags.ReadWrite | SQLiteOpenFlags.FullMutex,
                storeDateTimeAsTicks: false,
                dateTimeStringFormat: "yyyy'-'MM'-'dd' 'HH':'mm':'ss'.'fff"
            );
            var conn = new SQLiteConnection(connStr) {
                BusyTimeout = new TimeSpan(0, 0, 20)
            };
            conn.BeginTransaction();
            return conn;
        }

        public static void EnsureMigrationVersion(int expectedVersion) {
            using var db = NewConnection();

            var version = db.ExecuteScalar<int>("SELECT version FROM migration LIMIT 1;");

            if (version != expectedVersion) {
                throw new InvalidOperationException($"Database migration version is {version} while expected {expectedVersion}.");
            }
        }

        public static DbMessage? GetMessageByOriginalId(this SQLiteConnection db, long id) {
            return db.Find<DbMessage>(msg => msg.original_id == id);
        }

        public static DbMessage? UpdateMessageContent(this SQLiteConnection db, long msgId, string text, bool isParsed) {
            db.Execute(
                $@"
                    UPDATE {T.MESSAGES}
                    SET content = ?, is_parsed = ? 
                    WHERE {T.MESSAGES}.id = ?;
                ", text, isParsed ? 1 : 0, msgId);

            return db.Find<DbMessage>(msgId);
        }

        public static DbMessageSource GetOrCreateMessageSource(this SQLiteConnection db, long guildId, long channelId, string channelName) {
            var msgSource = db.Find<DbMessageSource>(src => src.guild_id == guildId && src.channel_id == channelId);

            if (msgSource == null) {
                msgSource = new DbMessageSource() {
                    guild_id = guildId,
                    channel_id = channelId,
                    channel_name = channelName
                };
                db.Insert(msgSource);
                msgSource.id = SQLite3.LastInsertRowid(db.Handle);
            }

            return msgSource;
        }

        public static DbCalendarEntry? GetCalendarEntryByMessageId(this SQLiteConnection db, long msgId) {
            return db.Find<DbCalendarEntry>(e => e.message_id == msgId);
        }

        public static void UpdateCalendarEntry(this SQLiteConnection db, long id, DateTime datetime, string description) {
            db.Execute($"UPDATE {T.CALENDAR} SET datetime = ?, description = ? WHERE id = ?", datetime, description, id);
        }

        public static void DeleteCalendarEntry(this SQLiteConnection db, long id) {
            db.Delete<DbCalendarEntry>(id);
        }

        public static void DeleteMessageWithCalendarEntries(this SQLiteConnection db, long msgId) {
            db.Execute($"DELETE FROM {T.CALENDAR} WHERE message_id = ?", msgId);
            db.Execute($"DELETE FROM {T.MESSAGES} WHERE id = ?", msgId);
        }

        public static void DeleteCalendarEventsWithNoSourceMessages(this SQLiteConnection db) {
            db.Execute(
                @$"DELETE FROM {T.CALENDAR} WHERE id NOT IN
                    (SELECT {T.CALENDAR}.id FROM {T.CALENDAR} JOIN {T.MESSAGES} ON {T.CALENDAR}.message_id=={T.MESSAGES}.id)
                ");
        }
    }
}
