using Remora.Discord.Core;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace Bot.Calendar {
    public static class MessageAnalysis {
        static readonly string[] ANT_GROUP_NAMES = new string[] { "Gold", "Red", "Black", "Blue", "Green" };

        static readonly Regex
            REC_ANT_GROUP_NAME = new(@$"\b({string.Join("|", ANT_GROUP_NAMES)})\b", RegexOptions.IgnoreCase),
            REC_VS_1 = new(@"(@[^\n]+) +vs +([^\n]+)"),
            REC_VS_2 = new(@"([^\n]+) +vs +([^\n]+)"),
            REC_VS_3 = new(@"([^\n ]+) +vs +([^\n]+)");

        static readonly Func<int, string> RE_DATE_NUMBERED = (int i) => @"(" +
            @$"(?<year{i}1>\d\d\d\d).(?<month{i}1>\d\d).(?<day{i}1>\d\d?))|" +
            @$"((?<day{i}2>\d\d?)[.\/-](?<month{i}2>\d\d).(?<year{i}2>\d\d\d\d))|" +
            @$"((?<_day_or_month{i}1>\d\d?)[.\/-](?<_day_or_month{i}2>\d?\d))";

        static readonly string[] RE_MONTH_NAMES = new string[]{
            @"(sty(cze[nń]|cznia)?|jan(uary)?)",
            @"(lut(y|ego)|feb(ruary))",
            @"(mar(zec|ca)?|mar(ch)?)",
            @"(kwie(cie[nń]|tnia)?|apr(il)?)",
            @"(maja?|may)",
            @"(cze(rwiec|rwca)?|june?)",
            @"(lip(iec|ca)?|july?)",
            @"(sie(rpie[nń]|rpnia)?|aug(ust)?)",
            @"(wrz(esie[nń]|e[sś]nia)?|(sep(tember)?|spt))",
            @"(pa[zź](dziernika?)?|oct(ober)?)",
            @"(lis(topad|topada)?|nov(ember)?)",
            @"(gru(dzień|dnia)?|dec(ember)?)"
        };

        static readonly Regex[] REC_MONTH_NAMES = RE_MONTH_NAMES.Select(m => new Regex(m, RegexOptions.IgnoreCase)).ToArray();

        static readonly Func<int, string> RE_DATE_VERBAL = (int i) =>
            @$"(?<day{i}>\d\d?).*?(?<_month_name{i}>" + string.Join("|", RE_MONTH_NAMES) + @$")([^0-9]*(?<year{i}>\d\d\d\d))?";

        static readonly Func<int, string> RE_TIME = (int i) =>
            @$"((?<hour{i}1>\d\d?)[:.](?<minutes{i}>\d\d)|(?<hour{i}2>\d\d))";

        static readonly string[] RE_RELATIVE_EXPR = new string[] {
            @"dzisiaj|dziś|today", @"jutro|tomorrow", @"pojutrze|after tomorrow"
        };

        static readonly Regex[] REC_RELATIVE_EXPR = RE_RELATIVE_EXPR.Select(r => new Regex(r, RegexOptions.IgnoreCase)).ToArray();

        static readonly Regex REC_DATETIME = new(
            @"(" +
                @$"({RE_DATE_VERBAL(3)})" +
                @"[^0-9]+" +
                @$"({RE_TIME(3)})" +
            @")|(" +
                @$"({string.Join('|', RE_RELATIVE_EXPR)})" +
                @"[^0-9]+" +
                @$"({RE_TIME(4)})" +
            @")|(" +
                @$"({RE_DATE_NUMBERED(1)})" +
                @"[^0-9]+" +
                @$"({RE_TIME(1)})" +
            @")|(" +
                @$"({RE_TIME(2)})" +
                @"[^0-9]+" +
                @$"({RE_DATE_NUMBERED(2)})" +
            @")",
            RegexOptions.IgnoreCase | RegexOptions.Compiled | RegexOptions.Singleline
        );

        static readonly string[] RE_GROUPS = new Regex(@"\(\?<([^>]+)")
            .Matches(REC_DATETIME.ToString()).Select(m => m.Groups[1].Value).ToArray();
        static readonly string[] RE_GROUPS_YEAR = RE_GROUPS.Where(x => x.StartsWith("year")).ToArray();
        static readonly string[] RE_GROUPS_MONTH = RE_GROUPS.Where(x => x.StartsWith("month")).ToArray();
        static readonly string[] RE_GROUPS_DAY = RE_GROUPS.Where(x => x.StartsWith("day")).ToArray();
        static readonly string[] RE_GROUPS_HOUR = RE_GROUPS.Where(x => x.StartsWith("hour")).ToArray();
        static readonly string[] RE_GROUPS_MINS = RE_GROUPS.Where(x => x.StartsWith("minutes")).ToArray();
        static readonly string[] RE_GROUPS_MONTH_NAMES = RE_GROUPS.Where(x => x.StartsWith("_month_name")).ToArray();
        static readonly string[] RE_GROUPS_DAY_OR_MONTH = RE_GROUPS.Where(x => x.StartsWith("_day_or_month")).ToArray();

        static readonly Regex REC_CUSTOM_EMOJI = new(@"<:[a-zA-Z]+:[0-9]+>");
        static readonly Regex REC_STRIKED_TEXT = new(@"(?<![.+?])(~{2})(?!~~)(.+?)(?<!~~)\1(?![.+?])", RegexOptions.IgnoreCase | RegexOptions.Singleline);


        public record ParsedMessage(string Content, DateTime? DateTime, string? Group, (string, string)? Versus);


        public static ParsedMessage? AnalyzeMessageContent(string text, DateTime messageDateTime) {
            var messageDate = messageDateTime.Date;

            string? group = null;
            string content = text;
            DateTime? datetime = null;

            (string, string)? vs = null;
            Match? vsMatch = null;
            foreach (var vsRegex in new[]{REC_VS_1, REC_VS_2, REC_VS_3}) {
                vsMatch = vsRegex.Match(text);
                if (vsMatch.Groups.Count >= 2) {
                    vs = (vsMatch.Groups[1].Value, vsMatch.Groups[2].Value);
                    break;
                }
            }

            var textForDates = text;
            if (vs != null && vsMatch != null) {
                textForDates = text.Replace(vsMatch.Groups[0].Value, "");
            }

            var foundGroups = REC_ANT_GROUP_NAME.Matches(text).Select(m => m.Groups[1].Value).ToArray();

            if (foundGroups.Length == 1) {
                group = foundGroups[0];
            } else if (foundGroups.Length == 2) {
                group = $"{foundGroups[0]} <-> {foundGroups[1]}";
            }

            var datetimeMatch = REC_DATETIME.Match(textForDates);

            if (datetimeMatch.Success) {
                var year_str = GetFirstValue(datetimeMatch, RE_GROUPS_YEAR);
                var month_str = GetFirstValue(datetimeMatch, RE_GROUPS_MONTH);
                var day_str = GetFirstValue(datetimeMatch, RE_GROUPS_DAY);
                var hour_str = GetFirstValue(datetimeMatch, RE_GROUPS_HOUR);
                var mins_str = GetFirstValue(datetimeMatch, RE_GROUPS_MINS);
                var monthName = GetFirstValue(datetimeMatch, RE_GROUPS_MONTH_NAMES);
                var dayOrMonth_str = RE_GROUPS_DAY_OR_MONTH.Aggregate(new List<string>(), (acc, groupName) => {
                    var m = datetimeMatch.Groups[groupName];
                    if (m != null && m.Success)
                        acc.Add(m.Value);

                    return acc;
                });

                int? year, month, day, hour, mins;
                year = year_str != null ? int.Parse(year_str) : null;
                month = month_str != null ? int.Parse(month_str) : null;
                day = day_str != null ? int.Parse(day_str) : null;
                hour = hour_str != null ? int.Parse(hour_str) : null;
                mins = mins_str != null ? int.Parse(mins_str) : null;

                if ((day == null || month == null) && dayOrMonth_str.Count == 2) {
                    day = int.Parse(dayOrMonth_str[0].ToString());
                    month = int.Parse(dayOrMonth_str[1].ToString());
                }

                if (monthName != null) {
                    int idx = 0;
                    foreach (var r in REC_MONTH_NAMES) {
                        if (r.IsMatch(monthName)) {
                            month = idx + 1;
                            break;
                        }
                        idx += 1;
                    }
                } else if (month_str != null) {
                    month = int.Parse(month_str);
                }

                if (year == null && month != null && day != null) {
                    year = messageDate.Year;
                }

                DateTime? date = null;
                if (year != null && month != null && day != null) {
                    date = new DateTime(year.Value, month.Value, day.Value);
                } else {
                    int idx = 0;
                    foreach (var r in REC_RELATIVE_EXPR) {
                        if (r.IsMatch(datetimeMatch.Groups[0].Value)) {
                            date = new DateTime(messageDate.Year, messageDate.Month, messageDate.Day);
                            date = date.Value.AddDays(idx);
                            break;
                        }
                        idx += 1;
                    }
                }

                if (mins == null) {
                    mins = 0;
                }

                TimeSpan? timeDelta = hour != null ? new TimeSpan(0, hour.Value, mins.Value, 0, 0) : null;

                if (date != null && timeDelta != null) {
                    content = content.Replace(datetimeMatch.Groups[0].Value, "").Trim();
                    datetime = date.Value + timeDelta.Value;
                }
            }

            return new ParsedMessage(content, datetime, group, vs);
        }

        private static string? GetFirstValue(Match regexMatch, string[] groupNames) {
            foreach (var groupName in groupNames) {
                var val = regexMatch.Groups[groupName];
                if (val != null && val.Success)
                    return val.Value;
            }
            return null;
        }

        public static string CleanupMessage(string text) {
            // remove stuff like <:ginAnt:800747442878021714>
            text = REC_CUSTOM_EMOJI.Replace(text, "");

            // remove striked-out text

            foreach (var match in REC_STRIKED_TEXT.Matches(text).ToArray()) {
                if (match!.Success) {
                    text = text.Replace(match.Value, "");
                }
            }

            return text.Trim();
        }

        static readonly Regex REC_MENTION_CHANNEL = new(@"<#([^>]+)>");
        static readonly Regex REC_MENTION_MEMBER = new(@"<@!?([^>]+)>");

        /**
         * Mentions are transformed into the way the client shows it. e.g. `<#id>` will transform into `#name`.
         */
        public static async Task<string> TransformMentionsToReadableForm(MessageAPIs apis, string text) {
            foreach (Match match in REC_MENTION_CHANNEL.Matches(text)) {
                string id_str = match.Groups[1].Value;
                if (ulong.TryParse(id_str, out var id)) {
                    var channel = await apis.channelAPI.GetChannelAsync(new Snowflake(id));
                    if (channel.IsSuccess) {
                        text = text.Replace(match.Groups[0].Value, $"#{channel.Entity.Name.Value}");
                    }
                }
            }

            foreach (Match match in REC_MENTION_MEMBER.Matches(text)) {
                string id_str = match!.Groups[1].Value;
                if (ulong.TryParse(id_str, out var id)) {
                    var user = await apis.userAPI.GetUserAsync(new Snowflake(id));
                    if (user.IsSuccess) {
                        text = text.Replace(match.Groups[0].Value, $"@{user.Entity.Username}");
                    }
                }
            }

            return text;
        }
    }
}
