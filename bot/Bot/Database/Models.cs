#pragma warning disable IDE1006 // Naming Styles

using SQLite;
using System;

namespace Bot.Database {
    interface T {
        public const string MESSAGES = "messages";
        public const string MESSAGE_SOURCES = "message_sources";
        public const string CALENDAR = "calendar";
    }

    public abstract record WithTimestamps {
        [NotNull]
        public DateTime created_at { get; set; }
        [NotNull]
        public DateTime modified_at { get; set; }

        public WithTimestamps() {
            created_at = DateTime.Now;
            modified_at = DateTime.Now;
        }
    }

    [Table(T.MESSAGES)]
    public record DbMessage : WithTimestamps {
        [PrimaryKey, AutoIncrement]
        public long id { get; set; }
        [NotNull]
        public long original_id { get; set; }

        [NotNull]
        public long source_id { get; set; }

        [NotNull]
        public string content { get; set; }

        [NotNull]
        public int is_parsed { get; set; }
    }

    [Table(T.MESSAGE_SOURCES)]
    public record DbMessageSource : WithTimestamps {
        [PrimaryKey, AutoIncrement]
        public long id { get; set; }
        [NotNull]
        public long guild_id { get; set; }
        [NotNull]
        public long channel_id { get; set; }
        [NotNull]
        public string channel_name { get; set; }
    }

    [Table(T.CALENDAR)]
    public record DbCalendarEntry : WithTimestamps {
        [PrimaryKey, AutoIncrement]
        public long id { get; set; }
        [NotNull]
        public long message_id { get; set; }
        [NotNull]
        public DateTime datetime { get; set; }
        [NotNull]
        public string description { get; set; }
    }

}
