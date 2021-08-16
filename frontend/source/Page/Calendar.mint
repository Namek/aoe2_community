component Page.Calendar {
  const MONTH_NAMES = ["Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec", "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
  const DAY_NAMES = ["Pon", "Wt", "Śr", "Czw", "Pt", "Sob", "Nd"]

  connect Calendar exposing { today, currentMonth, currentYear }

  style app {
    justify-content: center;
    flex-direction: column;
    align-items: center;
    display: flex;
  }

  style currentMonth {
    font-size: 2em;
    margin-bottom: 1em;
    text-align: center;
    font-weight: bold;
  }

  style month {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr 1fr;
    grid-template-rows: auto;

    max-width: 90vw;
    width: 100%;
    justify-items: center;
    align-items: center;

    * {
      min-width: 100%;
    }
  }

  style day {
    display: flex;
    flex-direction: column;
    min-height: 100px;
    height: 100%;
    align-items: center;
    padding: 5px;
    border-bottom: 1px solid black;
    border-right: 1px solid black;
    overflow: hidden;

    &:nth-child(7n + 1) {
      border-left: 1px solid black;
    }

    &:nth-child(8) {
      border-top-left-radius: 5px;
    }

    &:nth-child(8),
    &:nth-child(9),
    &:nth-child(10),
    &:nth-child(11),
    &:nth-child(12),
    &:nth-child(13),
    &:nth-child(14) {
      border-top: 1px solid black;
    }

    &:nth-child(14) {
      border-top-right-radius: 5px;
    }

    &:last-child {
      border-bottom-right-radius: 5px;
    }
  }

  style prev {
    color: #ccc;
  }

  style name {
    text-align: center;
    font-weight: bold;
  }

  style event (colorId : number) {
    font-size: 0.8em;

    if (colorId == 1) {
      background-color: #334A61;
    } else {
      background-color: #476787;
    }

    border-radius: 3px;
    color: white;
    padding: 0 3px;
    margin-bottom: 3px;
    font-weight: normal;
    white-space: pre-wrap;
  }

  style eventTime {
    color: #ddd;
    float: left;
  }

  fun componentDidMount {
    if (@ENABLE_CALENDAR == "1") {
      Calendar.init()
    } else {
      Promise.never()
    }
  }

  fun render : Html {
    try {
      firstMonthDay =
        Time.from(currentYear, currentMonth, 1)

      <div::app>
        <div::currentMonth>
          <{ "#{MONTH_NAMES[currentMonth - 1] or ""} #{currentYear}" }>

          <div>
            <button onClick={Calendar.setPrevMonth}>
              "<"
            </button>

            <button onClick={Calendar.setNextMonth}>
              ">"
            </button>
          </div>
        </div>

        <div::month>
          for (day of DAY_NAMES) {
            <div::name>
              <{ day }>
            </div>
          }

          for (day of Calendar.lastDaysFromPreviousMonth(currentMonth, currentYear)) {
            <div::day::prev>
              <{ "#{day}" }>

              <{ renderEvents(day, currentMonth - 1, currentYear) }>
            </div>
          }

          for (day of Time.range(firstMonthDay, Time.endOf("month", firstMonthDay))) {
            <div::day>
              <{ Time.format("d", day) }>

              <{ renderEvents(Time.dayNum(day), currentMonth, currentYear) }>
            </div>
          }
        </div>
      </div>
    }
  }

  fun renderEvents (day : Number, givenMonth : Number, givenYear : Number) : Html {
    try {
      {month, year} =
        if (givenMonth == 0) {
          {12, givenYear - 1}
        } else {
          {givenMonth, givenYear}
        }

      hash =
        Calendar.hashDate(day, month, year)

      events =
        Map.get(hash, Calendar.daysData) or []

      <div>
        for (evt of events) {
          <div::event(evt.sourceId)>
            <span::eventTime>
              <{ Time.format("HH:ss", evt.datetime) }>
            </span>

            "#{evt.name}"
          </div>
        }
      </div>
    }
  }
}
