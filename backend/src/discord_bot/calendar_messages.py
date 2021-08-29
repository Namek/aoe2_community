import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

from dateutil.relativedelta import relativedelta

ANT_GROUP_NAMES = ['Gold', 'Red', 'Black', 'Blue', 'Green']
ANT_GROUP_NAMES_SMALL = [name.lower() for name in ANT_GROUP_NAMES]
REC_VS = re.compile(r'([^\n]+) +vs +([^\n]+)')
REC_YEAR = re.compile(r'\d\d\d\d')
RE_DATE_NUMBERED = lambda i: r'(' +\
    rf'(?P<year{i}1>\d\d\d\d).(?P<month{i}1>\d\d).(?P<day{i}1>\d\d?))|' +\
    rf'((?P<day{i}2>\d\d?)[.\/-](?P<month{i}2>\d\d).(?P<year{i}2>\d\d\d\d))|' +\
    rf'((?P<_day_or_month{i}1>\d\d?)[.\/-](?P<_day_or_month{i}2>\d?\d))'

RE_MONTH_NAMES = [
    '(sty(cze[nń]|cznia)?|jan(uary)?)',
    '(lut(y|ego)|feb(ruary))',
    '(mar(zec|ca)?|mar(ch)?)',
    '(kwie(cie[nń]|tnia)?|apr(il)?)',
    '(maja?|may)',
    '(cze(rwiec|rwca)?|june?)',
    '(lip(iec|ca)?|july?)',
    '(sie(rpie[nń]|rpnia)?|aug(ust)?)',
    '(wrz(esie[nń]|e[sś]nia)?|(sep(tember)?|spt))',
    '(pa[zź](dziernika?)?|oct(ober)?)',
    '(lis(topad|topada)?|nov(ember)?)',
    '(gru(dzień|dnia)?|dec(ember)?)'
]

REC_MONTH_NAMES = [re.compile(r, flags=re.IGNORECASE) for r in RE_MONTH_NAMES]
RE_DATE_VERBAL = lambda i:\
    rf'(?P<day{i}>\d\d?).*?(?P<_month_name{i}>' + '|'.join(RE_MONTH_NAMES) + rf')([^0-9]*(?P<year{i}>\d\d\d\d))?'
RE_TIME = lambda i: rf'((?P<hour{i}1>\d\d?)[:.](?P<minutes{i}>\d\d)|(?P<hour{i}2>\d\d))'
RE_RELATIVE_EXPR = [r'dzisiaj|today', r'jutro|tomorrow', r'pojutrze|after tomorrow']
REC_RELATIVE_EXPR = [re.compile(r, flags=re.IGNORECASE) for r in RE_RELATIVE_EXPR]
REC_DATETIME = re.compile(
    r'(' +
        r'(' + RE_DATE_VERBAL(3) + r')' +
        r'[^0-9]+' +
        r'(' + RE_TIME(3) + r')' +
    r')|(' +
        r'(' + '|'.join(RE_RELATIVE_EXPR) + r')' +
        r'[^0-9]+' +
        r'(' + RE_TIME(4) + r')' +
    r')|(' +
        r'(' + RE_DATE_NUMBERED(1) + r')' +
        r'[^0-9]+' +
        r'(' + RE_TIME(1) + r')' +
    r')|(' +
        r'(' + RE_TIME(2) + r')' +
        r'[^0-9]+' +
        r'(' + RE_DATE_NUMBERED(2) + r')' +
    r')',
    flags=re.IGNORECASE | re.DOTALL
)
RE_GROUPS = [x.group(1) for x in re.finditer(r'\?P<([^>]+)', REC_DATETIME.pattern)]
RE_GROUPS_YEAR = [x for x in RE_GROUPS if x.startswith('year')]
RE_GROUPS_MONTH = [x for x in RE_GROUPS if x.startswith('month')]
RE_GROUPS_DAY =  [x for x in RE_GROUPS if x.startswith('day')]
RE_GROUPS_HOUR = [x for x in RE_GROUPS if x.startswith('hour')]
RE_GROUPS_MINS = [x for x in RE_GROUPS if x.startswith('minutes')]
RE_GROUPS_MONTH_NAMES = [x for x in RE_GROUPS if x.startswith('_month_name')]
RE_GROUPS_DAY_OR_MONTH = [x for x in RE_GROUPS if x.startswith('_day_or_month')]

ROTATING_MATCH_PREFIX = "Rotacyjny: "
RE_CUSTOM_EMOJI = re.compile(r'<:[a-zA-Z]+:[0-9]+>')


@dataclass
class ParsedMessage:
    content: Optional[str]
    datetime: Optional[datetime]
    group: Optional[str]
    vs: Optional[List[str]]


def cleanup_message(text: str) -> str:
    # remove stuff like <:ginAnt:800747442878021714>
    text = RE_CUSTOM_EMOJI.sub("", text)

    match = re.findall(r"(?<![.+?])(~{2})(?!~~)(.+?)(?<!~~)\1(?![.+?])", text)
    if match:
        for _, m in match:
            text = re.sub(f"~~{re.escape(m)}~~", '', text)
        
    return text.strip()


def analyze_message_content(text: str, message_datetime: datetime) -> Optional[ParsedMessage]:
    try:
        return _analyze_message_content(text, message_datetime)
    except:
        return None


def _analyze_message_content(text: str, message_datetime: datetime) -> ParsedMessage:
    text_small = text.lower()
    message_date = message_datetime.date()

    (group, date, time, content) = (None, None, None, text)
    vs = REC_VS.search(text)
    vs = [vs.group(1), vs.group(2)] if vs else None

    found_groups = []
    for gi in range(0, len(ANT_GROUP_NAMES)):
        if ANT_GROUP_NAMES_SMALL[gi] in text_small:
            found_groups.append(ANT_GROUP_NAMES[gi])

    if len(found_groups) == 1:
        group = found_groups[0]

    if len(found_groups) == 2:
        group = f"{ROTATING_MATCH_PREFIX}{found_groups[0]} <-> {found_groups[1]}"

    dt = REC_DATETIME.search(text)

    if dt:
        year_str = get_first_val(dt, RE_GROUPS_YEAR)
        month_str = get_first_val(dt, RE_GROUPS_MONTH)
        day_str = get_first_val(dt, RE_GROUPS_DAY)
        hour_str = get_first_val(dt, RE_GROUPS_HOUR)
        mins_str = get_first_val(dt, RE_GROUPS_MINS)
        month_name = get_first_val(dt, RE_GROUPS_MONTH_NAMES)
        day_or_month_str = [m for g in RE_GROUPS_DAY_OR_MONTH if (m := dt.group(g))]

        year = int(year_str) if year_str else None
        month = int(month_str) if month_str else None
        day = int(day_str) if day_str else None
        hour = int(hour_str) if hour_str else None
        mins = int(mins_str) if mins_str else None

        if not year:
            year = message_date.year

        if (not day or not month) and len(day_or_month_str) == 2:
            day = int(day_or_month_str[0])
            month = int(day_or_month_str[1])
    
        if month_name:
            for idx, r in enumerate(REC_MONTH_NAMES):
                if r.search(month_name):
                    month = idx+1
                    break
        elif month_str:
            month = int(month_str)
        
        if year and month and day:
            date = datetime(year, month, day)
        else:
            for idx, r in enumerate(REC_RELATIVE_EXPR):
                if r.match(dt.group(0)):
                    date = datetime(year=message_date.year, month=message_date.month, day=message_date.day)
                    date += relativedelta(day=idx)
                    break

        if not mins:
            mins = 0

        time_delta = timedelta(hours=hour, minutes=mins) if hour else None

        if date and time_delta:
            content = content.replace(dt.group(0), '').strip()
            dt = date + time_delta
        else:
            dt = None

    return ParsedMessage(content, dt, group, vs)


def get_first_val(regex_match, group_names: List[str]):
    vals = [regex_match.group(g) for g in group_names]
    for val in vals:
        if val:
            return val
    return None
