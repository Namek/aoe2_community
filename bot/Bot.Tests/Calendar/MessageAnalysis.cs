using Bot.Calendar;
using System;
using Xunit;

namespace Bot.Tests.Calendar {
    public class MessageAnalysisTests {
        static readonly DateTime today;
        static readonly string today_str;

        static MessageAnalysisTests() {
            today = DateTime.Today.Date;
            today_str = today.ToString("dd.MM.yyyy");
        }

        static string MakeCase(string text) => $"blabla\n{text}\nblabla";

        [Theory]
        [ClassData(typeof(DateTimeTestCases))]
        public void Test_DateTime(string src, string expectation) {
            var res = MessageAnalysis.AnalyzeMessageContent(MakeCase(src), today);
            string datetime = res.DateTime.Value.ToString("dd.MM.yyyy H:mm");
            Assert.Equal(expectation, datetime);
        }

        class DateTimeTestCases : TheoryData<string, string> {
            public DateTimeTestCases() {
                Add(@"Green Ants 2
@Jan  vs @Czerw
19.02.2022 sobota godz. 20:00""", "19.02.2022 20:00");
                Add(@"blue ants 2
@vandrarek vs @Hadzik1990 
20.02.2022 niedziela 17:00", "20.02.2022 17:00");
                Add("14.07.2021 18:30", "14.07.2021 18:30");
                Add("14.07.2021   18:30", "14.07.2021 18:30");
                Add("14.07.2021 g. 18:30", "14.07.2021 18:30");
                Add("14.07.2021  godz 18:30", "14.07.2021 18:30");
                Add("15.07.2021 godzina 16:15", "15.07.2021 16:15");
                Add("2021.07.20 o 20:00", "20.07.2021 20:00");
                Add("17.08 20.00", $"17.08.{today.Year} 20:00");
                Add("godzina 19:00 , 11.08.2021", "11.08.2021 19:00");
                Add("11.08.2022 środa 20", "11.08.2022 20:00");
                Add("Wtorek, 24.08.2021 21:30", "24.08.2021 21:30");
                Add("17.08.2021 Wtorek 20:00", "17.08.2021 20:00");
                Add("31.08 (wtorek) 16:00", $"31.08.{today.Year} 16:00");
                Add("10-07 14.00", $"10.07.{today.Year} 14:00");
                Add("1 Lipca, 21", $"01.07.{today.Year} 21:00");
                Add("8 maja 2021\ngodz. 21:10", "08.05.2021 21:10");
                Add("8 maja\ngodz. 21:15", $"08.05.{today.Year} 21:15");
                Add("Dzisiaj o 20:00", today_str + " 20:00");
                Add("Dzisiaj o 12", today_str + " 12:00");
                Add("25.08 środa 20:00", $"25.08.{today.Year} 20:00");
                Add("24.08 wtorek 21:15", $"24.08.{today.Year} 21:15");
                Add("2021.08.01 o 20:00", "01.08.2021 20:00");
                Add("Gold Ants 16.04.2022 Sobota, godzina 20:00 @Barles vs @ElNoniro", "16.04.2022 20:00");
            }
        }

        [Theory]
        [ClassData(typeof(VersusTestCases))]
        public void Test_Versus(string src, string player1, string player2) {
            var res = MessageAnalysis.AnalyzeMessageContent(MakeCase(src), today);
            Assert.Equal(player1, res.Versus.Value.Item1);
            Assert.Equal(player2, res.Versus.Value.Item2);
        }

        class VersusTestCases : TheoryData<string, string, string> {
            public VersusTestCases() {
                Add("RandomNickname vs @GivE_Me_A_BEER", "RandomNickname", "@GivE_Me_A_BEER");
                Add("MortiS vs AsAp | DSAWEr", "MortiS", "AsAp | DSAWEr");
                Add("AsAp | DSAWEr vs slawkens", "AsAp | DSAWEr", "slawkens");
            }
        }

        [Theory]
        [ClassData(typeof(GroupTestCases))]
        public void Test_Group(string src, string expectation) {
            var res = MessageAnalysis.AnalyzeMessageContent(MakeCase(src), today);
            Assert.Equal(expectation, res.Group);
        }

        class GroupTestCases : TheoryData<string, string> {
            public GroupTestCases() {
                Add("Red Black", "Red <-> Black");
                Add("Red <-> Black", "Red <-> Black");
                Add("Red<->Black", "Red <-> Black");
                Add("Red - Black", "Red <-> Black");
                Add("Mecz rotacyjny Blue <-> Green", "Blue <-> Green");
                Add("Gold Ants @Redi vs Greenie", "Gold");
                Add("Gold: @Redi vs Greenie", "Gold");
                Add("Gold Redi vs Greenie", "Gold");
            }
        }

        [Theory]
        [ClassData(typeof(ContentTestCases))]
        public async void Test_Content(string src, string expectation) {
            var res = MessageAnalysis.AnalyzeMessageContent(MessageAnalysis.CleanupMessage(src), today);
            Assert.Equal(expectation, res.Content);
        }

        class ContentTestCases : TheoryData<string, string> {
            public ContentTestCases() {
                Add(
                    "MortiS vs AsAp | DSAWEr\nMecz rotacyjny Red <-> Black <:ginAnt:800747442878021714>\n15.07.2021 godz. 17:10",
                    "MortiS vs AsAp | DSAWEr\nMecz rotacyjny Red <-> Black");
                Add("some ~~crossed out~~ text ~~continued ~ here ~~ ", "some  text");
                Add("~~~ ~~", "");
                Add("~~some\nmultiline\nannouncement~~", "");
            }
        }
    }
}
