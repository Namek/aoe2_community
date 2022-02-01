import datetime as dt
import pytest

from src.discord_bot.calendar_messages import analyze_message_content, cleanup_message
import src.discord_bot.calendar_messages as cal

message_datetime = dt.datetime.today()


def make_case(text):
    return f"bla bla\n{text}\nbla bla"


# @pytest.mark.only
def test_datetime():
    today = message_datetime.date()
    today_str = today.strftime('%d.%m.%Y')

    print(cal.REC_DATETIME.pattern)

    cases = [
        ["14.07.2021 18:30", "14.07.2021 18:30"],
        ["14.07.2021 r. 18:30", "14.07.2021 18:30"],
        ["14.07.2021   18:30", "14.07.2021 18:30"],
        ["14.07.2021 g. 18:30", "14.07.2021 18:30"],
        ["14.07.2021  godz 18:30", "14.07.2021 18:30"],
        ["15.07.2021 godzina 16:15", "15.07.2021 16:15"],
        ["2021.07.20 o 20:00", "20.07.2021 20:00"],
        ["17.08 20.00", f"17.08.{today.year} 20:00"],
        ["godzina 19:00 , 11.08.2021", "11.08.2021 19:00"],
        ["11.08.2022 środa 20", "11.08.2022 20:00"],
        ["Wtorek, 24.08.2021 21:30", "24.08.2021 21:30"],
        ["17.08.2021 Wtorek 20:00", "17.08.2021 20:00"],
        ["31.08 (wtorek) 16:00", f"31.08.{today.year} 16:00"],
        ["10-07 14.00", f"10.07.{today.year} 14:00"],
        ["1 Lipca, 21", f"01.07.{today.year} 21:00"],
        ["8 maja 2021\ngodz. 21:10", "08.05.2021 21:10"],
        ["8 maja\ngodz. 21:15", f"08.05.{today.year} 21:15"],
        ["Dzisiaj o 20:00", today_str + " 20:00"],
        ["Dzisiaj o 12", today_str + " 12:00"],
        ["25.08 środa 20:00", f"25.08.{today.year} 20:00"],
        ["24.08 wtorek 21:15", f"24.08.{today.year} 21:15"],
        ["2021.08.01 o 20:00", "01.08.2021 20:00"],
        # ["18:08 środa 20:00", f'18.08.{today.year} 20:00'],
        # ["15.07.2021 przełożone z godziny 16:15 na 17:10", "15.07.2021 17:10"],
    ]

    for [src, expectation] in cases:
        print(src)
        res = analyze_message_content(make_case(src), message_datetime)
        assert(res)
        print(res.datetime)
        datetime = res.datetime.strftime('%d.%m.%Y %H:%M') if res.datetime else ""
        print("res: " + datetime)
        assert(datetime == expectation)


def test_vs():
    cases = [
        ["RandomNickname vs @GivE_Me_A_BEER", ["RandomNickname", "@GivE_Me_A_BEER"]],
        ["MortiS vs AsAp | DSAWEr", ["MortiS", "AsAp | DSAWEr"]],
        ["AsAp | DSAWEr vs slawkens", ["AsAp | DSAWEr", "slawkens"]]
    ]

    for case in cases:
        res = analyze_message_content(make_case(case[0]), message_datetime)
        assert(res.vs == case[1])


def test_group():
    cases = [
        ["Red Black", "Red <-> Black"],
        ["Red <-> Black", "Red <-> Black"],
        ["Red<->Black", "Red <-> Black"],
        ["Red - Black", "Red <-> Black"],
        ["Mecz rotacyjny Blue <-> Green", "Blue <-> Green"],
        ["Gold Ants @Redi vs Greenie", "Gold"],
        ["Gold: @Redi vs Greenie", "Gold"],
        ["Gold Redi vs Greenie", "Gold"],
    ]

    for [input, expectation] in cases:
        res = analyze_message_content(make_case(input), message_datetime)
        assert(res.group == expectation)


def test_content():
    cases = [
        [
            "MortiS vs AsAp | DSAWEr\nMecz rotacyjny Red <-> Black <:ginAnt:800747442878021714>\n15.07.2021 godz. 17:10",
            "MortiS vs AsAp | DSAWEr\nMecz rotacyjny Red <-> Black",
        ],
        ["some ~~crossed out~~ text ~~continued ~ here ~~ ", 'some  text'],
        ["~~~ ~~", ""],
        ["~~some\nmultiline\nannouncement~~", ""],
    ]

    for [input, expectation] in cases:
        res = analyze_message_content(cleanup_message(input), message_datetime)
        assert(res.content == expectation)

